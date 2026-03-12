import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Printer, ChevronLeft } from "lucide-react";
import { listBoxes, getConfig } from "@/api/client";
import type { StorageBox } from "@/types";

type Layout = "letter" | "avery";

export default function QRBatchPrint() {
  const navigate = useNavigate();
  const [boxes, setBoxes] = useState<StorageBox[]>([]);
  const [baseUrl, setBaseUrl] = useState("");
  const [layout, setLayout] = useState<Layout>("letter");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listBoxes({ page: 1, page_size: 100 }),
      getConfig(),
    ]).then(([boxRes, configRes]) => {
      setBoxes(boxRes.data.boxes);
      setBaseUrl(configRes.data.base_url);
      setLoading(false);
    });
  }, []);

  const labelsPerPage = layout === "letter" ? 12 : 8;
  const cols = layout === "letter" ? 3 : 2;
  const pages: StorageBox[][] = [];
  for (let i = 0; i < boxes.length; i += labelsPerPage) {
    pages.push(boxes.slice(i, i + labelsPerPage));
  }

  if (loading) {
    return (
      <div className="text-center py-16 text-slate-400 dark:text-slate-500">
        Loading...
      </div>
    );
  }

  return (
    <div>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { margin: 0; padding: 0; }

          .batch-page {
            page-break-after: always;
            display: grid !important;
          }
          .batch-page:last-child {
            page-break-after: auto;
          }

          /* Letter layout: 3x4 grid of 2.5"x2.5" labels */
          .batch-page.layout-letter {
            grid-template-columns: repeat(3, 2.5in);
            grid-template-rows: repeat(4, 2.5in);
            gap: 0;
            justify-content: center;
          }
          @page {
            size: letter;
            margin: 0.5in;
          }
          .layout-letter .batch-label {
            width: 2.5in;
            height: 2.5in;
            border: 1px solid #000;
            padding: 0.1in;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
          }
          .layout-letter .batch-label svg {
            width: 1.6in !important;
            height: 1.6in !important;
          }

          /* Avery 94237: 2x4 grid of 2"x3" labels */
          .batch-page.layout-avery {
            grid-template-columns: repeat(2, 4in);
            grid-template-rows: repeat(4, 2in);
            gap: 0;
            justify-content: center;
          }
          .layout-avery .batch-label {
            width: 4in;
            height: 2in;
            border: 1px dashed #ccc;
            padding: 0.1in;
            box-sizing: border-box;
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 0.15in;
          }
          .layout-avery .batch-label svg {
            width: 1.5in !important;
            height: 1.5in !important;
            flex-shrink: 0;
          }

          .batch-label-code {
            font-size: 10pt;
            font-weight: bold;
            font-family: monospace;
            letter-spacing: 0.04em;
          }
          .batch-label-name {
            font-size: 7pt;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 100%;
          }

          .screen-preview { display: none !important; }
        }

        @media not print {
          .print-only { display: none; }
        }
      `}</style>

      {/* Controls */}
      <div className="no-print">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 transition-colors"
          >
            <ChevronLeft size={16} />
            Back to Inventory
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
          >
            <Printer size={16} />
            Print All
          </button>
        </div>

        <div className="mb-6">
          <h1 className="stencil-heading mb-4">Batch QR Print</h1>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-slate-500 dark:text-slate-400">Layout:</span>
            <div className="flex items-center bg-slate-100 dark:bg-navy-800 rounded-md overflow-hidden">
              <button
                onClick={() => setLayout("letter")}
                className={`px-4 py-2 text-xs uppercase tracking-wider font-medium transition-colors ${
                  layout === "letter"
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                Letter Grid (12/page)
              </button>
              <button
                onClick={() => setLayout("avery")}
                className={`px-4 py-2 text-xs uppercase tracking-wider font-medium transition-colors ${
                  layout === "avery"
                    ? "bg-amber-500 text-slate-900"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
              >
                Avery 94237 (8/page)
              </button>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            {boxes.length} box{boxes.length !== 1 ? "es" : ""} &middot;{" "}
            {pages.length} page{pages.length !== 1 ? "s" : ""} &middot;{" "}
            {layout === "letter" ? "2.5\" x 2.5\" labels, 3x4 grid" : "Avery Presta 94237 (4\" x 2\"), 2x4 grid"}
          </p>
        </div>

        {/* Screen preview */}
        <div className="screen-preview space-y-8">
          {pages.map((page, pi) => (
            <div key={pi} className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-3">Page {pi + 1} of {pages.length}</div>
              <div
                className="grid gap-3"
                style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
              >
                {page.map((box) => (
                  <div
                    key={box.id}
                    className="border border-slate-200 dark:border-navy-700 rounded p-3 flex flex-col items-center"
                  >
                    <QRCodeSVG
                      value={`${baseUrl}/boxes/code/${box.box_code}`}
                      size={layout === "letter" ? 100 : 80}
                      level="M"
                      includeMargin={false}
                    />
                    <div className="mt-2 text-xs font-mono font-bold text-center">
                      {box.box_code}
                    </div>
                    <div className="text-xs text-slate-500 truncate max-w-full text-center">
                      {box.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Print-only pages */}
      <div className="print-only">
        {pages.map((page, pi) => (
          <div key={pi} className={`batch-page layout-${layout}`}>
            {page.map((box) => (
              <div key={box.id} className="batch-label">
                <QRCodeSVG
                  value={`${baseUrl}/boxes/code/${box.box_code}`}
                  size={layout === "letter" ? 140 : 120}
                  level="M"
                  includeMargin={false}
                />
                {layout === "letter" ? (
                  <>
                    <div className="batch-label-code" style={{ marginTop: "4px" }}>{box.box_code}</div>
                    <div className="batch-label-name">{box.name}</div>
                  </>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", overflow: "hidden", minWidth: 0 }}>
                    <div className="batch-label-code">{box.box_code}</div>
                    <div className="batch-label-name" style={{ marginTop: "4px" }}>{box.name}</div>
                    {box.location_name && (
                      <div style={{ fontSize: "6pt", color: "#666", marginTop: "2px" }}>{box.location_name}</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {boxes.length === 0 && (
        <div className="text-center py-16 text-slate-400">
          No boxes to print. Create some boxes first.
        </div>
      )}
    </div>
  );
}
