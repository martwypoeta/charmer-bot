# Charmer

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9)](https://docs.astral.sh/uv)
[![Ruff](https://img.shields.io/badge/Ruff-lint%2Fformat-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff)
[![ty](https://img.shields.io/badge/ty-typecheck-DE5FE9)](https://docs.astral.sh/ty)

My Discord bot for random things I want, built with discord.py.

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `;help` | — | Show all commands and uptime |
| `;user [user]` | `ui` `userinfo` `whois` | Display user information |
| `;google <query>` | — | Search the web via Google |
| `;ip <ip\|domain>` | `ipv4` | IP geolocation lookup |
| `;password [length]` | `pass` `pw` | Generate a secure password (sent via DM) |
| `;remind <time> <message>` | `remindme` | Set a reminder — e.g. `2h`, `30m`, `5d` |
| `;screenshot <url>` | `ss` `webshot` | Take a website screenshot |
| `;screenshot grant <user>` | — | Grant screenshot permission *(Administrator)* |
| `;screenshot revoke <user>` | — | Revoke screenshot permission *(Administrator)* |
| `;screenshot list` | `ls` | List users with screenshot permission *(Administrator)* |
| `;subdomains <domain>` | `sub` `subdomain` | Find subdomains via crt.sh |

## Quick Setup

**Requirements:**

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.14 (installed automatically by uv via [`.python-version`](.python-version))

```bash
cp .env.example .env   # fill in your values
uv sync
uv run main.py
```

On first run, the bot applies [`bot/schema.sql`](bot/schema.sql) to your database.

## Environment Variables

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `DISCORD_TOKEN` | Bot token | [Discord Developer Portal → Applications → Bot](https://discord.com/developers/applications) |
| `DATABASE_DSN` | PostgreSQL connection string | Your Postgres provider (e.g. [Neon](https://neon.tech)) |
| `SCREENSHOT_API_TOKEN` | Screenshot API token | [screenshotapi.net → Dashboard](https://app.screenshotapi.net) |

## Scripts

```bash
uv run main.py              # start the bot
uv run ruff check .         # lint
uv run ruff format .        # format
uv run ruff format --check .  # check formatting (CI)
uv run ty check             # type check
```

## License

Charmer is licensed under the [GNU Affero General Public License v3](LICENSE). <img align="right" width="120" src="https://www.gnu.org/graphics/agplv3-155x51.png" alt="AGPLv3 Logo">
