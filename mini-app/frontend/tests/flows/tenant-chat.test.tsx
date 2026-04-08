import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  fetchPublicTenant: vi.fn(),
  postPublicChatQuery: vi.fn(),
}));

vi.mock("@/lib/public-chat-api", () => ({
  fetchPublicTenant: mocks.fetchPublicTenant,
  postPublicChatQuery: mocks.postPublicChatQuery,
}));

import { TenantChatPage } from "@/components/chat/tenant-chat-page";

describe("TenantChatPage", () => {
  beforeEach(() => {
    mocks.fetchPublicTenant.mockResolvedValue({
      id: 1,
      name: "Test University",
      slug: "test-u",
      branding: {
        logo_url: null,
        primary_color: "#0044aa",
        app_title: null,
      },
    });
    mocks.postPublicChatQuery.mockResolvedValue({
      answer: "Indexed answer.",
      citations: [],
      support: "high",
      session_id: 42,
      retrieval: {},
    });
  });

  it("sends a message and displays the assistant reply", async () => {
    const user = userEvent.setup();
    render(<TenantChatPage slug="test-u" />);

    await waitFor(() => {
      expect(screen.queryByText(/Loading assistant/)).not.toBeInTheDocument();
    });

    await user.type(
      screen.getByPlaceholderText(/Type your question/),
      "When is tuition due?",
    );
    await user.click(screen.getByRole("button", { name: /Send message/ }));

    await waitFor(() => {
      expect(screen.getByText("Indexed answer.")).toBeInTheDocument();
    });

    expect(mocks.postPublicChatQuery).toHaveBeenCalledWith(
      "test-u",
      expect.objectContaining({
        message: "When is tuition due?",
        answer_mode: "concise",
      }),
    );
  });
});
