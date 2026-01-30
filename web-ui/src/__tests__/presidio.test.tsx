import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PresidioDemo from "../pages/PresidioDemo";

const mockFetch = (data: unknown) =>
  Promise.resolve({ ok: true, json: async () => data } as Response);

describe("PresidioDemo", () => {
  beforeEach(() => {
    // @ts-expect-error mock fetch
    global.fetch = (url: string) => {
      if (url.includes("supportedentities")) {
        return mockFetch(["PERSON", "EMAIL_ADDRESS"]);
      }
      if (url.includes("/analyze")) {
        return mockFetch([
          { entity_type: "PERSON", start: 0, end: 4, score: 0.9 },
        ]);
      }
      return mockFetch({});
    };
  });

  it("renders analyze flow and displays results", async () => {
    render(<PresidioDemo />);
    const analyzeButtons = screen.getAllByRole("button", { name: /analyze/i });
    fireEvent.click(analyzeButtons[1]);

    await waitFor(() => {
      expect(screen.getByTitle(/PERSON/)).toBeInTheDocument();
    });
  });
});
