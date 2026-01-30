import { useEffect, useState } from "react";
import { listRulepacks, listSits } from "../api/sit";

export default function SitDashboard() {
  const [sitCount, setSitCount] = useState<number | null>(null);
  const [rulepackCount, setRulepackCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listSits(), listRulepacks()])
      .then(([sits, packs]) => {
        setSitCount(sits.length);
        setRulepackCount(packs.length);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err));
      });
  }, []);

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>SIT Service</h1>
          <p>Overview of curated SITs and rule pack exports.</p>
        </div>
      </div>

      {error && (
        <div className="error">
          <strong>Unable to load SIT metrics.</strong>
          <div className="code-block">{error}</div>
        </div>
      )}

      <div className="card-grid">
        <div className="card">
          <small>Total SITs</small>
          <h2>{sitCount ?? "—"}</h2>
          <div>Library of sensitive info types.</div>
        </div>
        <div className="card">
          <small>Rule Packs</small>
          <h2>{rulepackCount ?? "—"}</h2>
          <div>Exports ready for Purview.</div>
        </div>
        <div className="card">
          <small>Status</small>
          <h2>Ready</h2>
          <div>API connected to SIT service.</div>
        </div>
      </div>
    </div>
  );
}
