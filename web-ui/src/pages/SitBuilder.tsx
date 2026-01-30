import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getScan, type ScanFileResult } from "../api/scan";
import { createKeywordList, createSit } from "../api/sit";
import { groupKeywords } from "../utils/sitBuilder";

type Step = 1 | 2 | 3 | 4;

export default function SitBuilder() {
  const [params] = useSearchParams();
  const [scanId, setScanId] = useState(params.get("scanId") || "");
  const [files, setFiles] = useState<ScanFileResult[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [primaryId, setPrimaryId] = useState<string>("");
  const [supportingRegex, setSupportingRegex] = useState<string[]>([]);
  const [supportingKeywords, setSupportingKeywords] = useState<string[]>([]);
  const [keywordGrouping, setKeywordGrouping] = useState<"single" | "split">("single");
  const [mode, setMode] = useState<"ANY" | "ALL" | "MIN_N">("ANY");
  const [minN, setMinN] = useState(1);
  const [maxN, setMaxN] = useState<number | undefined>(undefined);
  const [sitName, setSitName] = useState("New SIT");
  const [sitDescription, setSitDescription] = useState("");
  const [entityType, setEntityType] = useState("");
  const [step, setStep] = useState<Step>(1);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!scanId) return;
    getScan(scanId)
      .then((data) => {
        setFiles(data.files);
        setSelectedFiles(data.files.map((file) => file.file_id));
      })
      .catch((err) => setMessage(err instanceof Error ? err.message : String(err)));
  }, [scanId]);

  const selectedFileItems = useMemo(
    () => files.filter((file) => selectedFiles.includes(file.file_id)),
    [files, selectedFiles]
  );

  const regexCandidates = useMemo(() => {
    const map = new Map<string, { id: string; regex: string; entity_type: string }>();
    selectedFileItems.forEach((file) => {
      file.regex_candidates.forEach((candidate) => {
        if (candidate.regex) {
          map.set(candidate.id, {
            id: candidate.id,
            regex: candidate.regex,
            entity_type: candidate.entity_type,
          });
        }
      });
    });
    return Array.from(map.values());
  }, [selectedFileItems]);

  const keywordCandidates = useMemo(() => {
    const map = new Map<string, number>();
    selectedFileItems.forEach((file) => {
      file.keyword_candidates.forEach((candidate) => {
        map.set(candidate.keyword, (map.get(candidate.keyword) || 0) + candidate.count);
      });
    });
    return Array.from(map.entries()).map(([keyword, count]) => ({ keyword, count }));
  }, [selectedFileItems]);

  const primaryCandidate = regexCandidates.find((item) => item.id === primaryId);

  const toggleFile = (fileId: string) => {
    setSelectedFiles((prev) =>
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    );
  };

  const toggleSupportRegex = (id: string) => {
    setSupportingRegex((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleSupportKeyword = (keyword: string) => {
    setSupportingKeywords((prev) =>
      prev.includes(keyword)
        ? prev.filter((item) => item !== keyword)
        : [...prev, keyword]
    );
  };

  const handleSave = async () => {
    if (!primaryCandidate && !supportingKeywords.length) {
      setMessage("Select a primary element before saving.");
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const keywordListIds: string[] = [];
      const grouped = groupKeywords(supportingKeywords, keywordGrouping);
      for (const listItems of grouped) {
        const list = await createKeywordList({
          name: `${sitName}-${listItems.join("-")}`,
          items: listItems,
        });
        keywordListIds.push(list.id);
      }

      const supportingItems = [
        ...supportingRegex.map((id) => {
          const regexItem = regexCandidates.find((item) => item.id === id);
          return regexItem
            ? { type: "regex", value: regexItem.regex }
            : null;
        }),
        ...keywordListIds.map((id) => ({ type: "keyword_list", keyword_list_id: id })),
      ].filter(Boolean) as { type: string; value?: string; keyword_list_id?: string }[];

      const sit = await createSit({
        name: sitName,
        description: sitDescription,
        version: {
          entity_type: entityType || primaryCandidate?.entity_type,
          source: scanId ? `scan:${scanId}` : undefined,
          primary_element: primaryCandidate
            ? { type: "regex", value: primaryCandidate.regex }
            : { type: "keyword", value: supportingKeywords[0] || "" },
          supporting_logic: {
            mode,
            min_n: mode === "MIN_N" ? minN : undefined,
            max_n: mode === "MIN_N" ? maxN : undefined,
          },
          supporting_groups: [
            {
              name: "context",
              items: supportingItems,
            },
          ],
        },
      });

      setMessage(`SIT saved: ${sit.name}`);
      setStep(4);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="header">
        <div>
          <h1>SIT Builder</h1>
          <p>Build SIT definitions from scan findings.</p>
        </div>
      </div>

      {message && <div className="notice">{message}</div>}

      <section className="panel">
        <div className="panel-inner page">
          {step === 1 && (
            <div className="page">
              <div className="option-group">
                <label>Scan ID</label>
                <input
                  className="input"
                  value={scanId}
                  onChange={(event) => setScanId(event.target.value)}
                />
                <button className="button ghost" onClick={() => setStep(1)}>
                  Load scan
                </button>
              </div>
              <div className="option-group">
                <label>Select files</label>
                {files.map((file) => (
                  <label key={file.file_id} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={selectedFiles.includes(file.file_id)}
                      onChange={() => toggleFile(file.file_id)}
                    />
                    {file.virtual_path}
                  </label>
                ))}
              </div>
              <button className="button" onClick={() => setStep(2)}>
                Next: Primary
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="page">
              <div className="option-group">
                <label>SIT name</label>
                <input className="input" value={sitName} onChange={(e) => setSitName(e.target.value)} />
              </div>
              <div className="option-group">
                <label>Description</label>
                <input className="input" value={sitDescription} onChange={(e) => setSitDescription(e.target.value)} />
              </div>
              <div className="option-group">
                <label>Entity type</label>
                <input className="input" value={entityType} onChange={(e) => setEntityType(e.target.value)} />
              </div>
              <div className="option-group">
                <label>Primary element (regex)</label>
                {regexCandidates.map((candidate) => (
                  <label key={candidate.id} className="checkbox-item">
                    <input
                      type="radio"
                      name="primary"
                      checked={primaryId === candidate.id}
                      onChange={() => setPrimaryId(candidate.id)}
                    />
                    {candidate.regex}
                  </label>
                ))}
              </div>
              <button className="button" onClick={() => setStep(3)}>
                Next: Supporting
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="page">
              <div className="option-group">
                <label>Supporting mode</label>
                <select className="select" value={mode} onChange={(e) => setMode(e.target.value as "ANY" | "ALL" | "MIN_N")}>
                  <option value="ANY">ANY / OR</option>
                  <option value="ALL">ALL / AND</option>
                  <option value="MIN_N">MIN_N</option>
                </select>
                {mode === "MIN_N" && (
                  <div className="page">
                    <input className="input" type="number" min={1} value={minN} onChange={(e) => setMinN(Number(e.target.value))} />
                    <input className="input" type="number" min={minN} placeholder="max (optional)" value={maxN ?? ""} onChange={(e) => setMaxN(e.target.value ? Number(e.target.value) : undefined)} />
                  </div>
                )}
              </div>
              <div className="option-group">
                <label>Supporting regex</label>
                {regexCandidates.map((candidate) => (
                  <label key={`support-${candidate.id}`} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={supportingRegex.includes(candidate.id)}
                      onChange={() => toggleSupportRegex(candidate.id)}
                    />
                    {candidate.regex}
                  </label>
                ))}
              </div>
              <div className="option-group">
                <label>Supporting keywords</label>
                {keywordCandidates.map((candidate) => (
                  <label key={candidate.keyword} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={supportingKeywords.includes(candidate.keyword)}
                      onChange={() => toggleSupportKeyword(candidate.keyword)}
                    />
                    {candidate.keyword} ({candidate.count})
                  </label>
                ))}
              </div>
              <div className="option-group">
                <label>Keyword grouping</label>
                <select
                  className="select"
                  value={keywordGrouping}
                  onChange={(e) => setKeywordGrouping(e.target.value as "single" | "split")}
                >
                  <option value="single">Single keyword list</option>
                  <option value="split">Split into multiple lists</option>
                </select>
              </div>
              <button className="button" onClick={handleSave} disabled={loading}>
                {loading ? "Saving..." : "Save SIT"}
              </button>
            </div>
          )}

          {step === 4 && (
            <div className="notice">
              SIT saved successfully. Visit the SIT Library to review and export.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
