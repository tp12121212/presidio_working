import { useEffect, useState } from "react";
import {
  createRulepack,
  exportRulepack,
  getSit,
  listSits,
  setRulepackSelections,
  type SitDetail,
} from "../api/sit";

export default function SitExport() {
  const [sits, setSits] = useState<SitDetail[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [name, setName] = useState("Presidio Rule Pack");
  const [version, setVersion] = useState("1.0.0");
  const [publisher, setPublisher] = useState("Presidio");
  const [locale, setLocale] = useState("en-US");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    listSits()
      .then(async (items) => {
        const details = await Promise.all(items.map((sit) => getSit(sit.id)));
        setSits(details);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const toggleVersion = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      if (!selected.length) {
        throw new Error("Select at least one SIT version.");
      }
      const rulepack = await createRulepack({
        name,
        version,
        publisher,
        locale,
      });
      await setRulepackSelections(rulepack.id, selected);
      const blob = await exportRulepack(rulepack.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${name.replace(/\s+/g, "-")}-${version}.xml`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setSuccess("Rule pack generated and downloaded.");
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
          <h1>Rule Pack Export</h1>
          <p>Generate a Purview rule pack from selected SIT versions.</p>
        </div>
      </div>

      {(error || success) && (
        <div className={error ? "error" : "notice"}>
          <strong>{error || success}</strong>
        </div>
      )}

      <section className="panel">
        <div className="panel-inner split">
          <div className="page">
            <div className="option-group">
              <label>Rule pack name</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="option-group">
              <label>Version</label>
              <input className="input" value={version} onChange={(e) => setVersion(e.target.value)} />
            </div>
            <div className="option-group">
              <label>Publisher</label>
              <input className="input" value={publisher} onChange={(e) => setPublisher(e.target.value)} />
            </div>
            <div className="option-group">
              <label>Locale</label>
              <input className="input" value={locale} onChange={(e) => setLocale(e.target.value)} />
            </div>
            <button className="button" onClick={handleExport} disabled={loading}>
              {loading ? "Generating..." : "Generate Rule Pack"}
            </button>
          </div>

          <div className="page">
            <label>Available SIT Versions</label>
            <div className="checkbox-list">
              {sits.length === 0 && <div>Loading SIT versions...</div>}
              {sits.map((sit) => (
                <div key={sit.id}>
                  <strong>{sit.name}</strong>
                  {sit.versions.map((versionItem) => (
                    <label key={versionItem.id} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={selected.includes(versionItem.id)}
                        onChange={() => toggleVersion(versionItem.id)}
                      />
                      Version {versionItem.version_number} — {versionItem.entity_type || "—"}
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
