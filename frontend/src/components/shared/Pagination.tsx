import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const totalPages = pageSize === 0 ? 1 : Math.ceil(total / pageSize);
  const sizes = [10, 25, 0]; // 0 = ALL

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4">
      <div className="flex items-center gap-2">
        <span className="section-label">Show</span>
        {sizes.map((s) => (
          <button
            key={s}
            onClick={() => {
              onPageSizeChange(s);
              onPageChange(1);
            }}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              pageSize === s
                ? "bg-amber-500 text-slate-900 font-semibold"
                : "bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700"
            }`}
          >
            {s === 0 ? "ALL" : s}
          </button>
        ))}
      </div>

      {pageSize !== 0 && totalPages > 1 && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-1.5 rounded bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm font-mono text-slate-600 dark:text-slate-400 min-w-[80px] text-center">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1.5 rounded bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      <div className="text-xs font-mono text-slate-500 dark:text-slate-500">
        {total} total
      </div>
    </div>
  );
}
