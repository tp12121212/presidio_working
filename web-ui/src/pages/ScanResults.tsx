import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getScan, type ScanFileResult, type ScanResult } from "../api/scan";
import {
  buildNonOverlappingSpans,
  entityColorMap,
  sliceWithHighlights,
} from "../utils/highlight";

function buildTree(files: ScanFileResult[]) {
  const tree: Record<string, ScanFileResult[]> = {};
  files.forEach((file) => {
    const root = file.virtual_path.split("::")[0];
    tree[root] = tree[root] || [];
    tree[root].push(file);
  });
  return tree;
}

export default function ScanResults() {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [scanInput, setScanInput] = useState(scanId || "");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) return;
    getScan(scanId)
      .then(setScan)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [scanId]);

  const tree = useMemo(() => buildTree(scan?.files || []), [scan]);

  const renderPreview = (file: ScanFileResult) => {
    if (!file.text_preview) return <div className="notice">No preview available.</div>;
    const spans = buildNonOverlappingSpans(
      file.entities.map((entity) => ({
        entity_type: entity.entity_type,
        start: entity.start,
        end: entity.end,
        score: entity.score || 0,
      }))
    );
    const chunks = sliceWithHighlights(file.text_preview, spans);
    return (
      <div className="highlight-box">
        {chunks.map((chunk, idx) =>
          chunk.span ? (
            <mark
              key={`${chunk.span.start}-${idx}`}
              className="highlight"
              style={{ background: entityColorMap(chunk.span.entity_type) }}
            >
              {chunk.text}
            </mark>
          ) : (
            <span key={`plain-${idx}`}>{chunk.text}</span>
          )
        )}
      </div>
    );
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>Scan Results</h1>
          <p>Review extracted entities by file and build SITs from findings.</p>
        </div>
        <div className="option-group">
          <label>Scan ID</label>
          <input
            className="input"
            value={scanInput}
            onChange={(event) => setScanInput(event.target.value)}
          />
          <button className="button ghost" onClick={() => navigate(`/scan/results/${scanInput}`)}>
            Load
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {scan && (
        <div className="notice">
          Status: {scan.status} {scan.error ? `— ${scan.error}` : ""}
          <button className="button secondary" onClick={() => navigate(`/sit/builder?scanId=${scan.scan_id}`)}>
            Build SIT from this scan
          </button>
        </div>
      )}

      {!scan && <div className="notice">Enter a scan ID to load results.</div>}

      {scan &&
        Object.entries(tree).map(([root, files]) => (
          <section key={root} className="panel">
            <div className="panel-inner page">
              <h3>{root}</h3>
              {files.map((file) => (
                <div key={file.file_id} className="drawer">
                  <div className="page">
                    <strong>{file.virtual_path}</strong>
                    <div>
                      Extraction: {file.extraction.method}{" "}
                      {file.extraction.ocr_used ? "(OCR)" : ""}
                    </div>
                    {file.extraction.warnings.length > 0 && (
                      <div className="notice">
                        {file.extraction.warnings.join(" | ")}
                      </div>
                    )}
                    {renderPreview(file)}

                    <table className="table">
                      <thead>
                        <tr>
                          <th>Entity</th>
                          <th>Value</th>
                          <th>Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {file.entities.length === 0 && (
                          <tr>
                            <td colSpan={3}>No entities detected.</td>
                          </tr>
                        )}
                        {file.entities.map((entity, idx) => (
                          <tr key={`${file.file_id}-entity-${idx}`}>
                            <td>{entity.entity_type}</td>
                            <td>{entity.text || "—"}</td>
                            <td>{entity.score?.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    <div className="split">
                      <div>
                        <h4>Regex Candidates</h4>
                        {file.regex_candidates.length === 0 && <p>None</p>}
                        {file.regex_candidates.map((candidate) => (
                          <div key={candidate.id} className="entity-tag">
                            {candidate.regex}
                          </div>
                        ))}
                      </div>
                      <div>
                        <h4>Keyword Candidates</h4>
                        {file.keyword_candidates.length === 0 && <p>None</p>}
                        {file.keyword_candidates.map((candidate) => (
                          <div key={candidate.keyword} className="entity-tag">
                            {candidate.keyword} ({candidate.count})
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
    </div>
  );
}
