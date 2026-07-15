from app.models.order import Order


def resolve_order_id(raw: str, candidates: list[Order]) -> str | None:
    """Lets the user refer to an order from a just-displayed list without
    retyping the full ORD-YYYYMMDD-NNNN id: an exact id, its 1-based
    position in that list, or a unique trailing-digit suffix all resolve
    to the same order_id. Returns None if nothing matches or the match
    is ambiguous (a suffix shared by more than one candidate)."""
    raw = raw.strip()

    for order in candidates:
        if order.order_id == raw:
            return order.order_id

    if raw.isdigit():
        index = int(raw)
        if 1 <= index <= len(candidates):
            return candidates[index - 1].order_id

    suffix_matches = [order for order in candidates if order.order_id.endswith(raw)]
    if len(suffix_matches) == 1:
        return suffix_matches[0].order_id

    return None
