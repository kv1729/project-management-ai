"use client";

import { useState } from "react";
import { askBoardAI, type ChatMessage } from "@/lib/api";

type ChatSidebarProps = {
  token: string;
  onBoardUpdate?: (response: Awaited<ReturnType<typeof askBoardAI>>) => void;
};

export const ChatSidebar = ({ token, onBoardUpdate }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [isPending, setIsPending] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isPending) return;

    const userMessage: ChatMessage = { role: "user", content: trimmedQuestion };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setQuestion("");
    setError("");
    setIsPending(true);

    try {
      const response = await askBoardAI(token, trimmedQuestion, messages);
      setMessages([...nextMessages, { role: "assistant", content: response.assistant_response }]);
      onBoardUpdate?.(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The assistant could not respond."
      );
    } finally {
      setIsPending(false);
    }
  };

  return (
    <aside className="flex min-h-[520px] flex-col rounded-[28px] border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
      <div className="border-b border-[var(--stroke)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--primary-blue)]">
          Board assistant
        </p>
        <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
          Ask about your work
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Ask for a summary or request a board change.
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto py-5" aria-live="polite">
        {messages.length === 0 ? (
          <p className="rounded-2xl bg-[var(--surface)] p-4 text-sm leading-6 text-[var(--gray-text)]">
            What should we focus on next?
          </p>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={
                message.role === "user"
                  ? "ml-6 rounded-2xl rounded-br-sm bg-[var(--navy-dark)] p-3 text-sm leading-6 text-white"
                  : "mr-6 rounded-2xl rounded-bl-sm bg-[var(--surface)] p-3 text-sm leading-6 text-[var(--navy-dark)]"
              }
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.2em] opacity-60">
                {message.role === "user" ? "You" : "Assistant"}
              </p>
              <p>{message.content}</p>
            </div>
          ))
        )}
        {isPending ? (
          <p className="text-sm font-semibold text-[var(--primary-blue)]" role="status">
            Thinking...
          </p>
        ) : null}
      </div>

      {error ? <p className="mb-3 text-sm font-semibold text-[var(--secondary-purple)]" role="alert">{error}</p> : null}
      <form className="space-y-3" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="assistant-question">Ask the board assistant</label>
        <textarea
          id="assistant-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question..."
          rows={3}
          disabled={isPending}
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none transition placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={isPending || !question.trim()}
          className="w-full rounded-2xl bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isPending ? "Sending..." : "Send question"}
        </button>
      </form>
    </aside>
  );
};