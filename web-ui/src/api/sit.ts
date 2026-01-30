export interface SitSummary {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
}

export interface SitVersion {
  id: string;
  version_number: number;
  entity_type?: string | null;
  confidence?: string | null;
  source?: string | null;
  created_at: string;
  primary_element?: { element_type: string; value: string } | null;
  supporting_logic?: { mode: string; min_n?: number | null } | null;
  supporting_groups: {
    name: string;
    items: { item_type: string; value?: string | null; keyword_list_id?: string | null }[];
  }[];
}

export interface SitDetail extends SitSummary {
  versions: SitVersion[];
}

export interface Rulepack {
  id: string;
  name: string;
  version: string;
  description?: string | null;
  publisher?: string | null;
  locale?: string | null;
  created_at: string;
  selections: string[];
}

const SIT_BASE = import.meta.env.VITE_SIT_BASE_URL || "/api/sit";

async function handleJson(res: Response) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function listSits(): Promise<SitSummary[]> {
  const res = await fetch(`${SIT_BASE}/sits`);
  return handleJson(res);
}

export async function getSit(id: string): Promise<SitDetail> {
  const res = await fetch(`${SIT_BASE}/sits/${id}`);
  return handleJson(res);
}

export async function listRulepacks(): Promise<Rulepack[]> {
  const res = await fetch(`${SIT_BASE}/rulepacks`);
  return handleJson(res);
}

export async function createKeywordList(payload: {
  name: string;
  description?: string;
  items: string[];
}): Promise<{ id: string }> {
  const res = await fetch(`${SIT_BASE}/keyword-lists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}

export async function createSit(payload: {
  name: string;
  description?: string;
  version: {
    entity_type?: string;
    confidence?: string;
    source?: string;
    primary_element: { type: string; value: string };
    supporting_logic: { mode: string; min_n?: number; max_n?: number };
    supporting_groups: {
      name: string;
      items: { type: string; value?: string; keyword_list_id?: string }[];
    }[];
  };
}): Promise<SitDetail> {
  const res = await fetch(`${SIT_BASE}/sits/from-scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}

export async function createRulepack(payload: {
  name: string;
  version: string;
  description?: string;
  publisher?: string;
  locale?: string;
}): Promise<Rulepack> {
  const res = await fetch(`${SIT_BASE}/rulepacks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}

export async function setRulepackSelections(
  rulepackId: string,
  versionIds: string[]
): Promise<void> {
  const res = await fetch(`${SIT_BASE}/rulepacks/${rulepackId}/selections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version_ids: versionIds }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
}

export async function exportRulepack(rulepackId: string): Promise<Blob> {
  const res = await fetch(`${SIT_BASE}/rulepacks/${rulepackId}/export`, {
    method: "POST",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.blob();
}
