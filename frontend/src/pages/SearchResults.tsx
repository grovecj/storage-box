import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Package, MapPin } from "lucide-react";
import { search } from "@/api/client";
import type { SearchResult } from "@/types";

export default function SearchResults() {
  const [params] = useSearchParams();
  const query = params.get("q") || "";
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (query) {
      setLoading(true);
      search(query)
        .then((r) => setResults(r.data))
        .finally(() => setLoading(false));
    }
  }, [query]);

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
      <h1 className="stencil-heading mb-6">
        Results for "{query}"
      </h1>

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
          <h2 className="section-label mb-3">
            Items ({results.items.length})
          </h2>
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
        </section>
      )}
    </div>
  );
}
