# DailyBot CLI

A command-line interface for [DailyBot](https://www.dailybot.com) that lets **people** and **software agents** share progress updates, blockers, and feedback — straight from the terminal.

Whether you're a developer who lives in the terminal or an AI agent running in a CI pipeline, the DailyBot CLI gives you a fast way to submit check-ins without leaving your workflow.

## Installation

```bash
pip install dailybot-cli
```

Or via the install script:

```bash
curl -sSL https://cli.dailybot.com/install.sh | bash
```

Requires Python 3.9+.

## For humans

Authenticate once with your DailyBot email, then submit updates and check pending check-ins right from your terminal.

```bash
# Log in (one-time setup, email OTP)
dailybot login

# See what check-ins are waiting for you
dailybot status

# Submit a free-text update
dailybot update "Finished the auth module, starting on tests."

# Or use structured fields
dailybot update --done "Auth module" --doing "Tests" --blocked "None"
```

Run `dailybot` with no arguments to enter **interactive mode** — if you're not logged in yet, it will walk you through authentication first, then let you submit updates step by step.

## For agents

Any software agent — AI coding assistants, CI jobs, deploy scripts, bots — can report activity through the CLI using an API key. This lets teams get visibility into what automated processes are doing, alongside human updates.

Set the `DAILYBOT_API_KEY` environment variable, then:

```bash
# Report a deployment
dailybot agent update "Deployed v2.1 to staging"

# Name the agent so the team knows who's reporting
dailybot agent update "Built feature X" --name "Claude Code"

# Include structured data
dailybot agent update "Tests passed" --name "CI Bot" --json-data '{"suite": "integration", "passed": 42}'
```

## Commands

| Command | Description |
|---|---|
| `dailybot login` | Authenticate with email OTP |
| `dailybot logout` | Log out and revoke token |
| `dailybot status` | Show pending check-ins for today |
| `dailybot update` | Submit a check-in update (free-text or structured) |
| `dailybot agent update` | Submit an agent activity report (API key) |

Run `dailybot --help` for full details on any command.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
