"""Dailybot CLI - The command-line bridge between humans and agents."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__: str = version("dailybot-cli")
except PackageNotFoundError:
    __version__: str = "0.0.0"
