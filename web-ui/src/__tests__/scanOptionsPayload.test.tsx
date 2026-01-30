import { describe, it, expect, vi } from "vitest";
import { scanEmail } from "../api/scan";

describe("scan options payload", () => {
  it("includes email options in multipart payload", async () => {
    const fetchMock = vi.fn(async () =>
      Promise.resolve({ ok: true, json: async () => ({ scan_id: "1" }) })
    );
    // @ts-expect-error mock fetch
    global.fetch = fetchMock;

    const file = new File(["hi"], "mail.eml", { type: "message/rfc822" });
    await scanEmail(file, {
      includeHeaders: true,
      parseHtml: false,
      includeAttachments: false,
      includeInlineImages: false,
    });

    const body = fetchMock.mock.calls[0][1].body as FormData;
    expect(body.get("include_headers")).toBe("true");
    expect(body.get("parse_html")).toBe("false");
    expect(body.get("include_attachments")).toBe("false");
    expect(body.get("include_inline_images")).toBe("false");
  });
});
