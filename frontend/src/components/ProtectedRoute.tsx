import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { homeFor } from "../utils/homeFor";
import type { Role } from "../types";

export default function ProtectedRoute({ allowedRoles }: { allowedRoles: Role[] }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={homeFor(user.role)} replace />;
  }
  return <Outlet />;
}