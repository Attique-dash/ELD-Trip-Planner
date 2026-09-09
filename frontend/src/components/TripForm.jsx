import { useState } from 'react'

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    currentLocation: '',
    pickupLocation: '',
    dropoffLocation: '',
    currentCycleUsed: '0',
  })

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      ...form,
      currentCycleUsed: parseFloat(form.currentCycleUsed || '0'),
    })
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <h2>Plan a Trip</h2>

      <label>
        Current Location
        <input
          name="currentLocation"
          value={form.currentLocation}
          onChange={handleChange}
          placeholder="e.g. Chicago, IL"
          required
        />
      </label>

      <label>
        Pickup Location
        <input
          name="pickupLocation"
          value={form.pickupLocation}
          onChange={handleChange}
          placeholder="e.g. St. Louis, MO"
          required
        />
      </label>

      <label>
        Dropoff Location
        <input
          name="dropoffLocation"
          value={form.dropoffLocation}
          onChange={handleChange}
          placeholder="e.g. Dallas, TX"
          required
        />
      </label>

      <label>
        Current Cycle Used (Hrs)
        <input
          type="number"
          name="currentCycleUsed"
          value={form.currentCycleUsed}
          onChange={handleChange}
          min="0"
          max="70"
          step="0.5"
          required
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? 'Planning...' : 'Plan Trip'}
      </button>
    </form>
  )
}
