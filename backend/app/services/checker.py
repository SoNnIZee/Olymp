from __future__ import annotations


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split()).upper()


def check_answer(*, answer: str, correct_answer: str, answer_type: str) -> bool:
    """
    MVP checker:
    - text: case-insensitive, whitespace-normalized compare
    - int: integer parse compare
    - float: float parse, compare with small tolerance, supports comma decimal separator
    """
    at = (answer_type or "text").strip().lower()

    if at == "int":
        try:
            return int(answer.strip()) == int(correct_answer.strip())
        except Exception:
            return False

    if at == "float":
        try:
            a = float(answer.strip().replace(",", "."))
            b = float(correct_answer.strip().replace(",", "."))
        except Exception:
            return False
        return abs(a - b) <= 1e-6

    return _normalize_text(answer) == _normalize_text(correct_answer)

