export function groupKeywords(
  keywords: string[],
  mode: "single" | "split"
): string[][] {
  if (keywords.length === 0) return [];
  if (mode === "single") {
    return [keywords];
  }
  return keywords.map((keyword) => [keyword]);
}
