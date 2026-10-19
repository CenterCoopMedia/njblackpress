"""A CSV refresh must not invent activity from a missing final year."""
from activity import csv_activity

for status in (True, False, None):
    for ending in ("", "?", "Unknown", "1979"):
        assert csv_activity({"Year ceased": ending}, status) is status
assert csv_activity({"Activity status": "active"}, None) is True
assert csv_activity({"Activity status": "ceased"}, True) is False
assert csv_activity({"isActive": "unverified"}, True) is None
assert csv_activity({"Year ceased": ""}) is None
try:
    csv_activity({"Activity status": "maybe"})
except ValueError:
    pass
else:
    raise AssertionError("Invalid explicit activity must stop conversion")
print("PASS: CSV refresh preserves tri-state activity unless explicitly changed")
