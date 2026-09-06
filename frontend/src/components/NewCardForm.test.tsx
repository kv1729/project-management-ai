import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NewCardForm } from "@/components/NewCardForm";

describe("NewCardForm", () => {
  it("does not submit a blank title", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /add a card/i }));
    await user.click(screen.getByRole("button", { name: /add card/i }));

    expect(onAdd).not.toHaveBeenCalled();
    expect(screen.getByPlaceholderText("Card title")).toBeInTheDocument();
  });

  it("cancels an open form and clears entered values", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /add a card/i }));
    await user.type(screen.getByPlaceholderText("Card title"), "Discarded card");
    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByPlaceholderText("Card title")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add a card/i })).toBeInTheDocument();
    expect(onAdd).not.toHaveBeenCalled();
  });
});
