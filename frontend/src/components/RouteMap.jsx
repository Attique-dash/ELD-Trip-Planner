import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet'
import L from 'leaflet'

// Default Leaflet marker icons don't load correctly with bundlers unless we
// point them at the CDN explicitly.
const icon = (color) =>
  new L.Icon({
    iconUrl: `https://unpkg.com/leaflet-color-markers@1.0.0/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
  })

export default function RouteMap({ locations, route }) {
  if (!locations || !route) return null

  const center = [locations.pickup.lat, locations.pickup.lon]

  return (
    <div className="map-wrapper">
      <MapContainer center={center} zoom={6} scrollWheelZoom={true} style={{ height: '420px', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Marker position={[locations.current.lat, locations.current.lon]} icon={icon('green')}>
          <Popup>Current location: {locations.current.name}</Popup>
        </Marker>
        <Marker position={[locations.pickup.lat, locations.pickup.lon]} icon={icon('blue')}>
          <Popup>Pickup: {locations.pickup.name}</Popup>
        </Marker>
        <Marker position={[locations.dropoff.lat, locations.dropoff.lon]} icon={icon('red')}>
          <Popup>Dropoff: {locations.dropoff.name}</Popup>
        </Marker>

        <Polyline positions={route.leg1_geometry} pathOptions={{ color: '#2563eb', weight: 4 }} />
        <Polyline positions={route.leg2_geometry} pathOptions={{ color: '#dc2626', weight: 4 }} />
      </MapContainer>
      <p className="route-distance">Total distance: {route.total_distance_miles} miles</p>
    </div>
  )
}
