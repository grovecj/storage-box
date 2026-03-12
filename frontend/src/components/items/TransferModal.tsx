import { useState, useEffect } from "react";
import { ArrowLeftRight } from "lucide-react";
import Modal from "@/components/shared/Modal";
import { transferItem, listBoxes } from "@/api/client";
import type { BoxItem, StorageBox } from "@/types";

interface TransferModalProps {
  open: boolean;
  item: BoxItem | null;
  fromBoxId: number;
  fromBoxCode: string;
  onClose: () => void;
  onTransferred: () => void;
}

export default function TransferModal({
  open,
  item,
  fromBoxId,
  fromBoxCode,
  onClose,
  onTransferred,
}: TransferModalProps) {
  const [boxes, setBoxes] = useState<StorageBox[]>([]);
  const [toBoxId, setToBoxId] = useState<number | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      listBoxes({ page: 1, page_size: 100 }).then((r) => {
        setBoxes(r.data.boxes.filter((b) => b.id !== fromBoxId));
      });
      setQuantity(1);
      setToBoxId(null);
      setError(null);
    }
  }, [open, fromBoxId]);

  if (!item) return null;

  const handleSubmit = async () => {
    if (!toBoxId || quantity < 1) return;
    setSaving(true);
    setError(null);
    try {
      await transferItem({
        from_box_id: fromBoxId,
        to_box_id: toBoxId,
        item_id: item.item_id,
        quantity,
      });
      onTransferred();
      onClose();
    } catch {
      setError("Failed to transfer item");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Transfer Item">
      <div className="space-y-4">
        <div className="bg-slate-50 dark:bg-navy-800 rounded-md p-3">
          <div className="text-sm text-slate-500 dark:text-slate-400">Item</div>
          <div className="font-semibold text-slate-800 dark:text-slate-100">
            {item.name}
          </div>
          <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            From <span className="box-code">{fromBoxCode}</span> &middot;{" "}
            Available: <span className="font-mono">{item.quantity}</span>
          </div>
        </div>

        <div>
          <label className="section-label">Destination Box</label>
          <select
            value={toBoxId ?? ""}
            onChange={(e) => setToBoxId(parseInt(e.target.value))}
            className="mt-1 w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
          >
            <option value="">Select a box...</option>
            {boxes.map((b) => (
              <option key={b.id} value={b.id}>
                {b.box_code} — {b.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="section-label">Quantity</label>
          <input
            type="number"
            min={1}
            max={item.quantity}
            value={quantity}
            onChange={(e) =>
              setQuantity(
                Math.min(item.quantity, Math.max(1, parseInt(e.target.value) || 1))
              )
            }
            className="mt-1 w-24 px-3 py-2 text-sm font-mono bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
          />
          <span className="ml-2 text-xs text-slate-400">
            max {item.quantity}
          </span>
        </div>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!toBoxId || saving}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowLeftRight size={16} />
            {saving ? "Transferring..." : "Transfer"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
