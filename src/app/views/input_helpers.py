"""Retry-on-invalid-input prompt helpers shared by every console View.

Each function loops forever until the user provides a value that parses
and satisfies the given constraints, printing a specific error message
and re-prompting on each invalid attempt rather than letting a raw
ValueError crash the app (see CLAUDE.md).
"""


def prompt_nonblank_str(prompt: str) -> str:
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw
        print("빈 값은 입력할 수 없습니다. 다시 입력해주세요.")


def prompt_int(prompt: str, *, min_value: int | None = None) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print(f"'{raw}'는 올바른 정수가 아닙니다. 다시 입력해주세요.")
            continue
        if min_value is not None and value < min_value:
            print(f"{min_value} 이상의 값을 입력해주세요.")
            continue
        return value


def prompt_float(
    prompt: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    exclusive_min: bool = False,
) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print(f"'{raw}'는 올바른 숫자가 아닙니다. 다시 입력해주세요.")
            continue
        if min_value is not None:
            if exclusive_min and value <= min_value:
                print(f"{min_value}보다 큰 값을 입력해주세요.")
                continue
            if not exclusive_min and value < min_value:
                print(f"{min_value} 이상의 값을 입력해주세요.")
                continue
        if max_value is not None and value > max_value:
            print(f"{max_value} 이하의 값을 입력해주세요.")
            continue
        return value
