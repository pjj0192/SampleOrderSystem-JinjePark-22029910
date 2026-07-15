from app.views.progress_bar import render_progress_bar


def test_renders_empty_bar_at_zero_progress():
    assert render_progress_bar(0.0, width=10) == "[----------] 0%"


def test_renders_full_bar_at_full_progress():
    assert render_progress_bar(1.0, width=10) == "[##########] 100%"


def test_renders_half_filled_bar_at_half_progress():
    assert render_progress_bar(0.5, width=10) == "[#####-----] 50%"


def test_rounds_percentage_to_nearest_whole_number():
    assert render_progress_bar(0.333, width=10) == "[###-------] 33%"


def test_clamps_progress_above_one_to_full_bar():
    assert render_progress_bar(1.5, width=10) == "[##########] 100%"


def test_clamps_negative_progress_to_empty_bar():
    assert render_progress_bar(-0.2, width=10) == "[----------] 0%"
