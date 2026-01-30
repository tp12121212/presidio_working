export interface AnalyzerResult {
  entity_type: string;
  start: number;
  end: number;
  score: number;
}

export interface AnalyzeOptions {
  entities?: string[];
  language?: string;
  scoreThreshold?: number;
}

export interface RedactOptions {
  mode: "replace" | "mask" | "entity_tag";
  maskChar?: string;
}

const ANALYZER_BASE =
  import.meta.env.VITE_ANALYZER_BASE_URL || "/api/analyzer";
const ANONYMIZER_BASE =
  import.meta.env.VITE_ANONYMIZER_BASE_URL || "/api/anonymizer";

async function handleJson(res: Response) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function analyzeText(
  text: string,
  options: AnalyzeOptions
): Promise<AnalyzerResult[]> {
  const payload = {
    text,
    language: options.language || "en",
    entities: options.entities && options.entities.length ? options.entities : undefined,
    score_threshold: options.scoreThreshold,
  };

  const res = await fetch(`${ANALYZER_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}

export async function fetchSupportedEntities(language = "en"): Promise<string[]> {
  const res = await fetch(`${ANALYZER_BASE}/supportedentities?language=${language}`);
  return handleJson(res);
}

export async function redactText(
  text: string,
  results: AnalyzerResult[],
  options: RedactOptions
): Promise<string> {
  const analyzer_results = results.map((item) => ({
    entity_type: item.entity_type,
    start: item.start,
    end: item.end,
    score: item.score,
  }));

  let anonymizers: Record<string, { type: string; [key: string]: unknown }> = {
    DEFAULT: { type: "replace", new_value: "[REDACTED]" },
  };

  if (options.mode === "mask") {
    anonymizers = {
      DEFAULT: {
        type: "mask",
        masking_char: options.maskChar || "*",
        chars_to_mask: 100,
        from_end: false,
      },
    };
  }

  if (options.mode === "entity_tag") {
    anonymizers = {};
    results.forEach((item) => {
      anonymizers[item.entity_type] = {
        type: "replace",
        new_value: `<${item.entity_type}>`,
      };
    });
    if (!Object.keys(anonymizers).length) {
      anonymizers = {
        DEFAULT: { type: "replace", new_value: "[REDACTED]" },
      };
    }
  }

  const res = await fetch(`${ANONYMIZER_BASE}/anonymize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, analyzer_results, anonymizers }),
  });
  const data = await handleJson(res);
  return data.text || data.result || data;
}
