---
name: oahelper-setup
description: Install, connect and troubleshoot the oahelper MCP server (oahelper-mcp) in Claude Code, Claude Desktop, Cursor, VS Code, Codex or any MCP client. Use when the user says "set up oahelper", "oahelper isn't connecting", "session rejected", "daily cap reached", "the oahelper tools are missing", or asks how to refresh their OAHelper cookie.
---

# Set up and fix oahelper-mcp

Part of [oahelper-mcp](https://github.com/SirjanSingh/oahelper-mcp) by Sirjan Singh.

The session cookie is a password. Never ask the user to paste it into chat, never print
`.env`, and never echo a header value back. Check whether a key is set, not what it is.

## 1. Find the install

Locate the folder that holds `server.py` (ask if it is not obvious). Everything below is
relative to it.

## 2. Diagnose in this order, stop at the first failure

| Check | How | If it fails |
|---|---|---|
| Python 3.10+ | `python --version` | Install a newer Python |
| `mcp` installed in the Python the client launches | `<that python> -c "import mcp"` | `pip install -r requirements.txt` into that interpreter, or point the client at the venv's Python |
| Server starts | `<python> server.py` should sit silently waiting on stdin (Ctrl+C to stop) | Read the traceback, fix it |
| Client registered | Claude Code: `claude mcp list`. Others: open the config file from the README | Add it with absolute paths, restart the client |
| Session present | `oahelper_status()` says `cookie set: yes` | Walk the user through the cookie steps below |
| Session valid | `oahelper_status(online=true)` says `session valid` | Cookie expired: redo the cookie steps |

`oahelper_status(online=true)` costs one live request; plain `oahelper_status()` costs none.

## 3. Cookie steps (the user does these, not you)

1. Copy `.env.example` to `.env` if it does not exist.
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
- Client shows "failed" or "connection closed": almost always a relative path or the
  wrong Python. Use absolute paths to both.

Finish by reporting each check as pass or fail in one short list.
