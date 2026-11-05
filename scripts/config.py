"""Static configuration for the FARBOUD AI profile generator."""
import os

USERNAME = "iliyahaddad"
API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

PRODUCT = "FARBOUD AI"
SUBTITLE = "MATRIX INTELLIGENCE SYSTEM"
TAGLINE = "Beyond Code. Beyond Intelligence."

# Repositories to feature (matched case-insensitively against public repos).
FEATURED = ("BasicForge", "NexaPack", "vTPM2")

WIDTH = 1200
HEIGHT = 1090

COLORS = {
    "bg": "#020806",
    "green": "#00FF88",
    "green2": "#00C878",
    "highlight": "#8AFFC1",
    "panel": "#03140C",
    "text": "#E8FFF2",
    "muted": "#5E8F76",
}

# Network behaviour
HTTP_TIMEOUT = 20
HTTP_RETRIES = 4
MAX_LANGUAGE_REPOS = 40      # repos queried for language bytes
MAX_EVENTS = 6
MAX_REPOS_SHOWN = 5

ASSET_ANIMATED = "assets/farboud-matrix.svg"
ASSET_STATIC = "assets/farboud-static.svg"
