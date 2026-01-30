import { render, screen, waitFor } from "@testing-library/react";
import SitLibrary from "../pages/SitLibrary";

const mockFetch = (data: unknown) =>
  Promise.resolve({ ok: true, json: async () => data } as Response);

describe("SitLibrary", () => {
  beforeEach(() => {
    // @ts-expect-error mock fetch
    global.fetch = (url: string) => {
      if (url.endsWith("/sits")) {
        return mockFetch([
          {
            id: "sit-1",
            name: "Passport Number",
            description: "Passport identifiers",
            created_at: new Date().toISOString(),
          },
        ]);
      }
      if (url.includes("/sits/sit-1")) {
        return mockFetch({
          id: "sit-1",
          name: "Passport Number",
          description: "Passport identifiers",
          created_at: new Date().toISOString(),
          versions: [],
        });
      }
      return mockFetch([]);
    };
  });

  it("renders SITs list", async () => {
    render(<SitLibrary />);
    await waitFor(() => {
      expect(screen.getByText("Passport Number")).toBeInTheDocument();
    });
  });
});
