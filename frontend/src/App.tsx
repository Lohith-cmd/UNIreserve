import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/useAuth";
import { homeFor } from "./utils/homeFor";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import BrowseBook from "./pages/BrowseBook";
import MyBookings from "./pages/MyBookings";
import AdminApprovals from "./pages/AdminApprovals";
import AdminAnalytics from "./pages/AdminAnalytics";
import AdminManage from "./pages/AdminManage";

function RootRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? homeFor(user.role) : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute allowedRoles={["Student", "Faculty"]} />}>
        <Route element={<Layout />}>
          <Route path="/book" element={<BrowseBook />} />
          <Route path="/my-bookings" element={<MyBookings />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["Admin"]} />}>
        <Route element={<Layout />}>
          <Route path="/admin" element={<AdminApprovals />} />
          <Route path="/admin/analytics" element={<AdminAnalytics />} />
          <Route path="/admin/manage" element={<AdminManage />} />
        </Route>
      </Route>

      <Route path="*" element={<RootRedirect />} />
    </Routes>
  );
}