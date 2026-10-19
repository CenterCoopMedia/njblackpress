"""CSV activity is independent of missing cessation dates."""


def csv_activity(row, previous=None):
    value = (row.get("Activity status", row.get("isActive", "")) or "").strip().lower()
    if not value:
        return previous
    states = {"true": True, "active": True, "false": False, "ceased": False,
              "historical": False, "null": None, "unknown": None, "unverified": None,
              "resource": None}
    if value not in states:
        raise ValueError(f"Invalid explicit activity status: {value!r}")
    return states[value]
