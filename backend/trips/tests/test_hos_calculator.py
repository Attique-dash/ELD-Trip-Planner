import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from trips.services.hos_calculator import (
    HOSCalculator,
    split_segments_into_days,
    compute_totals_by_status,
)


class TestHOSCalculator(unittest.TestCase):

    def test_short_trip_no_rest_needed(self):
        """A short trip (well under 11 hrs driving) should need no 10-hr resets."""
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=50, leg1_hours=1, leg2_miles=200, leg2_hours=4)

        statuses = [s.status for s in plan.segments]
        self.assertIn("driving", statuses)
        self.assertNotIn("sleeper_berth", statuses)
        # total on-clock time = 1 (drive) + 1 (pickup) + 4 (drive) + 1 (dropoff) = 7
        self.assertAlmostEqual(plan.total_trip_hours, 7, places=1)

    def test_30_min_break_after_8_hours_driving(self):
        """Driving more than 8 cumulative hours must trigger a 30-min break."""
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=0, leg1_hours=0, leg2_miles=500, leg2_hours=10)

        break_segments = [s for s in plan.segments if s.status == "off_duty" and "break" in s.label.lower()]
        self.assertTrue(len(break_segments) >= 1, "Expected at least one 30-minute break")
        self.assertAlmostEqual(break_segments[0].duration, 0.5, places=2)

    def test_11_hour_driving_limit_enforced(self):
        """No single duty window should ever contain more than 11 hours of driving."""
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=0, leg1_hours=0, leg2_miles=1400, leg2_hours=28)

        # walk through segments, tracking driving hours between any 10+ hr off-duty resets
        driving_in_window = 0.0
        for seg in plan.segments:
            if seg.status == "driving":
                driving_in_window += seg.duration
                self.assertLessEqual(driving_in_window, 11.001,
                                      "Exceeded 11-hour driving limit within a window")
            elif seg.status in ("off_duty", "sleeper_berth") and seg.duration >= 10:
                driving_in_window = 0.0

    def test_long_trip_triggers_10_hour_reset(self):
        """A trip needing more than 11 hours of driving must include a 10-hr off-duty block."""
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=0, leg1_hours=0, leg2_miles=1400, leg2_hours=28)

        long_rests = [s for s in plan.segments if s.status in ("off_duty", "sleeper_berth") and s.duration >= 10]
        self.assertTrue(len(long_rests) >= 1, "Expected at least one 10-hour+ rest period")
        self.assertGreater(plan.days, 1)

    def test_fuel_stop_added_over_1000_miles(self):
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=0, leg1_hours=0, leg2_miles=1500, leg2_hours=27)
        self.assertGreaterEqual(plan.fuel_stops, 1)
        fuel_segments = [s for s in plan.segments if s.label == "Fuel stop"]
        self.assertEqual(len(fuel_segments), plan.fuel_stops)

    def test_cycle_limit_forces_34_hour_restart(self):
        """If current_cycle_used is already near 70, a 34-hr restart must appear."""
        calc = HOSCalculator(current_cycle_used_hours=68)
        plan = calc.plan(leg1_miles=0, leg1_hours=0, leg2_miles=300, leg2_hours=6)

        restarts = [s for s in plan.segments if s.duration >= 34]
        self.assertTrue(len(restarts) >= 1, "Expected a 34-hour restart when cycle limit is nearly used up")
        self.assertTrue(any("restart" in w.lower() for w in plan.warnings))

    def test_pickup_and_dropoff_are_one_hour_each(self):
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=20, leg1_hours=0.5, leg2_miles=100, leg2_hours=2)

        pickup = [s for s in plan.segments if "pickup" in s.label.lower() and s.status == "on_duty_not_driving"]
        dropoff = [s for s in plan.segments if "dropoff" in s.label.lower() and s.status == "on_duty_not_driving"]
        self.assertAlmostEqual(sum(s.duration for s in pickup), 1.0, places=2)
        self.assertAlmostEqual(sum(s.duration for s in dropoff), 1.0, places=2)

    def test_split_into_days_and_totals_equal_24(self):
        """Every generated day's segments must total exactly 24 hours (matches the
        paper log rule that Off+Sleeper+Driving+OnDuty = 24)."""
        calc = HOSCalculator(current_cycle_used_hours=0)
        plan = calc.plan(leg1_miles=100, leg1_hours=2, leg2_miles=1200, leg2_hours=24)

        day_lists = split_segments_into_days(plan.segments)
        self.assertGreaterEqual(len(day_lists), 1)
        for i, day in enumerate(day_lists[:-1]):  # last day may be a partial day
            totals = compute_totals_by_status(day)
            self.assertAlmostEqual(sum(totals.values()), 24, places=1,
                                    msg=f"Day {i + 1} does not total 24 hours")


if __name__ == "__main__":
    unittest.main()
