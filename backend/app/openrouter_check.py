from app.openrouter import OpenRouterError, complete


def main() -> int:
    try:
        print(complete("2+2"))
    except OpenRouterError as error:
        print(f"OpenRouter connectivity check failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())