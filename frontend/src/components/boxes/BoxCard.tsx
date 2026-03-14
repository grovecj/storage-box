import { Link } from "react-router-dom";
import { Package, MapPin } from "lucide-react";
import GroupBadge from "@/components/groups/GroupBadge";
import type { StorageBox } from "@/types";

interface BoxCardProps {
  box: StorageBox;
}

export default function BoxCard({ box }: BoxCardProps) {
  const modified = new Date(box.updated_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link
      to={`/boxes/${box.id}`}
      className="group block bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg shadow-sm hover:shadow-md hover:border-l-4 hover:border-l-amber-400 transition-all duration-150"
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <span className="box-code">{box.box_code}</span>
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              box.item_count > 0 ? "bg-green-500" : "bg-slate-300 dark:bg-slate-600"
            }`}
          />
        </div>

        <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 truncate group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
          {box.name}
        </h3>

        {box.group_name && (
          <div className="mb-2">
            <GroupBadge name={box.group_name} />
          </div>
        )}

        <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Package size={14} />
            {box.item_count} item{box.item_count !== 1 ? "s" : ""}
          </span>
          {(box.location_name || (box.latitude != null && box.longitude != null)) && (
            <span className="flex items-center gap-1">
              <MapPin size={14} />
              <span className="text-xs truncate max-w-[140px]">
                {box.location_name || `${box.latitude!.toFixed(3)}, ${box.longitude!.toFixed(3)}`}
              </span>
            </span>
          )}
        </div>

        <div className="mt-3 text-xs text-slate-400 dark:text-slate-500">
          Modified {modified}
        </div>
      </div>
    </Link>
  );
}
