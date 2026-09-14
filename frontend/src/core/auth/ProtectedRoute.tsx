import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./useAuth";

export default function ProtectedRoute() {
  const { isLoading, isError } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="h-8 w-8 rounded-full border-2 border-white/20 border-t-white animate-spin" />
      </div>
    );
  }

  if (isError) return <Navigate to="/login" replace />;

  return <Outlet />;
}
