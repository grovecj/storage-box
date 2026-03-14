interface GroupBadgeProps {
  name: string;
}

export default function GroupBadge({ name }: GroupBadgeProps) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium tracking-wide uppercase bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-navy-700 rounded">
      {name}
    </span>
  );
}
