import { useEffect } from "react";
import { Link } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import { Package, MapPin } from "lucide-react";
import "leaflet/dist/leaflet.css";
import L, { LatLngBounds } from "leaflet";
import type { StorageBox } from "@/types";

// Fix default marker icon (Leaflet + bundlers issue)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface BoxMapViewProps {
  boxes: StorageBox[];
  total?: number;
}

// Helper component to auto-fit map bounds
function MapBoundsFitter({ boxes }: { boxes: StorageBox[] }) {
  const map = useMap();

  useEffect(() => {
    if (boxes.length === 0) return;

    if (boxes.length === 1) {
      map.setView([boxes[0]!.latitude!, boxes[0]!.longitude!], 13);
      return;
    }

    const bounds = new LatLngBounds(
      boxes.map((box) => [box.latitude!, box.longitude!] as [number, number])
    );

    map.fitBounds(bounds, {
      padding: [50, 50],
      maxZoom: 15,
    });
  }, [map, boxes]);

  return null;
}

export default function BoxMapView({ boxes, total }: BoxMapViewProps) {
  // Separate geolocated from non-geolocated boxes
  const geolocatedBoxes = boxes.filter(
    (box) => box.latitude != null && box.longitude != null
  );
  const nonGeolocatedBoxes = boxes.filter(
    (box) => box.latitude == null || box.longitude == null
  );

  // Default center (fallback if no boxes have location)
  const defaultCenter: [number, number] = [37.7749, -122.4194]; // San Francisco

  return (
    <div className="space-y-6">
      {/* Map Section */}
      {geolocatedBoxes.length === 0 ? (
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg p-12 text-center">
          <MapPin className="mx-auto mb-4 text-slate-300 dark:text-slate-600" size={48} />
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            No boxes have location data yet.
          </p>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-2">
            Use "Set Location" on box detail pages to enable map view.
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg overflow-hidden">
          <div
            className="h-[60vh] sm:h-[500px] w-full"
            style={{ minHeight: "400px" }}
          >
            <MapContainer
              center={defaultCenter}
              zoom={10}
              style={{ height: "100%", width: "100%" }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {geolocatedBoxes.map((box) => (
                <Marker
                  key={box.id}
                  position={[box.latitude!, box.longitude!]}
                >
                  <Popup>
                    <div className="min-w-[200px]">
                      <div className="mb-2">
                        <span className="box-code text-xs">{box.box_code}</span>
                      </div>
                      <h3 className="font-semibold text-slate-800 text-sm mb-2">
                        {box.name}
                      </h3>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
                        <span className="flex items-center gap-1">
                          <Package size={12} />
                          {box.item_count} item{box.item_count !== 1 ? "s" : ""}
                        </span>
                        {box.location_name && (
                          <span className="flex items-center gap-1">
                            <MapPin size={12} />
                            <span className="truncate max-w-[120px]">
                              {box.location_name}
                            </span>
                          </span>
                        )}
                      </div>
                      <Link
                        to={`/boxes/${box.id}`}
                        className="inline-block w-full text-center px-3 py-1.5 text-xs font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded transition-colors"
                      >
                        View Box
                      </Link>
                    </div>
                  </Popup>
                </Marker>
              ))}
              <MapBoundsFitter boxes={geolocatedBoxes} />
            </MapContainer>
          </div>
          {geolocatedBoxes.length > 0 && (
            <div className="px-4 py-2 bg-slate-50 dark:bg-navy-800 border-t border-slate-200 dark:border-navy-700">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Showing {geolocatedBoxes.length} geolocated box
                {geolocatedBoxes.length !== 1 ? "es" : ""}
                {total != null && total > boxes.length && (
                  <span className="text-amber-600 dark:text-amber-400">
                    {" "}(showing {boxes.length} of {total} total boxes)
                  </span>
                )}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Non-geolocated boxes list */}
      {nonGeolocatedBoxes.length > 0 && (
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 dark:bg-navy-800 border-b border-slate-200 dark:border-navy-700">
            <h2 className="section-label">
              Boxes Without Location ({nonGeolocatedBoxes.length})
            </h2>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-navy-800">
            {nonGeolocatedBoxes.map((box) => (
              <Link
                key={box.id}
                to={`/boxes/${box.id}`}
                className="block px-4 py-3 hover:bg-slate-50 dark:hover:bg-navy-800 transition-colors group"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="box-code text-xs">{box.box_code}</span>
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 truncate group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                        {box.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <Package size={12} />
                        {box.item_count}
                      </span>
                      {box.location_name && (
                        <span className="truncate">{box.location_name}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-slate-400 dark:text-slate-600 group-hover:text-amber-500 transition-colors">
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
