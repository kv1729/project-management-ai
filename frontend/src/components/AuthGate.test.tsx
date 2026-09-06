import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";
import { initialData } from "@/lib/kanban";

const boardResponse = {
  name: "Kanban Studio",
  board: initialData,
  version: 1,
  updated_at: "2026-01-01T00:00:00Z",
};

describe("AuthGate", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/auth/login")) {
          return Promise.resolve(
            new Response(JSON.stringify({ access_token: "test-token", token_type: "bearer" }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            })
          );
        }
        if (url.endsWith("/api/board") && init?.method === "PUT") {
          return Promise.resolve(
            new Response(JSON.stringify(boardResponse), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            })
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify(boardResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          })
        );
      })
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it("requires sign-in and rejects invalid credentials", async () => {
    const user = userEvent.setup();
    render(<AuthGate />);

    await screen.findByRole("heading", { name: "Welcome back" });
    await user.type(screen.getByLabelText("Username"), "user");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("persists a valid session and logs out", async () => {
    const user = userEvent.setup();
    const firstRender = render(<AuthGate />);

    await screen.findByRole("heading", { name: "Welcome back" });
    await user.type(screen.getByLabelText("Username"), "user");
    await user.type(screen.getByLabelText("Password"), "password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    firstRender.unmount();
    render(<AuthGate />);
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Log out" }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument()
    );
    expect(window.localStorage.getItem("kanban-studio-authenticated")).toBeNull();
  });
});