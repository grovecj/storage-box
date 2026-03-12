import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Printer, ChevronLeft } from "lucide-react";
import { getBox, getConfig } from "@/api/client";
import type { StorageBox } from "@/types";

export default function QRPrint() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [box, setBox] = useState<StorageBox | null>(null);
  const [baseUrl, setBaseUrl] = useState("");

  useEffect(() => {
    if (id) {
      getBox(parseInt(id)).then((r) => setBox(r.data));
      getConfig().then((r) => setBaseUrl(r.data.base_url));
    }
  }, [id]);

  if (!box) {
    return (
      <div className="text-center py-16 text-slate-400 dark:text-slate-500">
        Loading...
      </div>
    );
  }

  const qrUrl = `${baseUrl}/boxes/code/${box.box_code}`;

  return (
    <div>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { margin: 0; padding: 0; }
          .qr-label {
            width: 2.5in;
            height: 2.5in;
            border: 2px solid #000;
            padding: 0.15in;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            box-sizing: border-box;
          }
          .qr-label svg {
            width: 1.8in !important;
            height: 1.8in !important;
          }
          .qr-label-code {
            font-size: 11pt;
            font-weight: bold;
            font-family: monospace;
            letter-spacing: 0.05em;
            margin-top: 4px;
          }
          .qr-label-name {
            font-size: 8pt;
            margin-top: 2px;
          }
          .qr-screen-preview { display: none; }
        }
        @media not print {
          .qr-print-only { display: none; }
        }
      `}</style>

      {/* Controls - hidden when printing */}
      <div className="no-print flex items-center justify-between mb-8">
        <button
          onClick={() => navigate(`/boxes/${box.id}`)}
          className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-amber-500 transition-colors"
        >
          <ChevronLeft size={16} />
          Back to {box.box_code}
        </button>
        <button
          onClick={() => window.print()}
          className="flex items-center gap-2 px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
        >
          <Printer size={16} />
          Print
        </button>
      </div>

      {/* Screen preview */}
      <div className="qr-screen-preview flex flex-col items-center py-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200" style={{ width: "2.5in", height: "2.5in", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <QRCodeSVG
            value={qrUrl}
            size={172}
            level="M"
            includeMargin={false}
          />
          <div className="mt-1 text-center">
            <div className="text-sm font-mono font-bold tracking-wider">
              {box.box_code}
            </div>
            <div className="text-xs text-slate-600 truncate max-w-[2in]">
              {box.name}
            </div>
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-400">Prints at 2.5" &times; 2.5" with border</p>
      </div>

      {/* Print-only label */}
      <div className="qr-print-only">
        <div className="qr-label">
          <QRCodeSVG
            value={qrUrl}
            size={172}
            level="M"
            includeMargin={false}
          />
          <div className="qr-label-code">{box.box_code}</div>
          <div className="qr-label-name">{box.name}</div>
        </div>
      </div>
    </div>
  );
}
