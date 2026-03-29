import type { ReactNode } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/lib/api", () => ({
  getStoredToken: vi.fn(() => null),
  setStoredToken: vi.fn(),
  AUTH_TOKEN_KEY: "chaty_admin_token",
}));

const mocks = vi.hoisted(() => ({
  postLogin: vi.fn(),
  getMe: vi.fn(),
}));

vi.mock("@/lib/admin-api", () => ({
  postLogin: mocks.postLogin,
  getMe: mocks.getMe,
}));

vi.mock("next/link", () => ({
  default ({
    children,
    href,
  }: {
    children: ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  },
}));

import AdminLoginPage from "@/app/admin/login/page";

describe("AdminLoginPage", () => {
  beforeEach(() => {
    replace.mockClear();
    mocks.postLogin.mockResolvedValue({
      access_token: "jwt",
      token_type: "bearer",
      expires_in: 3600,
    });
    mocks.getMe.mockResolvedValue({
      id: 1,
      email: "a@b.com",
      full_name: null,
      role: "super_admin",
      tenant_id: null,
      is_active: true,
    });
  });

  it("submits credentials and redirects super_admin to /admin", async () => {
    const user = userEvent.setup();
    render(<AdminLoginPage />);

    await user.type(screen.getByLabelText(/Email/i), "a@b.com");
    await user.type(screen.getByLabelText(/Password/i), "secret-pass");
    await user.click(screen.getByRole("button", { name: /Sign in/i }));

    await waitFor(() => {
      expect(mocks.postLogin).toHaveBeenCalledWith("a@b.com", "secret-pass");
    });
    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/admin");
    });
  });
});
