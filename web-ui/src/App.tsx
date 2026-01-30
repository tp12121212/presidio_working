import { NavLink, Route, Routes } from "react-router-dom";
import PresidioDemo from "./pages/PresidioDemo";
import ScanFiles from "./pages/ScanFiles";
import ScanResults from "./pages/ScanResults";
import SitBuilder from "./pages/SitBuilder";
import EntityTypes from "./pages/EntityTypes";
import SitDashboard from "./pages/SitDashboard";
import SitLibrary from "./pages/SitLibrary";
import SitExport from "./pages/SitExport";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">Presidio Studio</div>
          <div className="brand-sub">Analyze, redact, and curate SITs</div>
        </div>
        <nav className="nav-section">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `nav-item${isActive ? " active" : ""}`
            }
          >
            Presidio Demo
          </NavLink>
          <div className="nav-item">Scan Files ▾</div>
          <div className="nav-sub">
            <NavLink
              to="/scan/files"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Upload & Scan
            </NavLink>
            <NavLink
              to="/scan/results"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Scan Results
            </NavLink>
          </div>
          <NavLink
            to="/sit/builder"
            className={({ isActive }) =>
              `nav-item${isActive ? " active" : ""}`
            }
          >
            SIT Builder
          </NavLink>
          <NavLink
            to="/entities"
            className={({ isActive }) =>
              `nav-item${isActive ? " active" : ""}`
            }
          >
            Entity Types
          </NavLink>
          <div className="nav-item">SIT Service ▾</div>
          <div className="nav-sub">
            <NavLink
              to="/sit"
              end
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/sit/library"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              SIT Library
            </NavLink>
            <NavLink
              to="/sit/export"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Rule Pack Export
            </NavLink>
          </div>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<PresidioDemo />} />
          <Route path="/scan/files" element={<ScanFiles />} />
          <Route path="/scan/results" element={<ScanResults />} />
          <Route path="/scan/results/:scanId" element={<ScanResults />} />
          <Route path="/sit/builder" element={<SitBuilder />} />
          <Route path="/entities" element={<EntityTypes />} />
          <Route path="/sit" element={<SitDashboard />} />
          <Route path="/sit/library" element={<SitLibrary />} />
          <Route path="/sit/export" element={<SitExport />} />
        </Routes>
      </main>
    </div>
  );
}
