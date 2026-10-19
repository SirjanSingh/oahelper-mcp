"""OAHelper MCP server: your OAHelper Pro account in Claude Code, saved offline.

Personal use only, on your own logged-in session. OAHelper's Terms of Service forbid
automated access, so this fetches only what you ask for, one company at a time, waits
2s between requests, stops at a daily cap, and caches everything so nothing is fetched
twice. Never a whole-site crawl.

Everything fetched is also written as markdown to library/<company>/ so it can be read
offline (by you, by Claude, or in Obsidian). library/ and cache/ are gitignored: they are
personal copies of paid content and must never be pushed anywhere.

Auth: your browser session in .env next to this file (see .env.example). Never paste it into chat.

Register:  claude mcp add oahelper -s user -- python /absolute/path/to/oahelper-mcp/server.py
"""
import base64, json, re, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime
from html import unescape
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
LIB = HERE / "library"
API = "https://www.oahelper.in/api/proxy"
SITE = "https://www.oahelper.in"
MIN_GAP = 2.0            # seconds between live requests
DEFAULT_DAILY_CAP = 300  # live requests per day; OAHELPER_DAILY_CAP in .env overrides
DAY = 86400
_last = 0.0
_live = 0                # live requests made by this process, used for sync budgets
_me = None

# question fields that can carry solution or answer content
ANSWER_FIELDS = ["solution_cpp", "solution_python", "solution_java", "solution",
                 "solution_code", "sql_solution", "js_solution", "bash_solution",
                 "editorial", "prompt_solution", "input_test_case", "output_test_case",
                 "google_doc_link", "youtube_tutorial"]


# ---------- config and HTTP ----------

def _env():
    """Read KEY=VALUE lines from .env next to this file. Values are never logged."""
    out, f = {}, HERE / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _authed():
    env = _env()
    return bool(env.get("OAHELPER_COOKIE") or env.get("OAHELPER_BEARER"))


def _headers():
    env = _env()
    h = {"Content-Type": "application/json",
         "User-Agent": env.get("OAHELPER_USER_AGENT") or "Mozilla/5.0 (oahelper-mcp personal)",
         "Referer": SITE + "/"}
    if env.get("OAHELPER_COOKIE"):
        h["Cookie"] = env["OAHELPER_COOKIE"]
    if env.get("OAHELPER_BEARER"):
        tok = env["OAHELPER_BEARER"]
        h["Authorization"] = tok if tok.lower().startswith("bearer ") else f"Bearer {tok}"
    return h


def _count_request():
    """Enforce the daily cap. Only today's count is kept."""
    f = CACHE / "_usage.json"
    today = date.today().isoformat()
    try:
        n = json.loads(f.read_text(encoding="utf-8")).get(today, 0)
    except (OSError, ValueError):
        n = 0
    cap = int(_env().get("OAHELPER_DAILY_CAP") or DEFAULT_DAILY_CAP)
    if n >= cap:
        raise RuntimeError(f"Daily cap reached ({n}/{cap} live requests today). Cached and "
                           f"offline data still work. Raise OAHELPER_DAILY_CAP in .env only "
                           f"if you mean to.")
    CACHE.mkdir(exist_ok=True)
    f.write_text(json.dumps({today: n + 1}), encoding="utf-8")


def _fetch(path, raw=False):
    """One polite GET. Returns the full JSON envelope (or bytes when raw)."""
    global _last, _live
    _count_request()
    wait = MIN_GAP - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(API + path, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            raise RuntimeError(f"HTTP {e.code}: session rejected. Refresh OAHELPER_COOKIE in "
                               f".env (next to server.py) from a logged-in browser. {msg}")
        raise RuntimeError(f"HTTP {e.code}: {msg}")
    finally:
        _last = time.monotonic()
        _live += 1
    if raw:
        return body
    d = json.loads(body.decode("utf-8"))
    if d.get("status") != "success":
        raise RuntimeError(d.get("message") or f"API error: {body[:300]!r}")
    return d


def _safe(key):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(key))


def _cached(kind, key, fetch, refresh=False, max_age=None):
    """Disk cache. A copy fetched logged-out is refetched once a session is configured."""
    f = CACHE / kind / (_safe(key) + ".json")
    if f.exists() and not refresh:
        c = json.loads(f.read_text(encoding="utf-8"))
        fresh = max_age is None or time.time() - c.get("fetched_at", 0) < max_age
        if fresh and (c.get("authed") or not _authed()):
            return c["data"], True
    data = fetch()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"authed": _authed(), "fetched_at": time.time(), "data": data},
                            ensure_ascii=False), encoding="utf-8")
    return data, False


def _peek(kind, key):
    f = CACHE / kind / (_safe(key) + ".json")
    return json.loads(f.read_text(encoding="utf-8"))["data"] if f.exists() else None


def _whoami():
    """User id and Pro status from the session cookie (one request per server start)."""
    global _me
    if _me is None:
        if not _authed():
            raise RuntimeError("No session configured in .env (next to server.py).")
        d = _fetch("/user-shell")["data"]
        _me = {"user_id": d["summary"]["user_id"],
               "is_premium": bool(d.get("premium", {}).get("is_premium")),
               "plan": d["summary"].get("premium_plan")}
    return _me


# ---------- ids and text ----------

def _num(ref):
    """Refs are base64 of '<id>|0': MjM3OHww -> 2378."""
    if str(ref).isdigit():
        return str(ref)
    return base64.b64decode(ref + "=" * (-len(ref) % 4)).decode().split("|")[0]


def _slug(s):
    """Accept a slug or a full .../company-questions/<slug> URL."""
    m = re.search(r"company-questions/([^/?#]+)", s)
    return m.group(1) if m else s.strip().strip("/")


def _qref(s):
    """Accept a question ref or a full .../problems/<ref>/... URL."""
    m = re.search(r"problems/([^/?#]+)", s)
    return m.group(1) if m else s.strip().strip("/")


def _slugify(s, n=60):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:n] or "untitled"


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _text(html):
    """Rough HTML to text; passes plain text or markdown through untouched."""
    if not html or not re.search(r"<(p|div|br|li|ul|ol|pre|code|span|h\d|table)\b", html, re.I):
        return (html or "").strip()
    html = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|pre|tr)>", "\n", html)
    html = re.sub(r"(?i)<li[^>]*>", "- ", html)
    return re.sub(r"\n{3,}", "\n\n", unescape(re.sub(r"<[^>]+>", "", html))).strip()


def _join(xs):
    return ", ".join(str(x) for x in (xs or []) if x) or "UNKNOWN"


# ---------- API calls (all cached) ----------

def _search(name, refresh=False):
    q = urllib.parse.urlencode({"action": "search", "q": name})
    return _cached("search", name.lower(), lambda: _fetch(f"/company?{q}")["data"],
                   refresh, max_age=DAY)[0]


def _set_questions(cref, refresh=False):
    q = urllib.parse.urlencode({"action": "get_questions_by_company", "company_ref": cref})
    return _cached("setq", cref, lambda: _fetch(f"/question?{q}")["data"],
                   refresh, max_age=7 * DAY)[0]


def _question(ref, refresh=False):
    q = urllib.parse.urlencode({"action": "get_question", "question_ref": ref})
    return _cached("question", ref, lambda: _fetch(f"/question?{q}")["data"], refresh)


def _mcq(ref, refresh=False):
    q = urllib.parse.urlencode({"action": "get_mcq_items_with_answers", "question_id": _num(ref)})
    return _cached("mcq", ref, lambda: _fetch(f"/question-mcq-items?{q}")["data"], refresh)


def _community(ref, refresh=False):
    q = urllib.parse.urlencode({"action": "get_solutions", "question_id": _num(ref),
                                "sort": "hot", "user_id": _whoami()["user_id"]})
    return _cached("community", ref, lambda: _fetch(f"/community-solutions?{q}")["data"],
                   refresh, max_age=7 * DAY)


def _images(co, ref, budget=None):
    """Save a question's images to library/<co>/images/. Returns (saved, skipped)."""
    q = urllib.parse.urlencode({"action": "get_question_images", "question_ref": ref})
    lst, _ = _cached("images", ref, lambda: _fetch(f"/question_images?{q}")["data"])
    d = LIB / co / "images"
    d.mkdir(parents=True, exist_ok=True)
    saved = skipped = 0
    for im in lst or []:
        iid = im.get("id")
        if list(d.glob(f"{iid}.*")):
            saved += 1
            continue
        if budget and not budget():
            skipped += 1
            continue
        b = _fetch("/serve_image?" + urllib.parse.urlencode(
            {"id": iid, "w": _whoami()["user_id"], "v": "orig"}), raw=True)
        ext = "png" if b[:4] == b"\x89PNG" else "jpg" if b[:2] == b"\xff\xd8" else \
              "webp" if b[8:12] == b"WEBP" else "gif" if b[:3] == b"GIF" else None
        if not ext:
            raise RuntimeError(f"image {iid}: response was not an image")
        (d / f"{iid}.{ext}").write_bytes(b)
        saved += 1
    return saved, skipped


def _interviews(company, pages=2, refresh=False):
    """Interview experiences whose company matches, full text included in the list call."""
    items, key = {}, _norm(company)
    for p in range(pages):
        q = urllib.parse.urlencode({"action": "get_all", "limit": 12, "offset": p * 12,
                                    "search": company, "sort": "relevance"})
        d, _ = _cached("interviews", f"{company.lower()}-{p}",
                       lambda q=q: _fetch(f"/interview-experiences?{q}"), refresh, max_age=3 * DAY)
        for x in d.get("data", []):
            if key in _norm(x.get("company")) or key == _norm(x.get("practice_company_key")):
                items[x["id"]] = x
        if not d.get("hasMore"):
            break
    return sorted(items.values(), key=lambda x: x.get("interview_date") or "", reverse=True)


# ---------- offline library (markdown) ----------

def _qfile(co, ref, title):
    return LIB / co / "questions" / f"{ref}-{_slugify(title)}.md"


def _write_question(co, ref):
    """Compose the question's markdown from everything cached for it. Returns the text."""
    q = _peek("question", ref)
    if q is None:
        return None
    L = [f"# {q.get('title')}", "",
         f"- set: {q.get('company_name')}  |  type: {q.get('question_type')}  |  "
         f"difficulty: {q.get('difficulty')} ({q.get('difficulty_score')})  |  "
         f"premium: {'yes' if q.get('premium_required') else 'no'}",
         f"- ref: `{ref}`  |  source: {SITE}/problems/{ref}/{_slugify(q.get('title'))}",
         f"- saved: {date.today()}", "", "## Statement", "",
         q.get("md_problem_statement") or _text(q.get("problem_statement")) or "(none returned)"]
    for k in ANSWER_FIELDS:
        v = q.get(k)
        if v:
            L += ["", f"## {k}", "", v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)]
    mcq = _peek("mcq", ref)
    if mcq:
        L += ["", f"## MCQ answers ({len(mcq)})"]
        for i, m in enumerate(sorted(mcq, key=lambda m: m.get("mcq_index") or 0), 1):
            L += ["", f"### Q{i}", "", _text(m.get("stem")), ""]
            for j in range(1, 7):
                opt = m.get(f"option_{j}")
                if opt:
                    L.append(f"{'ABCDEF'[j - 1]}. {_text(opt)}")
            L += ["", f"**Answer: {_join(m.get('correct_option_letters'))}**"
                  f"{' (' + m['selection_type'] + ')' if m.get('selection_type') else ''}"]
            if m.get("solution_explanation"):
                L += ["", _text(m["solution_explanation"])]
    for f in sorted((CACHE / "solution").glob(f"{_safe(ref)}-*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))["data"]
        lang, code = s.get("language") or f.stem.rsplit("-", 1)[-1], s.get("solution") or ""
        L += ["", f"## Official solution ({lang})", "",
              code if code.lstrip().startswith("```") else f"```{lang}\n{code}\n```"]
    com = _peek("community", ref)
    if com:
        L += ["", f"## Community solutions ({len(com)})"]
        for c in com:
            L.append("")
            for k, v in c.items():
                if isinstance(v, str) and "\n" in v:
                    L += [f"```{c.get('language') or ''}", v, "```"]
                elif v not in (None, "", [], {}) and not re.search(r"user|email|id$", k):
                    L.append(f"- {k}: {v}")
    ims = _peek("images", ref)
    if ims:
        files = [p for im in ims for p in (LIB / co / "images").glob(f"{im.get('id')}.*")]
        L += ["", f"## Images ({len(files)} of {len(ims)} saved)", ""]
        L += [f"![](../images/{p.name})" for p in files]
    elif q.get("has_image"):
        L += ["", "## Images", "", "Not saved yet: call oahelper_question with include_images=true."]
    text = "\n".join(L) + "\n"
    f = _qfile(co, ref, q.get("title"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    return text


def _write_set(co, meta, questions):
    ref = meta.get("id")
    L = [f"# {meta.get('name')}", "",
         f"- company_ref: `{ref}`  |  date: {meta.get('date') or 'UNKNOWN'}",
         f"- questions: {meta.get('question_count', len(questions))} "
         f"(free {meta.get('free_question_count', '?')}, premium {meta.get('premium_question_count', '?')})",
         f"- types: {_join(meta.get('question_types'))}  |  roles: {_join(meta.get('roles'))}",
         f"- colleges: {_join(meta.get('colleges'))}  |  campus: {_join(meta.get('campus_types'))}",
         f"- saved: {date.today()}", "", "## Questions", ""]
    for i, x in enumerate(sorted(questions, key=lambda x: x.get("sort_order") or 0), 1):
        qf = _qfile(co, x["id"], x.get("title"))
        name = f"[{x.get('title')}](../questions/{qf.name})" if qf.exists() else \
               f"{x.get('title')} (not saved yet)"
        tags = ", ".join(x.get("lc_tags") or [])
        L.append(f"{i}. {name}  ({x.get('question_type')}, difficulty {x.get('difficulty_score')}"
                 f"{', premium' if x.get('premium_required') else ''}, added {x.get('date_added')}"
                 f"{', ' + tags if tags else ''})  `{x['id']}`")
    d = LIB / co / "sets"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{ref}-{_slugify(meta.get('name'))}.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def _write_interviews(co, items):
    d = LIB / co / "interviews"
    d.mkdir(parents=True, exist_ok=True)
    for x in items:
        L = [f"# {x.get('company')}: {x.get('role') or 'UNKNOWN role'} "
             f"({x.get('interview_date') or 'date UNKNOWN'})", "",
             f"- result: {x.get('result') or 'UNKNOWN'}  |  difficulty: {x.get('difficulty') or 'UNKNOWN'}"
             f"  |  type: {x.get('interview_type') or 'UNKNOWN'}",
             f"- college: {x.get('college') or 'UNKNOWN'}  |  rounds: {x.get('rounds') or 'UNKNOWN'}",
             f"- posted: {(x.get('created_at') or '')[:10]}  |  id: {x.get('id')}  |  "
             f"source: {SITE}/interview-experiences", "",
             "## Topics asked", "", _text(x.get("topics_asked")) or "UNKNOWN", "",
             "## Experience", "", _text(x.get("experience")) or "(empty)"]
        (d / f"{x.get('id')}-{_slugify(x.get('role'), 40)}.md").write_text(
            "\n".join(L) + "\n", encoding="utf-8")


def _write_index(co):
    d = LIB / co
    sets = sorted((d / "sets").glob("*.md")) if (d / "sets").exists() else []
    qs = list((d / "questions").glob("*.md")) if (d / "questions").exists() else []
    ivs = sorted((d / "interviews").glob("*.md"), reverse=True) if (d / "interviews").exists() else []
    imgs = list((d / "images").glob("*")) if (d / "images").exists() else []
    title = lambda f: f.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ").strip()
    L = [f"# {co}: OAHelper offline pack", "",
         f"updated {datetime.now():%Y-%m-%d %H:%M}  |  {len(sets)} OA sets, {len(qs)} questions, "
         f"{len(ivs)} interview experiences, {len(imgs)} images", "",
         "Personal copy of paid content. Do not share or commit.", "", "## OA sets", ""]
    L += [f"- [{title(f)}](sets/{f.name})" for f in sets] or ["(none)"]
    L += ["", "## Interview experiences", ""]
    L += [f"- [{title(f)}](interviews/{f.name})" for f in ivs] or ["(none)"]
    (d / "index.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return d / "index.md"


# ---------- tools ----------

mcp = FastMCP("oahelper")


@mcp.tool()
def oahelper_search(company: str) -> str:
    """Find a company's OA question sets on OAHelper by name (e.g. "Amazon", "Kickdrum").

    Lists each set with its company_ref, date and question counts. To download a
    company's sets into the offline library, use oahelper_sync.
    """
    sets = _search(company)
    if not sets:
        return f"No OAHelper sets found for '{company}'."
    groups = {}
    for s in sets:
        groups.setdefault(s.get("unique_company_name") or "?", []).append(s)
    L = [f"{len(sets)} sets for '{company}':"]
    for co, ss in groups.items():
        L += ["", f"## {co} ({len(ss)} sets)"]
        for s in sorted(ss, key=lambda s: s.get("date") or "", reverse=True):
            L.append(f"- {s.get('date')}  {s.get('name')}  `{s.get('id')}`  "
                     f"{s.get('question_count')} Qs (premium {s.get('premium_question_count')}), "
                     f"{_join(s.get('question_types'))}")
    return "\n".join(L)


@mcp.tool()
def oahelper_sync(company: str, max_items: int = 20, include_images: bool = False,
                  include_interviews: bool = True) -> str:
    """Download one company's OAHelper content into the offline library, newest sets first:
    set lists, every question statement, MCQ answers, and interview experiences.

    Makes at most max_items live requests per call, then says how much is left, so call it
    again to continue. Already-saved items cost nothing. Official solutions are NOT fetched
    here because each one uses the account's daily solution quota; use oahelper_solution.
    Read the result from library/<company>/index.md.
    """
    start = _live
    budget = lambda: _live - start < max_items
    sets = _search(company)
    if not sets:
        return f"No OAHelper sets found for '{company}'."
    names = [s.get("unique_company_name") for s in sets]
    co = next((n for n in names if _norm(n) == _norm(company)), None) or \
         max(set(names), key=names.count)
    sets = sorted([s for s in sets if s.get("unique_company_name") == co],
                  key=lambda s: s.get("date") or "", reverse=True)
    done = pending = img_skipped = 0
    errors = []
    for s in sets:
        if not budget():
            pending += s.get("question_count") or 0
            continue
        try:
            qs = _set_questions(s["id"])
        except RuntimeError as e:
            errors.append(f"set {s.get('name')}: {e}")
            continue
        for x in qs:
            ref = x["id"]
            if _peek("question", ref) is None and not budget():
                pending += 1
                continue
            try:
                q, _ = _question(ref)
                if q.get("question_type") == "mcq" and budget():
                    _mcq(ref)
                if include_images and q.get("has_image"):
                    img_skipped += _images(co, ref, budget)[1]
                _write_question(co, ref)
                done += 1
            except RuntimeError as e:
                errors.append(f"{x.get('title')} `{ref}`: {e}")
                if "cap reached" in str(e) or "session rejected" in str(e):
                    break
        _write_set(co, s, qs)
    ivs = []
    if include_interviews and budget():
        try:
            ivs = _interviews(company)
            _write_interviews(co, ivs)
        except RuntimeError as e:
            errors.append(f"interviews: {e}")
    idx = _write_index(co)
    L = [f"{co}: {len(sets)} sets, {done} questions saved this run, {len(ivs)} interview "
         f"experiences, {_live - start} live requests.",
         f"library: {idx.parent}",
         f"index: {idx}"]
    if pending or img_skipped:
        L.append(f"NOT DONE: {pending} questions{f' and {img_skipped} images' if img_skipped else ''} "
                 f"left. Call oahelper_sync again to continue.")
    else:
        L.append("Complete for this company.")
    if errors:
        L += ["errors:"] + [f"- {e}" for e in errors[:8]]
    return "\n".join(L)


@mcp.tool()
def oahelper_company(slug_or_url: str, refresh: bool = False) -> str:
    """List one OAHelper set page by slug or URL, e.g. "kickdrum-mcq24sep" or
    https://www.oahelper.in/company-questions/kickdrum-mcq24sep. Returns question refs
    for oahelper_question. For a company by name, use oahelper_search or oahelper_sync.
    """
    slug = _slug(slug_or_url)
    q = urllib.parse.urlencode({"action": "get_company_page", "v": 5, "slug": slug})
    d, hit = _cached("company", slug, lambda: _fetch(f"/company?{q}")["data"], refresh)
    c, qs = d.get("company", {}), d.get("questions", [])
    co = c.get("unique_company_name") or _slugify(slug)
    _write_set(co, c, qs)
    _write_index(co)
    L = [f"# {c.get('name', slug)}" + ("  (cached)" if hit else ""),
         f"company_ref: {c.get('id')}  |  date: {c.get('date')}  |  questions: {c.get('question_count')} "
         f"(free {c.get('free_question_count')}, premium {c.get('premium_question_count')})",
         f"types: {_join(c.get('question_types'))}  |  roles: {_join(c.get('roles'))}  |  "
         f"colleges: {_join(c.get('colleges'))}", ""]
    for i, x in enumerate(qs, 1):
        L.append(f"{i}. `{x.get('id')}` {x.get('title')}  ({x.get('question_type')}, "
                 f"difficulty {x.get('difficulty_score')}{', premium' if x.get('premium_required') else ''})")
    return "\n".join(L)


@mcp.tool()
def oahelper_question(ref_or_url: str, include_images: bool = False,
                      include_community: bool = False, refresh: bool = False) -> str:
    """Read one OAHelper question: full statement, MCQ answers with explanations (for MCQ
    sets), any saved official solution, and optionally community solutions and images.
    Saves it to the offline library.

    ref_or_url: a question ref like "MjM3OHww" or a https://www.oahelper.in/problems/... URL.
    """
    ref = _qref(ref_or_url)
    q, _ = _question(ref, refresh)
    co = q.get("unique_company_name") or "unknown"
    notes = []
    if q.get("question_type") == "mcq":
        try:
            _mcq(ref, refresh)
        except RuntimeError as e:
            notes.append(f"MCQ answers unavailable: {e}")
    if include_community:
        try:
            _community(ref, refresh)
        except RuntimeError as e:
            notes.append(f"community solutions unavailable: {e}")
    if include_images and q.get("has_image"):
        _images(co, ref)
    text = _write_question(co, ref)
    _write_index(co)
    return text + ("\n" + "\n".join(notes) if notes else "")


@mcp.tool()
def oahelper_solution(ref_or_url: str, language: str = "cpp") -> str:
    """Fetch OAHelper's official solution for one coding question (language: cpp, python,
    java). Each new fetch uses one of the account's limited daily solution requests, so
    only call this when the user asks for the official solution. Saved solutions are free.
    """
    ref = _qref(ref_or_url)
    q = urllib.parse.urlencode({"action": "get_solution", "user_id": _whoami()["user_id"],
                                "question_id": _num(ref), "language": language})
    s, hit = _cached("solution", f"{ref}-{language}",
                     lambda: _fetch(f"/solution-requests?{q}")["data"])
    if _peek("question", ref) is None:
        _question(ref)
    co = (_peek("question", ref) or {}).get("unique_company_name") or "unknown"
    _write_question(co, ref)
    quota = "already saved, no quota used" if hit else \
        "no daily limit on your plan" if s.get("daily_limit") == -1 else \
        f"quota: {s.get('remaining_requests')} of {s.get('daily_limit')} left today"
    return f"## Official solution ({s.get('language') or language})  [{quota}]\n\n" \
           f"```{language}\n{s.get('solution')}\n```"


@mcp.tool()
def oahelper_interviews(company: str, pages: int = 2) -> str:
    """Interview experiences for a company from OAHelper (12 per page, most relevant first).
    Saves each full write-up to library/<company>/interviews/ and returns a short list;
    read the saved files for the full text.
    """
    items = _interviews(company, pages)
    sets = _peek("search", company.lower()) or []
    co = next((s.get("unique_company_name") for s in sets
               if _norm(s.get("unique_company_name")) == _norm(company)), None) or _slugify(company)
    _write_interviews(co, items)
    _write_index(co)
    if not items:
        return f"No interview experiences matched '{company}'."
    L = [f"{len(items)} interview experiences for '{company}', saved to {LIB / co / 'interviews'}:", ""]
    for x in items:
        L.append(f"- {x.get('interview_date') or '?'}  {x.get('role') or '?'}  |  "
                 f"{x.get('result') or '?'}  |  {x.get('difficulty') or '?'}  |  "
                 f"topics: {(_text(x.get('topics_asked')) or 'UNKNOWN')[:150]}")
    return "\n".join(L)


@mcp.tool()
def oahelper_offline(company: str = "") -> str:
    """What is saved offline. No network call. With no company, lists every company in the
    library; with a company, returns its index (sets, interviews, counts)."""
    if not LIB.exists():
        return "Library is empty."
    if not company:
        L = []
        for d in sorted(p for p in LIB.iterdir() if p.is_dir()):
            n = lambda sub: len(list((d / sub).glob("*"))) if (d / sub).exists() else 0
            L.append(f"- {d.name}: {n('sets')} sets, {n('questions')} questions, "
                     f"{n('interviews')} interviews, {n('images')} images")
        return f"Offline library at {LIB}:\n" + ("\n".join(L) or "(empty)")
    d = LIB / _slugify(company)
    if not d.exists():
        d = next((p for p in LIB.iterdir() if _norm(p.name) == _norm(company)), d)
    if not d.exists():
        return f"Nothing saved for '{company}'. Use oahelper_sync to fetch it."
    return _write_index(d.name).read_text(encoding="utf-8")


@mcp.tool()
def oahelper_status(online: bool = False) -> str:
    """Session and usage status. online=true also checks Pro status with the site
    (one request); by default no network call is made."""
    env = _env()
    try:
        used = json.loads((CACHE / "_usage.json").read_text(encoding="utf-8")).get(date.today().isoformat(), 0)
    except (OSError, ValueError):
        used = 0
    cap = int(env.get("OAHELPER_DAILY_CAP") or DEFAULT_DAILY_CAP)
    L = [f"cookie set: {'yes' if env.get('OAHELPER_COOKIE') else 'no'}  |  "
         f"bearer set: {'yes' if env.get('OAHELPER_BEARER') else 'no'}",
         f"live requests today: {used}/{cap}",
         f"library: {LIB}"]
    if online:
        try:
            me = _whoami()
            L.append(f"session valid  |  Pro: {'yes' if me['is_premium'] else 'no'}"
                     f"{' (' + me['plan'] + ')' if me.get('plan') else ''}")
        except RuntimeError as e:
            L.append(f"session check failed: {e}")
    return "\n".join(L)


if __name__ == "__main__":
    mcp.run()
