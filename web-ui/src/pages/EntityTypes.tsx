import { useEffect, useState } from "react";
import { fetchEntityTypes } from "../api/entities";

const LOCAL_KEY = "sit_only_entities";

export default function EntityTypes() {
  const [presidioEntities, setPresidioEntities] = useState<string[]>([]);
  const [sitEntities, setSitEntities] = useState<string[]>(() => {
    const stored = localStorage.getItem(LOCAL_KEY);
    return stored ? JSON.parse(stored) : [];
  });
  const [newEntity, setNewEntity] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEntityTypes()
      .then(setPresidioEntities)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const addEntity = () => {
    if (!newEntity.trim()) return;
    const updated = [...sitEntities, newEntity.trim().toUpperCase()];
    setSitEntities(updated);
    localStorage.setItem(LOCAL_KEY, JSON.stringify(updated));
    setNewEntity("");
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>Entity Types</h1>
          <p>Presidio entities are read-only. Add SIT-only entities for rulepack modeling.</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <section className="panel">
        <div className="panel-inner split">
          <div>
            <h3>Presidio Entities</h3>
            <div className="checkbox-list">
              {presidioEntities.map((entity) => (
                <div key={entity} className="entity-tag">
                  {entity}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3>SIT-only Entities</h3>
            <div className="page">
              <div className="option-group">
                <label>New SIT-only entity</label>
                <input
                  className="input"
                  value={newEntity}
                  onChange={(event) => setNewEntity(event.target.value)}
                />
                <button className="button" onClick={addEntity}>
                  Add
                </button>
              </div>
              <div className="checkbox-list">
                {sitEntities.map((entity) => (
                  <div key={entity} className="entity-tag">
                    {entity}
                  </div>
                ))}
              </div>
              <div className="notice">
                SIT-only entities do not alter Presidio detection unless custom recognizers are configured.
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
