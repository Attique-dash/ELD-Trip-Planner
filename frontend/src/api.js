import axios from 'axios'

// Set VITE_API_URL when you deploy the backend (e.g. in a .env file or on
// Vercel's environment variables). Falls back to local Django dev server.
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function planTrip({ currentLocation, pickupLocation, dropoffLocation, currentCycleUsed }) {
  const response = await axios.post(`${API_BASE}/api/plan-trip/`, {
    current_location: currentLocation,
    pickup_location: pickupLocation,
    dropoff_location: dropoffLocation,
    current_cycle_used: currentCycleUsed,
  })
  return response.data
}
