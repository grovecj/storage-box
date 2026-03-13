import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, MapPin, Clock, Printer, Map, LayoutGrid } from "lucide-react";
import BoxCard from "@/components/boxes/BoxCard";
import CreateBoxModal from "@/components/boxes/CreateBoxModal";
import BoxMapView from "@/components/boxes/BoxMapView";
import { listBoxes } from "@/api/client";
import { useGeolocation } from "@/hooks/useGeolocation";
import type { StorageBox } from "@/types";

export default function Dashboard() {
  const [boxes, setBoxes] = useState<StorageBox[]>([]);
  const [allBoxes, setAllBoxes] = useState<StorageBox[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<"recent" | "proximity">("recent");
  const [view, setView] = useState<"grid" | "map">("grid");
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const navTo = useNavigate();
  const geo = useGeolocation();

  const fetchBoxes = useCallback(async (append = false) => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20, sort };
      if (sort === "proximity" && geo.latitude != null && geo.longitude != null) {
        params.lat = geo.latitude;
        params.lng = geo.longitude;
      }
      const res = await listBoxes(params as Parameters<typeof listBoxes>[0]);
      setBoxes((prev) => append ? [...prev, ...res.data.boxes] : res.data.boxes);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  }, [page, sort, geo.latitude, geo.longitude]);

  const fetchAllBoxes = useCallback(async () => {
    setLoading(true);
    try {
      const pageSize = 100;
      let currentPage = 1;
      let all: StorageBox[] = [];
      let fetchedTotal = 0;

      // Fetch pages until we have all boxes
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const params: Record<string, unknown> = { page: currentPage, page_size: pageSize };
        const res = await listBoxes(params as Parameters<typeof listBoxes>[0]);
        all = [...all, ...res.data.boxes];
        fetchedTotal = res.data.total;
        if (all.length >= fetchedTotal || res.data.boxes.length < pageSize) break;
        currentPage++;
      }

      setAllBoxes(all);
      setTotal(fetchedTotal);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (view === "grid") {
      fetchBoxes(page > 1);
    } else {
      fetchAllBoxes();
    }
  }, [view, fetchBoxes, fetchAllBoxes, page]);

  const [pendingProximity, setPendingProximity] = useState(false);

  const handleViewChange = (newView: "grid" | "map") => {
    setView(newView);
  };

  const handleSortChange = (newSort: "recent" | "proximity") => {
    if (newSort === "proximity") {
      if (geo.latitude != null && geo.longitude != null) {
        // Already have coordinates — switch immediately
        if (sort !== "proximity") {
          setPage(1);
          setBoxes([]);
        }
        setSort("proximity");
        setPendingProximity(false);
      } else {
        // Request location, wait for coordinates before switching
        setPendingProximity(true);
        geo.requestLocation();
      }
    } else {
      setPendingProximity(false);
      if (sort !== "recent") {
        setPage(1);
        setBoxes([]);
      }
      setSort("recent");
    }
  };

  // Switch to proximity sort once coordinates arrive
  useEffect(() => {
    if (pendingProximity && geo.latitude != null && geo.longitude != null) {
      setPage(1);
      setBoxes([]);
      setSort("proximity");
      setPendingProximity(false);
    }
  }, [pendingProximity, geo.latitude, geo.longitude]);

  // Reset pending state if geolocation fails
  useEffect(() => {
    if (pendingProximity && geo.error) {
      setPendingProximity(false);
    }
  }, [pendingProximity, geo.error]);

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="stencil-heading">Inventory</h1>
          <p className="mt-2 text-sm font-mono text-slate-500 dark:text-slate-400">
            {total} box{total !== 1 ? "es" : ""}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-100 dark:bg-navy-800 rounded-md overflow-hidden">
            <button
              onClick={() => handleViewChange("grid")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                view === "grid"
                  ? "bg-amber-500 text-slate-900"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              }`}
            >
              <LayoutGrid size={14} />
              Grid
            </button>
            <button
              onClick={() => handleViewChange("map")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                view === "map"
                  ? "bg-amber-500 text-slate-900"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              }`}
            >
              <Map size={14} />
              Map
            </button>
          </div>
          {view === "grid" && (
            <div className="flex items-center bg-slate-100 dark:bg-navy-800 rounded-md overflow-hidden">
              <button
                onClick={() => handleSortChange("recent")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                  sort === "recent"
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                <Clock size={14} />
                Recent
              </button>
              <button
                onClick={() => handleSortChange("proximity")}
                disabled={pendingProximity}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                  sort === "proximity"
                    ? "bg-amber-500 text-slate-900"
                    : pendingProximity
                      ? "bg-amber-200 dark:bg-amber-900/40 text-slate-500"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                <MapPin size={14} className={pendingProximity ? "animate-pulse" : ""} />
                {pendingProximity ? "Locating..." : "Near Me"}
              </button>
            </div>
          )}
          <button
            onClick={() => navTo("/qr-batch")}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium uppercase tracking-wider bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700 rounded-md transition-colors"
          >
            <Printer size={14} />
            Print All QR
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
          >
            <Plus size={16} />
            New Box
          </button>
        </div>
      </div>

      {/* Content: Grid or Map View */}
      {loading ? (
        <div className="text-center py-16 text-slate-400 dark:text-slate-500">
          Loading boxes...
        </div>
      ) : (view === "grid" ? boxes.length : allBoxes.length) === 0 ? (
        <div className="text-center py-16">
          <p className="text-slate-400 dark:text-slate-500 mb-4">
            No storage boxes yet
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
          >
            <Plus size={16} />
            Create Your First Box
          </button>
        </div>
      ) : view === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {boxes.map((box) => (
            <BoxCard key={box.id} box={box} />
          ))}
        </div>
      ) : (
        <BoxMapView boxes={allBoxes} total={total} />
      )}

      {/* Load more (only in grid view) */}
      {view === "grid" && total > boxes.length && (
        <div className="text-center mt-6">
          <button
            onClick={() => setPage(page + 1)}
            className="px-6 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-navy-700 rounded-md transition-colors"
          >
            Load More
          </button>
        </div>
      )}

      <CreateBoxModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={fetchBoxes}
      />
    </div>
  );
}
