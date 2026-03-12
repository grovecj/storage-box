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

      {/* QR Code - print optimized */}
      <div className="flex flex-col items-center py-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
          <QRCodeSVG
            value={qrUrl}
            size={256}
            level="M"
            includeMargin={false}
            imageSettings={{
              src: "",
              height: 0,
              width: 0,
              excavate: false,
            }}
          />
        </div>

        <div className="mt-6 text-center">
          <div className="text-2xl font-mono font-bold tracking-wider text-amber-600 dark:text-amber-400">
            {box.box_code}
          </div>
          <div className="mt-1 text-lg font-semibold text-slate-700 dark:text-slate-300">
            {box.name}
          </div>
        </div>
      </div>
    </div>
  );
}
