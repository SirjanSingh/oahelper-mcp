"""Part of oahelper-mcp by Sirjan Singh (https://github.com/SirjanSingh/oahelper-mcp).

Summarise the /api/proxy calls in a browser HAR without leaking anything sensitive.

Prints, per distinct method + path + action: query parameter names (values only for
safe keys), request body key names, response status, and the response JSON shape
(keys, types, array lengths). Never prints header values or response values.

Usage:
    python har_endpoints.py www.oahelper.in.har
"""
import json, re, sys
from collections import OrderedDict
from urllib.parse import urlsplit, parse_qsl

SAFE = re.compile(r"^(action|slug|v|page|limit|offset|per_page|page_size|sort|order|q|query|search|"
                  r"type|tab|filter|status|[a-z_]*_ref|company|company_name|unique_company_name)$")
SECRET = re.compile(r"token|session|device|signature|email|user|password|auth|cookie|phone", re.I)
SENSITIVE_HEADERS = {"cookie", "set-cookie", "authorization"}


def shape(v, depth=0):
    """Type skeleton of a JSON value, no content."""
    if depth >= 3:
        return type(v).__name__
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in list(v.items())[:40]}
    if isinstance(v, list):
        return [f"len={len(v)}", shape(v[0], depth + 1)] if v else ["len=0"]
    return type(v).__name__


def main(path):
    har = json.load(open(path, encoding="utf-8"))
    entries = har["log"]["entries"]
    leaked = set()
    seen = OrderedDict()
    for e in entries:
        req, res = e["request"], e["response"]
        for h in req.get("headers", []) + res.get("headers", []):
            if h["name"].lower() in SENSITIVE_HEADERS and h.get("value"):
                leaked.add(h["name"].lower())
        u = urlsplit(req["url"])
        if "/api/proxy" not in u.path:
            continue
        params = parse_qsl(u.query, keep_blank_values=True)
        action = dict(params).get("action", "")
        key = (req["method"], u.path.split("/api/proxy", 1)[1], action)
        if key in seen:
            seen[key]["count"] += 1
            continue
        qp = [f"{k}={v}" if SAFE.match(k) and not SECRET.search(k) else f"{k}=<{'redacted' if SECRET.search(k) else 'value'}>"
              for k, v in params]
        body_keys = None
        txt = (req.get("postData") or {}).get("text")
        if txt:
            try:
                b = json.loads(txt)
                body_keys = {k: (v if isinstance(v, (str, int)) and SAFE.match(k) and not SECRET.search(k)
                                 else type(v).__name__) for k, v in b.items()} if isinstance(b, dict) else type(b).__name__
            except ValueError:
                body_keys = "non-json"
        resp_shape = None
        ct = res.get("content", {})
        if ct.get("text"):
            try:
                resp_shape = shape(json.loads(ct["text"]))
            except ValueError:
                resp_shape = f"non-json ({ct.get('mimeType')})"
        seen[key] = {"count": 1, "status": res.get("status"), "query": qp,
                     "body": body_keys, "response": resp_shape}

    print(f"HAR entries: {len(entries)}  |  distinct /api/proxy calls: {len(seen)}")
    print("sensitive headers present in file: " + (", ".join(sorted(leaked)) or "none (sanitized)"))
    for (m, p, a), d in seen.items():
        print(f"\n### {m} {p}" + (f"  action={a}" if a else "") + f"  [{d['status']}] x{d['count']}")
        if d["query"]:
            print("query:", "&".join(d["query"]))
        if d["body"] is not None:
            print("body:", json.dumps(d["body"]))
        if d["response"] is not None:
            print("response:", json.dumps(d["response"])[:1500])


if __name__ == "__main__":
    main(sys.argv[1])
