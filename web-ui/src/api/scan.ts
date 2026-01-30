export interface ScanEntity {
  entity_type: string;
  start: number;
  end: number;
  text?: string;
  score?: number;
}

export interface RegexCandidate {
  id: string;
  label: string;
  start: number;
  end: number;
  text?: string;
  entity_type: string;
  score?: number;
  regex?: string;
}

export interface KeywordCandidate {
  keyword: string;
  count: number;
  entity_types: string[];
}

export interface ScanFileResult {
  file_id: string;
  virtual_path: string;
  mime_type?: string;
  text_preview?: string;
  extraction: {
    method: string;
    ocr_used: boolean;
    warnings: string[];
    text_chars: number;
  };
  entities: ScanEntity[];
  regex_candidates: RegexCandidate[];
  keyword_candidates: KeywordCandidate[];
}

export interface ScanResult {
  scan_id: string;
  status: string;
  error?: string | null;
  files: ScanFileResult[];
}

export interface ScanOptions {
  entityTypes?: string[];
  threshold?: number;
  language?: string;
  ocrMode?: "auto" | "force" | "off";
  includeHeaders?: boolean;
  parseHtml?: boolean;
}

const SCAN_BASE = import.meta.env.VITE_SCAN_BASE_URL || "/api/scan";

async function handleJson(res: Response) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

function appendOptions(form: FormData, options?: ScanOptions) {
  if (!options) return;
  if (options.entityTypes?.length) {
    form.append("entity_types", options.entityTypes.join(","));
  }
  if (options.threshold !== undefined) {
    form.append("threshold", String(options.threshold));
  }
  if (options.language) {
    form.append("language", options.language);
  }
  if (options.ocrMode) {
    form.append("ocr_mode", options.ocrMode);
  }
  if (options.includeHeaders !== undefined) {
    form.append("include_headers", String(options.includeHeaders));
  }
  if (options.parseHtml !== undefined) {
    form.append("parse_html", String(options.parseHtml));
  }
}

export async function scanFile(file: File, options?: ScanOptions): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  appendOptions(form, options);
  const res = await fetch(`${SCAN_BASE}/file`, { method: "POST", body: form });
  const data = await handleJson(res);
  return data.scan_id;
}

export async function scanArchive(
  file: File,
  options?: ScanOptions
): Promise<string> {
  const form = new FormData();
  form.append("archive_file", file);
  appendOptions(form, options);
  const res = await fetch(`${SCAN_BASE}/archive`, { method: "POST", body: form });
  const data = await handleJson(res);
  return data.scan_id;
}

export async function scanEmail(
  file: File,
  options?: ScanOptions
): Promise<string> {
  const form = new FormData();
  form.append("email_file", file);
  appendOptions(form, options);
  const res = await fetch(`${SCAN_BASE}/email`, { method: "POST", body: form });
  const data = await handleJson(res);
  return data.scan_id;
}

export async function scanBatch(
  files: File[],
  paths: string[],
  options?: ScanOptions
): Promise<string> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  paths.forEach((path) => form.append("paths", path));
  appendOptions(form, options);
  const res = await fetch(`${SCAN_BASE}/batch`, { method: "POST", body: form });
  const data = await handleJson(res);
  return data.scan_id;
}

export async function getScan(scanId: string): Promise<ScanResult> {
  const res = await fetch(`${SCAN_BASE}/${scanId}`);
  return handleJson(res);
}
