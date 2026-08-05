import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, it, expect, vi } from "vitest";

const deleteAccount = vi.fn();
const logout = vi.fn();

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", email: "test@example.com", display_name: "Test User" },
    logout,
  }),
}));

vi.mock("@/lib/api/auth", () => ({
  authApi: {
    updateProfile: vi.fn(),
    deleteAccount: () => {
      deleteAccount();
      return Promise.resolve();
    },
  },
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: ({ mutationFn, onSuccess }) => ({
    isPending: false,
    isError: false,
    error: null,
    mutate: () => {
      const result = mutationFn();
      if (result?.then) result.then(onSuccess);
    },
  }),
}));

import { SettingsPage } from "@/features/settings/components/SettingsPage";

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders danger zone with delete button", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Delete Account")).toBeInTheDocument();
  });

  it("requires confirmation before deleting", () => {
    render(<SettingsPage />);
    fireEvent.click(screen.getByText("Delete Account"));
    expect(screen.getByText("Yes, delete my account")).toBeInTheDocument();
    expect(deleteAccount).not.toHaveBeenCalled();
  });

  it("deletes account and logs out on confirm", async () => {
    render(<SettingsPage />);
    fireEvent.click(screen.getByText("Delete Account"));
    fireEvent.click(screen.getByText("Yes, delete my account"));
    await waitFor(() => expect(deleteAccount).toHaveBeenCalled());
    await waitFor(() => expect(logout).toHaveBeenCalled());
  });

  it("cancels deletion without calling API", () => {
    render(<SettingsPage />);
    fireEvent.click(screen.getByText("Delete Account"));
    fireEvent.click(screen.getByText("Cancel"));
    expect(deleteAccount).not.toHaveBeenCalled();
    expect(screen.getByText("Delete Account")).toBeInTheDocument();
  });
});
