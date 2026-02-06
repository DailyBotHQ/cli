# DailyBot CLI

Submit check-in updates from your terminal.

## Installation

```bash
pip install dailybot-cli
```

Or via the install script:

```bash
curl -sSL https://cli.dailybot.com/install.sh | bash
```

Requires Python 3.9+.

## Quick start

```
dailybot auth login          # Authenticate with email OTP
dailybot status              # View pending check-ins
dailybot update "message"    # Submit a free-text update
dailybot update --done "X" --doing "Y" --blocked "None"
```

## Agent mode

Requires the `DAILYBOT_API_KEY` environment variable:

```
dailybot agent update "Deployed v2.1" --name "My Agent"
```

## Interactive mode

Run `dailybot` without arguments to enter interactive mode.

## Usage

```
Usage: dailybot [OPTIONS] COMMAND [ARGS]...

  DailyBot CLI - Submit check-in updates from your terminal.

  Quick start:
    dailybot auth login          # Authenticate with email OTP
    dailybot status              # View pending check-ins
    dailybot update "message"    # Submit a free-text update
    dailybot update --done "X" --doing "Y" --blocked "None"

  Agent mode (requires DAILYBOT_API_KEY env var):
    dailybot agent update "Deployed v2.1" --name "My Agent"

  Run without arguments for interactive mode.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  agent   Submit updates via API key (for agents / CI).
  auth    Manage authentication.
  status  Show pending check-ins.
  update  Submit a check-in update.
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
