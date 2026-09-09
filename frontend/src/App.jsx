import { useState } from 'react'
import TripForm from './components/TripForm'
import RouteMap from './components/RouteMap'
import LogSheet from './components/LogSheet'
import { planTrip } from './api'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (formData) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await planTrip(formData)
      setResult(data)
    } catch (err) {
      const message = err.response?.data?.error || 'Something went wrong. Please check your locations and try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>🚚 ELD Trip Planner</h1>
        <p>Enter a trip and get a route + auto-generated driver daily logs.</p>
      </header>

      <TripForm onSubmit={handleSubmit} loading={loading} />

      {error && <div className="error-box">{error}</div>}

      {result && (
        <>
          <section className="summary">
            <h2>Trip Summary</h2>
            <ul>
              <li>Total distance: {result.route.total_distance_miles} miles</li>
              <li>Total driving time: {result.trip_summary.total_driving_hours} hrs</li>
              <li>Total trip time (incl. stops/rests): {result.trip_summary.total_trip_hours} hrs</li>
              <li>Fuel stops: {result.trip_summary.fuel_stops}</li>
              <li>Days required: {result.trip_summary.days_required}</li>
            </ul>
            {result.trip_summary.warnings?.length > 0 && (
              <div className="warnings">
                {result.trip_summary.warnings.map((w, i) => (
                  <p key={i}>⚠️ {w}</p>
                ))}
              </div>
            )}
          </section>

          <RouteMap locations={result.locations} route={result.route} />

          <section className="log-sheets">
            <h2>Driver Daily Logs</h2>
            {result.log_sheets.map((sheet) => (
              <LogSheet key={sheet.day} daySheet={sheet} dayLabel={`Day ${sheet.day}`} />
            ))}
          </section>
        </>
      )}
    </div>
  )
}
