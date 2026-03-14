import { useRef, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface GroupFilterProps {
  groups: Array<{ id: number; name: string; box_count: number }>;
  activeGroupId: number | null; // null = "All", -1 = "Ungrouped"
  onSelect: (groupId: number | null) => void;
}

export default function GroupFilter({
  groups,
  activeGroupId,
  onSelect,
}: GroupFilterProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = () => {
    if (!scrollRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 1);
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener("resize", checkScroll);
    return () => window.removeEventListener("resize", checkScroll);
  }, [groups]);

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = 200;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
    setTimeout(checkScroll, 150);
  };

  const ungroupedCount = groups.find((g) => g.id === -1)?.box_count || 0;
  const totalCount = groups.reduce((sum, g) => sum + g.box_count, 0);
  const filteredGroups = groups.filter((g) => g.id !== -1);

  return (
    <div className="relative mb-6">
      {canScrollLeft && (
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 flex items-center justify-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-full shadow-md hover:bg-slate-50 dark:hover:bg-navy-800 transition-colors"
          aria-label="Scroll left"
        >
          <ChevronLeft size={16} className="text-slate-600 dark:text-slate-400" />
        </button>
      )}
      {canScrollRight && (
        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 flex items-center justify-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-full shadow-md hover:bg-slate-50 dark:hover:bg-navy-800 transition-colors"
          aria-label="Scroll right"
        >
          <ChevronRight size={16} className="text-slate-600 dark:text-slate-400" />
        </button>
      )}

      <div
        ref={scrollRef}
        onScroll={checkScroll}
        className="flex gap-2 overflow-x-auto pb-2 px-1"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {/* All */}
        <button
          onClick={() => onSelect(null)}
          className={`flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-wider font-medium whitespace-nowrap rounded-md border transition-all ${
            activeGroupId === null
              ? "bg-amber-500 text-slate-900 border-amber-500 shadow-md"
              : "bg-white dark:bg-navy-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-navy-700 hover:border-amber-400 dark:hover:border-amber-500 hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          All
          <span className="font-mono text-[10px] opacity-75">{totalCount}</span>
        </button>

        {/* Groups */}
        {filteredGroups.map((group) => (
          <button
            key={group.id}
            onClick={() => onSelect(group.id)}
            className={`flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-wider font-medium whitespace-nowrap rounded-md border transition-all ${
              activeGroupId === group.id
                ? "bg-amber-500 text-slate-900 border-amber-500 shadow-md"
                : "bg-white dark:bg-navy-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-navy-700 hover:border-amber-400 dark:hover:border-amber-500 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            {group.name}
            <span className="font-mono text-[10px] opacity-75">
              {group.box_count}
            </span>
          </button>
        ))}

        {/* Ungrouped */}
        {ungroupedCount > 0 && (
          <button
            onClick={() => onSelect(-1)}
            className={`flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-wider font-medium whitespace-nowrap rounded-md border transition-all ${
              activeGroupId === -1
                ? "bg-amber-500 text-slate-900 border-amber-500 shadow-md"
                : "bg-white dark:bg-navy-900 text-slate-500 dark:text-slate-500 border-slate-200 dark:border-navy-700 border-dashed hover:border-amber-400 dark:hover:border-amber-500 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            Ungrouped
            <span className="font-mono text-[10px] opacity-75">
              {ungroupedCount}
            </span>
          </button>
        )}
      </div>
    </div>
  );
}
