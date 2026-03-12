import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  MapPin,
  Printer,
  Trash2,
  Edit,
  Plus,
  Crosshair,
  Map,
} from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import Modal from "@/components/shared/Modal";
import ItemTable from "@/components/items/ItemTable";
import AddItemModal from "@/components/items/AddItemModal";
import TransferModal from "@/components/items/TransferModal";
import { getBox, getBoxByCode, updateBox, deleteBox, getAuditLog } from "@/api/client";
import type { StorageBox, BoxItem, AuditLogEntry } from "@/types";

// Fix default marker icon (Leaflet + bundlers issue)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function BoxDetail() {
  const { id, code } = useParams();
  const navigate = useNavigate();
  const [box, setBox] = useState<StorageBox | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"items" | "audit">("items");
  const [refreshKey, setRefreshKey] = useState(0);

  // Modals
  const [showAddItem, setShowAddItem] = useState(false);
  const [transferItem, setTransferItem] = useState<BoxItem | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [showMap, setShowMap] = useState(false);

  // Audit log
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const fetchBox = async () => {
    setLoading(true);
    try {
      const res = code
        ? await getBoxByCode(code)
        : await getBox(parseInt(id!));
      setBox(res.data);
      setNameInput(res.data.name);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLog = async () => {
    if (!box) return;
    setAuditLoading(true);
    try {
      const res = await getAuditLog(box.id, { page: 1, page_size: 50 });
      setAuditLogs(res.data.logs);
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    fetchBox();
  }, [id, code]);

  useEffect(() => {
    if (activeTab === "audit" && box) fetchAuditLog();
  }, [activeTab, box?.id, refreshKey]);

  const handleSaveName = async () => {
    if (!box || !nameInput.trim()) return;
    await updateBox(box.id, { name: nameInput.trim() });
    setEditingName(false);
    fetchBox();
  };

  const [locationUpdating, setLocationUpdating] = useState(false);

  const handleUpdateLocation = async () => {
    if (!box) return;
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    setLocationUpdating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          await updateBox(box.id, {
            location: {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            },
          });
          await fetchBox();
        } finally {
          setLocationUpdating(false);
        }
      },
      (error) => {
        setLocationUpdating(false);
        alert(`Location error: ${error.message}`);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleDelete = async () => {
    if (!box) return;
    await deleteBox(box.id);
    navigate("/");
  };

  const handleItemsChanged = () => {
    setRefreshKey((k) => k + 1);
    fetchBox();
  };

  if (loading) {
    return (
      <div className="text-center py-16 text-slate-400 dark:text-slate-500">
        Loading...
      </div>
    );
  }

  if (!box) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-500 dark:text-slate-400">Box not found</p>
        <button
          onClick={() => navigate("/")}
          className="mt-4 text-amber-500 hover:text-amber-400 text-sm"
        >
          Back to Inventory
        </button>
      </div>
    );
  }

  const actionMap: Record<string, string> = {
    BOX_CREATED: "Box created",
    BOX_UPDATED: "Box updated",
    BOX_DELETED: "Box deleted",
    ITEM_ADDED: "Item added",
    ITEM_REMOVED: "Item removed",
    ITEM_UPDATED: "Item updated",
    ITEM_TRANSFERRED: "Item transferred out",
    ITEM_RECEIVED: "Item received",
  };

  return (
    <div>
      {/* Back link */}
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 mb-4 transition-colors"
      >
        <ChevronLeft size={16} />
        Back to Inventory
      </button>

      {/* Box header */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex-1">
            <span className="box-code text-base">{box.box_code}</span>

            {editingName ? (
              <div className="flex items-center gap-2 mt-2">
                <input
                  type="text"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                  className="text-xl font-bold bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-100"
                  autoFocus
                />
                <button
                  onClick={handleSaveName}
                  className="px-3 py-1 text-xs font-semibold uppercase bg-amber-500 text-slate-900 rounded"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditingName(false);
                    setNameInput(box.name);
                  }}
                  className="px-3 py-1 text-xs text-slate-500 hover:text-slate-700"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 mt-2 flex items-center gap-2">
                {box.name}
                <button
                  onClick={() => setEditingName(true)}
                  className="p-1 text-slate-400 hover:text-amber-500 transition-colors"
                >
                  <Edit size={16} />
                </button>
              </h1>
            )}

            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-slate-500 dark:text-slate-400">
              {box.latitude != null && box.longitude != null ? (
                <button
                  onClick={() => setShowMap(!showMap)}
                  className="flex items-center gap-1 hover:text-amber-500 transition-colors cursor-pointer"
                  title={showMap ? "Hide map" : "Show on map"}
                >
                  {showMap ? <Map size={14} /> : <MapPin size={14} />}
                  <span className="font-mono text-xs">
                    {box.latitude.toFixed(5)}, {box.longitude.toFixed(5)}
                  </span>
                </button>
              ) : (
                <span className="text-slate-400">No location set</span>
              )}
              <span>
                Created{" "}
                {new Date(box.created_at).toLocaleDateString()}
              </span>
            </div>

            {/* Inline map */}
            {showMap && box.latitude != null && box.longitude != null && (
              <div className="mt-4 rounded-lg overflow-hidden border border-slate-200 dark:border-navy-700" style={{ height: 300 }}>
                <MapContainer
                  center={[box.latitude, box.longitude]}
                  zoom={15}
                  style={{ height: "100%", width: "100%" }}
                  scrollWheelZoom={true}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <Marker position={[box.latitude, box.longitude]}>
                    <Popup>
                      <strong>{box.box_code}</strong><br />{box.name}
                    </Popup>
                  </Marker>
                </MapContainer>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleUpdateLocation}
              disabled={locationUpdating}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium uppercase tracking-wider bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700 rounded-md transition-colors disabled:opacity-50"
              title="Update location"
            >
              <Crosshair size={14} className={locationUpdating ? "animate-spin" : ""} />
              {locationUpdating ? "Locating..." : "Set Location"}
            </button>
            <button
              onClick={() => navigate(`/boxes/${box.id}/qr`)}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium uppercase tracking-wider bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700 rounded-md transition-colors"
            >
              <Printer size={14} />
              QR Code
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium uppercase tracking-wider bg-red-50 dark:bg-red-900/20 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-md transition-colors"
            >
              <Trash2 size={14} />
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-slate-200 dark:border-navy-700 mb-6">
        <button
          onClick={() => setActiveTab("items")}
          className={`pb-3 text-sm font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "items"
              ? "text-amber-500 border-b-2 border-amber-400"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          }`}
        >
          Items ({box.item_count})
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-3 text-sm font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "audit"
              ? "text-amber-500 border-b-2 border-amber-400"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          }`}
        >
          Audit Log
        </button>
        {activeTab === "items" && (
          <div className="ml-auto pb-3">
            <button
              onClick={() => setShowAddItem(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
            >
              <Plus size={14} />
              Add Item
            </button>
          </div>
        )}
      </div>

      {/* Tab content */}
      {activeTab === "items" && (
        <ItemTable
          boxId={box.id}
          onTransfer={(item) => setTransferItem(item)}
          refreshKey={refreshKey}
        />
      )}

      {activeTab === "audit" && (
        <div className="space-y-3">
          {auditLoading ? (
            <div className="text-center py-8 text-slate-400">Loading...</div>
          ) : auditLogs.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No audit entries yet
            </div>
          ) : (
            auditLogs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-3 py-3 border-b border-slate-100 dark:border-navy-800"
              >
                <div className="w-2 h-2 mt-2 rounded-full bg-amber-400 flex-shrink-0" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    {actionMap[log.action] || log.action}
                  </div>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                      {"item_name" in log.details && (
                        <span>{String(log.details.item_name)}</span>
                      )}
                      {"quantity" in log.details && (
                        <span> &times; {String(log.details.quantity)}</span>
                      )}
                      {"to_box" in log.details && (
                        <span> &rarr; {String(log.details.to_box)}</span>
                      )}
                      {"from_box" in log.details && log.action === "ITEM_RECEIVED" && (
                        <span> &larr; {String(log.details.from_box)}</span>
                      )}
                    </div>
                  )}
                  <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Modals */}
      <AddItemModal
        open={showAddItem}
        boxId={box.id}
        onClose={() => setShowAddItem(false)}
        onAdded={handleItemsChanged}
      />

      <TransferModal
        open={!!transferItem}
        item={transferItem}
        fromBoxId={box.id}
        fromBoxCode={box.box_code}
        onClose={() => setTransferItem(null)}
        onTransferred={handleItemsChanged}
      />

      <Modal
        open={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Box"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Are you sure you want to delete{" "}
            <span className="box-code">{box.box_code}</span>?
          </p>
          {box.item_count > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-md p-3 text-sm text-red-700 dark:text-red-400">
              This box contains <strong>{box.item_count} item{box.item_count !== 1 ? "s" : ""}</strong>.
              All items will be permanently removed.
            </div>
          )}
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              Delete Permanently
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
