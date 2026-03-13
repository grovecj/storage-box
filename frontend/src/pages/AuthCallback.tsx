import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export default function AuthCallback() {
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      // Read token from URL fragment (not query param) for security
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      const token = params.get("token");

      if (!token) {
        console.error("No token in callback URL");
        navigate("/login");
        return;
      }

      // Clear the fragment from the URL immediately
      window.history.replaceState(null, "", window.location.pathname);

      try {
        await login(token);
        navigate("/");
      } catch (error) {
        console.error("Login failed:", error);
        navigate("/login");
      }
    };

    handleCallback();
  }, [login, navigate]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-amber-500 animate-spin mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Completing sign in...</p>
      </div>
    </div>
  );
}
