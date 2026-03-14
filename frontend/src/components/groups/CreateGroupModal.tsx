import { useState } from "react";
import { Crosshair, Loader2 } from "lucide-react";
import Modal from "@/components/shared/Modal";
import { useGeolocation } from "@/hooks/useGeolocation";

interface CreateGroupModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (data: {
    name: string;
    latitude?: number;
    longitude?: number;
  }) => void;
}

export default function CreateGroupModal({
  open,
  onClose,
  onCreated,
}: CreateGroupModalProps) {
  const [name, setName] = useState("");
  const [useLocation, setUseLocation] = useState(false);
  const [manualLat, setManualLat] = useState("");
  const [manualLng, setManualLng] = useState("");
  const [saving, setSaving] = useState(false);
  const geo = useGeolocation();

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);

    try {
      const data: {
        name: string;
        latitude?: number;
        longitude?: number;
      } = { name: name.trim() };

      if (useLocation && geo.latitude != null && geo.longitude != null) {
        data.latitude = geo.latitude;
        data.longitude = geo.longitude;
      } else if (manualLat && manualLng) {
        data.latitude = parseFloat(manualLat);
        data.longitude = parseFloat(manualLng);
      }

      onCreated(data);
      setName("");
      setManualLat("");
      setManualLng("");
      setUseLocation(false);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Group">
      <div className="space-y-4">
        <div>
          <label className="section-label">Group Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder='e.g. "Garage", "Storage Unit #4"'
            className="mt-1 w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
            autoFocus
          />
        </div>

        <div>
          <label className="section-label">GPS Location (Optional)</label>
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

            <div className="text-xs text-slate-400 text-center">
              or enter manually
            </div>

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
            {saving ? "Creating..." : "Create Group"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
