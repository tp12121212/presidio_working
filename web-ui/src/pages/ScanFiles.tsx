import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearEntityTypesCache, fetchEntityTypes } from "../api/entities";
import { scanArchive, scanBatch, scanEmail, scanFile } from "../api/scan";

const FALLBACK_ENTITIES = [
  "PERSON",
  "EMAIL_ADDRESS",
  "PHONE_NUMBER",
  "CREDIT_CARD",
  "US_SSN",
  "LOCATION",
];

type ScanOptionsState = {
  entityTypes: string[];
  selectedEntities: string[];
  threshold: number;
  ocrMode: "auto" | "force" | "off";
  language: string;
  includeHeaders: boolean;
  parseHtml: boolean;
  includeAttachments: boolean;
  includeInlineImages: boolean;
};

type ScanFilesProps = {
  embedded?: boolean;
  optionsState?: ScanOptionsState;
  onOptionsChange?: (next: ScanOptionsState) => void;
};

export default function ScanFiles({
  embedded = false,
  optionsState,
  onOptionsChange,
}: ScanFilesProps) {
  const navigate = useNavigate();
  const [entityTypes, setEntityTypes] = useState<string[]>(
    optionsState?.entityTypes ?? FALLBACK_ENTITIES
  );
  const [selectedEntities, setSelectedEntities] = useState<string[]>(
    optionsState?.selectedEntities ?? ["PERSON", "EMAIL_ADDRESS"]
  );
  const [threshold, setThreshold] = useState(optionsState?.threshold ?? 0.35);
  const [ocrMode, setOcrMode] = useState<"auto" | "force" | "off">(
    optionsState?.ocrMode ?? "auto"
  );
  const [language, setLanguage] = useState(optionsState?.language ?? "en");
  const [includeHeaders, setIncludeHeaders] = useState(
    optionsState?.includeHeaders ?? true
  );
  const [parseHtml, setParseHtml] = useState(
    optionsState?.parseHtml ?? true
  );
  const [includeAttachments, setIncludeAttachments] = useState(
    optionsState?.includeAttachments ?? true
  );
  const [includeInlineImages, setIncludeInlineImages] = useState(
    optionsState?.includeInlineImages ?? true
  );
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [entityError, setEntityError] = useState<string | null>(null);

  const syncOptions = (next: Partial<ScanOptionsState>) => {
    if (!onOptionsChange) return;
    onOptionsChange({
      entityTypes,
      selectedEntities,
      threshold,
      ocrMode,
      language,
      includeHeaders,
      parseHtml,
      includeAttachments,
      includeInlineImages,
      ...next,
    });
  };

  useEffect(() => {
    if (!optionsState) return;
    setEntityTypes(optionsState.entityTypes);
    setSelectedEntities(optionsState.selectedEntities);
    setThreshold(optionsState.threshold);
    setOcrMode(optionsState.ocrMode);
    setLanguage(optionsState.language);
    setIncludeHeaders(optionsState.includeHeaders);
    setParseHtml(optionsState.parseHtml);
    setIncludeAttachments(optionsState.includeAttachments);
    setIncludeInlineImages(optionsState.includeInlineImages);
  }, [optionsState]);

  const loadEntities = async (force = false) => {
    setEntityError(null);
    try {
      if (force) {
        clearEntityTypesCache();
      }
      const data = await fetchEntityTypes({ force });
      const next = data.length ? data : FALLBACK_ENTITIES;
      setEntityTypes(next);
      const selection = next.slice(0, 6);
      setSelectedEntities(selection);
      syncOptions({ entityTypes: next, selectedEntities: selection });
    } catch (err) {
      setEntityError(
        err instanceof Error ? err.message : "Failed to load entity types."
      );
      setEntityTypes(FALLBACK_ENTITIES);
      setSelectedEntities(FALLBACK_ENTITIES);
      syncOptions({
        entityTypes: FALLBACK_ENTITIES,
        selectedEntities: FALLBACK_ENTITIES,
      });
    }
  };

  useEffect(() => {
    if (!embedded) {
      void loadEntities();
    }
  }, [embedded]);

  useEffect(() => {
    if (embedded) {
      syncOptions({});
    }
  }, [
    embedded,
    entityTypes,
    selectedEntities,
    threshold,
    ocrMode,
    language,
    includeHeaders,
    parseHtml,
    includeAttachments,
    includeInlineImages,
  ]);

  const options = {
    entityTypes: selectedEntities,
    threshold,
    language,
    ocrMode,
    includeHeaders,
    parseHtml,
    includeAttachments,
    includeInlineImages,
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
      {!embedded && (
        <div className="header">
          <div>
            <h1>Scan Files</h1>
            <p>
              Upload files, directories, archives, or emails for OCR + Presidio
              analysis.
            </p>
          </div>
        </div>
      )}

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

          {!embedded && (
            <aside className="options">
              <div className="option-group">
                <label>Entity types</label>
                {entityError && (
                  <div className="error">
                    Failed to load entity types. {entityError}
                    <button
                      className="button link-button"
                      onClick={() => loadEntities(true)}
                      type="button"
                    >
                      Retry
                    </button>
                  </div>
                )}
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
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={includeAttachments}
                    onChange={() => setIncludeAttachments((prev) => !prev)}
                  />
                  Include attachments
                </label>
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={includeInlineImages}
                    onChange={() => setIncludeInlineImages((prev) => !prev)}
                  />
                  Include inline images
                </label>
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
