from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonEmptyId = Annotated[str, Field(min_length=1)]


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyId
    title: str
    details: str


class Column(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: NonEmptyId
    title: str
    cardIds: list[NonEmptyId]


class BoardData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[Column] = Field(min_length=1)
    cards: dict[NonEmptyId, Card]

    @field_validator("columns")
    @classmethod
    def unique_column_ids(cls, columns: list[Column]) -> list[Column]:
        ids = [column.id for column in columns]
        if len(ids) != len(set(ids)):
            raise ValueError("column IDs must be unique")
        return columns

    @model_validator(mode="after")
    def validate_card_references(self) -> "BoardData":
        listed_ids = [card_id for column in self.columns for card_id in column.cardIds]
        if len(listed_ids) != len(set(listed_ids)):
            raise ValueError("each card must appear in exactly one column")
        if set(listed_ids) != set(self.cards):
            raise ValueError("columns and cards must contain the same card IDs")
        for card_id, card in self.cards.items():
            if card.id != card_id:
                raise ValueError("card ID must match its map key")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BoardResponse(BaseModel):
    name: str
    board: BoardData
    version: int = Field(gt=0)
    updated_at: str


class BoardUpdateRequest(BaseModel):
    board: BoardData
    version: int = Field(gt=0)


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=20)


class AIOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_response: str = Field(min_length=1, max_length=4000)
    board_update: BoardData | None = None


class AIResponse(BaseModel):
    assistant_response: str
    board_updated: bool
    board: BoardData
    version: int = Field(gt=0)
    updated_at: str
