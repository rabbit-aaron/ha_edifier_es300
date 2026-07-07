"""Constants for the Edifier ES300 integration."""

from datetime import timedelta

DOMAIN = "edifier_es300"

DEFAULT_PORT = 8080

# We hold one long-lived connection. While it's open the speaker keeps pushing
# heart_beat (~3s active, ~7s idle) and status frames on its own, so we don't
# poll -- we just watch that they keep arriving. This is the watchdog tick.
WATCHDOG_INTERVAL = timedelta(seconds=5)

# If no frame (heartbeat or status) arrives within this window, treat the
# connection as dead and reconnect on the next tick.
HEARTBEAT_TIMEOUT = 15.0

# Per-request ceiling; the library's futures have no timeout of their own.
COMMAND_TIMEOUT = 5.0
