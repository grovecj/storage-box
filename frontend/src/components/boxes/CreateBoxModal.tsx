import { useState } from "react";
import { Crosshair, Loader2 } from "lucide-react";
import Modal from "@/components/shared/Modal";
import { createBox } from "@/api/client";
import { useGeolocation } from "@/hooks/useGeolocation";

interface CreateBoxModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateBoxModal({
  open,
  onClose,
  onCreated,
}: CreateBoxModalProps) {
  const [name, setName] = useState("");
  const [locationName, setLocationName] = useState("");
  const [useLocation, setUseLocation] = useState(false);
  const [manualLat, setManualLat] = useState("");
  const [manualLng, setManualLng] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const geo = useGeolocation();

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError(null);

    try {
      let location: { latitude: number; longitude: number } | null = null;
      if (useLocation && geo.latitude != null && geo.longitude != null) {
        location = { latitude: geo.latitude, longitude: geo.longitude };
      } else if (manualLat && manualLng) {
        location = {
          latitude: parseFloat(manualLat),
          longitude: parseFloat(manualLng),
        };
      }

      await createBox({
        name: name.trim(),
        location,
        location_name: locationName.trim() || null,
      });
      setName("");
      setLocationName("");
      setManualLat("");
      setManualLng("");
      setUseLocation(false);
      onCreated();
      onClose();
    } catch {
      setError("Failed to create box");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create New Box">
      <div className="space-y-4">
        <div>
          <label className="section-label">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Holiday Decorations"
            className="mt-1 w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
            autoFocus
          />
        </div>

        <div>
          <label className="section-label">Location Name</label>
          <input
            type="text"
            value={locationName}
            onChange={(e) => setLocationName(e.target.value)}
            placeholder='e.g. "Garage Shelf 3"'
            className="mt-1 w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
          />
        </div>

        <div>
          <label className="section-label">GPS Location</label>
          <div className="mt-2 space-y-2">
            <button
              type="button"
              onClick={() => {
                setUseLocation(true);
                geo.requestLocation();
              }}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-slate-100 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md hover:bg-slate-200 dark:hover:bg-navy-700 transition-colors w-full"
            >
              {geo.loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Crosshair size={16} />
              )}
              {useLocation && geo.latitude
                ? `${geo.latitude.toFixed(5)}, ${geo.longitude?.toFixed(5)}`
                : "Use My Location"}
            </button>

            <div className="text-xs text-slate-400 text-center">or enter manually</div>

            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                step="any"
                value={manualLat}
                onChange={(e) => {
                  setManualLat(e.target.value);
                  setUseLocation(false);
                }}
                placeholder="Latitude"
                className="px-3 py-2 text-sm font-mono bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
              />
              <input
                type="number"
                step="any"
                value={manualLng}
                onChange={(e) => {
                  setManualLng(e.target.value);
                  setUseLocation(false);
                }}
                placeholder="Longitude"
                className="px-3 py-2 text-sm font-mono bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
              />
            </div>
          </div>
          {geo.error && (
            <p className="mt-1 text-xs text-red-500">{geo.error}</p>
          )}
        </div>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!name.trim() || saving}
            className="px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Creating..." : "Create Box"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
