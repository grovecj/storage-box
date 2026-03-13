import { useState, useEffect, useCallback } from "react";
import { Edit, ArrowLeftRight, Trash2, Plus, X } from "lucide-react";
import Pagination from "@/components/shared/Pagination";
import Modal from "@/components/shared/Modal";
import { listItems, updateItem, removeItem, listTags } from "@/api/client";
import type { BoxItem, Tag } from "@/types";

interface ItemTableProps {
  boxId: number;
  onTransfer: (item: BoxItem) => void;
  refreshKey: number;
}

export default function ItemTable({ boxId, onTransfer, refreshKey }: ItemTableProps) {
  const [items, setItems] = useState<BoxItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [editingItem, setEditingItem] = useState<BoxItem | null>(null);
  const [editQty, setEditQty] = useState(1);
  const [editTags, setEditTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [newTag, setNewTag] = useState("");
  const [deleteItem, setDeleteItem] = useState<BoxItem | null>(null);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listItems(boxId, { page, page_size: pageSize });
      setItems(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  }, [boxId, page, pageSize]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems, refreshKey]);

  const handleEdit = (item: BoxItem) => {
    setEditingItem(item);
    setEditQty(item.quantity);
    setEditTags([...item.tags]);
    listTags().then((r) => setAvailableTags(r.data));
  };

  const handleSaveEdit = async () => {
    if (!editingItem) return;
    await updateItem(boxId, editingItem.item_id, {
      quantity: editQty,
      tags: editTags,
    });
    setEditingItem(null);
    fetchItems();
  };

  const handleDelete = async () => {
    if (!deleteItem) return;
    await removeItem(boxId, deleteItem.item_id);
    setDeleteItem(null);
    fetchItems();
  };

  const addEditTag = (tag: string) => {
    const t = tag.trim().toUpperCase();
    if (t && !editTags.includes(t)) setEditTags([...editTags, t]);
    setNewTag("");
  };

  if (loading && items.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 dark:text-slate-500">
        Loading items...
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-slate-400 dark:text-slate-500 text-sm">
          No items in this box yet
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-navy-700">
              <th className="text-left py-2 px-3 section-label">Name</th>
              <th className="text-left py-2 px-3 section-label">Qty</th>
              <th className="text-left py-2 px-3 section-label">Tags</th>
              <th className="text-right py-2 px-3 section-label">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className="border-b border-slate-100 dark:border-navy-800 hover:bg-slate-50 dark:hover:bg-navy-800/50 transition-colors"
              >
                <td className="py-3 px-3 font-medium text-slate-800 dark:text-slate-200">
                  {item.name}
                </td>
                <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-400">
                  {item.quantity}
                </td>
                <td className="py-3 px-3">
                  <div className="flex flex-wrap gap-1">
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 text-xs font-mono bg-slate-200 dark:bg-navy-700 text-slate-600 dark:text-slate-400 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="flex justify-end gap-1">
                    <button
                      onClick={() => handleEdit(item)}
                      className="p-1.5 rounded text-slate-400 hover:text-amber-500 hover:bg-slate-100 dark:hover:bg-navy-700 transition-colors"
                      title="Edit"
                    >
                      <Edit size={15} />
                    </button>
                    <button
                      onClick={() => onTransfer(item)}
                      className="p-1.5 rounded text-slate-400 hover:text-blue-500 hover:bg-slate-100 dark:hover:bg-navy-700 transition-colors"
                      title="Transfer"
                    >
                      <ArrowLeftRight size={15} />
                    </button>
                    <button
                      onClick={() => setDeleteItem(item)}
                      className="p-1.5 rounded text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-navy-700 transition-colors"
                      title="Remove"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="sm:hidden space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-lg p-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-slate-800 dark:text-slate-200">
                  {item.name}
                </div>
                <div className="font-mono text-sm text-slate-500 mt-1">
                  Qty: {item.quantity}
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => handleEdit(item)}
                  className="p-1.5 rounded text-slate-400 hover:text-amber-500"
                >
                  <Edit size={15} />
                </button>
                <button
                  onClick={() => onTransfer(item)}
                  className="p-1.5 rounded text-slate-400 hover:text-blue-500"
                >
                  <ArrowLeftRight size={15} />
                </button>
                <button
                  onClick={() => setDeleteItem(item)}
                  className="p-1.5 rounded text-slate-400 hover:text-red-500"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
            {item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
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
        ))}
      </div>

      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Edit modal */}
      <Modal
        open={!!editingItem}
        onClose={() => setEditingItem(null)}
        title="Edit Item"
      >
        {editingItem && (
          <div className="space-y-4">
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Editing <strong>{editingItem.name}</strong>
            </div>
            <div>
              <label className="section-label">Quantity</label>
              <input
                type="number"
                min={1}
                value={editQty}
                onChange={(e) => setEditQty(Math.max(1, parseInt(e.target.value) || 1))}
                className="mt-1 w-24 px-3 py-2 text-sm font-mono bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
              />
            </div>
            <div>
              <label className="section-label">Tags</label>
              <div className="mt-1 flex flex-wrap gap-2 mb-2">
                {editTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono bg-slate-200 dark:bg-navy-700 text-slate-700 dark:text-slate-300 rounded-full"
                  >
                    {tag}
                    <button
                      onClick={() => setEditTags(editTags.filter((t) => t !== tag))}
                      className="hover:text-red-500"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {availableTags
                  .filter((t) => !editTags.includes(t.name))
                  .map((tag) => (
                    <button
                      key={tag.id}
                      onClick={() => addEditTag(tag.name)}
                      className="px-2 py-0.5 text-xs font-mono bg-slate-100 dark:bg-navy-800 text-slate-500 dark:text-slate-400 rounded-full hover:bg-amber-100 dark:hover:bg-amber-900/30 hover:text-amber-600 dark:hover:text-amber-400 transition-colors border border-slate-200 dark:border-navy-700"
                    >
                      + {tag.name}
                    </button>
                  ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addEditTag(newTag);
                    }
                  }}
                  placeholder="New tag..."
                  className="flex-1 px-3 py-1.5 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
                />
                <button
                  onClick={() => addEditTag(newTag)}
                  disabled={!newTag.trim()}
                  className="p-1.5 bg-slate-200 dark:bg-navy-700 rounded-md hover:bg-slate-300 dark:hover:bg-navy-600 disabled:opacity-30 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setEditingItem(null)}
                className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete confirmation */}
      <Modal
        open={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        title="Remove Item"
      >
        {deleteItem && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Remove <strong>{deleteItem.name}</strong> (qty: {deleteItem.quantity}) from this box?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteItem(null)}
                className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
