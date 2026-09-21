# Frontend Development Guide

## Purpose

This directory contains the Next.js frontend for the Project Management MVP. It is statically exported during the Docker build and served by the FastAPI backend.

## Current Stack

- Next.js 16 with the App Router
- React 19 and TypeScript with strict type checking
- Tailwind CSS 4, with project color variables in `src/app/globals.css`
- `@dnd-kit/core` and `@dnd-kit/sortable` for drag and drop
- Vitest, Testing Library, and jsdom for unit and component tests
- Playwright for browser integration tests

## Current Structure

- `src/app/layout.tsx`: root layout, metadata, and Google font setup
- `src/app/page.tsx`: renders the authenticated app at `/`
- `src/app/globals.css`: Tailwind import, design tokens, and global styles
- `src/components/AuthGate.tsx`: session state, backend login, board loading, serialized versioned saves, and logout
- `src/components/ChatSidebar.tsx`: authenticated AI chat messages, loading/error states, and board-update reconciliation callbacks
- `src/components/SignInForm.tsx`: credential form and sign-in validation
- `src/components/KanbanBoard.tsx`: board state, drag handlers, column renaming, card add/delete behavior, and save callbacks
- `src/components/KanbanColumn.tsx`: droppable column, sortable card list, rename input, and new-card form
- `src/components/KanbanCard.tsx`: sortable card with a delete action
- `src/components/KanbanCardPreview.tsx`: drag-overlay card presentation
- `src/components/NewCardForm.tsx`: controlled add-card form with validation and cancel behavior
- `src/lib/kanban.ts`: `Card`, `Column`, and `BoardData` types, demo data, ID generation, and card movement logic
- `src/lib/api.ts`: typed same-origin login, board load/save, and AI board requests
- `src/lib/auth.ts`: browser token/session storage helpers
- `src/**/*.test.{ts,tsx}`: Vitest unit and component tests, including mocked AI chat requests
- `tests/`: Playwright end-to-end tests

## Commands

Run these commands from `frontend/`:

- `npm run dev`: start the Next.js development server
- `npm run build`: create a production build
- `npm run start`: serve the production build
- `npm run lint`: run ESLint
- `npm run test:unit`: run Vitest tests once
- `npm run test:unit:watch`: run Vitest in watch mode
- `npm run test:e2e`: run Playwright browser tests
- `npm run test:all`: run unit tests followed by Playwright tests

The Vitest configuration enforces at least 80% for statements, branches, functions, and lines across production components and board logic.

## Testing Expectations

Test behavior at the closest useful boundary:

- Keep pure Kanban state and movement logic covered with focused unit tests, including invalid IDs, same-column moves, cross-column moves, and drops on columns.
- Test component workflows through accessible labels and roles: renaming columns, adding valid cards, rejecting blank titles, cancelling forms, and deleting cards.
- Keep Playwright tests for user-visible flows that cross the rendered application boundary, including loading the board and drag-and-drop behavior. They run in the installed Google Chrome by default (`BROWSER_CHANNEL` and `PLAYWRIGHT_EXECUTABLE_PATH` override this), so no Playwright browser download is required.
- Mock network and AI services in frontend tests once those integrations are introduced; do not make real OpenRouter calls from automated tests.
- Maintain a minimum of 80% statements, branches, functions, and lines coverage for the applicable frontend test run.

## Conventions

- Use the `@/*` import alias for `src/*` imports.
- Preserve strict TypeScript types and existing component prop contracts unless a phase explicitly changes them.
- Keep board updates immutable and put reusable board rules in `src/lib/kanban.ts` rather than duplicating them in components.
- Prefer accessible HTML controls and Testing Library queries by role, label, or visible text.
- Keep the existing color tokens and typography conventions unless a documented design change requires an update.
- Keep frontend work scoped to the current phase; do not add AI behavior before its planned phase is approved.

## Current Baseline

The app starts at `/` behind a sign-in gate using the MVP credentials `user` / `password`. The client stores the backend bearer token in browser `localStorage`, loads the user's board through the typed API client, and persists rename, add, delete, and drag-and-drop changes with versioned saves. It renders five fixed demo columns and an authenticated sidebar chat that uses mocked AI responses in automated tests.
