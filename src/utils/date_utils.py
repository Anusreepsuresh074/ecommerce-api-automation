from datetime import datetime


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def pivot_between(timestamps: list[str], fraction: float) -> str:
    """An ISO-8601 UTC instant between two neighbouring timestamps, `fraction` of the way through the
    sorted list — so no product sits exactly on the boundary and the filter's result is unambiguous."""
    ordered = sorted(parse_iso(value) for value in timestamps)
    index = max(0, min(len(ordered) - 2, int(len(ordered) * fraction)))
    middle = ordered[index] + (ordered[index + 1] - ordered[index]) / 2
    return middle.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
