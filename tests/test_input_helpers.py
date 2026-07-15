from app.views.input_helpers import prompt_choice, prompt_float, prompt_int, prompt_nonblank_str


def _feed_inputs(monkeypatch, values):
    scripted = iter(values)
    monkeypatch.setattr("builtins.input", lambda *_: next(scripted))


def test_prompt_nonblank_str_returns_first_valid_value(monkeypatch):
    _feed_inputs(monkeypatch, ["S-001"])

    assert prompt_nonblank_str("prompt > ") == "S-001"


def test_prompt_nonblank_str_retries_on_blank_input(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["", "   ", "S-001"])

    result = prompt_nonblank_str("prompt > ")

    assert result == "S-001"
    assert capsys.readouterr().out.count("다시 입력") == 2


def test_prompt_int_returns_parsed_value(monkeypatch):
    _feed_inputs(monkeypatch, ["10"])

    assert prompt_int("prompt > ") == 10


def test_prompt_int_retries_on_non_numeric_input(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["abc", "10"])

    result = prompt_int("prompt > ")

    assert result == 10
    assert "올바른 정수가 아닙니다" in capsys.readouterr().out


def test_prompt_int_retries_when_below_min_value(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["0", "-5", "10"])

    result = prompt_int("prompt > ", min_value=1)

    assert result == 10
    assert capsys.readouterr().out.count("이상의 값") == 2


def test_prompt_float_returns_parsed_value(monkeypatch):
    _feed_inputs(monkeypatch, ["0.5"])

    assert prompt_float("prompt > ") == 0.5


def test_prompt_float_retries_on_non_numeric_input(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["not-a-number", "0.5"])

    result = prompt_float("prompt > ")

    assert result == 0.5
    assert "올바른 숫자가 아닙니다" in capsys.readouterr().out


def test_prompt_float_retries_when_at_or_below_exclusive_min(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["0", "-1", "0.5"])

    result = prompt_float("prompt > ", min_value=0, exclusive_min=True)

    assert result == 0.5


def test_prompt_float_retries_when_above_max_value(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["1.5", "0.9"])

    result = prompt_float("prompt > ", max_value=1.0)

    assert result == 0.9


def test_prompt_choice_returns_matching_uppercased_value(monkeypatch):
    _feed_inputs(monkeypatch, ["y"])

    assert prompt_choice("prompt > ", {"Y", "N"}) == "Y"


def test_prompt_choice_retries_on_value_not_in_choices(monkeypatch, capsys):
    _feed_inputs(monkeypatch, ["maybe", "N"])

    result = prompt_choice("prompt > ", {"Y", "N"})

    assert result == "N"
    assert "다시 입력" in capsys.readouterr().out
