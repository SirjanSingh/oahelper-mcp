# oahelper-mcp

**Built by [Sirjan Singh](https://github.com/SirjanSingh)**

[![GitHub stars](https://img.shields.io/github/stars/SirjanSingh/oahelper-mcp?style=social)](https://github.com/SirjanSingh/oahelper-mcp/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-black)](https://modelcontextprotocol.io)

An MCP server that lets Claude Code, Claude Desktop, Cursor, Codex or any other MCP client
read your **own** [OAHelper](https://www.oahelper.in) Pro account: company OA question
sets, full problem statements, MCQ answer keys, official solutions and interview
experiences. Everything it fetches is also saved as plain markdown on your disk, so you
can prep offline, in Obsidian, or with an agent that never touches the network again.

It is one Python file with a single dependency (the official `mcp` SDK). HTTP is the
standard library.

> **Read this first.** OAHelper's Terms of Service forbid automated access and scraping,
> and the penalty can be losing your Pro account. This tool is built to be used the way
> a person uses the site: one company at a time, only when you ask, 2 seconds between
> requests, a hard daily cap (300 by default), and a disk cache so nothing is fetched
> twice. It uses your own logged-in browser session, ships no content, and gives you
> nothing your plan does not already include. Whether to run it is your decision and
> your risk. Do not use it to crawl the site, and never publish or share what it saves.

## What you get

| Tool | What it does | Network |
|---|---|---|
| `oahelper_search(company)` | Lists a company's OA sets with dates, counts and refs | 1 request (cached 1 day) |
| `oahelper_sync(company, max_items=20)` | Downloads a company's sets, questions, MCQ answers and interview write-ups into the library, newest first. Stops after `max_items` requests and tells you how much is left | up to `max_items` |
| `oahelper_company(slug_or_url)` | One set page by slug or `.../company-questions/<slug>` URL | 1 request |
| `oahelper_question(ref_or_url)` | One question: statement, MCQ answers with explanations, optional images and community solutions | 1 to 4 requests |
| `oahelper_solution(ref_or_url, language)` | Official solution (`cpp`, `python`, `java`). Uses your plan's solution quota | 1 request |
| `oahelper_interviews(company)` | Interview experiences for a company, full text saved | 1 to 2 requests |
| `oahelper_offline(company="")` | What is already saved. Works with no session at all | none |
| `oahelper_status(online=False)` | Is a session configured, requests used today, optional Pro check | none or 1 |

The library layout:

```
library/<company>/
  index.md            sets, interviews and counts, with links
  sets/<ref>-<name>.md
  questions/<ref>-<title>.md
  interviews/<id>-<role>.md
  images/             only when you ask for them
```

`library/`, `cache/` and `.env` are gitignored. Keep it that way.

## Requirements

- Python 3.10 or newer
- An OAHelper account (most content needs Pro)
- Any MCP client that can launch a local stdio server

## Install

```bash
git clone https://github.com/SirjanSingh/oahelper-mcp.git
cd oahelper-mcp
python -m venv .venv
```

Activate it (`source .venv/bin/activate` on macOS/Linux, `.venv\Scripts\activate` on
Windows), then:

```bash
pip install -r requirements.txt
```

### Add your session

1. Copy `.env.example` to `.env` in the same folder.
2. Open <https://www.oahelper.in> in your browser while logged in.
3. Press F12, open the **Network** tab, reload, and click any request whose URL contains
   `/api/proxy/`.
4. Under **Request Headers**, copy the whole `cookie` value into `OAHELPER_COOKIE`. If
   there is an `authorization` header, copy it into `OAHELPER_BEARER`. Copying your
   `user-agent` into `OAHELPER_USER_AGENT` is optional.

The session lasts until you log out on the site. When tools start returning
`session rejected`, repeat these steps. Treat the cookie like a password: do not paste it
into a chat with any AI, and do not commit it.

Check it works:

```bash
python -c "import server; print(server.oahelper_status(online=True))"
```

You should see `session valid | Pro: yes`.

## Connect it to your agent

Every client below needs the same two things: the Python that has `mcp` installed, and
the absolute path to `server.py`. In the examples, replace `/path/to/oahelper-mcp` with
your clone, and use `.venv/bin/python` (macOS/Linux) or `.venv\\Scripts\\python.exe`
(Windows, escaped backslashes in JSON).

### Claude Code

```bash
claude mcp add oahelper -s user -- /path/to/oahelper-mcp/.venv/bin/python /path/to/oahelper-mcp/server.py
```

`-s user` makes it available in every project; use `-s local` for the current project
only. Run `claude mcp list` to confirm it shows as connected, or `/mcp` inside a session.

**Optional skill.** Copy `skills/oa-prep/` to `~/.claude/skills/oa-prep/` and Claude Code
will turn "prep me for Amazon's OA" into a full study guide: it syncs the company, reads
the saved pack, adds public sources and writes a dated guide with every past question
mapped to the nearest LeetCode problem.

### Claude Desktop

Edit `claude_desktop_config.json` (Settings, Developer, Edit Config):

```json
{
  "mcpServers": {
    "oahelper": {
      "command": "/path/to/oahelper-mcp/.venv/bin/python",
      "args": ["/path/to/oahelper-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop.

### Cursor

Same JSON as Claude Desktop, in `~/.cursor/mcp.json` (all projects) or
`.cursor/mcp.json` (one project).

### VS Code (Copilot agent mode)

`.vscode/mcp.json` uses a `servers` key:

```json
{
  "servers": {
    "oahelper": {
      "type": "stdio",
      "command": "/path/to/oahelper-mcp/.venv/bin/python",
      "args": ["/path/to/oahelper-mcp/server.py"]
    }
  }
}
```

### OpenAI Codex CLI

```bash
codex mcp add oahelper -- /path/to/oahelper-mcp/.venv/bin/python /path/to/oahelper-mcp/server.py
```

or in `~/.codex/config.toml`:

```toml
[mcp_servers.oahelper]
command = "/path/to/oahelper-mcp/.venv/bin/python"
args = ["/path/to/oahelper-mcp/server.py"]
```

### Gemini CLI, Windsurf, Cline and others

Any client that reads an `mcpServers` JSON block takes the Claude Desktop snippet
unchanged. Check your client's docs for where its config file lives.

## Using it

Ask in plain language. Some prompts that work well:

- "What OA sets does OAHelper have for Juspay?"
- "Sync Amazon from OAHelper, then tell me the topic mix of their last three OAs."
- "Show me question `MjM3OHww` with the MCQ answers."
- "Get the official C++ solution for that one."
- "What have people said about Atlassian's interview rounds this year?"
- "What do I already have saved offline?"

A typical prep loop: `oahelper_sync` a company (call again while it says `NOT DONE`),
then let the agent read `library/<company>/index.md` and the files it links. Reading the
library costs no requests.

## Configuration

All in `.env`:

| Key | Default | Meaning |
|---|---|---|
| `OAHELPER_COOKIE` | | Browser `cookie` header from a logged-in session |
| `OAHELPER_BEARER` | | `authorization` header, if the site sends one |
| `OAHELPER_USER_AGENT` | generic | Your browser's user agent, so requests match your session |
| `OAHELPER_DAILY_CAP` | `300` | Live requests per day before the server refuses |

The 2 second gap between requests is `MIN_GAP` in `server.py`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `session rejected` / HTTP 401 or 403 | Cookie expired. Copy a fresh one into `.env` |
| `Daily cap reached` | Wait until tomorrow. Cached and offline tools still work |
| Client shows the server as failed | Use absolute paths, and the Python that has `mcp` installed. Run `python server.py` by hand: it should sit silently waiting on stdin |
| `ModuleNotFoundError: mcp` | The client is launching a different Python. Point `command` at the venv's interpreter |
| Premium content missing | Your account is not Pro, or the cached copy was fetched logged out. Pass `refresh=true` |

## How it was built

The site has no public API. The endpoints were found by recording a HAR of normal
browsing on a personal account and summarising it with `tools/har_endpoints.py`, which
prints paths, parameter names and response shapes but never header values or response
content. If the site changes and something breaks, record a new HAR, run that script on
it, and compare.

## Author

I am **Sirjan Singh**. I built this to prep for my own placement OAs.

- GitHub: [@SirjanSingh](https://github.com/SirjanSingh)
- LinkedIn: [Sirjan Singh](https://www.linkedin.com/in/sirjan-singh-573534286)

If this saved you prep time, **star the repo**. It is the only way I find out it helped
someone, and it helps other people preparing for OAs find it. Issues and pull requests
are welcome.

## License

MIT, copyright (c) 2026 Sirjan Singh, for the code in this repository. It grants nothing over OAHelper's content, which
belongs to OAHelper and its contributors.

This project is not affiliated with or endorsed by OAHelper.
