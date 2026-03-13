import { useEffect, useState } from "react";
import { Package } from "lucide-react";
import api from "@/api/client";

export default function Login() {
  const [isDevMode, setIsDevMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if we're in dev mode (OAuth not configured)
    const checkDevMode = async () => {
      try {
        // Try to get dev token to see if it's available
        const response = await api.get("/auth/dev-token");
        if (response.status === 200) {
          setIsDevMode(true);
        }
      } catch (err) {
        // If dev-token endpoint returns 403, OAuth is configured
        setIsDevMode(false);
      }
    };
    checkDevMode();
  }, []);

  const handleGoogleLogin = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = "/api/v1/auth/google";
  };

  const handleDevLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get("/auth/dev-token");
      const token = response.data.access_token;
      localStorage.setItem("auth_token", token);
      window.location.href = "/";
    } catch (err) {
      setError("Dev login failed. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-amber-500 p-4 rounded-2xl">
              <Package className="w-12 h-12 text-white" />
            </div>
          </div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
            Storage Boxes
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Track the location and contents of your storage containers
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-6">
          <div className="space-y-4">
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span className="font-medium">Sign in with Google</span>
            </button>

            {isDevMode && (
              <button
                onClick={handleDevLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-amber-500 rounded-lg shadow-sm bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="font-medium">
                  {loading ? "Signing in..." : "Dev Login (localhost only)"}
                </span>
              </button>
            )}

            {error && (
              <div className="text-sm text-red-600 dark:text-red-400 text-center">
                {error}
              </div>
            )}
          </div>

          <div className="text-center text-sm text-gray-500 dark:text-gray-400">
            <p>
              Sign in to access your boxes and inventory.
            </p>
          </div>
        </div>

        <div className="text-center text-xs text-gray-500 dark:text-gray-400">
          <p>Mobile-first web app for tracking storage containers</p>
        </div>
      </div>
    </div>
  );
}
