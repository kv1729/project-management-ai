import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SignInForm } from "@/components/SignInForm";

describe("SignInForm", () => {
  it("shows an error for invalid credentials", async () => {
    const onSignIn = vi.fn();
    const user = userEvent.setup();
    render(<SignInForm onSignIn={onSignIn} />);

    await user.type(screen.getByLabelText("Username"), "user");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "The username or password is incorrect."
    );
    expect(onSignIn).not.toHaveBeenCalled();
  });

  it("submits valid credentials", async () => {
    const onSignIn = vi.fn();
    const user = userEvent.setup();
    render(<SignInForm onSignIn={onSignIn} />);

    await user.type(screen.getByLabelText("Username"), "user");
    await user.type(screen.getByLabelText("Password"), "password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(onSignIn).toHaveBeenCalledOnce();
  });
});