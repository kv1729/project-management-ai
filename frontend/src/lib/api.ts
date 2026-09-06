import type { BoardData } from "@/lib/kanban";

export type BoardResponse = {
  name: string;
  board: BoardData;
  version: number;
  updated_at: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIResponse = {
  assistant_response: string;
  board_updated: boolean;
  board: BoardData;
  version: number;
  updated_at: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
};

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the status message when the response is not JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
};

export const login = (username: string, password: string) =>
  request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const getBoard = (token: string) =>
  request<BoardResponse>("/api/board", {
    headers: { Authorization: `Bearer ${token}` },
  });

export const saveBoard = (token: string, board: BoardData, version: number) =>
  request<BoardResponse>("/api/board", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ board, version }),
  });

export const askBoardAI = (
  token: string,
  question: string,
  history: ChatMessage[]
) =>
  request<AIResponse>("/api/ai/board", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ question, history }),
  });
