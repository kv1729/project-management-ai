"use client";

import { startTransition, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { SignInForm } from "@/components/SignInForm";
import { clearSession, getAccessToken, hasStoredSession, storeAccessToken } from "@/lib/auth";
import { getBoard, login, saveBoard, type AIResponse, type BoardResponse } from "@/lib/api";

const BoardSession = ({ token, onLogout }: { token: string; onLogout: () => void }) => {
  const [boardResponse, setBoardResponse] = useState<BoardResponse | null>(null);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const versionRef = useRef(0);
  const saveQueueRef = useRef(Promise.resolve());

  useEffect(() => {
    let isCurrent = true;
    void getBoard(token)
      .then((response) => {
        if (!isCurrent) return;
        versionRef.current = response.version;
        startTransition(() => setBoardResponse(response));
      })
      .catch(() => {
        if (isCurrent) setLoadError("We could not load your board. Please sign in again.");
      });
    return () => {
      isCurrent = false;
    };
  }, [token]);

  if (loadError) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <section className="rounded-2xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">{loadError}</p>
          <button type="button" onClick={onLogout} className="mt-4 rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white">Return to sign in</button>
        </section>
      </main>
    );
  }

  if (!boardResponse) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-[var(--gray-text)]" aria-label="Loading board">Loading board...</main>;
  }

  const handleBoardChange = (board: BoardResponse["board"]) => {
    saveQueueRef.current = saveQueueRef.current
      .catch(() => undefined)
      .then(() => saveBoard(token, board, versionRef.current))
      .then((response) => {
        versionRef.current = response.version;
        setBoardResponse(response);
        setSaveError("");
      })
      .catch((error: unknown) => {
        setSaveError(error instanceof Error ? error.message : "We could not save that change.");
      });
  };

  const handleAIBoardUpdate = (response: AIResponse) => {
    versionRef.current = response.version;
    setBoardResponse((current) => current ? { ...current, board: response.board, version: response.version, updated_at: response.updated_at } : current);
    setSaveError("");
  };

  return (
    <KanbanBoard
      initialBoard={boardResponse.board}
      onBoardChange={handleBoardChange}
      saveError={saveError}
      onLogout={onLogout}
      chatToken={token}
      onAIBoardUpdate={handleAIBoardUpdate}
    />
  );
};

export const AuthGate = () => {
  const storedSession = useSyncExternalStore(
    () => () => {},
    () => hasStoredSession(window.localStorage),
    () => false
  );
  const [sessionOverride, setSessionOverride] = useState<boolean | null>(null);
  const [tokenOverride, setTokenOverride] = useState<string | null>(null);
  const [signInError, setSignInError] = useState("");
  const [isSigningIn, setIsSigningIn] = useState(false);
  const storedToken = useSyncExternalStore(
    () => () => {},
    () => getAccessToken(window.localStorage),
    () => null
  );
  const token = tokenOverride ?? storedToken;
  const isAuthenticated = sessionOverride ?? Boolean(storedSession && storedToken);

  if (!isAuthenticated) {
    return (
      <SignInForm
        error={signInError}
        isSubmitting={isSigningIn}
        onSignIn={async (username, password) => {
          setIsSigningIn(true);
          setSignInError("");
          try {
            const response = await login(username, password);
            storeAccessToken(window.localStorage, response.access_token);
            setTokenOverride(response.access_token);
            setSessionOverride(true);
          } catch {
            setSignInError("We could not sign you in with those credentials.");
          } finally {
            setIsSigningIn(false);
          }
        }}
      />
    );
  }

  if (!token) {
    clearSession(window.localStorage);
    return (
      <SignInForm
        error="Your session is no longer available. Please sign in again."
        onSignIn={async (username, password) => {
          const response = await login(username, password);
          storeAccessToken(window.localStorage, response.access_token);
          setTokenOverride(response.access_token);
          setSessionOverride(true);
        }}
      />
    );
  }

  return <BoardSession token={token} onLogout={() => { clearSession(window.localStorage); setTokenOverride(null); setSessionOverride(false); }} />;
};