
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./index.css";

const API = "http://localhost:8003";
const TOKEN_KEY = "workforce_access_token";

const http = axios.create({ baseURL: API });

const METHOD_STYLE = {
  GET: "bg-emerald-50 text-emerald-700",
  POST: "bg-blue-50 text-blue-700",
  PUT: "bg-amber-50 text-amber-700",
  PATCH: "bg-violet-50 text-violet-700",
  DELETE: "bg-red-50 text-red-700",
};

function getError(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((x) => x.msg).join(", ");
  return error.response?.data?.message || error.message || "Request failed";
}

function resolveSchema(schema, definitions) {
  if (!schema) return {};
  if (schema.$ref) {
    const name = schema.$ref.split("/").pop();
    return resolveSchema(definitions?.[name] || {}, definitions);
  }
  return schema;
}

function exampleFor(schema, definitions, depth = 0) {
  const s = resolveSchema(schema, definitions);
  if (depth > 4) return null;
  if (s.example !== undefined) return s.example;
  if (s.default !== undefined) return s.default;
  if (s.enum?.length) return s.enum[0];

  if (s.type === "object" || s.properties) {
    return Object.fromEntries(
      Object.entries(s.properties || {}).map(([key, value]) => [
        key,
        exampleFor(value, definitions, depth + 1),
      ]),
    );
  }

  if (s.type === "array") return [];
  if (s.type === "integer" || s.type === "number") return 0;
  if (s.type === "boolean") return false;
  if (s.format === "date") return new Date().toISOString().slice(0, 10);
  if (s.format === "date-time") return new Date().toISOString();
  return "";
}

function operationName(path, method, operation) {
  return operation.summary ||
    operation.operationId ||
    `${method.toUpperCase()} ${path}`;
}

function groupName(operation, path) {
  const tag = operation.tags?.[0];
  if (tag) return tag;
  const parts = path.split("/").filter(Boolean);
  return parts.length > 1 ? parts[1].replaceAll("-", " ") : "General";
}

function getInitials(name = "User") {
  return name.trim().split(/\s+/).slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "").join("");
}

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onLogin(email.trim(), password);
    } catch (e) {
      setError(getError(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen grid lg:grid-cols-2 bg-white">
      <section className="hidden lg:flex flex-col justify-between bg-slate-950 text-white p-12 xl:p-16">
        <div className="flex items-center gap-3 text-lg font-bold">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-600 text-xl">W</span>
          WorkForce <span className="text-blue-400">AI Pro</span>
        </div>
        <div className="max-w-xl">
          <p className="text-xs font-bold tracking-[.25em] text-blue-300">WORKFORCE INTELLIGENCE</p>
          <h1 className="mt-5 text-5xl font-extrabold leading-tight tracking-tight">
            Better workforce decisions start here.
          </h1>
          <p className="mt-6 max-w-lg text-slate-300 leading-7">
            Manage people operations, employee information, and attrition insights from one secure workspace.
          </p>
          <div className="mt-9 grid gap-3 text-sm text-slate-200">
            <p>✓ Role-based access control</p>
            <p>✓ HR operations and workforce analytics</p>
            <p>✓ AI risk and retention intelligence</p>
          </div>
        </div>
        <p className="text-xs text-slate-400">WORKFORCE AI PRO · ENTERPRISE WORKSPACE</p>
      </section>

      <section className="flex items-center justify-center p-6 sm:p-12">
        <form onSubmit={submit} className="w-full max-w-md">
          <div className="mb-9 flex items-center gap-3 font-bold lg:hidden">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 text-white">W</span>
            WorkForce AI Pro
          </div>
          <p className="text-xs font-bold tracking-[.2em] text-blue-600">SECURE SIGN IN</p>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">Welcome back</h2>
          <p className="mt-2 text-sm text-slate-500">Sign in with your existing workforce account.</p>

          {error && <div role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

          <label className="mt-7 block text-sm font-semibold text-slate-700">
            Email address
            <input type="email" required autoComplete="username" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              placeholder="you@company.com" />
          </label>

          <label className="mt-5 block text-sm font-semibold text-slate-700">
            Password
            <input type="password" required autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              placeholder="Enter your password" />
          </label>

          <button disabled={busy} className="mt-7 w-full rounded-xl bg-blue-600 px-4 py-3.5 font-bold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700">
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="mt-5 text-center text-xs text-slate-400">Access is determined by your assigned role.</p>
        </form>
      </section>
    </main>
  );
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [schema, setSchema] = useState(null);
  const [schemaError, setSchemaError] = useState("");
  const [busySchema, setBusySchema] = useState(true);
  const [selectedKey, setSelectedKey] = useState("");
  const [activeGroup, setActiveGroup] = useState("All modules");
  const [search, setSearch] = useState("");
  const [pathValues, setPathValues] = useState({});
  const [queryValues, setQueryValues] = useState({});
  const [bodyText, setBodyText] = useState("{}");
  const [requestBusy, setRequestBusy] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [requestError, setRequestError] = useState("");
  const [notice, setNotice] = useState("");
  const [page, setPage] = useState("workspace");

  const authConfig = useCallback(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    return savedToken ? { headers: { Authorization: `Bearer ${savedToken}` } } : {};
  }, []);

  const loadProfile = useCallback(async (savedToken) => {
    const result = await http.get("/api/auth/me", {
      headers: { Authorization: `Bearer ${savedToken}` },
    });
    setUser(result.data);
  }, []);

  const loadSchema = useCallback(async () => {
    setBusySchema(true);
    setSchemaError("");
    try {
      const result = await http.get("/openapi.json");
      setSchema(result.data);
    } catch (e) {
      setSchemaError(getError(e));
    } finally {
      setBusySchema(false);
    }
  }, []);

  useEffect(() => {
    loadSchema();
  }, [loadSchema]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    http.get("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((result) => {
        if (!cancelled) setUser(result.data);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        if (!cancelled) {
          setToken("");
          setUser(null);
        }
      });
    return () => { cancelled = true; };
  }, [token]);

  const operations = useMemo(() => {
    const result = [];
    for (const [path, methods] of Object.entries(schema?.paths || {})) {
      for (const [method, operation] of Object.entries(methods)) {
        if (!["get", "post", "put", "patch", "delete"].includes(method)) continue;
        result.push({
          key: `${method.toUpperCase()} ${path}`,
          path,
          method: method.toUpperCase(),
          operation,
          group: groupName(operation, path),
          title: operationName(path, method, operation),
        });
      }
    }
    return result.sort((a, b) => a.group.localeCompare(b.group) || a.path.localeCompare(b.path));
  }, [schema]);

  const groups = useMemo(
    () => ["All modules", ...new Set(operations.map((item) => item.group))],
    [operations],
  );

  const filtered = useMemo(() => operations.filter((item) => {
    const matchesGroup = activeGroup === "All modules" || item.group === activeGroup;
    const text = `${item.title} ${item.path} ${item.method} ${item.group}`.toLowerCase();
    return matchesGroup && text.includes(search.toLowerCase());
  }), [operations, activeGroup, search]);

  const selected = operations.find((item) => item.key === selectedKey) || null;
  const definitions = schema?.components?.schemas || {};

  function chooseOperation(item) {
    setSelectedKey(item.key);
    setPathValues({});
    setQueryValues({});
    setRequestError("");
    setResponseData(null);
    setNotice("");

    const content = item.operation.requestBody?.content || {};
    const jsonSchema = content["application/json"]?.schema ||
      content["multipart/form-data"]?.schema ||
      content["application/x-www-form-urlencoded"]?.schema;

    setBodyText(JSON.stringify(exampleFor(jsonSchema, definitions), null, 2));
  }

  async function handleLogin(email, password) {
    const result = await http.post("/api/auth/login", { email, password });
    const nextToken = result.data?.access_token;
    if (!nextToken) throw new Error("The server did not return an access token.");

    localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
    await loadProfile(nextToken);
    setNotice("Signed in successfully.");
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setSelectedKey("");
    setResponseData(null);
    setNotice("");
    setPage("workspace");
  }

  async function executeRequest(event) {
    event.preventDefault();
    if (!selected) return;

    setRequestBusy(true);
    setRequestError("");
    setNotice("");
    setResponseData(null);

    try {
      let url = selected.path;
      const params = selected.operation.parameters || [];
      const query = {};

      for (const param of params) {
        if (param.in === "path") {
          const value = pathValues[param.name];
          if (value === undefined || value === "") {
            throw new Error(`Enter the required path parameter: ${param.name}`);
          }
          url = url.replace(`{${param.name}}`, encodeURIComponent(value));
        } else if (param.in === "query") {
          const value = queryValues[param.name];
          if (value !== undefined && value !== "") query[param.name] = value;
          else if (param.required) throw new Error(`Enter the required query parameter: ${param.name}`);
        }
      }

      let body;
      if (selected.operation.requestBody) {
        try {
          body = JSON.parse(bodyText || "{}");
        } catch {
          throw new Error("Request body must be valid JSON.");
        }
      }

      const result = await http.request({
        url,
        method: selected.method,
        params: query,
        data: body,
        ...authConfig(),
      });

      setResponseData({
        status: result.status,
        data: result.data,
        headers: result.headers,
      });

      if (selected.path.includes("/auth/login") && result.data?.access_token) {
        localStorage.setItem(TOKEN_KEY, result.data.access_token);
        setToken(result.data.access_token);
        await loadProfile(result.data.access_token);
      }
      setNotice("Request completed successfully.");
    } catch (e) {
      setRequestError(getError(e));
      setResponseData({
        status: e.response?.status || "Error",
        data: e.response?.data || { message: e.message },
      });
      if (e.response?.status === 401) {
        setNotice("Authentication failed or your session expired. Sign in again.");
      }
    } finally {
      setRequestBusy(false);
    }
  }

  if (!user) return <Login onLogin={handleLogin} />;

  const displayName =
    [user.first_name, user.last_name].filter(Boolean).join(" ") ||
    user.email || "User";
  const role = String(user.role || "").toUpperCase();
  const pathParams = selected?.operation.parameters?.filter((p) => p.in === "path") || [];
  const queryParams = selected?.operation.parameters?.filter((p) => p.in === "query") || [];
  const requestSchema = selected?.operation.requestBody?.content?.["application/json"]?.schema;
  const requestProperties = resolveSchema(requestSchema, definitions).properties || {};
  const hasRequiredAuth = selected && !selected.path.includes("/auth/login") &&
    !selected.path.includes("/auth/register");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-6">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 text-lg font-extrabold text-white">W</span>
          <div><p className="font-extrabold tracking-tight">WorkForce <span className="text-blue-600">AI Pro</span></p><p className="mt-0.5 text-[9px] font-bold tracking-widest text-slate-400">HR INTELLIGENCE</p></div>
        </div>

        <div className="px-4 pt-6">
          <p className="px-3 pb-2 text-[10px] font-bold tracking-[.2em] text-slate-400">WORKSPACE</p>
          {[
            ["workspace", "Overview", "▦"],
            ["operations", "HR operations", "♙"],
            ["intelligence", "AI & intelligence", "◈"],
            ["api", "All backend features", "⌘"],
          ].map(([id, label, icon]) => (
            <button key={id} onClick={() => { setPage(id); setActiveGroup("All modules"); }}
              className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-semibold transition ${page === id ? "bg-blue-50 text-blue-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}>
              <span className="w-5 text-center text-lg">{icon}</span>{label}
            </button>
          ))}
        </div>

        <div className="mt-7 min-h-0 flex-1 overflow-y-auto px-4">
          <p className="px-3 pb-2 text-[10px] font-bold tracking-[.2em] text-slate-400">BACKEND MODULES</p>
          {groups.filter((group) => group !== "All modules").map((group) => (
            <button key={group} onClick={() => { setPage("api"); setActiveGroup(group); }}
              className={`mb-1 w-full truncate rounded-lg px-3 py-2 text-left text-xs capitalize ${page === "api" && activeGroup === group ? "bg-slate-100 font-bold text-blue-700" : "text-slate-500 hover:bg-slate-50"}`}>
              {group}
            </button>
          ))}
        </div>

        <div className="border-t border-slate-100 p-4">
          <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">{getInitials(displayName)}</span>
            <div className="min-w-0 flex-1"><p className="truncate text-xs font-bold">{displayName}</p><p className="mt-1 text-[10px] text-slate-500">{role}</p></div>
            <button title="Sign out" onClick={signOut} className="rounded-lg px-2 py-1 text-slate-500 hover:bg-white hover:text-red-600">↪</button>
          </div>
        </div>
      </aside>

      <main className="min-h-screen lg:pl-64">
        <header className="sticky top-0 z-10 flex min-h-20 items-center justify-between gap-4 border-b border-slate-200 bg-white/95 px-5 backdrop-blur sm:px-8">
          <div>
            <p className="text-[10px] font-bold tracking-[.2em] text-blue-600">WORKFORCE INTELLIGENCE PLATFORM</p>
            <h1 className="mt-1 text-lg font-extrabold tracking-tight text-slate-900 sm:text-xl">
              {page === "workspace" ? "Overview" : page === "operations" ? "HR operations" : page === "intelligence" ? "AI & intelligence" : "Backend feature workspace"}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-[10px] font-bold text-emerald-700 sm:inline-flex">● Signed in</span>
            <span className="grid h-9 w-9 place-items-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 lg:hidden">{getInitials(displayName)}</span>
            <button onClick={signOut} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 lg:hidden">Sign out</button>
          </div>
        </header>

        <div className="mx-auto max-w-[1600px] p-4 sm:p-7">
          {schemaError && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Unable to load the backend API catalogue: {schemaError}
              <button onClick={loadSchema} className="ml-3 font-bold underline">Retry</button>
            </div>
          )}

          {page === "workspace" && (
            <>
              <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-950 via-blue-950 to-blue-700 p-6 text-white shadow-lg sm:p-9">
                <div className="relative z-10 max-w-2xl">
                  <p className="text-[10px] font-bold tracking-[.25em] text-blue-200">YOUR WORKSPACE</p>
                  <h2 className="mt-3 text-2xl font-extrabold tracking-tight sm:text-3xl">Welcome back, {displayName.split(" ")[0]}.</h2>
                  <p className="mt-3 text-sm leading-6 text-blue-100">Manage workforce operations and use the registered backend features available to your account.</p>
                  <button onClick={() => setPage("api")} className="mt-6 rounded-xl bg-white px-4 py-3 text-xs font-bold text-blue-800 hover:bg-blue-50">Explore backend features →</button>
                </div>
                <div className="absolute -right-10 -top-20 h-64 w-64 rounded-full border-[35px] border-white/10" />
                <div className="absolute -bottom-24 right-40 h-48 w-48 rounded-full bg-blue-400/20 blur-2xl" />
              </section>

              <div className="mt-7 flex flex-wrap items-end justify-between gap-3">
                <div><h2 className="text-lg font-extrabold">Platform overview</h2><p className="mt-1 text-xs text-slate-500">Live catalogue of registered backend endpoints.</p></div>
                <button onClick={loadSchema} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold hover:bg-slate-50">↻ Refresh API catalogue</button>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  ["Registered operations", operations.length, "API operations discovered"],
                  ["Available modules", Math.max(0, groups.length - 1), "Grouped from API tags"],
                  ["Your role", role || "—", "Backend-assigned access role"],
                  ["Session", token ? "Active" : "Signed out", "Authentication status"],
                ].map(([label, value, caption]) => (
                  <article key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <p className="text-xs font-semibold text-slate-500">{label}</p>
                    <p className="mt-4 break-words text-2xl font-extrabold tracking-tight text-slate-900">{busySchema ? "…" : value}</p>
                    <p className="mt-2 text-[11px] text-slate-400">{caption}</p>
                  </article>
                ))}
              </div>

              <section className="mt-7 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div><h3 className="font-extrabold">Feature groups</h3><p className="mt-1 text-xs text-slate-500">Choose a group to use its registered operations in this application.</p></div>
                  <button onClick={() => setPage("api")} className="text-xs font-bold text-blue-700 hover:underline">View all →</button>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {groups.filter((group) => group !== "All modules").slice(0, 9).map((group) => (
                    <button key={group} onClick={() => { setActiveGroup(group); setPage("api"); }}
                      className="rounded-xl border border-slate-200 p-4 text-left transition hover:border-blue-300 hover:bg-blue-50/40">
                      <span className="grid h-9 w-9 place-items-center rounded-lg bg-blue-50 text-lg text-blue-700">◇</span>
                      <p className="mt-3 text-sm font-bold capitalize">{group}</p>
                      <p className="mt-1 text-xs text-slate-500">{operations.filter((item) => item.group === group).length} operations available</p>
                    </button>
                  ))}
                </div>
              </section>
            </>
          )}

          {(page === "operations" || page === "intelligence") && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
              <p className="text-[10px] font-bold tracking-[.2em] text-blue-600">{page === "operations" ? "PEOPLE OPERATIONS" : "WORKFORCE INTELLIGENCE"}</p>
              <h2 className="mt-3 text-xl font-extrabold">{page === "operations" ? "HR operations" : "AI & intelligence"}</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Choose a feature group below. The operation workspace will use the actual registered API methods and schemas. Operations are restricted by your backend's authentication and role permissions.
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {groups.filter((group) => group !== "All modules").map((group) => (
                  <button key={group} onClick={() => { setActiveGroup(group); setPage("api"); }}
                    className="rounded-xl border border-slate-200 p-4 text-left hover:border-blue-300 hover:bg-blue-50/40">
                    <p className="font-bold capitalize">{group}</p>
                    <p className="mt-2 text-xs text-slate-500">{operations.filter((item) => item.group === group).length} registered operations</p>
                  </button>
                ))}
              </div>
            </section>
          )}

          {page === "api" && (
            <div className="grid min-w-0 gap-5 xl:grid-cols-[330px_minmax(0,1fr)]">
              <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <div className="border-b border-slate-100 p-4">
                  <h2 className="font-extrabold">Feature operations</h2>
                  <p className="mt-1 text-xs text-slate-500">{filtered.length} matching operations</p>
                  <input value={search} onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search operations…"
                    className="mt-4 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-xs outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50" />
                  <select value={activeGroup} onChange={(e) => setActiveGroup(e.target.value)}
                    className="mt-3 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs capitalize outline-none focus:border-blue-500">
                    {groups.map((group) => <option key={group} value={group}>{group}</option>)}
                  </select>
                </div>

                <div className="max-h-[65vh] overflow-y-auto p-2">
                  {busySchema && <p className="p-4 text-xs text-slate-500">Loading registered operations…</p>}
                  {!busySchema && filtered.length === 0 && <p className="p-4 text-xs text-slate-500">No matching operations. Check the backend OpenAPI schema.</p>}
                  {filtered.map((item) => (
                    <button key={item.key} onClick={() => chooseOperation(item)}
                      className={`mb-1 w-full rounded-xl p-3 text-left ${selectedKey === item.key ? "bg-blue-50 ring-1 ring-blue-200" : "hover:bg-slate-50"}`}>
                      <div className="flex items-center gap-2">
                        <span className={`rounded-md px-2 py-1 text-[9px] font-extrabold ${METHOD_STYLE[item.method] || "bg-slate-100 text-slate-700"}`}>{item.method}</span>
                        <span className="min-w-0 truncate text-xs font-bold text-slate-800">{item.title}</span>
                      </div>
                      <code className="mt-2 block break-all text-[10px] text-slate-400">{item.path}</code>
                    </button>
                  ))}
                </div>
              </section>

              <section className="min-w-0">
                {!selected ? (
                  <div className="flex min-h-80 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
                    <span className="grid h-14 w-14 place-items-center rounded-2xl bg-blue-50 text-2xl text-blue-700">⌘</span>
                    <h2 className="mt-4 font-extrabold">Choose a backend operation</h2>
                    <p className="mt-2 max-w-sm text-sm text-slate-500">Select a feature from the left to view its parameters and run it within this frontend.</p>
                  </div>
                ) : (
                  <>
                    <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-[10px] font-bold uppercase tracking-[.18em] text-blue-600">{selected.group}</p>
                          <h2 className="mt-2 break-words text-lg font-extrabold">{selected.title}</h2>
                          <code className="mt-2 block break-all text-xs text-slate-500">{selected.path}</code>
                        </div>
                        <span className={`rounded-lg px-3 py-2 text-xs font-extrabold ${METHOD_STYLE[selected.method] || "bg-slate-100"}`}>{selected.method}</span>
                      </div>
                      {selected.operation.description && <p className="mt-4 text-sm leading-6 text-slate-500">{selected.operation.description}</p>}
                      {hasRequiredAuth && <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">This request uses your current session. The backend remains responsible for enforcing access permissions.</p>}

                      <form onSubmit={executeRequest} className="mt-6 space-y-5">
                        {pathParams.length > 0 && (
                          <div>
                            <h3 className="text-sm font-extrabold">Path parameters</h3>
                            <div className="mt-3 grid gap-3 sm:grid-cols-2">
                              {pathParams.map((param) => (
                                <label key={param.name} className="block text-xs font-semibold text-slate-600">
                                  {param.name}{param.required && <span className="text-red-500"> *</span>}
                                  <input required={param.required} value={pathValues[param.name] || ""}
                                    onChange={(e) => setPathValues((old) => ({ ...old, [param.name]: e.target.value }))}
                                    placeholder={param.description || param.name}
                                    className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50" />
                                </label>
                              ))}
                            </div>
                          </div>
                        )}

                        {queryParams.length > 0 && (
                          <div>
                            <h3 className="text-sm font-extrabold">Query parameters</h3>
                            <div className="mt-3 grid gap-3 sm:grid-cols-2">
                              {queryParams.map((param) => (
                                <label key={param.name} className="block text-xs font-semibold text-slate-600">
                                  {param.name}{param.required && <span className="text-red-500"> *</span>}
                                  <input required={param.required} value={queryValues[param.name] ?? ""}
                                    onChange={(e) => setQueryValues((old) => ({ ...old, [param.name]: e.target.value }))}
                                    placeholder={param.description || param.name}
                                    className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50" />
                                </label>
                              ))}
                            </div>
                          </div>
                        )}

                        {selected.operation.requestBody && (
                          <div>
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <h3 className="text-sm font-extrabold">Request body</h3>
                              <span className="text-[10px] text-slate-400">JSON · Edit values before submitting</span>
                            </div>
                            {Object.keys(requestProperties).length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-2">
                                {Object.entries(requestProperties).map(([key, value]) => (
                                  <span key={key} className="rounded-md bg-slate-100 px-2 py-1 text-[10px] text-slate-600">
                                    {key}{resolveSchema(value, definitions).type ? ` · ${resolveSchema(value, definitions).type}` : ""}
                                  </span>
                                ))}
                              </div>
                            )}
                            <textarea value={bodyText} onChange={(e) => setBodyText(e.target.value)}
                              spellCheck={false} rows={10}
                              className="mt-3 w-full rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-6 text-emerald-100 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                              aria-label="JSON request body" />
                          </div>
                        )}

                        <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-5">
                          <button disabled={requestBusy} className="rounded-xl bg-blue-600 px-5 py-3 text-xs font-bold text-white shadow-md shadow-blue-600/20 hover:bg-blue-700">
                            {requestBusy ? "Executing request…" : `Run ${selected.method} request`}
                          </button>
                          <button type="button" onClick={() => { setResponseData(null); setRequestError(""); setNotice(""); }}
                            className="rounded-xl border border-slate-200 px-5 py-3 text-xs font-bold text-slate-600 hover:bg-slate-50">Clear response</button>
                        </div>
                      </form>
                    </div>

                    {(responseData || requestError || notice) && (
                      <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
                          <div><h3 className="font-extrabold">Request result</h3><p className="mt-1 text-xs text-slate-500">Response returned by the backend API.</p></div>
                          {responseData && <span className={`rounded-lg px-3 py-2 text-xs font-extrabold ${Number(responseData.status) >= 200 && Number(responseData.status) < 300 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>HTTP {responseData.status}</span>}
                        </div>
                        {notice && <p className="px-5 pt-4 text-xs text-emerald-700">{notice}</p>}
                        {requestError && <p role="alert" className="px-5 pt-4 text-xs text-red-700">{requestError}</p>}
                        <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap break-words bg-slate-950 p-5 text-xs leading-6 text-emerald-100">{JSON.stringify(responseData?.data ?? {}, null, 2)}</pre>
                      </div>
                    )}
                  </>
                )}
              </section>
            </div>
          )}

          <footer className="mt-8 flex flex-wrap justify-between gap-2 border-t border-slate-200 py-5 text-[10px] text-slate-400">
            <span>© {new Date().getFullYear()} WorkForce AI Pro</span>
            <span>{operations.length} registered API operations · Role: {role}</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;
