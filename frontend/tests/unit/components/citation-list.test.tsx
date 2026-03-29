import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { CitationList } from "@/components/chat/citation-list";
import type { ChatCitation } from "@/types/public-chat";

const base: ChatCitation = {
  chunk_id: 1,
  source_id: 10,
  title: "Policy",
  url: "https://example.edu/p",
  source_type: "html_page",
  page_number: null,
  score: 0.9,
};

describe("CitationList", () => {
  it("renders an external link for safe https URLs", () => {
    render(<CitationList citations={[base]} primaryColor="#336699" />);
    const link = screen.getByRole("link", { name: /example\.edu\/p/ });
    expect(link).toHaveAttribute("href", "https://example.edu/p");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("shows page number for PDF citations", () => {
    const pdf: ChatCitation = {
      ...base,
      source_type: "pdf",
      page_number: 4,
      url: "https://example.edu/a.pdf",
    };
    render(<CitationList citations={[pdf]} primaryColor="#336699" />);
    expect(screen.getByText(/p\.4/)).toBeInTheDocument();
  });

  it("does not render a clickable link for unsafe URLs", () => {
    const bad: ChatCitation = {
      ...base,
      url: "javascript:alert(1)",
    };
    render(<CitationList citations={[bad]} primaryColor="#336699" />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText(/javascript:/)).toBeInTheDocument();
  });
});
