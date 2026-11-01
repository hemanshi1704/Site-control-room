import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import { STATUS } from "../api";

export default function SiteMap({ sites, selectedId, onSelect }) {
  return (
    <div className="map">
      <MapContainer center={[26.6, 74.9]} zoom={7} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {sites.map((s) => {
          const color = STATUS[s.status].color;
          return (
            <CircleMarker
              key={s.id}
              center={[s.lat, s.lng]}
              radius={selectedId === s.id ? 14 : 10}
              pathOptions={{ color: "#fff", weight: 2, fillColor: color, fillOpacity: 0.95 }}
              eventHandlers={{ click: () => onSelect(s.id) }}
            >
              <Tooltip direction="top" offset={[0, -8]}>
                <b>{s.name}</b>
                <br />
                {STATUS[s.status].label} · {Number(s.progress_pct)}% done
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
