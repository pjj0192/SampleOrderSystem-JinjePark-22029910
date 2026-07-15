def render_progress_bar(progress: float, width: int = 20) -> str:
    """Renders a fixed-width ASCII progress bar, e.g. "[#####-----] 50%".
    Clamps progress to [0, 1] so an overdue (>100%) or not-yet-started
    (<0%) job never produces a malformed bar."""
    clamped = max(0.0, min(progress, 1.0))
    filled = round(clamped * width)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {round(clamped * 100)}%"
