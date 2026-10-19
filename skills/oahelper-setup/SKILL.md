---
name: oahelper-setup
description: Install, connect and troubleshoot the oahelper MCP server (oahelper-mcp) in Claude Code, Claude Desktop, Cursor, VS Code, Codex or any MCP client. Use when the user says "set up oahelper", "oahelper isn't connecting", "session rejected", "daily cap reached", "the oahelper tools are missing", or asks how to refresh their OAHelper cookie.
---

# Set up and fix oahelper-mcp

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

The session cookie is a password. Never ask the user to paste it into chat, never print
`.env`, and never echo a header value back. Check whether a key is set, not what it is.

## 1. Find the install

Work out which way it was installed:
- **Claude Code plugin** (`oahelper@oahelper-mcp` in `claude plugin list`): the cookie is
  set with `/plugin configure oahelper@oahelper-mcp`.
- **uvx** (`uvx ... oahelper-mcp` in the client config): data folder `~/.oahelper` unless
  `OAHELPER_HOME` is set.
- **Clone** (`python .../server.py`): data folder is the clone itself.

`oahelper_status()` prints the data folder when the server is reachable.

## 2. Diagnose in this order, stop at the first failure

| Check | How | If it fails |
|---|---|---|
| Runtime | uvx installs: `uvx --version`. Clones: `python --version` is 3.10+ | Install uv, or a newer Python |
| Dependencies (clones only) | `<client's python> -c "import mcp"` | `pip install -r requirements.txt` into that interpreter. `mcp` must be below 2.0 |
| Server starts | Run the exact command from the client config by hand: it should sit silently waiting on stdin (Ctrl+C to stop) | Read the traceback, fix it |
| Client registered | Claude Code: `claude mcp list`. Others: open the config file from the README | Add it with absolute paths, restart the client |
| Session present | `oahelper_status()` says `cookie set: yes` | Walk the user through the cookie steps below |
| Session valid | `oahelper_status(online=true)` says `session valid` | Cookie expired: redo the cookie steps |

`oahelper_status(online=true)` costs one live request; plain `oahelper_status()` costs none.

## 3. Cookie steps (the user does these, not you)

1. Create `.env` in the data folder if it does not exist. Plugin users skip this and,
   after step 3, paste the cookie into `/plugin configure oahelper@oahelper-mcp` instead.
2. Log in at https://www.oahelper.in, open DevTools (F12), Network tab, reload.
3. Click any request whose URL contains `/api/proxy/`, copy the full `cookie` request
   header into `OAHELPER_COOKIE=` in `.env`. Copy `authorization` into
   `OAHELPER_BEARER=` if present.
4. Save. No restart is needed: the server rereads `.env` on every request.

## 4. Common errors

- `session rejected` / 401 / 403: cookie expired or the user logged out. Redo step 3.
- `Daily cap reached`: by design. Offline tools still work. Only raise
  `OAHELPER_DAILY_CAP` if the user explicitly asks, and remind them the cap protects
  their account.
- Premium content missing: account is not Pro, or the cache holds a logged-out copy.
  Retry the call with `refresh=true`.
- Client shows "failed" or "connection closed": `uvx` not on the PATH the client sees,
  or (clones) a relative path or the wrong Python. Use absolute paths.
- `No module named 'mcp.server.fastmcp'`: `mcp` 2.x is installed. Install `mcp<2`.

Finish by reporting each check as pass or fail in one short list.
