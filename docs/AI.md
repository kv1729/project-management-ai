# AI Board Operations

Part 9 adds the authenticated `POST /api/ai/board` route. The request contains a question and up to 20 previous `user` or `assistant` messages:

```json
{
  "question": "Move the analytics card to In Progress",
  "history": []
}
```

The backend loads the board belonging to the bearer token and sends that canonical board JSON, the question, and the bounded history to OpenRouter. The browser cannot provide a board or user ID for the operation.

OpenRouter must return JSON with exactly these fields:

```json
{
  "assistant_response": "Moved the analytics card.",
  "board_update": null
}
```

`board_update` is either `null` or a complete valid board document. Partial boards, operation lists, unknown fields, malformed JSON, and invalid card or column references are rejected. A valid update is saved transactionally using the board version read before the provider request. If another write occurs first, the update is rejected with `409` and cannot overwrite newer work.

The response includes the assistant text, whether the board changed, and the canonical board version. Provider failures and invalid structured output return `502`; missing boards return `404`. Conversation history is request-scoped and is not persisted.