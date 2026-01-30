let cachedEntities: string[] | null = null;
let inflight: Promise<string[]> | null = null;

export async function fetchEntityTypes(
  options: { force?: boolean } = {}
): Promise<string[]> {
  if (!options.force && cachedEntities) {
    return cachedEntities;
  }
  if (!options.force && inflight) {
    return inflight;
  }

  inflight = (async () => {
    const res = await fetch("/api/presidio/entities");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Request failed (${res.status})`);
    }
    const data = (await res.json()) as string[];
    cachedEntities = data;
    return data;
  })();

  try {
    return await inflight;
  } finally {
    inflight = null;
  }
}

export function clearEntityTypesCache() {
  cachedEntities = null;
}
