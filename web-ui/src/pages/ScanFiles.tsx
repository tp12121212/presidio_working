import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchEntityTypes } from "../api/entities";
import { scanArchive, scanBatch, scanEmail, scanFile } from "../api/scan";

const FALLBACK_ENTITIES = [
  "PERSON",
  "EMAIL_ADDRESS",
  "PHONE_NUMBER",
  "CREDIT_CARD",
  "US_SSN",
  "LOCATION",
];

export default function ScanFiles() {
  const navigate = useNavigate();
  const [entityTypes, setEntityTypes] = useState<string[]>(FALLBACK_ENTITIES);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([
    "PERSON",
    "EMAIL_ADDRESS",
  ]);
  const [threshold, setThreshold] = useState(0.35);
  const [ocrMode, setOcrMode] = useState<"auto" | "force" | "off">("auto");
  const [language, setLanguage] = useState("en");
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [parseHtml, setParseHtml] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchEntityTypes()
      .then((data) => {
        setEntityTypes(data);
        setSelectedEntities(data.slice(0, 6));
      })
      .catch(() => {
        setEntityTypes(FALLBACK_ENTITIES);
        setSelectedEntities(FALLBACK_ENTITIES);
      });
  }, []);

  const options = {
    entityTypes: selectedEntities,
    threshold,
    language,
    ocrMode,
    includeHeaders,
    parseHtml,
  };

  const toggleEntity = (entity: string) => {
    setSelectedEntities((prev) =>
      prev.includes(entity)
        ? prev.filter((item) => item !== entity)
        : [...prev, entity]
    );
  };

  const handleScan = async (action: () => Promise<string>) => {
    setLoading(true);
    setMessage(null);
    try {
      const scanId = await action();
      navigate(`/scan/results/${scanId}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleBatch = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files);
    const paths = fileArray.map((file) => (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name);
    await handleScan(() => scanBatch(fileArray, paths, options));
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>Scan Files</h1>
          <p>Upload files, directories, archives, or emails for OCR + Presidio analysis.</p>
        </div>
      </div>

      {message && <div className="error">{message}</div>}

      <div className="panel">
        <div className="panel-inner demo-layout">
          <div className="page">
            <div className="option-group">
              <label>Single file</label>
              <input
                type="file"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    handleScan(() => scanFile(file, options));
                  }
                }}
                disabled={loading}
              />
            </div>

            <div className="option-group">
              <label>Directory upload</label>
              <input
                type="file"
                multiple
                // @ts-expect-error webkitdirectory is supported in browsers
                webkitdirectory="true"
                onChange={(event) => handleBatch(event.target.files)}
                disabled={loading}
              />
            </div>

            <div className="option-group">
              <label>Archive upload (.zip/.7z/.rar/.tar/.tgz)</label>
              <input
                type="file"
                accept=".zip,.7z,.rar,.tar,.tgz"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    handleScan(() => scanArchive(file, options));
                  }
                }}
                disabled={loading}
              />
            </div>

            <div className="option-group">
              <label>Email upload (.eml/.msg)</label>
              <input
                type="file"
                accept=".eml,.msg"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    handleScan(() => scanEmail(file, options));
                  }
                }}
                disabled={loading}
              />
            </div>
          </div>

          <aside className="options">
            <div className="option-group">
              <label>Entity types</label>
              <div className="checkbox-list">
                {entityTypes.map((entity) => (
                  <label key={entity} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={selectedEntities.includes(entity)}
                      onChange={() => toggleEntity(entity)}
                    />
                    {entity}
                  </label>
                ))}
              </div>
            </div>

            <div className="option-group">
              <label>Confidence threshold ({threshold.toFixed(2)})</label>
              <input
                className="range"
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={threshold}
                onChange={(event) => setThreshold(Number(event.target.value))}
              />
            </div>

            <div className="option-group">
              <label>OCR mode</label>
              <select
                className="select"
                value={ocrMode}
                onChange={(event) =>
                  setOcrMode(event.target.value as "auto" | "force" | "off")
                }
              >
                <option value="auto">Auto</option>
                <option value="force">Force OCR</option>
                <option value="off">Disable OCR</option>
              </select>
            </div>

            <div className="option-group">
              <label>Language</label>
              <select
                className="select"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="en">English</option>
              </select>
            </div>

            <div className="option-group">
              <label>Email parsing</label>
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={includeHeaders}
                  onChange={() => setIncludeHeaders((prev) => !prev)}
                />
                Include headers
              </label>
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={parseHtml}
                  onChange={() => setParseHtml((prev) => !prev)}
                />
                Parse HTML body
              </label>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
