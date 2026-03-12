import { useState, useEffect, useRef } from "react";
import { Plus, X } from "lucide-react";
import Modal from "@/components/shared/Modal";
import { addItem, autocompleteItems, listTags } from "@/api/client";
import type { Tag } from "@/types";

interface AddItemModalProps {
  open: boolean;
  boxId: number;
  onClose: () => void;
  onAdded: () => void;
}

export default function AddItemModal({
  open,
  boxId,
  onClose,
  onAdded,
}: AddItemModalProps) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [suggestions, setSuggestions] = useState<{ id: number; name: string }[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      listTags().then((r) => setAvailableTags(r.data));
    }
  }, [open]);

  useEffect(() => {
    if (name.length >= 2) {
      const timer = setTimeout(() => {
        autocompleteItems(name).then((r) => {
          setSuggestions(r.data);
          setShowSuggestions(true);
        });
      }, 200);
      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [name]);

  const handleSubmit = async () => {
    if (!name.trim() || quantity < 1) return;
    setSaving(true);
    setError(null);
    try {
      await addItem(boxId, {
        name: name.trim(),
        quantity,
        tags: selectedTags,
      });
      setName("");
      setQuantity(1);
      setSelectedTags([]);
      onAdded();
      onClose();
    } catch {
      setError("Failed to add item");
    } finally {
      setSaving(false);
    }
  };

  const addTag = (tag: string) => {
    const t = tag.trim().toUpperCase();
    if (t && !selectedTags.includes(t)) {
      setSelectedTags([...selectedTags, t]);
    }
    setNewTag("");
  };

  const removeTag = (tag: string) => {
    setSelectedTags(selectedTags.filter((t) => t !== tag));
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Item">
      <div className="space-y-4">
        {/* Item name with autocomplete */}
        <div className="relative">
          <label className="section-label">Item Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="e.g. USB Cable"
            className="mt-1 w-full px-3 py-2 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
            autoFocus
          />
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute z-10 mt-1 w-full bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md shadow-lg max-h-40 overflow-y-auto"
            >
              {suggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setName(s.name);
                    setShowSuggestions(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-navy-700 text-slate-700 dark:text-slate-300"
                >
                  {s.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quantity */}
        <div>
          <label className="section-label">Quantity</label>
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="mt-1 w-24 px-3 py-2 text-sm font-mono bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="section-label">Tags</label>
          <div className="mt-1 flex flex-wrap gap-2 mb-2">
            {selectedTags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono bg-slate-200 dark:bg-navy-700 text-slate-700 dark:text-slate-300 rounded-full"
              >
                {tag}
                <button
                  onClick={() => removeTag(tag)}
                  className="hover:text-red-500"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>

          {/* Existing tags to click-add */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {availableTags
              .filter((t) => !selectedTags.includes(t.name))
              .map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => addTag(tag.name)}
                  className="px-2 py-0.5 text-xs font-mono bg-slate-100 dark:bg-navy-800 text-slate-500 dark:text-slate-400 rounded-full hover:bg-amber-100 dark:hover:bg-amber-900/30 hover:text-amber-600 dark:hover:text-amber-400 transition-colors border border-slate-200 dark:border-navy-700"
                >
                  + {tag.name}
                </button>
              ))}
          </div>

          {/* Custom tag input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTag(newTag);
                }
              }}
              placeholder="New tag..."
              className="flex-1 px-3 py-1.5 text-sm bg-slate-50 dark:bg-navy-800 border border-slate-200 dark:border-navy-700 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-400/50 text-slate-800 dark:text-slate-200"
            />
            <button
              onClick={() => addTag(newTag)}
              disabled={!newTag.trim()}
              className="p-1.5 bg-slate-200 dark:bg-navy-700 rounded-md hover:bg-slate-300 dark:hover:bg-navy-600 disabled:opacity-30 transition-colors"
            >
              <Plus size={16} />
            </button>
          </div>
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
            disabled={!name.trim() || saving}
            className="px-4 py-2 text-sm font-semibold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-900 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Adding..." : "Add Item"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
