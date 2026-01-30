import type { AnalyzerResult } from "../api/presidio";

export interface HighlightSpan {
  start: number;
  end: number;
  entity_type: string;
  score: number;
}

export function buildNonOverlappingSpans(results: AnalyzerResult[]): HighlightSpan[] {
  const sorted = [...results].sort((a, b) =>
    a.start === b.start ? b.end - a.end : a.start - b.start
  );
  const spans: HighlightSpan[] = [];
  let lastEnd = -1;
  for (const item of sorted) {
    if (item.start >= lastEnd) {
      spans.push({
        start: item.start,
        end: item.end,
        entity_type: item.entity_type,
        score: item.score,
      });
      lastEnd = item.end;
    }
  }
  return spans;
}

export function sliceWithHighlights(text: string, spans: HighlightSpan[]) {
  const chunks: { text: string; span?: HighlightSpan }[] = [];
  let cursor = 0;
  spans.forEach((span) => {
    if (span.start > cursor) {
      chunks.push({ text: text.slice(cursor, span.start) });
    }
    chunks.push({ text: text.slice(span.start, span.end), span });
    cursor = span.end;
  });
  if (cursor < text.length) {
    chunks.push({ text: text.slice(cursor) });
  }
  return chunks;
}

export const entityColorMap = (entity: string) => {
  const palette = [
    "#fee2e2",
    "#dbeafe",
    "#dcfce7",
    "#fef9c3",
    "#ede9fe",
    "#ffe4e6",
    "#d1fae5",
    "#e0f2fe",
  ];
  let hash = 0;
  for (let i = 0; i < entity.length; i += 1) {
    hash = entity.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % palette.length;
  return palette[index];
};
