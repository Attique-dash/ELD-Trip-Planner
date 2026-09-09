const ROW_ORDER = ['off_duty', 'sleeper_berth', 'driving', 'on_duty_not_driving']
const ROW_LABELS = {
  off_duty: 'Off Duty',
  sleeper_berth: 'Sleeper Berth',
  driving: 'Driving',
  on_duty_not_driving: 'On Duty (Not Driving)',
}

const CHART_LEFT = 130
const CHART_WIDTH = 920
const HOUR_WIDTH = CHART_WIDTH / 24
const ROW_HEIGHT = 40
const CHART_TOP = 30

function xForHour(hour) {
  return CHART_LEFT + hour * HOUR_WIDTH
}

function yForStatus(status) {
  const index = ROW_ORDER.indexOf(status)
  return CHART_TOP + index * ROW_HEIGHT + ROW_HEIGHT / 2
}

export default function LogSheet({ daySheet, dayLabel }) {
  const { segments, totals } = daySheet

  // Build a single continuous path: horizontal line for each segment's
  // duration at its status row, with vertical connectors between segments -
  // this recreates the "step graph" look of a real driver's paper log.
  let pathPoints = []
  segments.forEach((seg, i) => {
    const y = yForStatus(seg.status)
    const xStart = xForHour(seg.start_hour)
    const xEnd = xForHour(seg.end_hour)
    if (i === 0) {
      pathPoints.push(`M ${xStart} ${y}`)
    } else {
      pathPoints.push(`L ${xStart} ${y}`)
    }
    pathPoints.push(`L ${xEnd} ${y}`)
  })
  const pathD = pathPoints.join(' ')

  const chartHeight = ROW_ORDER.length * ROW_HEIGHT
  const svgHeight = CHART_TOP + chartHeight + 30

  return (
    <div className="log-sheet">
      <div className="log-sheet-header">
        <strong>Driver's Daily Log — {dayLabel}</strong>
        <span className="log-sheet-subtitle">(24 hours, midnight to midnight)</span>
      </div>

      <svg width="100%" viewBox={`0 0 ${CHART_LEFT + CHART_WIDTH + 200} ${svgHeight}`}>
        {/* hour tick labels */}
        {Array.from({ length: 25 }).map((_, h) => (
          <g key={h}>
            <line
              x1={xForHour(h)} y1={CHART_TOP}
              x2={xForHour(h)} y2={CHART_TOP + chartHeight}
              stroke="#ddd" strokeWidth={h % 6 === 0 ? 1.4 : 0.6}
            />
            {h % 2 === 0 && (
              <text x={xForHour(h)} y={CHART_TOP - 8} fontSize="10" textAnchor="middle" fill="#666">
                {h === 0 ? 'Mid' : h === 12 ? 'Noon' : h % 12}
              </text>
            )}
          </g>
        ))}

        {/* row labels + row separator lines */}
        {ROW_ORDER.map((status, i) => (
          <g key={status}>
            <line
              x1={CHART_LEFT} y1={CHART_TOP + i * ROW_HEIGHT}
              x2={CHART_LEFT + CHART_WIDTH} y2={CHART_TOP + i * ROW_HEIGHT}
              stroke="#bbb" strokeWidth="1"
            />
            <text x={CHART_LEFT - 8} y={CHART_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2 + 4}
              fontSize="11" textAnchor="end" fill="#333">
              {ROW_LABELS[status]}
            </text>
          </g>
        ))}
        <line
          x1={CHART_LEFT} y1={CHART_TOP + chartHeight}
          x2={CHART_LEFT + CHART_WIDTH} y2={CHART_TOP + chartHeight}
          stroke="#bbb" strokeWidth="1"
        />

        {/* the actual duty-status step line */}
        <path d={pathD} fill="none" stroke="#1d4ed8" strokeWidth="2.5" />

        {/* vertical connector dots at each status change */}
        {segments.map((seg, i) => (
          <circle key={i} cx={xForHour(seg.start_hour)} cy={yForStatus(seg.status)} r="2.5" fill="#1d4ed8" />
        ))}

        {/* totals column */}
        <text x={CHART_LEFT + CHART_WIDTH + 20} y={CHART_TOP - 8} fontSize="11" fontWeight="bold">
          Total Hrs
        </text>
        {ROW_ORDER.map((status, i) => (
          <text key={status} x={CHART_LEFT + CHART_WIDTH + 20}
            y={CHART_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2 + 4} fontSize="12">
            {totals[status]?.toFixed(2) ?? '0.00'}
          </text>
        ))}
      </svg>

      <div className="log-sheet-remarks">
        <strong>Remarks:</strong>
        <ul>
          {segments.filter((s) => s.label).map((s, i) => (
            <li key={i}>
              {formatHour(s.start_hour)} — {s.label}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function formatHour(hourFloat) {
  const h = Math.floor(hourFloat) % 24
  const m = Math.round((hourFloat % 1) * 60)
  const period = h < 12 ? 'AM' : 'PM'
  const displayHour = h % 12 === 0 ? 12 : h % 12
  return `${displayHour}:${m.toString().padStart(2, '0')} ${period}`
}
