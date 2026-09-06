import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import { initialData } from "@/lib/kanban";

const response = {
  assistant_response: "I found one priority item.",
  board_updated: false,
  board: initialData,
  version: 1,
  updated_at: "now",
};

describe("ChatSidebar", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders an empty state and disables blank submissions", () => {
    render(<ChatSidebar token="token" />);

    expect(screen.getByText("What should we focus on next?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send question" })).toBeDisabled();
  });

  it("submits a question, shows the response, and reports board updates", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ...response, board_updated: true, version: 2 }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);
    const onBoardUpdate = vi.fn();
    render(<ChatSidebar token="token" onBoardUpdate={onBoardUpdate} />);

    await user.type(screen.getByLabelText("Ask the board assistant"), "What is next?");
    await user.click(screen.getByRole("button", { name: "Send question" }));

    expect(await screen.findByText("I found one priority item.")).toBeInTheDocument();
    expect(screen.getByText("What is next?")).toBeInTheDocument();
    expect(onBoardUpdate).toHaveBeenCalledWith({ ...response, board_updated: true, version: 2 });
  });

  it("prevents duplicate submissions while waiting and shows errors", async () => {
    const user = userEvent.setup();
    let resolveRequest: (value: Response) => void = () => {};
    const fetchMock = vi.fn().mockReturnValue(
      new Promise<Response>((resolve) => {
        resolveRequest = resolve;
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<ChatSidebar token="token" />);

    await user.type(screen.getByLabelText("Ask the board assistant"), "First question");
    await user.click(screen.getByRole("button", { name: "Send question" }));
    expect(screen.getByRole("status")).toHaveTextContent("Thinking...");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();

    resolveRequest(new Response(JSON.stringify({ detail: "Assistant unavailable." }), { status: 502 }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Assistant unavailable.");
  });
});