import { useState, useEffect } from "react";
import { Download, Filter } from "lucide-react";
import { X } from "lucide-react";
import { listBoxes, listTags, generateReport } from "@/api/client";
import type { StorageBox, Tag, ReportRequest } from "@/types";

export default function Reports() {
  const [boxes, setBoxes] = useState<StorageBox[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [allBoxes, setAllBoxes] = useState(true);
  const [selectedBoxIds, setSelectedBoxIds] = useState<number[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [locationFilter, setLocationFilter] = useState("");
  const [format, setFormat] = useState<"html" | "pdf" | "csv" | "text">("html");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    listBoxes({ page: 1, page_size: 100 }).then((r) => setBoxes(r.data.boxes));
    listTags().then((r) => setTags(r.data));
  }, []);

  const toggleBox = (id: number) => {
    setSelectedBoxIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleTag = (name: string) => {
    setSelectedTags((prev) =>
      prev.includes(name) ? prev.filter((x) => x !== name) : [...prev, name]
    );
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const request: ReportRequest = {
        box_ids: allBoxes ? null : selectedBoxIds,
        tag_filter: selectedTags,
        location_filter: locationFilter.trim() || undefined,
        format,
      };

      const response = await generateReport(request);

      if (format === "html") {
        const blob = new Blob([response.data as string], { type: "text/html" });
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
      } else if (format === "text") {
        const blob = new Blob([response.data as string], { type: "text/plain; charset=utf-8" });
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
      } else if (format === "pdf") {
        const blob = new Blob([response.data as BlobPart], {
          type: "application/pdf",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "inventory-report.pdf";
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const blob = new Blob([response.data as BlobPart], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "inventory-report.csv";
        a.click();
        URL.revokeObjectURL(url);
      }
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="stencil-heading mb-6">Generate Report</h1>

      <div className="space-y-6">
        {/* Box selection */}
        <div>
          <h2 className="section-label mb-3">Include Boxes</h2>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="radio"
                checked={allBoxes}
                onChange={() => setAllBoxes(true)}
                className="accent-amber-500"
              />
              All boxes
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="radio"
                checked={!allBoxes}
                onChange={() => setAllBoxes(false)}
                className="accent-amber-500"
              />
              Selected boxes
            </label>
          </div>

          {!allBoxes && (
            <div className="mt-3 max-h-48 overflow-y-auto bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md p-3 space-y-1.5">
              {boxes.map((box) => (
                <label
                  key={box.id}
                  className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-100 dark:hover:bg-navy-700 px-2 py-1 rounded"
                >
                  <input
                    type="checkbox"
                    checked={selectedBoxIds.includes(box.id)}
                    onChange={() => toggleBox(box.id)}
                    className="accent-amber-500"
                  />
                  <span className="font-mono text-xs text-amber-600 dark:text-amber-400">
                    {box.box_code}
                  </span>
                  <span className="truncate">{box.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Tag filter */}
        <div>
          <h2 className="section-label mb-3 flex items-center gap-1">
            <Filter size={12} />
            Filter by Tags
          </h2>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <button
                key={tag.id}
                onClick={() => toggleTag(tag.name)}
                className={`px-3 py-1 text-xs font-mono rounded-full border transition-colors ${
                  selectedTags.includes(tag.name)
                    ? "bg-amber-500 text-slate-900 border-amber-500"
                    : "bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-navy-700 hover:border-amber-400"
                }`}
              >
                {selectedTags.includes(tag.name) && (
                  <X size={10} className="inline mr-1" />
                )}
                {tag.name}
              </button>
            ))}
            {tags.length === 0 && (
              <span className="text-xs text-slate-400">No tags available</span>
            )}
          </div>
        </div>

        {/* Location filter */}
        <div>
          <h2 className="section-label mb-3 flex items-center gap-1">
            <Filter size={12} />
            Filter by Location
          </h2>
          <input
            type="text"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            placeholder='e.g. "Garage" or "Shelf 3"'
            className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
          />
        </div>

        {/* Format */}
        <div>
          <h2 className="section-label mb-3">Format</h2>
          <div className="flex items-center bg-slate-100 dark:bg-navy-800 rounded-md overflow-hidden w-fit">
            {(["html", "pdf", "csv", "text"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFormat(f)}
                className={`px-4 py-2 text-xs uppercase tracking-wider font-medium transition-colors ${
                  format === f
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Generate */}
        <button
          onClick={handleGenerate}
          disabled={generating || (!allBoxes && selectedBoxIds.length === 0)}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Download size={16} />
          {generating ? "Generating..." : "Generate Report"}
        </button>
      </div>
    </div>
  );
}
