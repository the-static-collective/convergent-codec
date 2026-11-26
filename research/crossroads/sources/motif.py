def rpc_error(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def result(id_, payload):
    return {"jsonrpc": "2.0", "id": id_, "result": payload}


def bounded_case(args):
    case = args.get("case")
    if not isinstance(case, dict):
        raise ValueError("'case' must be an object")
    if case.get("schema", "motif.reason-case/v1") != "motif.reason-case/v1":
        raise ValueError("Unknown case schema; use motif.reason-case/v1")
    validate_case(case)
    # Avoid extremely lengthy caller-provided witness labels and messages.
    # A source field in a model is not proof of that source's real identity.
    return case


def public_branch_leads(args):
    query = args.get("query", "")
    page = args.get("page", 1)
    limit = args.get("limit", 12)
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError("query must be a short string")
    if type(page) is not int or not 1 <= page <= 50:
        raise ValueError("page must be 1–50")
    if type(limit) is not int or not 1 <= limit <= 30:
        raise ValueError("limit must be 1–30")
    url = GITHUB_BRANCHES + "?per_page=100&page=" + str(page)
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": "MOTIF-Native-Readonly-MCP/0.2"}
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            rows = json.loads(response.read(110_001))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        raise HoldError("Public GitHub branch source unavailable or rate limited: HOLD") from exc
    if not isinstance(rows, list) or len(rows) > 100:
        raise HoldError("Unexpected or excessive branch page: HOLD")
    heads = []
    seen = set()
    for row in rows:
        ref = row.get("name") if isinstance(row, dict) else None
        sha = row.get("commit", {}).get("sha") if isinstance(row, dict) and isinstance(row.get("commit"), dict) else None
        if not valid_ref(ref) or not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise HoldError("Invalid source pointer returned by remote: HOLD")
        if ref in seen:
            raise HoldError("Duplicate source pointer returned: HOLD")
        seen.add(ref)
        heads.append(Pointer(ref, sha, "github-public-api"))
    leads = (suggest(query, heads, limit=limit) if query.strip() else
             [p.as_dict() for p in sorted(heads, key=lambda p: p.ref)[:limit]])
    return {
        "schema": "motif.native-mcp.public-branch-leads/v1",
        "repository": CANONICAL_REPO,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "page": page,
        "page_size": len(rows),
        "possible_next_page": len(rows) == 100,
        "completeness": "SINGLE_GITHUB_PAGE_NOT_WHOLE_FOREST",
        "leads": leads,
        "source_only": True,
        "execution": "NONE",
        "merge": "NONE",
        "authority": "NONE",
        "note": "Public pointer discovery only. Query is lexical; no branches were read, executed, imported or promoted.",
    }
