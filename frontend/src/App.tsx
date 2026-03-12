import { Routes, Route } from "react-router-dom";
import { useTheme } from "@/hooks/useTheme";
import Navbar from "@/components/layout/Navbar";
import Dashboard from "@/pages/Dashboard";
import BoxDetail from "@/pages/BoxDetail";
import SearchResults from "@/pages/SearchResults";
import Reports from "@/pages/Reports";
import QRPrint from "@/pages/QRPrint";

export default function App() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
      <Navbar theme={theme} setTheme={setTheme} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/boxes/:id" element={<BoxDetail />} />
          <Route path="/boxes/code/:code" element={<BoxDetail />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/boxes/:id/qr" element={<QRPrint />} />
        </Routes>
      </main>
    </div>
  );
}
