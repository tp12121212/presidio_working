export async function fetchEntityTypes(): Promise<string[]> {
  const res = await fetch("/api/presidio/entities");
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}
