import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Package, Search, Sun, Moon, Menu, X } from "lucide-react";

interface NavbarProps {
  theme: "light" | "dark";
  setTheme: (theme: "light" | "dark") => void;
}

export default function Navbar({ theme, setTheme }: NavbarProps) {
  const [query, setQuery] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setMobileOpen(false);
    }
  };

  return (
    <nav className="bg-slate-800 dark:bg-navy-950 border-b border-slate-700 dark:border-navy-800 no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link
            to="/"
            className="flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors"
          >
            <Package size={22} strokeWidth={2.5} />
            <span className="text-base font-bold uppercase tracking-[0.15em]">
              Storage Box
            </span>
          </Link>

          {/* Center: Search */}
          <form
            onSubmit={handleSearch}
            className="hidden sm:flex items-center flex-1 max-w-md mx-8"
          >
            <div className="relative w-full">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search boxes, items, tags..."
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-slate-700 dark:bg-navy-800 text-slate-200 placeholder-slate-400 rounded-md border border-slate-600 dark:border-navy-700 focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-colors"
              />
            </div>
          </form>

          {/* Right: Nav links + Theme */}
          <div className="hidden sm:flex items-center gap-4">
            <Link
              to="/"
              className="text-sm text-slate-300 hover:text-amber-400 uppercase tracking-wider font-medium transition-colors"
            >
              Inventory
            </Link>
            <Link
              to="/reports"
              className="text-sm text-slate-300 hover:text-amber-400 uppercase tracking-wider font-medium transition-colors"
            >
              Reports
            </Link>
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-md text-slate-400 hover:text-amber-400 hover:bg-slate-700 dark:hover:bg-navy-800 transition-colors"
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="sm:hidden p-2 rounded-md text-slate-400 hover:text-amber-400"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="sm:hidden pb-4 space-y-3">
            <form onSubmit={handleSearch}>
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search..."
                  className="w-full pl-9 pr-4 py-2 text-sm bg-slate-700 text-slate-200 placeholder-slate-400 rounded-md border border-slate-600 focus:outline-none focus:ring-2 focus:ring-amber-400/50"
                />
              </div>
            </form>
            <div className="flex flex-col gap-2">
              <Link
                to="/"
                onClick={() => setMobileOpen(false)}
                className="text-sm text-slate-300 hover:text-amber-400 uppercase tracking-wider font-medium py-1"
              >
                Inventory
              </Link>
              <Link
                to="/reports"
                onClick={() => setMobileOpen(false)}
                className="text-sm text-slate-300 hover:text-amber-400 uppercase tracking-wider font-medium py-1"
              >
                Reports
              </Link>
            </div>
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-amber-400 py-1"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
