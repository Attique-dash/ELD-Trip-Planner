import { MapContainer, TileLayer, Marker, Polyline, Popup, CircleMarker } from 'react-leaflet'
import L from 'leaflet'

// Default Leaflet marker icons don't load correctly with bundlers unless we
// point them at the CDN explicitly.
const icon = (color) =>
  new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  })

export default function RouteMap({ locations, route }) {
  if (!locations || !route) return null

  const bounds = [
    [locations.current.lat, locations.current.lon],
    [locations.pickup.lat, locations.pickup.lon],
    [locations.dropoff.lat, locations.dropoff.lon],
  ]

  return (
    <div className="map-wrapper">
      <MapContainer bounds={bounds} scrollWheelZoom={true} style={{ height: '420px', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <CircleMarker center={[locations.current.lat, locations.current.lon]} radius={8} pathOptions={{ color: '#f97316', fillColor: '#f97316', fillOpacity: 1 }}>
          <Popup>Current location: {locations.current.name}</Popup>
        </CircleMarker>
        <CircleMarker center={[locations.pickup.lat, locations.pickup.lon]} radius={8} pathOptions={{ color: '#2563eb', fillColor: '#2563eb', fillOpacity: 1 }}>
          <Popup>Pickup: {locations.pickup.name}</Popup>
        </CircleMarker>
        <CircleMarker center={[locations.dropoff.lat, locations.dropoff.lon]} radius={8} pathOptions={{ color: '#dc2626', fillColor: '#dc2626', fillOpacity: 1 }}>
          <Popup>Dropoff: {locations.dropoff.name}</Popup>
        </CircleMarker>

        <Polyline positions={route.leg1_geometry} pathOptions={{ color: '#2563eb', weight: 4 }} />
        <Polyline positions={route.leg2_geometry} pathOptions={{ color: '#dc2626', weight: 4 }} />
      </MapContainer>
      <p className="route-distance">Total distance: {route.total_distance_miles} miles</p>
    </div>
  )
}
