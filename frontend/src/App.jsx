
import { useEffect, useState } from "react";
import axios from "axios";
import "./index.css";

const API_URL = "http://localhost:8003/api";
const TOKEN_KEY = "workforce_access_token";

const dashboardContent = {
  ADMIN: {
    title: "Administration Workspace",
    description: "Manage people, access, and workforce operations.",
    items: [
      {
        title: "User Management",
        description: "Manage user access and organizational roles.",
      },
      {
        title: "Employee Directory",
        description: "View employee records and workforce details.",
      },
      {
        title: "Departments",
        description: "Organize departments and reporting structures.",
      },
      {
        title: "Workforce Intelligence",
        description: "Explore workforce metrics and insights.",
      },
    ],
  },
  HR: {
    title: "Human Resources Workspace",
    description: "Manage employee information and HR operations.",
    items: [
      {
        title: "Employee Management",
        description: "View employee records and workforce details.",
      },
      {
        title: "Departments",
        description: "Explore your organization's departments.",
      },
      {
        title: "Workforce Overview",
        description: "Review workforce information and operations.",
      },
      {
        title: "Attrition Intelligence",
        description: "Workspace for employee attrition insights.",
      },
    ],
  },
  MANAGER: {
    title: "Manager Workspace",
    description: "Review team information and workforce insights.",
    items: [
      {
        title: "Team Overview",
        description: "Review your team's workforce information.",
      },
      {
        title: "Employee Directory",
        description: "Employee directory access depends on permissions.",
      },
      {
        title: "Workforce Insights",
        description: "Explore workforce information and trends.",
      },
      {
        title: "Attrition Intelligence",
        description: "Workspace for attrition insights.",
      },
    ],
  },
  EMPLOYEE: {
    title: "Employee Workspace",
    description: "Your personal workspace for workforce resources.",
    items: [
      {
        title: "My Profile",
        description: "Your personal and employment information.",
      },
      {
        title: "My Department",
        description: "Information about your department.",
      },
      {
        title: "Workforce Resources",
        description: "Access available workforce resources.",
      },
      {
        title: "My Account",
        description: "Your account and sign-in information.",
      },
    ],
  },
};

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Invalid input").join(", ");
  }

  return error.response?.data?.message || fallback;
}

function getEmployeeName(employee) {
  const firstName = employee.user?.first_name || "";
  const lastName = employee.user?.last_name || "";
  return `${firstName} ${lastName}`.trim() || "Unnamed employee";
}

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);

  const [view, setView] = useState("dashboard");
  const [employees, setEmployees] = useState([]);
  const [employeeLoading, setEmployeeLoading] = useState(false);
  const [employeeError, setEmployeeError] = useState("");
  const [employeeSearchInput, setEmployeeSearchInput] = useState("");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [employeeRefresh, setEmployeeRefresh] = useState(0);

  // Load employee data only when the directory is opened.
  useEffect(() => {
    if (view !== "employees") {
      return undefined;
    }

    const role = String(user?.role || "").toUpperCase();

    // This UI permission check complements backend RBAC.
    if (!["ADMIN", "HR"].includes(role)) {
      setEmployees([]);
      setEmployeeError(
        "You are not authorized to view the employee directory.",
      );
      setEmployeeLoading(false);
      return undefined;
    }

    const token = localStorage.getItem(TOKEN_KEY);

    if (!token) {
      setEmployees([]);
      setEmployeeError("Your session has expired. Please sign in again.");
      setEmployeeLoading(false);
      return undefined;
    }

    let cancelled = false;

    async function loadEmployees() {
      setEmployeeLoading(true);
      setEmployeeError("");

      try {
        const response = await axios.get(`${API_URL}/employees/`, {
          params: {
            search: employeeSearch.trim() || undefined,
            limit: 100,
          },
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!cancelled) {
          // The current API returns a list of employees.
          const data = response.data;
          setEmployees(Array.isArray(data) ? data : []);
        }
      } catch (requestError) {
        if (!cancelled) {
          setEmployees([]);
          setEmployeeError(
            getErrorMessage(
              requestError,
              "Unable to load employees. Please try again.",
            ),
          );
        }
      } finally {
        if (!cancelled) {
          setEmployeeLoading(false);
        }
      }
    }

    loadEmployees();

    return () => {
      cancelled = true;
    };
  }, [view, user, employeeSearch, employeeRefresh]);

  async function handleLogin(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email: email.trim(),
        password,
      });

      const { access_token, user_id, role } = response.data;

      if (!access_token) {
        throw new Error("The server did not return an access token.");
      }

      localStorage.setItem(TOKEN_KEY, access_token);

      // Use the verified login response as the initial identity.
      let loggedInUser = {
        id: user_id,
        user_id,
        email: email.trim(),
        role: String(role || "").toUpperCase(),
      };

      // Load the user's profile without losing a successful login
      // if the profile endpoint is temporarily unavailable.
      try {
        const profileResponse = await axios.get(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${access_token}`,
          },
        });

        loggedInUser = {
          ...profileResponse.data,
          ...loggedInUser,
          ...profileResponse.data,
          id: profileResponse.data.id ?? user_id,
          user_id: user_id ?? profileResponse.data.id,
          email: profileResponse.data.email || email.trim(),
          role: String(role || profileResponse.data.role || "").toUpperCase(),
        };
      } catch (profileError) {
        console.warn("Could not load the full user profile.", profileError);
      }

      setUser(loggedInUser);
      setView("dashboard");
      setPassword("");
    } catch (loginError) {
      localStorage.removeItem(TOKEN_KEY);
      setError(
        getErrorMessage(
          loginError,
          loginError.message || "Unable to sign in. Check your credentials.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setEmail("");
    setPassword("");
    setError("");
    setView("dashboard");
    setEmployees([]);
    setEmployeeError("");
    setEmployeeSearch("");
    setEmployeeSearchInput("");
  }

  function openEmployeeDirectory() {
    setEmployeeError("");
    setView("employees");
  }

  function handleEmployeeSearch(event) {
    event.preventDefault();
    setEmployeeSearch(employeeSearchInput.trim());
  }

  function clearEmployeeSearch() {
    setEmployeeSearchInput("");
    setEmployeeSearch("");
  }

  const role = String(user?.role || "").toUpperCase();
  const canViewEmployees = ["ADMIN", "HR"].includes(role);
  const dashboard = dashboardContent[role] || {
    title: "Workforce Workspace",
    description: "Welcome to your workforce workspace.",
    items: [],
  };

  const fullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    user?.email ||
    "User";

  // Employee Directory page
  if (user && view === "employees") {
    return (
      <div className="app-shell">
        <header className="topbar">
          <button
            className="brand-button"
            type="button"
            onClick={() => setView("dashboard")}
            aria-label="Return to dashboard"
          >
            <span className="brand-mark">W</span>
            <span className="brand-copy">
              <strong>WorkForce AI</strong>
              <small>PRO · WORKFORCE INTELLIGENCE</small>
            </span>
          </button>

          <div className="topbar-actions">
            <div className="user-chip">
              <span className="user-avatar">
                {fullName.charAt(0).toUpperCase()}
              </span>
              <span className="user-chip-text">
                <strong>{fullName}</strong>
                <small>{role}</small>
              </span>
            </div>
            <button
              className="button button-secondary logout-button"
              type="button"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="page-container">
          <button
            type="button"
            className="back-button"
            onClick={() => setView("dashboard")}
          >
            <span aria-hidden="true">←</span> Back to dashboard
          </button>

          <section className="page-heading">
            <div>
              <span className="eyebrow">PEOPLE OPERATIONS</span>
              <h1>Employee Directory</h1>
              <p>
                Search and review employee records across your organization.
              </p>
            </div>

            <button
              type="button"
              className="button button-primary"
              onClick={() => setEmployeeRefresh((current) => current + 1)}
              disabled={employeeLoading}
            >
              {employeeLoading ? "Refreshing..." : "↻ Refresh"}
            </button>
          </section>

          <section className="directory-summary">
            <div>
              <span className="summary-label">Records loaded</span>
              <strong>{employees.length}</strong>
              <small>
                {employees.length === 100
                  ? "Maximum 100 records per request"
                  : "Based on the current search"}
              </small>
            </div>
            <div>
              <span className="summary-label">Access level</span>
              <strong>{role}</strong>
              <small>Role-based access enabled</small>
            </div>
          </section>

          <section className="directory-panel">
            <div className="panel-heading">
              <div>
                <h2>Employee records</h2>
                <p>Search by name, email, employee code, or designation.</p>
              </div>
            </div>

            <form
              className="employee-search-form"
              onSubmit={handleEmployeeSearch}
            >
              <label className="search-field">
                <span className="sr-only">Search employees</span>
                <span aria-hidden="true" className="search-icon">
                  ⌕
                </span>
                <input
                  type="search"
                  value={employeeSearchInput}
                  onChange={(event) =>
                    setEmployeeSearchInput(event.target.value)
                  }
                  placeholder="Search employees..."
                />
              </label>

              <button className="button button-primary" type="submit">
                Search
              </button>

              <button
                className="button button-secondary"
                type="button"
                onClick={clearEmployeeSearch}
              >
                Clear
              </button>
            </form>

            {employeeLoading && (
              <div className="directory-message" role="status">
                <span className="loading-spinner" />
                Loading employee records...
              </div>
            )}

            {employeeError && !employeeLoading && (
              <div className="alert alert-error" role="alert">
                <strong>Unable to load directory</strong>
                <p>{employeeError}</p>
                <button
                  type="button"
                  className="text-button"
                  onClick={() => setEmployeeRefresh((current) => current + 1)}
                >
                  Try again
                </button>
              </div>
            )}

            {!employeeLoading && !employeeError && (
              <>
                <div className="table-wrapper">
                  <table className="employee-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Employee code</th>
                        <th>Department</th>
                        <th>Designation</th>
                        <th>Joining date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((employee) => {
                        const isActive = Boolean(employee.user?.is_active);

                        return (
                          <tr key={employee.id}>
                            <td>
                              <div className="employee-identity">
                                <span className="employee-avatar">
                                  {getEmployeeName(employee)
                                    .charAt(0)
                                    .toUpperCase()}
                                </span>
                                <span>
                                  <strong>{getEmployeeName(employee)}</strong>
                                  <small>{employee.user?.email || "—"}</small>
                                </span>
                              </div>
                            </td>
                            <td>{employee.employee_code || "—"}</td>
                            <td>{employee.department?.name || "Unassigned"}</td>
                            <td>{employee.designation || "—"}</td>
                            <td>{employee.joining_date || "—"}</td>
                            <td>
                              <span
                                className={`status-pill ${
                                  isActive ? "status-active" : "status-inactive"
                                }`}
                              >
                                <span className="status-dot" />
                                {isActive ? "Active" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {employees.length === 0 && (
                  <div className="empty-state">
                    <span className="empty-state-icon">⌕</span>
                    <h3>No employees found</h3>
                    <p>
                      {employeeSearch
                        ? "Try another search term or clear your search."
                        : "Employee records will appear here when available."}
                    </p>
                  </div>
                )}

                <div className="table-footer">
                  Showing {employees.length} employee
                  {employees.length === 1 ? "" : "s"}
                </div>
              </>
            )}
          </section>

          <p className="security-note">
            Employee information is available according to your assigned role
            and backend permissions.
          </p>
        </main>

        <footer className="app-footer">
          <span>WorkForce AI Pro</span>
          <span>People · Performance · Intelligence</span>
        </footer>
      </div>
    );
  }

  // Main dashboard
  if (user) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <button
            className="brand-button"
            type="button"
            onClick={() => setView("dashboard")}
            aria-label="Return to dashboard"
          >
            <span className="brand-mark">W</span>
            <span className="brand-copy">
              <strong>WorkForce AI</strong>
              <small>PRO · WORKFORCE INTELLIGENCE</small>
            </span>
          </button>

          <div className="topbar-actions">
            <div className="user-chip">
              <span className="user-avatar">
                {fullName.charAt(0).toUpperCase()}
              </span>
              <span className="user-chip-text">
                <strong>{fullName}</strong>
                <small>{role}</small>
              </span>
            </div>
            <button
              className="button button-secondary logout-button"
              type="button"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="page-container">
          <section className="welcome-banner">
            <div className="welcome-copy">
              <span className="eyebrow">YOUR WORKSPACE</span>
              <h1>{dashboard.title}</h1>
              <p>{dashboard.description}</p>
              <div className="welcome-meta">
                <span className="online-indicator" />
                Signed in as {role}
              </div>
            </div>

            <div className="welcome-art" aria-hidden="true">
              <div className="art-orbit orbit-one" />
              <div className="art-orbit orbit-two" />
              <div className="art-center">W</div>
              <span className="art-node node-one">+</span>
              <span className="art-node node-two">✦</span>
              <span className="art-node node-three">↗</span>
            </div>
          </section>

          <section className="dashboard-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">WORKSPACE OVERVIEW</span>
                <h2>Your modules</h2>
                <p>Quick access to your available workspace modules.</p>
              </div>
              <span className="role-badge">{role}</span>
            </div>

            <div className="dashboard-grid">
              {dashboard.items.map(({ title, description }, index) => {
                const isEmployeeModule =
                  title === "Employee Directory" ||
                  title === "Employee Management";

                return (
                  <article className="workspace-card" key={title}>
                    <div className="workspace-card-top">
                      <span className="workspace-number">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="workspace-card-symbol">
                        {["◈", "◎", "⌘", "✳"][index % 4]}
                      </span>
                    </div>

                    <h3>{title}</h3>
                    <p>{description}</p>

                    {canViewEmployees && isEmployeeModule && (
                      <button
                        type="button"
                        className="workspace-action"
                        onClick={openEmployeeDirectory}
                      >
                        Open employee directory <span>→</span>
                      </button>
                    )}

                    <div className="workspace-card-bottom">
                      <span className="workspace-status-dot" />
                      <span>
                        {canViewEmployees && isEmployeeModule
                          ? "Connected to workforce API"
                          : "Workspace module"}
                      </span>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="dashboard-notice">
            <span className="notice-icon">i</span>
            <p>
              Available features depend on your role. Backend authorization
              remains responsible for protecting workforce data.
            </p>
          </section>
        </main>

        <footer className="app-footer">
          <span>WorkForce AI Pro</span>
          <span>People · Performance · Intelligence</span>
        </footer>
      </div>
    );
  }

  // Login page
  return (
    <div className="login-page">
      <div className="login-decoration decoration-one" />
      <div className="login-decoration decoration-two" />

      <header className="login-brand">
        <span className="brand-mark">W</span>
        <span className="brand-copy">
          <strong>WorkForce AI</strong>
          <small>PRO · WORKFORCE INTELLIGENCE</small>
        </span>
      </header>

      <main className="login-layout">
        <section className="login-intro">
          <span className="eyebrow">THE INTELLIGENCE BEHIND YOUR PEOPLE</span>
          <h1>
            Build a stronger workforce.
            <span> Make smarter decisions.</span>
          </h1>
          <p>
            One connected workspace for people operations, workforce insights,
            and the next generation of HR intelligence.
          </p>

          <div className="login-feature-list">
            <div>
              <span className="feature-icon">✓</span>
              <span>
                <strong>Secure access</strong>
                <small>Token-based authentication</small>
              </span>
            </div>
            <div>
              <span className="feature-icon">◎</span>
              <span>
                <strong>Role-based workspace</strong>
                <small>Experience tailored to your role</small>
              </span>
            </div>
            <div>
              <span className="feature-icon">↗</span>
              <span>
                <strong>Workforce intelligence</strong>
                <small>Built for people-focused decisions</small>
              </span>
            </div>
          </div>
        </section>

        <section className="login-card">
          <div className="login-card-heading">
            <span className="login-card-icon">↗</span>
            <span className="eyebrow">WELCOME BACK</span>
            <h2>Sign in to your workspace</h2>
            <p>Enter your account details to continue.</p>
          </div>

          <form className="login-form" onSubmit={handleLogin}>
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              autoComplete="username"
              placeholder="you@company.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {error && (
              <div className="alert alert-error" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="button button-primary login-submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in to workspace"}
              {!loading && <span>→</span>}
            </button>
          </form>

          <div className="login-card-footer">
            <span className="secure-lock">▣</span>
            Your workspace is protected by secure authentication.
          </div>
        </section>
      </main>

      <footer className="login-footer">
        <span>© WorkForce AI Pro</span>
        <span>People · Performance · Intelligence</span>
      </footer>
    </div>
  );
}

export default App;
