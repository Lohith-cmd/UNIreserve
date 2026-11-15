import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { getErrorMessage } from "../api/errors";
import { homeFor } from "../utils/homeFor";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

const quickLogins = [
  { label: "Student", email: "student@uni.edu" },
  { label: "Faculty", email: "faculty@uni.edu" },
  { label: "Admin", email: "admin@uni.edu" },
];

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  async function doLogin(e: string, p: string) {
    setError("");
    setLoading(true);
    try {
      const u = await login(e, p);
      navigate(homeFor(u.role), { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(ev: FormEvent) {
    ev.preventDefault();
    doLogin(email, password);
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={handleSubmit}>
        <h1>UNIreserve</h1>
        <p className="muted">Sign in to book campus facilities</p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && <div className="error-banner">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>

        {USE_MOCK && (
          <div className="quick-login">
            <p className="muted">Mock mode: quick login as</p>
            {quickLogins.map((q) => (
              <button
                key={q.label}
                type="button"
                disabled={loading}
                onClick={() => doLogin(q.email, "mock")}
              >
                {q.label}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}