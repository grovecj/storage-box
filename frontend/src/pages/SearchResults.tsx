import { useState, useEffect, useMemo } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Package, MapPin, ChevronRight, Layers, List } from "lucide-react";
import { search } from "@/api/client";
import type { SearchResult, SearchItemResult } from "@/types";

interface GroupedItem {
  name: string;
  totalQuantity: number;
  allTags: string[];
  locations: {
    id: number;
    box_id: number;
    box_code: string;
    box_name: string;
    quantity: number;
    tags: string[];
  }[];
}

function groupItemsByName(items: SearchItemResult[]): GroupedItem[] {
  const map = new Map<string, GroupedItem>();
  for (const item of items) {
    const existing = map.get(item.name);
    if (existing) {
      existing.totalQuantity += item.quantity;
      existing.locations.push({
        id: item.id,
        box_id: item.box_id,
        box_code: item.box_code,
        box_name: item.box_name,
        quantity: item.quantity,
        tags: item.tags,
      });
      for (const tag of item.tags) {
        if (!existing.allTags.includes(tag)) existing.allTags.push(tag);
      }
    } else {
      map.set(item.name, {
        name: item.name,
        totalQuantity: item.quantity,
        allTags: [...item.tags],
        locations: [
          {
            id: item.id,
            box_id: item.box_id,
            box_code: item.box_code,
            box_name: item.box_name,
            quantity: item.quantity,
            tags: item.tags,
          },
        ],
      });
    }
  }
  return Array.from(map.values());
}

export default function SearchResults() {
  const [params] = useSearchParams();
  const query = params.get("q") || "";
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<"grouped" | "flat">("grouped");
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (query) {
      setLoading(true);
      setExpandedItems(new Set());
      search(query)
        .then((r) => setResults(r.data))
        .finally(() => setLoading(false));
    }
  }, [query]);

  const grouped = useMemo(
    () => (results ? groupItemsByName(results.items) : []),
    [results]
  );

  // Auto-expand when there's only one grouped result
  useEffect(() => {
    if (grouped.length === 1 && grouped[0]) {
      setExpandedItems(new Set([grouped[0].name]));
    }
  }, [grouped]);

  function toggleExpanded(name: string) {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  if (!query) {
    return (
      <div className="text-center py-16 text-slate-400 dark:text-slate-500">
        Enter a search query to find boxes and items.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-16 text-slate-400 dark:text-slate-500">
        Searching...
      </div>
    );
  }

  if (!results || (results.boxes.length === 0 && results.items.length === 0)) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-500 dark:text-slate-400">
          No results for "<span className="font-semibold">{query}</span>"
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="stencil-heading mb-6">Results for "{query}"</h1>

      {/* Boxes */}
      {results.boxes.length > 0 && (
        <section className="mb-8">
          <h2 className="section-label mb-3">
            Boxes ({results.boxes.length})
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {results.boxes.map((box) => (
              <Link
                key={box.id}
                to={`/boxes/${box.id}`}
                className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg p-4 hover:border-l-4 hover:border-l-amber-400 transition-all"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="box-code">{box.box_code}</span>
                  <span className="text-xs text-slate-400 font-mono">
                    {box.match_type === "contains_match"
                      ? "contains match"
                      : "direct match"}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 truncate">
                  {box.name}
                </h3>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <Package size={12} />
                    {box.item_count} items
                  </span>
                  {box.latitude != null && (
                    <span className="flex items-center gap-1">
                      <MapPin size={12} />
                      {box.latitude.toFixed(3)}, {box.longitude?.toFixed(3)}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Items */}
      {results.items.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-label">
              Items ({results.items.length})
            </h2>
            <div className="flex items-center bg-slate-100 dark:bg-navy-800 rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode("grouped")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                  viewMode === "grouped"
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                <Layers size={14} />
                By Item
              </button>
              <button
                onClick={() => setViewMode("flat")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wider font-medium transition-colors ${
                  viewMode === "flat"
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                <List size={14} />
                Flat
              </button>
            </div>
          </div>

          {viewMode === "grouped" ? (
            <div className="space-y-2">
              {grouped.map((group) => {
                const isExpanded = expandedItems.has(group.name);
                return (
                  <div
                    key={group.name}
                    className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg overflow-hidden"
                  >
                    {/* Group header — clickable to expand */}
                    <button
                      onClick={() => toggleExpanded(group.name)}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-navy-800 transition-colors"
                    >
                      <ChevronRight
                        size={16}
                        className={`text-slate-400 transition-transform ${
                          isExpanded ? "rotate-90" : ""
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-slate-800 dark:text-slate-200">
                          {group.name}
                        </span>
                        {group.allTags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {group.allTags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 text-xs font-mono bg-slate-200 dark:bg-navy-700 text-slate-600 dark:text-slate-400 rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="text-right shrink-0">
                        <span className="font-mono text-sm text-slate-500 dark:text-slate-400">
                          &times;{group.totalQuantity}
                        </span>
                        <div className="text-xs text-slate-400 dark:text-slate-500">
                          {group.locations.length} box
                          {group.locations.length !== 1 ? "es" : ""}
                        </div>
                      </div>
                    </button>

                    {/* Expanded location list */}
                    {isExpanded && (
                      <div className="border-t border-slate-100 dark:border-navy-800">
                        {group.locations.map((loc, idx) => (
                          <Link
                            key={loc.id}
                            to={`/boxes/${loc.box_id}`}
                            className={`flex items-center justify-between px-4 py-2.5 pl-11 hover:bg-amber-50 dark:hover:bg-amber-900/10 transition-colors ${
                              idx > 0
                                ? "border-t border-slate-50 dark:border-navy-800/50"
                                : ""
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <span className="box-code text-xs">
                                {loc.box_code}
                              </span>
                              <span className="text-sm text-slate-600 dark:text-slate-400">
                                {loc.box_name}
                              </span>
                            </div>
                            <span className="font-mono text-sm text-slate-500 dark:text-slate-400">
                              qty {loc.quantity}
                            </span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            /* Flat view — original layout */
            <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg overflow-hidden">
              {results.items.map((item, idx) => (
                <div
                  key={item.id}
                  className={`flex items-center justify-between px-4 py-3 ${
                    idx > 0
                      ? "border-t border-slate-100 dark:border-navy-800"
                      : ""
                  }`}
                >
                  <div className="flex-1">
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {item.name}
                    </span>
                    <span className="ml-2 font-mono text-sm text-slate-500">
                      &times;{item.quantity}
                    </span>
                    {item.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {item.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 text-xs font-mono bg-slate-200 dark:bg-navy-700 text-slate-600 dark:text-slate-400 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <Link
                    to={`/boxes/${item.box_id}`}
                    className="text-right ml-4"
                  >
                    <span className="box-code text-xs">{item.box_code}</span>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {item.box_name}
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
