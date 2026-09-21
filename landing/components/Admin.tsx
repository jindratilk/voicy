"use client";
import { useEffect, useState } from "react";
import Mark from "./Mark";
type Stats = {
  days: { day: string; views: number; downloads: number }[];
  total: { views: number; downloads: number };
  updatedAt: string;
};
export default function Admin() {
  const [stats, setStats] = useState<Stats | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function load() {
    try {
      const r = await fetch("/api/stats");
      if (r.ok) setStats(await r.json());
      else if (r.status !== 401) setError("Statistics could not be loaded.");
    } catch {
      setError("Could not connect.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  async function login(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = new FormData(e.currentTarget);
    try {
      const r = await fetch("/api/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: f.get("email"),
          password: f.get("password"),
        }),
      });
      if (!r.ok) setError((await r.json()).error);
      else await load();
    } catch {
      setError("Could not connect.");
    } finally {
      setBusy(false);
    }
  }
  const days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() - 29 + i);
    const key = d.toISOString().slice(0, 10);
    return (
      stats?.days.find((x) => x.day === key) ?? {
        day: key,
        views: 0,
        downloads: 0,
      }
    );
  });
  const max = Math.max(...days.map((x) => x.downloads), 1);
  return (
    <main className="admin-shell">
      <header className="admin-header">
        <a className="brand" href="/">
          <Mark />
          voicy <span style={{ color: "#666", fontWeight: 400 }}> / admin</span>
        </a>
        {stats && (
          <button
            onClick={async () => {
              await fetch("/api/auth", { method: "DELETE" });
              setStats(null);
            }}
          >
            Sign out
          </button>
        )}
      </header>
      {loading ? (
        <p>Loading…</p>
      ) : stats ? (
        <>
          <h1>A little perspective.</h1>
          <p className="notice">
            Website activity. No tracking inside the app.
          </p>
          <div className="metrics">
            <div>
              <strong>{stats.total.downloads.toLocaleString()}</strong>
              <span>Download starts · all time</span>
            </div>
            <div>
              <strong>{stats.total.views.toLocaleString()}</strong>
              <span>Page views · all time</span>
            </div>
            <div>
              <strong>
                {(
                  stats.days.find(
                    (d) => d.day === new Date().toISOString().slice(0, 10),
                  )?.downloads ?? 0
                ).toLocaleString()}
              </strong>
              <span>Download starts · today</span>
            </div>
          </div>
          <h2 style={{ fontSize: 20 }}>Last 30 days</h2>
          <div className="chart" role="img" aria-label="Download starts by day">
            {days.map((d) => (
              <div
                key={d.day}
                title={`${d.day}: ${d.downloads} downloads`}
                style={{ height: `${Math.max(1, (d.downloads / max) * 100)}%` }}
              />
            ))}
          </div>
          <div className="chart-labels">
            <span>{days[0].day}</span>
            <span>{days[29].day}</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>Date (UTC)</th>
                <th>Page views</th>
                <th>Download starts</th>
              </tr>
            </thead>
            <tbody>
              {stats.days.slice(0, 14).map((d) => (
                <tr key={d.day}>
                  <td>{d.day}</td>
                  <td>{d.views}</td>
                  <td>{d.downloads}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="notice">
            Download starts count successful full-file requests, not completed
            installations or unique people. Resumes using byte ranges are
            excluded. Page views may include repeat visits and bots.
          </p>
          <p className="notice">
            Updated {new Date(stats.updatedAt).toLocaleString()} ·{" "}
            <button
              onClick={load}
              style={{ background: "none", border: 0, color: "#ddd" }}
            >
              Refresh
            </button>
          </p>
          <p className="notice">
            Change your password using the private release handoff and the
            documented Vercel environment update procedure.
          </p>
        </>
      ) : (
        <>
          <h1>Welcome back.</h1>
          <form onSubmit={login}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              required
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={256}
            />
            <button className="button primary" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </>
      )}
      {error && (
        <p role="alert" className="notice">
          {error}
        </p>
      )}
    </main>
  );
}
