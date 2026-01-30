import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ScanResults from "../pages/ScanResults";

const mockScan = {
  scan_id: "scan-1",
  status: "completed",
  files: [
    {
      file_id: "file-1",
      virtual_path: "archive.zip::doc.pdf",
      extraction: { method: "text", ocr_used: false, warnings: [], text_chars: 10 },
      entities: [],
      regex_candidates: [],
      keyword_candidates: [],
      text_preview: "Sample",
    },
    {
      file_id: "file-2",
      virtual_path: "archive.zip::inner.msg::body.txt",
      extraction: { method: "text", ocr_used: false, warnings: [], text_chars: 10 },
      entities: [],
      regex_candidates: [],
      keyword_candidates: [],
      text_preview: "Sample",
    },
  ],
};

describe("ScanResults", () => {
  beforeEach(() => {
    // @ts-expect-error mock fetch
    global.fetch = () =>
      Promise.resolve({ ok: true, json: async () => mockScan } as Response);
  });

  it("groups results by virtual path root", async () => {
    render(
      <MemoryRouter initialEntries={["/scan/results/scan-1"]}>
        <Routes>
          <Route path="/scan/results/:scanId" element={<ScanResults />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("archive.zip")).toBeInTheDocument();
    });
  });
});
