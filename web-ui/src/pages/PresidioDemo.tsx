import { useEffect, useMemo, useState } from "react";
import {
  analyzeText,
  fetchSupportedEntities,
  redactText,
  type AnalyzerResult,
  type RedactOptions,
} from "../api/presidio";
import {
  buildNonOverlappingSpans,
  entityColorMap,
  sliceWithHighlights,
} from "../utils/highlight";

const FALLBACK_ENTITIES = [
  "PERSON",
  "EMAIL_ADDRESS",
  "PHONE_NUMBER",
  "CREDIT_CARD",
  "US_SSN",
  "LOCATION",
  "DATE_TIME",
  "IP_ADDRESS",
  "URL",
];

const SAMPLE_TEXT =
  "John Doe lives in Seattle. His email is john.doe@example.com and his SSN is 123-45-6789.\nCall him at (206) 555-0199 before 04/15/2025.";

export default function PresidioDemo() {
  const [activeTab, setActiveTab] = useState<"analyze" | "redact">("analyze");
  const [text, setText] = useState(SAMPLE_TEXT);
  const [language, setLanguage] = useState("en");
  const [supportedEntities, setSupportedEntities] = useState<string[]>([]);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [threshold, setThreshold] = useState(0.35);
  const [results, setResults] = useState<AnalyzerResult[]>([]);
  const [redacted, setRedacted] = useState("");
  const [redactionMode, setRedactionMode] = useState<RedactOptions["mode"]>(
    "replace"
  );
  const [maskChar, setMaskChar] = useState("*");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rawError, setRawError] = useState<string | null>(null);
  const [lastAnalyzedText, setLastAnalyzedText] = useState("");

  useEffect(() => {
    if (supportedEntities.length) {
      return;
    }
    fetchSupportedEntities(language)
      .then((entities) => {
        const sorted = entities.slice().sort();
        setSupportedEntities(sorted);
        setSelectedEntities(sorted.slice(0, 6));
      })
      .catch(() => {
        setSupportedEntities(FALLBACK_ENTITIES);
        setSelectedEntities(FALLBACK_ENTITIES.slice(0, 6));
      });
  }, [language, supportedEntities.length]);

  const spans = useMemo(
    () => buildNonOverlappingSpans(results),
    [results]
  );
  const chunks = useMemo(() => sliceWithHighlights(text, spans), [text, spans]);

  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => b.score - a.score);
  }, [results]);

  const analyze = async () => {
    setLoading(true);
    setError(null);
    setRawError(null);
    try {
      const response = await analyzeText(text, {
        entities: selectedEntities,
        language,
        scoreThreshold: threshold,
      });
      setResults(response);
      setLastAnalyzedText(text);
    } catch (err) {
      setError("We could not analyze the text. Check the analyzer service.");
      setRawError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const redact = async () => {
    setLoading(true);
    setError(null);
    setRawError(null);
    try {
      let currentResults = results;
      if (!currentResults.length || lastAnalyzedText !== text) {
        currentResults = await analyzeText(text, {
          entities: selectedEntities,
          language,
          scoreThreshold: threshold,
        });
        setResults(currentResults);
        setLastAnalyzedText(text);
      }
      const redactedText = await redactText(text, currentResults, {
        mode: redactionMode,
        maskChar,
      });
      setRedacted(redactedText);
    } catch (err) {
      setError("We could not redact the text. Check the anonymizer service.");
      setRawError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleEntity = (entity: string) => {
    setSelectedEntities((prev) =>
      prev.includes(entity) ? prev.filter((item) => item !== entity) : [...prev, entity]
    );
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>Presidio Demo</h1>
          <p>Detect and redact sensitive data with real-time entity insights.</p>
        </div>
      </div>

      <section className="panel">
        <div className="panel-inner demo-layout">
          <div className="page">
            <div className="tabs">
              <button
                className={`tab${activeTab === "analyze" ? " active" : ""}`}
                onClick={() => setActiveTab("analyze")}
              >
                Analyze
              </button>
              <button
                className={`tab${activeTab === "redact" ? " active" : ""}`}
                onClick={() => setActiveTab("redact")}
              >
                Redact
              </button>
            </div>

            <textarea
              className="textarea"
              value={text}
              onChange={(event) => setText(event.target.value)}
            />

            {activeTab === "analyze" && (
              <button className="button" onClick={analyze} disabled={loading}>
                {loading ? "Analyzing..." : "Analyze"}
              </button>
            )}

            {activeTab === "redact" && (
              <div className="page">
                <button className="button" onClick={redact} disabled={loading}>
                  {loading ? "Redacting..." : "Redact"}
                </button>
                <div className="highlight-box">
                  {redacted || "Run redaction to see the masked output."}
                </div>
              </div>
            )}

            {error && (
              <div className="error">
                <strong>{error}</strong>
                {rawError && <div className="code-block">{rawError}</div>}
              </div>
            )}

            {activeTab === "analyze" && (
              <>
                <div className="highlight-box">
                  {chunks.length === 0
                    ? "Add text to analyze."
                    : chunks.map((chunk, idx) =>
                        chunk.span ? (
                          <mark
                            key={`${chunk.span.start}-${idx}`}
                            className="highlight"
                            style={{ background: entityColorMap(chunk.span.entity_type) }}
                            title={`${chunk.span.entity_type} (${chunk.span.score.toFixed(2)})`}
                          >
                            {chunk.text}
                          </mark>
                        ) : (
                          <span key={`plain-${idx}`}>{chunk.text}</span>
                        )
                      )}
                </div>

                <table className="table">
                  <thead>
                    <tr>
                      <th>Entity</th>
                      <th>Value</th>
                      <th>Start</th>
                      <th>End</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedResults.length === 0 && (
                      <tr>
                        <td colSpan={5}>No entities detected yet.</td>
                      </tr>
                    )}
                    {sortedResults.map((item, idx) => (
                      <tr key={`${item.entity_type}-${item.start}-${idx}`}>
                        <td>
                          <span className="entity-tag">{item.entity_type}</span>
                        </td>
                        <td>{text.slice(item.start, item.end)}</td>
                        <td>{item.start}</td>
                        <td>{item.end}</td>
                        <td>{item.score.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>

          <aside className="options">
            <div className="option-group">
              <label>Entity types</label>
              <div className="checkbox-list">
                {supportedEntities.map((entity) => (
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
              <label>Redaction mode</label>
              <select
                className="select"
                value={redactionMode}
                onChange={(event) =>
                  setRedactionMode(event.target.value as RedactOptions["mode"])
                }
              >
                <option value="replace">Replace with [REDACTED]</option>
                <option value="entity_tag">Replace with &lt;ENTITY&gt;</option>
                <option value="mask">Mask with character</option>
              </select>
              {redactionMode === "mask" && (
                <input
                  className="input"
                  value={maskChar}
                  maxLength={1}
                  onChange={(event) => setMaskChar(event.target.value || "*")}
                />
              )}
            </div>

            <div className="notice">
              Entities are loaded from the analyzer service when available.
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
