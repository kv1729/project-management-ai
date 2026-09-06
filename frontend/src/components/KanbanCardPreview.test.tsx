import { render, screen } from "@testing-library/react";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";

const card = {
  id: "card-preview",
  title: "Preview card",
  details: "Shown while dragging.",
};

describe("KanbanCardPreview", () => {
  it("renders the card title and details", () => {
    render(<KanbanCardPreview card={card} />);

    expect(screen.getByRole("heading", { name: "Preview card" })).toBeInTheDocument();
    expect(screen.getByText("Shown while dragging.")).toBeInTheDocument();
  });
});
