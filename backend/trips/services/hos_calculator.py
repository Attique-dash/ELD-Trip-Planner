"""
HOS (Hours of Service) rules engine.

Implements the FMCSA property-carrying driver rules under the assumptions
given in the assessment:
  - 70 hours / 8 days cycle
  - No adverse driving conditions exception
  - Fuel stop at least once every 1,000 miles
  - 1 hour each for pickup and drop-off

This module is pure logic (no network calls) so it can be unit tested
in isolation from the routing/geocoding services.
"""

from dataclasses import dataclass, field
from typing import List

# ---- Rule constants (all in hours unless noted) ----
DRIVING_LIMIT = 11          # max driving hours within a duty window
WINDOW_LIMIT = 14           # max on-duty window (drive + on-duty-not-driving)
BREAK_AFTER_DRIVING = 8     # must take a 30-min break after this much driving
BREAK_DURATION = 0.5
OFF_DUTY_REQUIRED = 10      # consecutive hours off duty to reset daily clocks
CYCLE_LIMIT = 70            # hours on duty allowed in 8 days
RESTART_HOURS = 34          # consecutive hours off duty to reset the cycle
FUEL_INTERVAL_MILES = 1000
FUEL_DURATION = 0.5         # assumption: 30 min per fuel stop
PICKUP_DURATION = 1
DROPOFF_DURATION = 1
DEFAULT_AVG_SPEED_MPH = 55  # used if the routing API doesn't return a duration


@dataclass
class Segment:
    """One block of time on the ELD log (a single duty status)."""
    status: str        # "off_duty" | "sleeper_berth" | "driving" | "on_duty_not_driving"
    start_hour: float  # hours since the trip's clock started at 0
    end_hour: float
    label: str = ""

    @property
    def duration(self):
        return round(self.end_hour - self.start_hour, 4)


@dataclass
class TripPlan:
    segments: List[Segment] = field(default_factory=list)
    total_driving_hours: float = 0.0
    total_distance_miles: float = 0.0
    total_trip_hours: float = 0.0
    fuel_stops: int = 0
    days: int = 0
    warnings: List[str] = field(default_factory=list)


class HOSCalculator:
    """
    Builds a full duty-status timeline for a trip made of two driving legs:
      leg 1: current location -> pickup location
      leg 2: pickup location  -> dropoff location
    with a 1-hour on-duty stop at pickup, fuel stops every 1,000 miles,
    and a 1-hour on-duty stop at dropoff, all while respecting the
    11-hr / 14-hr / 30-min-break / 70-hr-8-day / 34-hr-restart rules.
    """

    def __init__(self, current_cycle_used_hours: float):
        # hours already on-duty in the current rolling 8-day / 70-hr window
        self.cycle_used = max(0.0, float(current_cycle_used_hours))
        self.clock = 0.0                # absolute hours since simulation start
        self.window_start = 0.0         # start of current 14-hr on-duty window
        self.driving_in_window = 0.0    # driving hours used in current window
        self.driving_since_break = 0.0  # driving hours since last 30-min break
        self.segments: List[Segment] = []
        self.warnings: List[str] = []

    # ---- internal helpers -------------------------------------------------

    def _add(self, status, duration, label=""):
        if duration <= 0:
            return
        start = self.clock
        end = self.clock + duration
        self.segments.append(Segment(status, start, end, label))
        self.clock = end

    def _start_new_duty_window(self):
        """Reset the 11-hr / 14-hr clocks. Used after a qualifying off-duty period."""
        self.window_start = self.clock
        self.driving_in_window = 0.0
        self.driving_since_break = 0.0

    def _take_off_duty(self, hours, label):
        self._add("off_duty", hours, label)
        self.cycle_used = max(0.0, self.cycle_used - 0)  # off duty doesn't add hours
        if hours >= RESTART_HOURS:
            self.cycle_used = 0.0
            self.warnings.append(
                f"34-hour restart taken at hour {round(self.clock - hours, 1)} "
                "- cycle hours reset to 0."
            )
        if hours >= OFF_DUTY_REQUIRED:
            self._start_new_duty_window()

    def _ensure_can_start_on_duty(self):
        """If cycle is maxed out, force a 34-hr restart before continuing."""
        if self.cycle_used >= CYCLE_LIMIT:
            self._take_off_duty(RESTART_HOURS, "Mandatory 34-hour restart (70-hr/8-day limit reached)")

    def _on_duty_not_driving(self, hours, label):
        self._ensure_can_start_on_duty()
        # on-duty-not-driving still counts toward the 14-hr window and cycle,
        # but not toward the 11-hr driving limit or the 8-hr break clock
        remaining_window = WINDOW_LIMIT - (self.clock - self.window_start)
        if remaining_window <= 0:
            self._take_off_duty(OFF_DUTY_REQUIRED, "Required 10-hr off duty (14-hr window used up)")
            remaining_window = WINDOW_LIMIT
        chunk = min(hours, remaining_window)
        self._add("on_duty_not_driving", chunk, label)
        self.cycle_used += chunk
        leftover = hours - chunk
        if leftover > 0:
            self._take_off_duty(OFF_DUTY_REQUIRED, "Required 10-hr off duty (14-hr window used up)")
            self._on_duty_not_driving(leftover, label)

    def _drive(self, hours_needed, distance_label):
        """Drive `hours_needed` hours total for this leg, inserting breaks,
        10-hr resets, and 34-hr restarts as required by the rules."""
        remaining = hours_needed
        while remaining > 1e-6:
            self._ensure_can_start_on_duty()

            room_in_window = WINDOW_LIMIT - (self.clock - self.window_start)
            room_in_driving_limit = DRIVING_LIMIT - self.driving_in_window
            room_before_break = BREAK_AFTER_DRIVING - self.driving_since_break
            room_in_cycle = CYCLE_LIMIT - self.cycle_used

            # whichever constraint is tightest determines how much we can drive now
            chunk = min(remaining, room_in_window, room_in_driving_limit,
                        room_before_break, room_in_cycle)

            if chunk <= 1e-6:
                # can't drive right now - figure out why and resolve it
                if room_in_cycle <= 1e-6:
                    self._take_off_duty(RESTART_HOURS, "Mandatory 34-hour restart (70-hr/8-day limit reached)")
                elif room_before_break <= 1e-6:
                    self._add("off_duty", BREAK_DURATION, "Required 30-minute break")
                    self.driving_since_break = 0.0
                    self.cycle_used += BREAK_DURATION
                elif room_in_window <= 1e-6 or room_in_driving_limit <= 1e-6:
                    self._take_off_duty(OFF_DUTY_REQUIRED, "Required 10-hr off duty (daily limit reached)")
                continue

            self._add("driving", chunk, distance_label)
            self.driving_in_window += chunk
            self.driving_since_break += chunk
            self.cycle_used += chunk
            remaining -= chunk

    # ---- public API ---------------------------------------------------

    def plan(self, leg1_miles, leg1_hours, leg2_miles, leg2_hours) -> TripPlan:
        self._ensure_can_start_on_duty()

        # --- Leg 1: current location -> pickup ---
        self._drive(leg1_hours, "Driving to pickup location")

        # --- Pickup stop (1 hr on-duty, not driving) ---
        self._on_duty_not_driving(PICKUP_DURATION, "At pickup location (loading)")

        # --- Leg 2: pickup -> dropoff, with fuel stops every 1,000 miles ---
        fuel_stops = int(leg2_miles // FUEL_INTERVAL_MILES)
        if leg2_miles > 0 and fuel_stops > 0:
            hours_per_segment = leg2_hours / (fuel_stops + 1)
            miles_per_segment = leg2_miles / (fuel_stops + 1)
            for i in range(fuel_stops):
                self._drive(hours_per_segment, f"Driving toward dropoff (leg {i + 1})")
                self._on_duty_not_driving(FUEL_DURATION, "Fuel stop")
            self._drive(hours_per_segment, "Driving toward dropoff (final leg)")
        else:
            self._drive(leg2_hours, "Driving to dropoff location")

        # --- Dropoff stop (1 hr on-duty, not driving) ---
        self._on_duty_not_driving(DROPOFF_DURATION, "At dropoff location (unloading)")

        total_driving = sum(s.duration for s in self.segments if s.status == "driving")
        total_miles = leg1_miles + leg2_miles
        days = int(self.clock // 24) + 1

        return TripPlan(
            segments=self.segments,
            total_driving_hours=round(total_driving, 2),
            total_distance_miles=round(total_miles, 1),
            total_trip_hours=round(self.clock, 2),
            fuel_stops=fuel_stops,
            days=days,
            warnings=self.warnings,
        )


def split_segments_into_days(segments: List[Segment]):
    """
    Splits a flat list of segments (which may span multiple 24-hour periods)
    into one list per calendar day, cutting any segment that crosses
    midnight into two pieces. This is what each individual paper log sheet
    needs, since one log sheet = one 24-hour period.
    """
    days = {}
    for seg in segments:
        start = seg.start_hour
        end = seg.end_hour
        while start < end:
            day_index = int(start // 24)
            day_end_boundary = (day_index + 1) * 24
            piece_end = min(end, day_end_boundary)
            days.setdefault(day_index, []).append(
                Segment(seg.status, start - day_index * 24, piece_end - day_index * 24, seg.label)
            )
            start = piece_end
    return [days[k] for k in sorted(days.keys())]


def compute_totals_by_status(day_segments: List[Segment]):
    """Returns total hours per duty status for one day's segments (for the
    'Total Hours' column on the right side of the paper log)."""
    totals = {"off_duty": 0.0, "sleeper_berth": 0.0, "driving": 0.0, "on_duty_not_driving": 0.0}
    for seg in day_segments:
        totals[seg.status] = round(totals.get(seg.status, 0.0) + seg.duration, 2)
    return totals
