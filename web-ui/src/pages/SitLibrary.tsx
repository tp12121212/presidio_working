import { useEffect, useMemo, useState } from "react";
import { getSit, listSits, type SitDetail, type SitSummary } from "../api/sit";

export default function SitLibrary() {
  const [sits, setSits] = useState<SitSummary[]>([]);
  const [selected, setSelected] = useState<SitDetail | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSits()
      .then(setSits)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const filtered = useMemo(() => {
    const query = search.toLowerCase();
    return sits.filter((sit) =>
      [sit.name, sit.description || ""].some((value) =>
        value.toLowerCase().includes(query)
      )
    );
  }, [sits, search]);

  const loadDetail = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getSit(id);
      setSelected(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>SIT Library</h1>
          <p>Review curated sensitive information types and versions.</p>
        </div>
      </div>

      {error && (
        <div className="error">
          <strong>Unable to load SITs.</strong>
          <div className="code-block">{error}</div>
        </div>
      )}

      <div className="split">
        <section className="panel">
          <div className="panel-inner">
            <div className="option-group">
              <label>Search</label>
              <input
                className="input"
                placeholder="Search SITs"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={3}>No SITs found.</td>
                  </tr>
                )}
                {filtered.map((sit) => (
                  <tr key={sit.id}>
                    <td>
                      <button
                        className="button ghost"
                        onClick={() => loadDetail(sit.id)}
                      >
                        {sit.name}
                      </button>
                    </td>
                    <td>{sit.description || "—"}</td>
                    <td>{new Date(sit.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="drawer">
          <h3>Detail</h3>
          {loading && <p>Loading SIT details...</p>}
          {!loading && !selected && <p>Select a SIT to view details.</p>}
          {!loading && selected && (
            <div className="page">
              <strong>{selected.name}</strong>
              <div>{selected.description}</div>

              {selected.versions.map((version) => (
                <div key={version.id} className="panel-inner">
                  <div className="entity-tag">Version {version.version_number}</div>
                  <div>Entity: {version.entity_type || "—"}</div>
                  <div>Confidence: {version.confidence || "—"}</div>
                  <div>Source: {version.source || "—"}</div>
                  {version.primary_element && (
                    <div>
                      Primary: {version.primary_element.element_type} →
                      {" "}{version.primary_element.value}
                    </div>
                  )}
                  {version.supporting_logic && (
                    <div>
                      Supporting logic: {version.supporting_logic.mode}
                      {version.supporting_logic.min_n
                        ? ` (min ${version.supporting_logic.min_n})`
                        : ""}
                    </div>
                  )}
                  {version.supporting_groups.map((group) => (
                    <div key={group.name}>
                      <strong>{group.name}</strong>
                      <ul>
                        {group.items.map((item, idx) => (
                          <li key={`${group.name}-${idx}`}>
                            {item.item_type} {item.value ? `: ${item.value}` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
