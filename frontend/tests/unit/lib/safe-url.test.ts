import { describe, it, expect } from "vitest";

import { isSafeHttpUrl } from "@/lib/safe-url";

describe("isSafeHttpUrl", () => {
  it("accepts http and https", () => {
    expect(isSafeHttpUrl("https://example.edu/path")).toBe(true);
    expect(isSafeHttpUrl("http://localhost:3000/a")).toBe(true);
  });

  it("rejects javascript and other schemes", () => {
    expect(isSafeHttpUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeHttpUrl("data:text/html,<html>")).toBe(false);
  });

  it("rejects empty or invalid", () => {
    expect(isSafeHttpUrl("")).toBe(false);
    expect(isSafeHttpUrl(null)).toBe(false);
    expect(isSafeHttpUrl("not a url")).toBe(false);
  });
});
