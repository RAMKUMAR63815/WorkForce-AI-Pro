
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./index.css";

const API = "http://localhost:8003";
const TOKEN_KEY = "workforce_access_token";

const http = axios.create({
  baseURL: API,
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

const MODULES = [
  { id: "overview", label: "Overview", icon: "◫", description: "Your workforce at a glance" },
  { id: "employees", label: "Employees", icon: "♙", description: "Employee directory and profiles", paths: ["/api/employees"] },
  { id: "departments", label: "Departments", icon: "▦", description: "Organize your teams", paths: ["/api/departments"] },
  { id: "attendance", label: "Attendance", icon: "◷", description: "Attendance records", paths: ["/api/attendance"] },
  { id: "shifts", label: "Shifts", icon: "◴", description: "Work schedules and shifts", paths: ["/api/shifts"] },
  { id: "leave", label: "Leave management", icon: "▤", description: "Leave requests and balances", paths: ["/api/leaves", "/api/leave", "/api/leave-balances"] },
  { id: "payroll", label: "Payroll", icon: "₹", description: "Compensation information", paths: ["/api/payroll"] },
  { id: "documents", label: "Documents", icon: "▧", description: "Employee files and records", paths: ["/api/documents"] },
  { id: "reviews", label: "Performance", icon: "☆", description: "Performance reviews", paths: ["/api/reviews", "/api/performance"] },
  { id: "datasets", label: "AI datasets", icon: "▥", description: "Prepare workforce data for analysis", paths: ["/api/datasets"] },
  { id: "attrition", label: "Attrition prediction", icon: "⌁", description: "Employee attrition analysis", paths: ["/api/attrition"] },
  { id: "risk", label: "Risk monitoring", icon: "△", description: "Monitor employee risk indicators", paths: ["/api/risk"] },
  { id: "forecasting", label: "Forecasting", icon: "↗", description: "Workforce planning forecasts", paths: ["/api/forecasting"] },
  { id: "analytics", label: "Analytics", icon: "▥", description: "Workforce insights", paths: ["/api/analytics"] },
  { id: "interventions", label: "Interventions", icon: "♡", description: "Employee support plans", paths: ["/api/interventions"] },
  { id: "alerts", label: "Alerts", icon: "♧", description: "Workforce notifications", paths: ["/api/alerts", "/api/notifications"] },
  { id: "reports", label: "Reports", icon: "▤", description: "Workforce reporting", paths: ["/api/reports"] },
  { id: "audit", label: "Activity history", icon: "◷", description: "Track important changes", paths: ["/api/audit", "/api/audit-logs"] },
  { id: "settings", label: "Settings", icon: "⚙", description: "Your account and preferences" },
];

const HIDDEN_TAGS = new Set(["default", "health", "authentication", "auth", "rbac"]);

function normalizePath(path = "") {
  return path.replace(/\/+$/, "") || "/";
}

function isApiPath(path = "") {
  return path.startsWith("/api/");
}

function operationLabel(path, method, operation = {}) {
  const summary = operation.summary || operation.operationId || "";

  if (summary) {
    return summary
      .replace(/[_-]/g, " ")
      .replace(/\b(create|update|delete|remove|post|put|patch|get)\b/gi, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  const parts = path.split("/").filter(Boolean);
  const last = (parts[parts.length - 1] || "Records")
    .replace(/\{.*?\}/g, "")
    .replace(/[-_]/g, " ")
    .trim();

  return last || "Records";
}

function resolveSchema(schema, definitions, depth = 0) {
  if (!schema || depth > 8) return {};

  if (schema.$ref) {
    const name = schema.$ref.split("/").pop();
    return resolveSchema(definitions[name], definitions, depth + 1);
  }

  if (schema.allOf) {
    return schema.allOf.reduce(
      (result, item) => ({
        ...result,
        ...resolveSchema(item, definitions, depth + 1),
        properties: {
          ...(result.properties || {}),
          ...(resolveSchema(item, definitions, depth + 1).properties || {}),
        },
      }),
      {},
    );
  }

  return schema;
}

function getResponseSchema(operation, definitions) {
  const responses = operation.responses || {};

  for (const code of ["200", "201", "202", "default"]) {
    const response = responses[code];
    const schema =
      response?.content?.["application/json"]?.schema ||
      response?.content?.["application/*+json"]?.schema;

    if (schema) return resolveSchema(schema, definitions);
  }

  return {};
}

function getRows(data) {
  if (Array.isArray(data)) return data;

  if (!data || typeof data !== "object") {
    return data == null ? [] : [{ result: data }];
  }

  for (const key of ["items", "results", "data", "employees", "records"]) {
    if (Array.isArray(data[key])) return data[key];
  }

  return [data];
}

function prettyLabel(value) {
  return String(value)
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Invalid value").join(", ");
  }

  return error?.message || "Something went wrong. Please try again.";
}

function statusClass(value) {
  const text = String(value || "").toLowerCase();

  if (
    text.includes("active") ||
    text.includes("approved") ||
    text.includes("success") ||
    text.includes("validated") ||
    text === "completed"
  ) {
    return "status-good";
  }

  if (
    text.includes("pending") ||
    text.includes("review") ||
    text.includes("warning") ||
    text.includes("progress")
  ) {
    return "status-pending";
  }

  if (
    text.includes("reject") ||
    text.includes("inactive") ||
    text.includes("error") ||
    text.includes("high") ||
    text.includes("failed")
  ) {
    return "status-bad";
  }

  return "status-neutral";
}

function Icon({ children }) {
  return <span className="wf-icon" aria-hidden="true">{children}</span>;
}

function Button({ children, onClick, variant = "primary", disabled = false, type = "button" }) {
  return (
    <button
      type={type}
      className={`wf-button wf-button-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function Field({ property, name, value, onChange, required = false }) {
  const schema = property || {};
  const label = prettyLabel(name);
  const type = schema.type;
  const format = schema.format;
  const enumValues = schema.enum;

  if (enumValues) {
    return (
      <label className="wf-field">
        <span>{label}{required ? " *" : ""}</span>
        <select
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
          required={required}
        >
          <option value="">Choose {label.toLowerCase()}</option>
          {enumValues.map((item) => (
            <option key={String(item)} value={item}>{prettyLabel(item)}</option>
          ))}
        </select>
      </label>
    );
  }

  if (type === "boolean") {
    return (
      <label className="wf-field">
        <span>{label}</span>
        <select
          value={String(value ?? false)}
          onChange={(event) => onChange(event.target.value === "true")}
        >
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </label>
    );
  }

  if (type === "object" || type === "array") {
    return (
      <label className="wf-field">
        <span>{label}{required ? " *" : ""} (JSON)</span>
        <textarea
          rows={3}
          value={typeof value === "string" ? value : JSON.stringify(value ?? (type === "array" ? [] : {}), null, 2)}
          onChange={(event) => onChange(event.target.value)}
          required={required}
        />
      </label>
    );
  }

  let inputType = "text";
  if (format === "date") inputType = "date";
  else if (format === "date-time") inputType = "datetime-local";
  else if (format === "email") inputType = "email";
  else if (type === "integer" || type === "number") inputType = "number";

  return (
    <label className="wf-field">
      <span>{label}{required ? " *" : ""}</span>
      <input
        type={inputType}
        value={value ?? ""}
        onChange={(event) => {
          const raw = event.target.value;
          if (type === "integer" && raw !== "") onChange(Number.parseInt(raw, 10));
          else if (type === "number" && raw !== "") onChange(Number(raw));
          else onChange(raw);
        }}
        required={required}
        min={schema.minimum}
        max={schema.maximum}
        maxLength={schema.maxLength}
        placeholder={schema.description || `Enter ${label.toLowerCase()}`}
      />
    </label>
  );
}

function Modal({ title, subtitle, onClose, children }) {
  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="wf-modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="wf-modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="wf-modal-heading">
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button className="wf-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        {children}
      </section>
    </div>
  );
}

function App() {
  const [activeModule, setActiveModule] = useState("overview");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [openApi, setOpenApi] = useState(null);
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [rows, setRows] = useState([]);
  const [notice, setNotice] = useState(null);
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [loginBusy, setLoginBusy] = useState(false);
  const [datasetName, setDatasetName] = useState("");
  const [datasetFile, setDatasetFile] = useState(null);
  const [documentCategory, setDocumentCategory] = useState("Employment document");
  const [documentFile, setDocumentFile] = useState(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [formBusy, setFormBusy] = useState(false);
  const [meBusy, setMeBusy] = useState(false);

  const definitions = useMemo(
    () => openApi?.components?.schemas || openApi?.definitions || {},
    [openApi],
  );

  const operations = useMemo(() => {
    const paths = openApi?.paths || {};
    const list = [];

    Object.entries(paths).forEach(([path, methods]) => {
      if (!isApiPath(path)) return;

      Object.entries(methods || {}).forEach(([method, operation]) => {
        if (!["get", "post", "put", "patch", "delete"].includes(method)) return;

        const tags = operation.tags || [];
        const tag = tags[0] || "";
        if (HIDDEN_TAGS.has(tag.toLowerCase())) return;

        list.push({
          path,
          method,
          operation,
          tags,
          label: operationLabel(path, method, operation),
          normalizedPath: normalizePath(path),
        });
      });
    });

    return list;
  }, [openApi]);

  const activeInfo = MODULES.find((item) => item.id === activeModule) || MODULES[0];

  const moduleOperations = useMemo(() => {
    if (activeModule === "overview" || activeModule === "settings") return [];

    const explicit = activeInfo.paths || [];
    const matched = operations.filter((item) => {
      const path = item.normalizedPath.toLowerCase();
      return explicit.some((candidate) => {
        const base = normalizePath(candidate).toLowerCase();
        return path === base || path.startsWith(`${base}/`);
      });
    });

    if (matched.length) return matched;

    const words = activeInfo.label.toLowerCase().split(/\s+/);
    return operations.filter((item) => {
      const target = `${item.path} ${item.tags.join(" ")} ${item.operation.summary || ""}`.toLowerCase();
      return words.some((word) => word.length > 3 && target.includes(word));
    });
  }, [activeModule, activeInfo, operations]);

  const readOperation = useMemo(() => {
    if (activeModule === "datasets") {
      return moduleOperations.find((item) =>
        item.method === "get" && normalizePath(item.path) === "/api/datasets",
      ) || moduleOperations.find((item) => item.method === "get" && !item.path.includes("{"));
    }

    if (activeModule === "documents") {
      return moduleOperations.find((item) =>
        item.method === "get" && normalizePath(item.path) === "/api/documents",
      ) || moduleOperations.find((item) =>
        item.method === "get" && item.path.endsWith("/my"),
      );
    }

    return moduleOperations.find((item) => item.method === "get" && !item.path.includes("{"))
      || moduleOperations.find((item) => item.method === "get");
  }, [activeModule, moduleOperations]);

  const loadSchema = useCallback(async () => {
    setLoadingSchema(true);

    try {
      const response = await axios.get(`${API}/openapi.json`, { timeout: 15000 });
      setOpenApi(response.data);
    } catch (error) {
      setNotice({
        type: "error",
        message: "Unable to connect to the workforce service. Check that the backend is running on port 8003.",
      });
    } finally {
      setLoadingSchema(false);
    }
  }, []);

  const loadProfile = useCallback(async () => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setUser(null);
      return;
    }

    setMeBusy(true);

    try {
      const response = await http.get("/api/auth/me");
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setMeBusy(false);
    }
  }, []);

  const loadModuleData = useCallback(async () => {
    if (activeModule === "overview" || activeModule === "settings") {
      setRows([]);
      return;
    }

    setLoadingData(true);
    setRows([]);
    setUploadResult(null);

    try {
      let response;

      if (activeModule === "datasets") {
        response = await http.get("/api/datasets/");
      } else if (activeModule === "documents") {
        const role = String(user?.role || "").toUpperCase();
        response = await http.get(
          role === "HR" || role === "ADMIN"
            ? "/api/documents/"
            : "/api/documents/my",
        );
      } else if (readOperation) {
        response = await http.get(readOperation.path);
      } else {
        setRows([]);
        return;
      }

      setRows(getRows(response.data));
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      setRows([]);
    } finally {
      setLoadingData(false);
    }
  }, [activeModule, readOperation, user?.role]);

  useEffect(() => {
    loadSchema();
    loadProfile();
  }, [loadSchema, loadProfile]);

  useEffect(() => {
    if (token) loadProfile();
    else setUser(null);
  }, [token, loadProfile]);

  useEffect(() => {
    loadModuleData();
  }, [loadModuleData]);

  useEffect(() => {
    if (!notice) return undefined;
    const id = window.setTimeout(() => setNotice(null), 6000);
    return () => window.clearTimeout(id);
  }, [notice]);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;

    const query = search.toLowerCase();
    return rows.filter((row) =>
      JSON.stringify(row).toLowerCase().includes(query),
    );
  }, [rows, search]);

  const columns = useMemo(() => {
    if (!filteredRows.length) return [];

    const preferred = [
      "id", "employee_code", "first_name", "last_name", "email",
      "name", "dataset_name", "category", "department", "designation",
      "joining_date", "status", "is_active", "created_at",
    ];

    const all = [...new Set(filteredRows.flatMap((row) =>
      row && typeof row === "object" ? Object.keys(row) : [],
    ))].filter((key) => !["hashed_password", "password", "file_path", "stored_path"].includes(key));

    return [
      ...preferred.filter((key) => all.includes(key)),
      ...all.filter((key) => !preferred.includes(key)),
    ].slice(0, 7);
  }, [filteredRows]);

  const login = async (event) => {
    event.preventDefault();
    setLoginBusy(true);

    try {
      const body = new URLSearchParams();
      body.set("username", loginForm.email.trim().toLowerCase());
      body.set("password", loginForm.password);

      let response;

      try {
        response = await axios.post(`${API}/api/auth/login`, body, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
      } catch (firstError) {
        if (firstError?.response?.status !== 422) throw firstError;

        response = await axios.post(`${API}/api/auth/login`, {
          email: loginForm.email.trim().toLowerCase(),
          password: loginForm.password,
        });
      }

      const accessToken = response.data.access_token || response.data.token;

      if (!accessToken) {
        throw new Error("The sign-in response did not contain an access token.");
      }

      localStorage.setItem(TOKEN_KEY, accessToken);
      setToken(accessToken);
      setNotice({ type: "success", message: "Welcome back. You are signed in." });
      setModal(null);
      setLoginForm({ email: "", password: "" });

      try {
        const profile = await http.get("/api/auth/me");
        setUser(profile.data);
      } catch {
        setUser(null);
      }
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setLoginBusy(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setRows([]);
    setNotice({ type: "success", message: "You have signed out." });
  };

  const openDataForm = (item) => {
    const requestBody = item.operation.requestBody;
    const content = requestBody?.content || {};
    const contentType = Object.keys(content).find((type) =>
      type.includes("application/json"),
    ) || Object.keys(content)[0];

    const bodySchema = resolveSchema(content[contentType]?.schema, definitions);
    const properties = bodySchema.properties || {};
    const required = bodySchema.required || [];

    const initial = {};

    Object.entries(properties).forEach(([name, property]) => {
      if (property.default !== undefined) initial[name] = property.default;
      else if (property.type === "boolean") initial[name] = false;
      else if (property.type === "array") initial[name] = [];
      else if (property.type === "object") initial[name] = {};
      else initial[name] = "";
    });

    setFormValues(initial);
    setModal({
      type: "data-form",
      operation: item,
      contentType,
      properties,
      required,
      label: item.label || activeInfo.label,
    });
  };

  const submitDataForm = async (event) => {
    event.preventDefault();
    if (!modal?.operation) return;

    setFormBusy(true);

    try {
      const { operation, contentType, properties } = modal;
      let body = {};

      Object.entries(formValues).forEach(([key, value]) => {
        const property = properties[key] || {};

        if (value === "" || value === undefined) return;

        if ((property.type === "object" || property.type === "array") && typeof value === "string") {
          try {
            body[key] = JSON.parse(value);
          } catch {
            throw new Error(`${prettyLabel(key)} must contain valid JSON.`);
          }
        } else {
          body[key] = value;
        }
      });

      const config = {};
      if (contentType) config.headers = { "Content-Type": contentType };

      const response = await http.request({
        method: operation.method,
        url: operation.path,
        data: body,
        ...config,
      });

      setNotice({
        type: "success",
        message: "Your changes have been saved successfully.",
      });
      setModal(null);

      if (response.data && typeof response.data === "object") {
        await loadModuleData();
      }
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setFormBusy(false);
    }
  };

  const uploadDataset = async (event) => {
    event.preventDefault();

    if (!datasetName.trim() || !datasetFile) {
      setNotice({ type: "error", message: "Enter a dataset name and choose a CSV file." });
      return;
    }

    if (!datasetFile.name.toLowerCase().endsWith(".csv")) {
      setNotice({ type: "error", message: "Please choose a CSV file." });
      return;
    }

    if (datasetFile.size > 20 * 1024 * 1024) {
      setNotice({ type: "error", message: "The CSV file must be 20 MB or smaller." });
      return;
    }

    const body = new FormData();
    body.append("dataset_name", datasetName.trim());
    body.append("file", datasetFile);

    setUploadBusy(true);

    try {
      const response = await http.post("/api/datasets/", body);
      setUploadResult(response.data);
      setDatasetName("");
      setDatasetFile(null);
      event.target.reset();

      setNotice({
        type: "success",
        message: "Dataset uploaded. Review its validation status below.",
      });

      const refreshed = await http.get("/api/datasets/");
      setRows(getRows(refreshed.data));
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setUploadBusy(false);
    }
  };

  const uploadDocument = async (event) => {
    event.preventDefault();

    if (!documentCategory.trim() || !documentFile) {
      setNotice({ type: "error", message: "Enter a document category and choose a file." });
      return;
    }

    const allowed = [".pdf", ".png", ".jpg", ".jpeg"];
    const extension = documentFile.name.slice(documentFile.name.lastIndexOf(".")).toLowerCase();

    if (!allowed.includes(extension)) {
      setNotice({ type: "error", message: "Choose a PDF, PNG or JPEG file." });
      return;
    }

    if (documentFile.size > 5 * 1024 * 1024) {
      setNotice({ type: "error", message: "The document must be 5 MB or smaller." });
      return;
    }

    const body = new FormData();
    body.append("category", documentCategory.trim());
    body.append("file", documentFile);

    setUploadBusy(true);

    try {
      await http.post("/api/documents/my", body);
      setDocumentFile(null);
      event.target.reset();

      setNotice({ type: "success", message: "Your document has been uploaded." });
      await loadModuleData();
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(error),
      });
    } finally {
      setUploadBusy(false);
    }
  };

  const exportRows = () => {
    if (!filteredRows.length) {
      setNotice({ type: "error", message: "There are no records to export." });
      return;
    }

    const keys = columns.length ? columns : Object.keys(filteredRows[0]);
    const escapeCsv = (value) => {
      const text = displayValue(value);
      return `"${text.replace(/"/g, '""')}"`;
    };

    const csv = [
      keys.map(escapeCsv).join(","),
      ...filteredRows.map((row) => keys.map((key) => escapeCsv(row[key])).join(",")),
    ].join("\r\n");

    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${activeModule}-records.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const overviewCards = [
    { label: "Employees", value: "—", icon: "♙", note: "Live workforce records", module: "employees" },
    { label: "Departments", value: "—", icon: "▦", note: "Your organization structure", module: "departments" },
    { label: "AI datasets", value: "—", icon: "▥", note: "Available for analysis", module: "datasets" },
    { label: "Attrition insights", value: "—", icon: "⌁", note: "Prediction services", module: "attrition" },
  ];

  const hasAuth = Boolean(token);
  const noDataMessage = loadingSchema
    ? "Preparing your workspace…"
    : !hasAuth
      ? "Sign in to view your workforce information."
      : !moduleOperations.length
        ? "This area is not connected to an available service yet."
        : "No records are available yet.";

  return (
    <div className="wf-app">
      <style>{`
        :root {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: #182230;
          background: #f5f7fb;
          font-synthesis: none;
        }
        * { box-sizing: border-box; }
        body { margin: 0; }
        button, input, select, textarea { font: inherit; }
        button { cursor: pointer; }
        button:disabled { opacity: .55; cursor: not-allowed; }
        .wf-app { min-height: 100vh; background: #f5f7fb; }
        .wf-layout { display: flex; min-height: 100vh; }
        .wf-sidebar { width: 248px; flex-shrink: 0; background: #111c35; color: #d6deef; padding: 23px 14px; display: flex; flex-direction: column; }
        .wf-brand { display:flex; align-items:center; gap:11px; padding:0 10px 27px; color:#fff; }
        .wf-brand-mark { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:#6b7cff; font-size:20px; font-weight:800; }
        .wf-brand-name { font-weight:750; font-size:15px; letter-spacing:-.3px; }
        .wf-brand-sub { margin-top:3px; color:#9aa8c4; font-size:11px; }
        .wf-nav-title { padding:13px 12px 8px; color:#8493b1; font-size:10px; font-weight:750; letter-spacing:1.3px; text-transform:uppercase; }
        .wf-nav { display:flex; flex-direction:column; gap:4px; overflow:auto; }
        .wf-nav button { border:0; display:flex; align-items:center; gap:11px; text-align:left; color:#b8c4db; background:transparent; border-radius:9px; padding:10px 12px; font-size:13px; transition:background .15s; }
        .wf-nav button:hover { background:#1b2a4b; color:white; }
        .wf-nav button.active { background:#30447a; color:white; box-shadow:inset 3px 0 #9ca9ff; }
        .wf-icon { width:21px; display:inline-flex; justify-content:center; font-size:17px; }
        .wf-sidebar-bottom { margin-top:auto; padding:18px 10px 0; color:#98a8c6; font-size:11px; line-height:1.6; }
        .wf-service-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#36d399; margin-right:7px; }
        .wf-main { min-width:0; flex:1; }
        .wf-topbar { min-height:72px; background:#fff; border-bottom:1px solid #e6eaf1; display:flex; align-items:center; justify-content:space-between; gap:16px; padding:14px 30px; }
        .wf-breadcrumb { font-size:12px; color:#8590a3; margin-bottom:4px; }
        .wf-top-title { font-weight:700; font-size:16px; }
        .wf-top-actions { display:flex; align-items:center; gap:12px; }
        .wf-user { display:flex; align-items:center; gap:9px; }
        .wf-avatar { display:grid; place-items:center; flex-shrink:0; width:36px; height:36px; border-radius:50%; background:#e7eaff; color:#4c56ba; font-size:13px; font-weight:800; }
        .wf-user-name { font-size:12px; font-weight:700; }
        .wf-user-role { font-size:11px; color:#8792a5; margin-top:3px; }
        .wf-content { padding:28px 30px 42px; max-width:1600px; margin:0 auto; }
        .wf-welcome { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:24px; }
        .wf-eyebrow { color:#5b65d9; font-size:11px; text-transform:uppercase; font-weight:800; letter-spacing:1.4px; margin-bottom:9px; }
        .wf-heading { font-size:27px; letter-spacing:-.9px; line-height:1.2; margin:0; font-weight:780; color:#17213a; }
        .wf-subtitle { font-size:13px; line-height:1.7; color:#7b879a; margin:9px 0 0; }
        .wf-button { display:inline-flex; justify-content:center; align-items:center; gap:8px; border:1px solid transparent; border-radius:9px; padding:10px 14px; font-size:12px; font-weight:700; transition:all .15s; }
        .wf-button-primary { background:#555fdb; color:white; }
        .wf-button-primary:hover { background:#454fc2; }
        .wf-button-secondary { background:#fff; color:#35415a; border-color:#e0e5ee; }
        .wf-button-secondary:hover { background:#f8f9fd; }
        .wf-button-danger { background:#fff2f2; color:#b23b42; border-color:#f3d3d5; }
        .wf-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; }
        .wf-card { background:#fff; border:1px solid #e8ecf3; border-radius:14px; padding:20px; box-shadow:0 2px 8px rgba(25,38,71,.025); }
        .wf-stat-top { display:flex; align-items:center; justify-content:space-between; }
        .wf-stat-icon { width:39px; height:39px; border-radius:11px; display:grid; place-items:center; background:#eef0ff; color:#555fdb; font-size:19px; }
        .wf-stat-label { font-size:12px; color:#7f8a9d; font-weight:600; }
        .wf-stat-value { font-size:27px; font-weight:780; letter-spacing:-.8px; margin-top:16px; color:#1b2540; }
        .wf-stat-note { color:#9aa3b2; font-size:11px; margin-top:7px; }
        .wf-section-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin:27px 0 14px; }
        .wf-section-title { font-size:15px; font-weight:750; margin:0; }
        .wf-section-sub { font-size:12px; color:#8a95a7; margin-top:5px; }
        .wf-shortcuts { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:13px; }
        .wf-shortcut { display:flex; gap:13px; align-items:flex-start; width:100%; text-align:left; background:white; border:1px solid #e7ebf3; border-radius:12px; padding:17px; }
        .wf-shortcut:hover { border-color:#aeb6ff; box-shadow:0 4px 15px #3e4bc00d; }
        .wf-shortcut-icon { width:38px; height:38px; flex-shrink:0; border-radius:10px; display:grid; place-items:center; background:#f0f1ff; color:#535fd7; font-size:18px; }
        .wf-shortcut-title { font-size:13px; font-weight:750; }
        .wf-shortcut-desc { font-size:11px; line-height:1.6; color:#8792a5; margin-top:5px; }
        .wf-panel { background:white; border:1px solid #e7ebf3; border-radius:14px; overflow:hidden; }
        .wf-panel-head { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:14px; padding:19px 21px; border-bottom:1px solid #edf0f5; }
        .wf-panel-title { margin:0; font-size:14px; font-weight:750; }
        .wf-panel-desc { margin:5px 0 0; color:#8b96a7; font-size:11px; }
        .wf-panel-actions { display:flex; align-items:center; gap:9px; flex-wrap:wrap; }
        .wf-search { border:1px solid #e0e5ee; border-radius:8px; padding:9px 12px; min-width:210px; font-size:12px; outline:none; background:#fff; }
        .wf-search:focus, .wf-field input:focus, .wf-field select:focus, .wf-field textarea:focus { border-color:#9ba4ff; box-shadow:0 0 0 3px #6874e21a; outline:none; }
        .wf-table-wrap { overflow:auto; }
        .wf-table { border-collapse:collapse; width:100%; min-width:650px; }
        .wf-table th { text-align:left; font-size:10px; color:#8490a3; font-weight:750; letter-spacing:.6px; text-transform:uppercase; padding:14px 18px; background:#fafbfe; border-bottom:1px solid #edf0f5; white-space:nowrap; }
        .wf-table td { padding:15px 18px; border-bottom:1px solid #f0f2f6; color:#465268; font-size:12px; max-width:260px; overflow-wrap:anywhere; }
        .wf-table tr:last-child td { border-bottom:0; }
        .wf-table tbody tr:hover { background:#fafbff; }
        .wf-status { display:inline-block; border-radius:30px; padding:5px 9px; font-size:10px; font-weight:750; white-space:nowrap; }
        .status-good { background:#e8f8f0; color:#21865d; }
        .status-pending { background:#fff5df; color:#a36c11; }
        .status-bad { background:#fff0f0; color:#b74149; }
        .status-neutral { background:#eff2f7; color:#66738a; }
        .wf-empty { padding:55px 20px; text-align:center; }
        .wf-empty-icon { margin:0 auto 14px; width:54px; height:54px; display:grid; place-items:center; background:#f0f1ff; border-radius:15px; color:#5863d6; font-size:24px; }
        .wf-empty-title { font-size:14px; font-weight:750; color:#303c55; }
        .wf-empty-desc { max-width:410px; margin:8px auto 18px; font-size:12px; line-height:1.7; color:#8b95a6; }
        .wf-notice { position:fixed; z-index:100; top:18px; right:18px; width:min(440px,calc(100vw - 36px)); border:1px solid #e1e6ef; background:#fff; box-shadow:0 12px 45px #1d2b471a; border-radius:12px; padding:14px 16px; display:flex; gap:11px; align-items:flex-start; }
        .wf-notice.success { border-left:4px solid #26a269; }
        .wf-notice.error { border-left:4px solid #d44f58; }
        .wf-notice-text { font-size:12px; line-height:1.6; color:#3c4960; }
        .wf-modal-backdrop { position:fixed; inset:0; z-index:90; background:#101a30a3; display:grid; place-items:center; padding:18px; overflow:auto; }
        .wf-modal { width:min(600px,100%); max-height:90vh; overflow:auto; background:white; border-radius:16px; padding:24px; box-shadow:0 24px 80px #101a3040; }
        .wf-modal-heading { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:20px; }
        .wf-modal-heading h2 { margin:0; font-size:19px; letter-spacing:-.4px; }
        .wf-modal-heading p { margin:6px 0 0; font-size:12px; color:#8691a3; line-height:1.6; }
        .wf-close { border:0; border-radius:8px; width:31px; height:31px; font-size:23px; color:#748096; background:#f3f5f9; }
        .wf-form { display:flex; flex-direction:column; gap:15px; }
        .wf-form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
        .wf-field { display:flex; flex-direction:column; gap:7px; font-size:12px; font-weight:650; color:#4c5870; min-width:0; }
        .wf-field input, .wf-field select, .wf-field textarea { width:100%; min-width:0; padding:10px 11px; border:1px solid #dfe4ed; border-radius:8px; background:#fff; color:#29354c; font-size:12px; }
        .wf-field textarea { resize:vertical; }
        .wf-form-footer { display:flex; justify-content:flex-end; gap:9px; margin-top:8px; }
        .wf-help { color:#8490a2; font-size:11px; line-height:1.7; }
        .wf-callout { border:1px solid #e5e8ff; background:#f6f7ff; border-radius:11px; padding:13px 15px; font-size:11px; color:#626c98; line-height:1.7; }
        .wf-upload-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin-bottom:20px; }
        .wf-upload-card { padding:20px; background:#fff; border:1px solid #e5e9f1; border-radius:13px; }
        .wf-upload-card h3 { margin:0 0 6px; font-size:14px; }
        .wf-upload-card > p { color:#8792a4; font-size:11px; line-height:1.65; margin:0 0 17px; }
        .wf-file { border:1px dashed #cbd2e2; border-radius:9px; background:#fafbfe; padding:15px; font-size:11px; width:100%; }
        .wf-file::file-selector-button { border:0; border-radius:6px; background:#e9ebff; color:#4d58c8; padding:8px 10px; margin-right:10px; font-weight:700; cursor:pointer; }
        .wf-result { margin-top:15px; padding:15px; border-radius:10px; border:1px solid #e3e8f0; background:#fafbfe; font-size:12px; }
        .wf-result pre { overflow:auto; white-space:pre-wrap; overflow-wrap:anywhere; font-size:11px; color:#58647a; }
        .wf-footer { text-align:center; font-size:10px; color:#a0a9b8; padding:28px 0 0; }
        .wf-mobile-menu { display:none; }
        @media(max-width:1100px) {
          .wf-sidebar { width:220px; }
          .wf-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
          .wf-content { padding:24px 20px; }
          .wf-shortcuts { grid-template-columns:repeat(2,minmax(0,1fr)); }
        }
        @media(max-width:760px) {
          .wf-layout { display:block; }
          .wf-sidebar { width:100%; padding:12px; }
          .wf-brand { padding:3px 7px 12px; }
          .wf-nav-title, .wf-sidebar-bottom { display:none; }
          .wf-nav { flex-direction:row; overflow-x:auto; padding-bottom:3px; }
          .wf-nav button { white-space:nowrap; flex-shrink:0; padding:9px 11px; }
          .wf-nav button.active { box-shadow:inset 0 -3px #9ca9ff; }
          .wf-topbar { padding:13px 16px; }
          .wf-content { padding:22px 14px; }
          .wf-heading { font-size:23px; }
          .wf-welcome { flex-direction:column; }
          .wf-grid { gap:10px; }
          .wf-card { padding:14px; }
          .wf-stat-value { font-size:23px; }
          .wf-shortcuts, .wf-upload-grid { grid-template-columns:1fr; }
          .wf-panel-head { padding:15px; }
          .wf-search { min-width:0; width:100%; }
          .wf-panel-actions { width:100%; }
          .wf-form-grid { grid-template-columns:1fr; }
          .wf-user-name { max-width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        }
      `}</style>

      {notice && (
        <div className={`wf-notice ${notice.type}`} role="status">
          <span>{notice.type === "success" ? "✓" : "!"}</span>
          <div className="wf-notice-text">{notice.message}</div>
          <button className="wf-close" onClick={() => setNotice(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      <div className="wf-layout">
        <aside className="wf-sidebar">
          <div className="wf-brand">
            <div className="wf-brand-mark">W</div>
            <div>
              <div className="wf-brand-name">WorkForce AI Pro</div>
              <div className="wf-brand-sub">Workforce intelligence</div>
            </div>
          </div>

          <div className="wf-nav-title">Workspace</div>
          <nav className="wf-nav" aria-label="Main navigation">
            {MODULES.map((item) => (
              <button
                key={item.id}
                className={activeModule === item.id ? "active" : ""}
                onClick={() => {
                  setActiveModule(item.id);
                  setSearch("");
                }}
              >
                <Icon>{item.icon}</Icon>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="wf-sidebar-bottom">
            <div><span className="wf-service-dot" />Workforce workspace</div>
            <div style={{ marginTop: 5 }}>Secure employee management</div>
          </div>
        </aside>

        <main className="wf-main">
          <header className="wf-topbar">
            <div>
              <div className="wf-breadcrumb">Workspace / {activeInfo.label}</div>
              <div className="wf-top-title">{activeInfo.label}</div>
            </div>

            <div className="wf-top-actions">
              {hasAuth ? (
                <>
                  <div className="wf-user">
                    <div className="wf-avatar">
                      {(user?.first_name || user?.email || "U").charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="wf-user-name">
                        {user
                          ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email
                          : meBusy ? "Loading profile…" : "Signed in"}
                      </div>
                      <div className="wf-user-role">{user?.role || "User"}</div>
                    </div>
                  </div>
                  <Button variant="secondary" onClick={logout}>Sign out</Button>
                </>
              ) : (
                <Button onClick={() => setModal({ type: "login" })}>Sign in</Button>
              )}
            </div>
          </header>

          <div className="wf-content">
            {activeModule === "overview" ? (
              <>
                <div className="wf-welcome">
                  <div>
                    <div className="wf-eyebrow">Workforce intelligence platform</div>
                    <h1 className="wf-heading">
                      {user?.first_name ? `Welcome back, ${user.first_name}` : "Your workforce, in focus."}
                    </h1>
                    <p className="wf-subtitle">
                      Manage employee information and access workforce insights from one workspace.
                    </p>
                  </div>
                  {!hasAuth && <Button onClick={() => setModal({ type: "login" })}>Sign in to continue →</Button>}
                </div>

                <div className="wf-grid">
                  {overviewCards.map((card) => (
                    <button
                      key={card.label}
                      className="wf-card"
                      style={{ textAlign: "left", cursor: "pointer", border: "1px solid #e8ecf3" }}
                      onClick={() => setActiveModule(card.module)}
                    >
                      <div className="wf-stat-top">
                        <span className="wf-stat-label">{card.label}</span>
                        <span className="wf-stat-icon">{card.icon}</span>
                      </div>
                      <div className="wf-stat-value">—</div>
                      <div className="wf-stat-note">{card.note}</div>
                    </button>
                  ))}
                </div>

                <div className="wf-section-head">
                  <div>
                    <h2 className="wf-section-title">Quick access</h2>
                    <div className="wf-section-sub">Jump into the areas you use most.</div>
                  </div>
                </div>

                <div className="wf-shortcuts">
                  {[
                    { id: "employees", title: "Employee directory", desc: "View employee profiles and workforce details.", icon: "♙" },
                    { id: "leave", title: "Leave management", desc: "Review leave information and requests.", icon: "▤" },
                    { id: "attendance", title: "Attendance", desc: "Access attendance information.", icon: "◷" },
                    { id: "datasets", title: "AI datasets", desc: "Upload and validate workforce CSV data.", icon: "▥" },
                    { id: "attrition", title: "Attrition prediction", desc: "Open available attrition analysis services.", icon: "⌁" },
                    { id: "reports", title: "Reports", desc: "Explore available workforce reporting features.", icon: "▧" },
                  ].map((item) => (
                    <button
                      className="wf-shortcut"
                      key={item.id}
                      onClick={() => setActiveModule(item.id)}
                    >
                      <span className="wf-shortcut-icon">{item.icon}</span>
                      <span>
                        <span className="wf-shortcut-title">{item.title}</span>
                        <span className="wf-shortcut-desc" style={{ display: "block" }}>{item.desc}</span>
                      </span>
                    </button>
                  ))}
                </div>

                <div className="wf-section-head">
                  <div>
                    <h2 className="wf-section-title">Workspace status</h2>
                    <div className="wf-section-sub">Connection and account information.</div>
                  </div>
                </div>

                <div className="wf-card">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 750 }}>Workforce service</div>
                      <div className="wf-help" style={{ marginTop: 5 }}>
                        {loadingSchema ? "Checking service connection…" : openApi ? "The backend service responded successfully." : "The backend service could not be reached."}
                      </div>
                    </div>
                    <span className={`wf-status ${openApi ? "status-good" : loadingSchema ? "status-pending" : "status-bad"}`}>
                      {loadingSchema ? "Connecting" : openApi ? "Connected" : "Unavailable"}
                    </span>
                  </div>
                  <div style={{ borderTop: "1px solid #edf0f5", marginTop: 17, paddingTop: 15, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 700 }}>Your account</div>
                      <div className="wf-help" style={{ marginTop: 5 }}>
                        {user ? `${user.email} · ${user.role}` : hasAuth ? "Your profile could not be loaded." : "Sign in to access protected workforce information."}
                      </div>
                    </div>
                    <Button variant="secondary" onClick={hasAuth ? loadProfile : () => setModal({ type: "login" })}>
                      {hasAuth ? "Refresh profile" : "Sign in"}
                    </Button>
                  </div>
                </div>
              </>
            ) : activeModule === "settings" ? (
              <>
                <div className="wf-welcome">
                  <div>
                    <div className="wf-eyebrow">Personal workspace</div>
                    <h1 className="wf-heading">Settings</h1>
                    <p className="wf-subtitle">Manage your current session and account details.</p>
                  </div>
                </div>
                <div className="wf-card" style={{ maxWidth: 700 }}>
                  <h2 className="wf-section-title">Account details</h2>
                  <div style={{ marginTop: 18, display: "grid", gap: 15 }}>
                    {[
                      ["Name", user ? [user.first_name, user.last_name].filter(Boolean).join(" ") : "Not signed in"],
                      ["Email", user?.email || "—"],
                      ["Role", user?.role || "—"],
                      ["Account status", user ? (user.is_active ? "Active" : "Inactive") : "—"],
                    ].map(([label, value]) => (
                      <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, paddingBottom: 12, borderBottom: "1px solid #edf0f5" }}>
                        <span className="wf-help">{label}</span>
                        <span style={{ fontSize: 12, fontWeight: 700, textAlign: "right" }}>{value}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: 18 }}>
                    {hasAuth
                      ? <Button variant="secondary" onClick={logout}>Sign out</Button>
                      : <Button onClick={() => setModal({ type: "login" })}>Sign in</Button>}
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="wf-welcome">
                  <div>
                    <div className="wf-eyebrow">Workforce management</div>
                    <h1 className="wf-heading">{activeInfo.label}</h1>
                    <p className="wf-subtitle">{activeInfo.description}.</p>
                  </div>
                  <div className="wf-panel-actions">
                    {activeModule === "datasets" && hasAuth && (
                      <Button onClick={() => document.getElementById("dataset-upload")?.scrollIntoView({ behavior: "smooth", block: "center" })}>
                        + Add dataset
                      </Button>
                    )}
                    {activeModule === "documents" && hasAuth && (
                      <Button onClick={() => document.getElementById("document-upload")?.scrollIntoView({ behavior: "smooth", block: "center" })}>
                        + Upload document
                      </Button>
                    )}
                    {activeModule !== "datasets" && activeModule !== "documents" && moduleOperations.some((item) => item.method !== "get") && hasAuth && (
                      <Button onClick={() => {
                        const item = moduleOperations.find((operation) => operation.method === "post" && operation.operation.requestBody);
                        if (item) openDataForm(item);
                        else setNotice({ type: "error", message: "A suitable form is not available for this section." });
                      }}>
                        + Add record
                      </Button>
                    )}
                  </div>
                </div>

                {!hasAuth && (
                  <div className="wf-callout" style={{ marginBottom: 18 }}>
                    Sign in to view protected workforce information. Your account permissions determine which records you can access.
                    <div style={{ marginTop: 12 }}>
                      <Button onClick={() => setModal({ type: "login" })}>Sign in</Button>
                    </div>
                  </div>
                )}

                {activeModule === "datasets" && hasAuth && (
                  <div className="wf-upload-card" id="dataset-upload" style={{ marginBottom: 20 }}>
                    <h3>Upload a workforce dataset</h3>
                    <p>Choose a CSV file to validate it before using it for workforce analysis. Maximum file size: 20 MB.</p>
                    <form className="wf-form" onSubmit={uploadDataset}>
                      <div className="wf-form-grid">
                        <label className="wf-field">
                          <span>Dataset name *</span>
                          <input
                            value={datasetName}
                            onChange={(event) => setDatasetName(event.target.value)}
                            minLength={2}
                            maxLength={150}
                            required
                            placeholder="e.g. Employee attrition 2026"
                          />
                        </label>
                        <label className="wf-field">
                          <span>CSV file *</span>
                          <input
                            className="wf-file"
                            type="file"
                            accept=".csv,text/csv"
                            required
                            onChange={(event) => setDatasetFile(event.target.files?.[0] || null)}
                          />
                        </label>
                      </div>
                      <div className="wf-callout">
                        Required CSV columns: <strong>attrition, age, monthlyincome, yearsatcompany, overtime, jobsatisfaction</strong>. Column names and data are checked by the backend.
                      </div>
                      <div>
                        <Button type="submit" disabled={uploadBusy}>
                          {uploadBusy ? "Uploading…" : "Upload and validate"}
                        </Button>
                      </div>
                    </form>

                    {uploadResult && (
                      <div className="wf-result">
                        <strong>Latest dataset result</strong>
                        <pre>{JSON.stringify(uploadResult, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}

                {activeModule === "documents" && hasAuth && (
                  <div className="wf-upload-card" id="document-upload" style={{ marginBottom: 20 }}>
                    <h3>Upload your document</h3>
                    <p>Supported files: PDF, PNG or JPEG. Maximum file size: 5 MB.</p>
                    <div className="wf-callout" style={{ marginBottom: 15 }}>
                      This upload is linked to the signed-in employee's profile. If your account does not have an employee profile, ask HR to link one before uploading.
                    </div>
                    <form className="wf-form" onSubmit={uploadDocument}>
                      <div className="wf-form-grid">
                        <label className="wf-field">
                          <span>Document category *</span>
                          <input
                            value={documentCategory}
                            onChange={(event) => setDocumentCategory(event.target.value)}
                            minLength={2}
                            maxLength={50}
                            required
                          />
                        </label>
                        <label className="wf-field">
                          <span>Choose file *</span>
                          <input
                            className="wf-file"
                            type="file"
                            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                            required
                            onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
                          />
                        </label>
                      </div>
                      <div>
                        <Button type="submit" disabled={uploadBusy}>
                          {uploadBusy ? "Uploading…" : "Upload document"}
                        </Button>
                      </div>
                    </form>
                  </div>
                )}

                <section className="wf-panel">
                  <div className="wf-panel-head">
                    <div>
                      <h2 className="wf-panel-title">
                        {activeModule === "datasets" ? "Available datasets" : activeModule === "documents" ? "Document records" : `${activeInfo.label} records`}
                      </h2>
                      <p className="wf-panel-desc">
                        {loadingData ? "Loading your records…" : `${filteredRows.length} ${filteredRows.length === 1 ? "record" : "records"} displayed`}
                      </p>
                    </div>
                    <div className="wf-panel-actions">
                      <input
                        className="wf-search"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Search records…"
                        aria-label="Search records"
                      />
                      <Button variant="secondary" onClick={loadModuleData} disabled={loadingData || !hasAuth}>
                        ↻ Refresh
                      </Button>
                      <Button variant="secondary" onClick={exportRows} disabled={!filteredRows.length}>
                        Export CSV
                      </Button>
                    </div>
                  </div>

                  {loadingData ? (
                    <div className="wf-empty">
                      <div className="wf-empty-icon">◌</div>
                      <div className="wf-empty-title">Loading records</div>
                      <div className="wf-empty-desc">Please wait while your information is retrieved.</div>
                    </div>
                  ) : filteredRows.length > 0 && columns.length > 0 ? (
                    <div className="wf-table-wrap">
                      <table className="wf-table">
                        <thead>
                          <tr>
                            {columns.map((key) => <th key={key}>{prettyLabel(key)}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {filteredRows.map((row, index) => (
                            <tr key={row.id ?? row.employee_code ?? index}>
                              {columns.map((key) => {
                                const value = row[key];
                                const isStatus = /status|state/i.test(key);

                                return (
                                  <td key={key}>
                                    {isStatus ? (
                                      <span className={`wf-status ${statusClass(value)}`}>{displayValue(value)}</span>
                                    ) : (
                                      displayValue(value)
                                    )}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="wf-empty">
                      <div className="wf-empty-icon">
                        {activeModule === "datasets" ? "▥" : activeModule === "documents" ? "▧" : "◇"}
                      </div>
                      <div className="wf-empty-title">
                        {search ? "No matching records" : !hasAuth ? "Sign in to continue" : moduleOperations.length ? "Nothing to display yet" : "This area is not configured yet"}
                      </div>
                      <div className="wf-empty-desc">
                        {search
                          ? "Try a different search term."
                          : noDataMessage}
                      </div>
                      {!hasAuth && <Button onClick={() => setModal({ type: "login" })}>Sign in</Button>}
                    </div>
                  )}
                </section>
              </>
            )}

            <div className="wf-footer">
              WorkForce AI Pro · Workforce intelligence and employee management
            </div>
          </div>
        </main>
      </div>

      {modal?.type === "login" && (
        <Modal
          title="Welcome back"
          subtitle="Sign in with your workforce account to continue."
          onClose={() => setModal(null)}
        >
          <form className="wf-form" onSubmit={login}>
            <label className="wf-field">
              <span>Email address</span>
              <input
                type="email"
                autoComplete="username"
                value={loginForm.email}
                onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
                required
                placeholder="you@company.com"
              />
            </label>
            <label className="wf-field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                required
                placeholder="Enter your password"
              />
            </label>
            <div className="wf-form-footer">
              <Button variant="secondary" onClick={() => setModal(null)}>Cancel</Button>
              <Button type="submit" disabled={loginBusy}>{loginBusy ? "Signing in…" : "Sign in"}</Button>
            </div>
          </form>
        </Modal>
      )}

      {modal?.type === "data-form" && (
        <Modal
          title={modal.label}
          subtitle="Enter the information below."
          onClose={() => setModal(null)}
        >
          <form className="wf-form" onSubmit={submitDataForm}>
            <div className="wf-form-grid">
              {Object.entries(modal.properties || {}).map(([name, property]) => (
                <Field
                  key={name}
                  name={name}
                  property={property}
                  value={formValues[name]}
                  required={(modal.required || []).includes(name)}
                  onChange={(value) => setFormValues((current) => ({ ...current, [name]: value }))}
                />
              ))}
            </div>
            {!Object.keys(modal.properties || {}).length && (
              <div className="wf-callout">
                This form needs fields defined by the backend before information can be submitted.
              </div>
            )}
            <div className="wf-form-footer">
              <Button variant="secondary" onClick={() => setModal(null)}>Cancel</Button>
              <Button type="submit" disabled={formBusy || !Object.keys(modal.properties || {}).length}>
                {formBusy ? "Saving…" : "Save"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

export default App;
