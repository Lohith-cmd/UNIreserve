import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const studentFacultyLinks = [
  { to: "/book", label: "Browse & Book" },
  { to: "/my-bookings", label: "My Bookings" },
];

const adminLinks = [
  { to: "/admin", label: "Approvals" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/manage", label: "Manage" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const links = user?.role === "Admin" ? adminLinks : studentFacultyLinks;

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <>
      <nav className="navbar">
        <strong className="brand">UNIreserve</strong>
        <div className="nav-links">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-user">
          <span>
            {user?.name} ({user?.role})
          </span>
          <button onClick={handleLogout}>Log out</button>
        </div>
      </nav>
      <main className="page">
        <Outlet />
      </main>
    </>
  );
}