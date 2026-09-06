import { askBoardAI, getBoard, login, saveBoard } from "@/lib/api";
import { initialData } from "@/lib/kanban";

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("logs in and sends board authorization", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "token", token_type: "bearer" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ name: "Kanban Studio", board: initialData, version: 1, updated_at: "now" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(login("user", "password")).resolves.toEqual({ access_token: "token", token_type: "bearer" });
    await getBoard("token");
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      headers: { "Content-Type": "application/json", Authorization: "Bearer token" },
    });
  });

  it("serializes versioned board saves", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ name: "Kanban Studio", board: initialData, version: 2, updated_at: "now" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await saveBoard("token", initialData, 1);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ board: initialData, version: 1 });
  });

  it("surfaces API error details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Board version is stale." }), { status: 409 })));

    await expect(saveBoard("token", initialData, 1)).rejects.toThrow("Board version is stale.");
  });

  it("sends chat questions and conversation history", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({
        assistant_response: "All clear.",
        board_updated: false,
        board: initialData,
        version: 1,
        updated_at: "now",
      }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await askBoardAI("token", "Summarize the board", [
      { role: "user", content: "Hello" },
    ]);

    expect(fetchMock.mock.calls[0][0]).toBe("/api/ai/board");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({
      question: "Summarize the board",
      history: [{ role: "user", content: "Hello" }],
    });
  });
});