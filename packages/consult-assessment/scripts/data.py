#!/usr/bin/env python3
"""Data analysis for readers. The reader is the analyst; these are its instruments.

  data.py profile <src-id|path>                          # format, columns, types, nulls, ranges, samples
  data.py run <procedure> <src-id|path> [options]        # a standard procedure; output is saved AND registered as a citable source
  data.py procedures                                     # list procedures with their options

Every `run` writes <analysis_dir>/<src>-<procedure>[-<tag>].md: a header naming
the source, procedure, and parameters, then a numbered result table whose first
column `line` is the physical line of that row in the source file, so a finding
can cite both the source row (src-014:L4501) and the analysis (src-031:L12).
The output is registered in the lint registry with kind: analysis and
derived_from: <src>, so validate.py accepts citations into it and coverage
figures show it. Registered outputs are never edited; re-run to regenerate
(a changed file gets a new id, like any source).

Formats: csv / tsv (delimiter sniffed), xlsx (openpyxl, optional), markdown pipe
tables, jsonl. Line numbers are exact for csv/tsv/md/jsonl. xlsx has no lines:
cite the analysis output instead, or export to csv first.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required")

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

NUM_RE = re.compile(r"^\(?-?[$€£]?\s?-?[\d,]*\.?\d+\)?%?$")
DATE_FMTS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M")


# ------------------------------------------------------------------ loading
def load_registry(reg_path):
    return yaml.safe_load(open(reg_path, encoding="utf-8")) or {"sources": []} if reg_path and Path(reg_path).exists() else {"sources": []}


def resolve(ref, reg_path):
    """src-id -> (path, id) via registry; path -> (path, id-or-None)."""
    if re.match(r"^src-\d{3}$", ref):
        reg = load_registry(reg_path)
        e = next((s for s in reg["sources"] if s["id"] == ref and s.get("status") == "active"), None)
        if not e:
            sys.exit(f"{ref} is not an active source in {reg_path}")
        return Path(reg_path).parent / e["file"], ref
    p = Path(ref)
    if not p.exists():
        sys.exit(f"no such file: {ref}")
    reg = load_registry(reg_path)
    sid = next((s["id"] for s in reg["sources"] if s.get("status") == "active"
                and (Path(reg_path).parent / s["file"]).resolve() == p.resolve()), None)
    return p, sid


def input_rows(a, ref):
    """Integrated mode consumes the engine's verified CSV snapshot, never a
    second parser over a subsequently changed file. Record IDs, not lines."""
    if getattr(a, "consult_root", None):
        from consult_bridge import table
        checked = table(a.consult_root, ref)
        for option in ("amount", "date", "by", "key", "seq", "cols"):
            names = getattr(a, option, None)
            if names:
                missing = [name.strip() for name in names.split(",") if name.strip() not in checked["header"]]
                if missing:
                    sys.exit(f"{ref}: unknown columns for --{option}: {missing}")
        if not hasattr(a, "_inputs"):
            a._inputs = {}
        previous = a._inputs.get(checked["id"])
        if previous and previous["hash"] != checked["hash"]:
            sys.exit(f"input changed during analysis: {checked['id']}")
        a._inputs[checked["id"]] = {"id": checked["id"], "hash": checked["hash"]}
        return Path(a.consult_root) / checked["file"], checked["id"], [(i, dict(zip(checked["header"], values))) for i, values in enumerate(checked["records"], 1)]
    path, sid = resolve(ref, a.registry)
    return path, sid, list(read_table(path))


def read_table(path):
    """Yield (line_no, row_dict). line_no is the physical line the row ends on (1-based)."""
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            sys.exit("openpyxl is required for xlsx; or export the sheet to csv")
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(next(rows), 1)]
        for i, r in enumerate(rows, 2):
            if any(c is not None and str(c).strip() for c in r):
                yield i, {h: ("" if c is None else str(c)) for h, c in zip(header, r)}
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if ext == ".jsonl":
        for i, line in enumerate(text.split("\n"), 1):
            if line.strip():
                yield i, {k: ("" if v is None else str(v)) for k, v in json.loads(line).items()}
        return
    if ext in (".md", ".markdown") or (text.lstrip().startswith("|") and "|---" in text):
        header, sep_seen = None, False
        for i, line in enumerate(text.split("\n"), 1):
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = cells
                continue
            if not sep_seen and all(re.match(r"^:?-+:?$", c) for c in cells if c):
                sep_seen = True
                continue
            yield i, dict(zip(header, cells))
        return
    # csv / tsv / txt: sniff delimiter
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        dialect = csv.excel
    rdr = csv.reader(text.splitlines(keepends=True), dialect)
    header = None
    for row in rdr:
        if header is None:
            if not any(c.strip() for c in row):
                continue
            header = [c.strip() or f"col{i}" for i, c in enumerate(row, 1)]
            continue
        if not any(c.strip() for c in row):
            continue
        yield rdr.line_num, dict(zip(header, row))


def to_num(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace(" ", "")
    if not t or t in ("-", "—"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%")
    try:
        v = float(t)
        return -v if neg else v
    except ValueError:
        return None


def to_date(s):
    if not s:
        return None
    t = str(s).strip()
    for f in DATE_FMTS:
        try:
            return datetime.strptime(t, f).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(t[:19]).date()
    except ValueError:
        return None


def guess_type(values):
    vals = [v for v in values if str(v).strip()]
    if not vals:
        return "empty"
    n = sum(1 for v in vals if to_num(v) is not None)
    d = sum(1 for v in vals if to_date(v) is not None)
    if d / len(vals) > 0.8:
        return "date"
    if n / len(vals) > 0.8:
        return "number"
    if len(set(vals)) <= 2 and all(str(v).lower() in ("y", "n", "yes", "no", "true", "false", "0", "1") for v in vals):
        return "bool"
    return "text"


def md(headers, rows):
    # Keep a multiline CSV field within one displayed table row; the source
    # record locator still returns its full original value when inspected.
    cell = lambda value: str(value).replace("\r", "\\r").replace("\n", "\\n").replace("|", "\\|")
    out = ["| " + " | ".join(cell(h) for h in headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(cell(c) for c in r) + " |")
    return "\n".join(out)


def fmt(v):
    return f"{v:,.2f}" if isinstance(v, float) else str(v)


# ------------------------------------------------------------------ profile
def cmd_profile(a):
    path, sid, rows = input_rows(a, a.src)
    unit = "R" if a.consult_root else "L"
    if not rows:
        print(f"{path}: no tabular rows found (is there a header?)")
        return
    cols = list(rows[0][1].keys())
    out = [f"# Profile — {sid or path.name}", "",
           f"file: `{path.name}`  format: `{path.suffix.lstrip('.') or 'txt'}`  data rows: **{len(rows)}**  "
           f"first data {'record' if a.consult_root else 'line'}: {unit}{rows[0][0]}  last: {unit}{rows[-1][0]}  columns: {len(cols)}", ""]
    table = []
    for c in cols:
        vals = [r[1].get(c, "") for r in rows]
        t = guess_type(vals)
        nonblank = [v for v in vals if str(v).strip()]
        blank = len(vals) - len(nonblank)
        distinct = len(set(nonblank))
        if t == "number":
            nums = [to_num(v) for v in nonblank if to_num(v) is not None]
            rng = f"min {fmt(min(nums))} · max {fmt(max(nums))} · sum {fmt(sum(nums))}" if nums else ""
        elif t == "date":
            ds = [to_date(v) for v in nonblank if to_date(v)]
            rng = f"{min(ds)} → {max(ds)}" if ds else ""
        else:
            top = Counter(nonblank).most_common(3)
            rng = "; ".join(f"{k[:30]} ({n})" for k, n in top)
        table.append([c, t, blank, distinct, rng])
    out.append(md(["column", "type", "blank", "distinct", "range / top values"], table))
    out += ["", "## First 5 rows", "", md(["record" if a.consult_root else "line"] + cols, [[ln] + [str(r.get(c, ""))[:40] for c in cols] for ln, r in rows[:5]])]
    text = "\n".join(out) + "\n"
    print(text)
    if a.analysis_dir and sid and not a.consult_root:
        p = Path(a.analysis_dir) / f"{sid}-profile.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"(saved {p}; profiles are not registered - they are orientation, not evidence)", file=sys.stderr)


# ------------------------------------------------------------------ procedures
PROCS = {}


def proc(name, help_, opts):
    def deco(fn):
        PROCS[name] = (fn, help_, opts)
        return fn
    return deco


def need(a, *names):
    missing = [n for n in names if not getattr(a, n, None)]
    if missing:
        sys.exit(f"procedure needs --{' --'.join(missing)}")


@proc("outliers", "largest absolute values, and round amounts (multiples of --round)", "--amount COL [--top 25] [--round 1000]")
def p_outliers(rows, a):
    need(a, "amount")
    vals = [(ln, r, to_num(r.get(a.amount))) for ln, r in rows]
    vals = [(ln, r, v) for ln, r, v in vals if v is not None]
    top = sorted(vals, key=lambda x: -abs(x[2]))[:a.top]
    rnd = [(ln, r, v) for ln, r, v in vals if v and abs(v) >= a.round and abs(v) % a.round == 0]
    sections = [("Largest by absolute amount", top), (f"Round amounts (multiples of {a.round:,})", rnd[:a.top])]
    return sections, {"rows": len(vals), "round_count": len(rnd), "round_total": sum(v for _, _, v in rnd)}


@proc("timing", "weekend / outside-period / after-cutoff postings", "--date COL [--period-start D] [--period-end D] [--cutoff D]")
def p_timing(rows, a):
    need(a, "date")
    ps, pe, co = (to_date(a.period_start), to_date(a.period_end), to_date(a.cutoff))
    weekend, outside, after, undated = [], [], [], []
    for ln, r in rows:
        d = to_date(r.get(a.date))
        if d is None:
            undated.append((ln, r, r.get(a.date, "")))
            continue
        if d.weekday() >= 5:
            weekend.append((ln, r, d))
        if (ps and d < ps) or (pe and d > pe):
            outside.append((ln, r, d))
        if co and d > co:
            after.append((ln, r, d))
    secs = [("Weekend postings", weekend), ("Unparseable dates", undated)]
    if ps or pe:
        secs.append((f"Outside period {ps or ''}..{pe or ''}", outside))
    if co:
        secs.append((f"After cutoff {co}", after))
    return secs, {"rows": len(rows), "weekend": len(weekend), "outside": len(outside), "after_cutoff": len(after), "undated": len(undated)}


@proc("group", "count and sum by one or two columns", "--by COL[,COL2] [--amount COL] [--top 50]")
def p_group(rows, a):
    need(a, "by")
    keys = [k.strip() for k in a.by.split(",")]
    agg = defaultdict(lambda: {"n": 0, "sum": 0.0, "first": None})
    for ln, r in rows:
        k = tuple(r.get(c, "") for c in keys)
        g = agg[k]
        g["n"] += 1
        if a.amount:
            v = to_num(r.get(a.amount))
            g["sum"] += v or 0
        g["first"] = g["first"] or ln
    items = sorted(agg.items(), key=lambda kv: -kv[1]["n"])[:a.top]
    rows_out = [(g["first"], dict(zip(keys, k)), (g["n"], g["sum"])) for k, g in items]
    return [("By " + ", ".join(keys), rows_out)], {"groups": len(agg), "rows": len(rows)}


@proc("duplicates", "rows sharing the same values on key columns", "--key COL[,COL2] [--top 50]")
def p_duplicates(rows, a):
    need(a, "key")
    keys = [k.strip() for k in a.key.split(",")]
    seen = defaultdict(list)
    for ln, r in rows:
        seen[tuple(r.get(c, "").strip() for c in keys)].append((ln, r))
    dups = [(k, v) for k, v in seen.items() if len(v) > 1 and any(x for x in k)]
    out = []
    for k, v in sorted(dups, key=lambda kv: -len(kv[1]))[:a.top]:
        for ln, r in v:
            out.append((ln, r, f"×{len(v)}"))
    return [("Duplicate keys " + ", ".join(keys), out)], {"duplicate_groups": len(dups), "rows_involved": sum(len(v) for _, v in dups)}


@proc("gaps", "gaps in a numeric sequence (check numbers, JE numbers)", "--seq COL")
def p_gaps(rows, a):
    need(a, "seq")
    def seqnum(x):
        m = re.findall(r"\d+", str(x or ""))
        return int(m[-1]) if m else None
    nums = sorted({n for ln, r in rows if (n := seqnum(r.get(a.seq))) is not None})
    gaps = [(nums[i] + 1, nums[i + 1] - 1) for i in range(len(nums) - 1) if nums[i + 1] - nums[i] > 1]
    out = [(0, {"gap_from": g0, "gap_to": g1, "missing": g1 - g0 + 1}, "") for g0, g1 in gaps[:200]]
    return [("Sequence gaps in " + a.seq, out)], {"min": nums[0] if nums else None, "max": nums[-1] if nums else None, "gaps": len(gaps), "missing_total": sum(g1 - g0 + 1 for g0, g1 in gaps)}


@proc("aging", "bucket rows by age of a date column as of --asof", "--date COL --asof D [--amount COL]")
def p_aging(rows, a):
    need(a, "date", "asof")
    asof = to_date(a.asof) or sys.exit("bad --asof")
    buckets = [("0-30", 0, 30), ("31-60", 31, 60), ("61-90", 61, 90), ("91-180", 91, 180), ("181-365", 181, 365), ("365+", 366, 10**9)]
    agg = {b[0]: {"n": 0, "sum": 0.0, "first": None} for b in buckets}
    old = []
    for ln, r in rows:
        d = to_date(r.get(a.date))
        if not d:
            continue
        age = (asof - d).days
        for name, lo, hi in buckets:
            if lo <= age <= hi:
                agg[name]["n"] += 1
                agg[name]["sum"] += (to_num(r.get(a.amount)) or 0) if a.amount else 0
                agg[name]["first"] = agg[name]["first"] or ln
                if lo >= 91:
                    old.append((ln, r, f"{age}d"))
                break
    summary = [(g["first"] or 0, {"bucket": b, "count": g["n"], "sum": fmt(g["sum"])}, "") for b, g in agg.items()]
    return [("Aging as of " + str(asof), summary), ("Items older than 90 days", old[:a.top])], {"rows": len(rows)}


@proc("blanks", "rows with blank required columns", "--cols COL[,COL2] [--top 50]")
def p_blanks(rows, a):
    need(a, "cols")
    cols = [c.strip() for c in a.cols.split(",")]
    out = [(ln, r, ", ".join(c for c in cols if not str(r.get(c, "")).strip())) for ln, r in rows if any(not str(r.get(c, "")).strip() for c in cols)]
    return [("Rows with blanks in " + ", ".join(cols), out[:a.top])], {"rows": len(rows), "blank_rows": len(out)}


@proc("filter", "rows where a column equals / contains / exceeds a value", "--where COL=VAL | COL~TEXT | COL>NUM | COL<NUM [--top 100]")
def p_filter(rows, a):
    need(a, "where")
    m = re.match(r"^(.+?)([=~<>])(.*)$", a.where) or sys.exit("--where COL=VAL | COL~TEXT | COL>NUM | COL<NUM")
    col, op, val = m.group(1).strip(), m.group(2), m.group(3).strip()
    out = []
    for ln, r in rows:
        v = str(r.get(col, ""))
        ok = (v.strip().lower() == val.lower() if op == "=" else val.lower() in v.lower() if op == "~"
              else (to_num(v) or 0) > float(val) if op == ">" else (to_num(v) or 0) < float(val))
        if ok:
            out.append((ln, r, ""))
    return [(f"Rows where {a.where}", out[:a.top])], {"rows": len(rows), "matched": len(out)}


@proc("recon", "compare two sources on a key: present in one but not the other, amount mismatches", "--other SRC --key COL [--amount COL]")
def p_recon(rows, a):
    need(a, "other", "key")
    _, _, other_rows = input_rows(a, a.other)
    if a.consult_root:
        for source_id, values in [(a.src, rows), (a.other, other_rows)]:
            keys = [str(r.get(a.key, "")).strip() for _, r in values]
            if any(not key for key in keys) or len(keys) != len(set(keys)):
                sys.exit(f"recon: {source_id} needs a nonempty unique {a.key} key; do not silently collapse or omit records")
    other = {str(r.get(a.key, "")).strip(): (ln, r) for ln, r in other_rows}
    mine = {str(r.get(a.key, "")).strip(): (ln, r) for ln, r in rows}
    only_a = [(ln, r, "") for k, (ln, r) in mine.items() if k and k not in other]
    only_b = [(ln, r, "") for k, (ln, r) in other.items() if k and k not in mine]
    mism = []
    if a.amount:
        for k, (ln, r) in mine.items():
            if k in other:
                va, vb = to_num(r.get(a.amount)), to_num(other[k][1].get(a.amount))
                if va is not None and vb is not None and abs(va - vb) > 0.005:
                    mism.append((ln, r, f"other={fmt(vb)} ({a.other}:{'R' if a.consult_root else 'L'}{other[k][0]})"))
    return [("Only in this source", only_a[:a.top]), (f"Only in {a.other}", only_b[:a.top]), ("Amount mismatches", mism[:a.top])], \
        {"this": len(mine), "other": len(other), "only_this": len(only_a), "only_other": len(only_b), "mismatches": len(mism)}


# ------------------------------------------------------------------ run + register
def register_output(reg_path, out_path, sid, procedure, params):
    reg = load_registry(reg_path)
    rel = os.path.relpath(out_path.resolve(), Path(reg_path).resolve().parent)
    h = hashlib.sha256(out_path.read_bytes()).hexdigest()[:16]
    for s in reg["sources"]:
        if s.get("sha") == h and s.get("status") == "active":
            return s["id"]
    for s in reg["sources"]:
        if s.get("file") == rel and s.get("status") == "active":
            s["status"] = "superseded"
    nums = [int(s["id"].split("-")[1]) for s in reg["sources"]]
    new_id = f"src-{(max(nums) + 1 if nums else 1):03d}"
    text = out_path.read_text(encoding="utf-8")
    reg["sources"].append({"id": new_id, "file": rel, "sha": h, "lines": text.count("\n") + 1, "words": len(text.split()),
                           "status": "active", "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "kind": "analysis", "derived_from": sid, "procedure": procedure, "params": params,
                           "note": f"{procedure} on {sid}"})
    with open(reg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(reg, f, sort_keys=False, allow_unicode=True)
    return new_id


def cmd_run(a):
    if a.procedure not in PROCS:
        sys.exit(f"unknown procedure {a.procedure}; one of {list(PROCS)}")
    fn, help_, opts = PROCS[a.procedure]
    path, sid, rows = input_rows(a, a.src)
    if not sid:
        sys.exit("run needs a registered source (src-id) so the output can be registered with provenance")
    if not rows:
        sys.exit(f"{path}: no tabular rows found")
    sections, stats = fn(rows, a)
    params = {k: v for k, v in vars(a).items() if k in ("amount", "date", "by", "key", "seq", "cols", "where", "other", "asof",
                                                          "period_start", "period_end", "cutoff", "round", "top") and v not in (None, "")}
    out = [f"# {a.procedure} — {sid}", "", f"source: {sid} (`{path.name}`, {len(rows)} data rows)  procedure: `{a.procedure}`  "
           f"params: `{json.dumps(params)}`  run: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", "",
           "stats: " + ", ".join(f"{k}={fmt(v) if isinstance(v, float) else v}" for k, v in stats.items()), ""]
    for title, items in sections:
        out += [f"## {title} ({len(items)})", ""]
        if not items:
            out += ["(none)", ""]
            continue
        cols = list(items[0][1].keys())
        show = cols[:10]
        rows_out = []
        for ln, r, extra in items:
            cells = [str(r.get(c, ""))[:40] for c in show]
            if isinstance(extra, tuple):  # group: (n, sum)
                cells = [str(r.get(c, ""))[:40] for c in cols] + [extra[0], fmt(extra[1])]
                hdr = cols + ["count", "sum"]
            else:
                hdr = show + (["note"] if extra != "" or any(e != "" for _, _, e in items) else [])
                if "note" in hdr:
                    cells.append(str(extra))
            row_source = a.other if a.consult_root and a.procedure == "recon" and title == f"Only in {a.other}" else sid
            locator = f"{row_source}:R{ln}" if a.consult_root else f"L{ln}"
            rows_out.append([locator if ln else ""] + cells)
        out += [md(["source record" if a.consult_root else "line"] + hdr, rows_out), ""]
    text = "\n".join(out)
    if a.consult_root:
        from consult_bridge import publish
        from uuid import uuid4
        inputs = list(a._inputs.values())
        run_id = uuid4().hex
        text += "\n\n## Reproducibility\n\n" + json.dumps({"run_id": run_id, "inputs": inputs, "procedure": a.procedure, "params": params,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "locator": "CSV data record, one-based after header; blank physical lines skipped"}, indent=2) + "\n"
        outp = Path(a.analysis_dir) / f"{sid}-{a.procedure}-{run_id}.md"
        outp.parent.mkdir(parents=True, exist_ok=True)
        with outp.open("x", encoding="utf-8") as output:
            output.write(text)
        # A card is discovery metadata, never registered as evidence itself.
        card = {"title": f"{a.procedure} on {sid}", "kind": "analysis", "summary": f"Versioned {a.procedure} output; inputs and parameters recorded", "keyItems": list(stats)}
        outp.with_suffix(".card.yaml").write_text(yaml.safe_dump(card, sort_keys=False), encoding="utf-8")
        try:
            registered = publish(a.consult_root, outp, a.intent, inputs)
        except (ValueError, OSError) as exc:
            sys.exit(f"Publication failed; unregistered artifact preserved at {outp}: {exc}")
        print(text)
        print(f"\n→ saved and registered as {registered['id']}: {outp}\n  cite CSV records as {sid}:R<number> and analysis lines as {registered['id']}:L<line>", file=sys.stderr)
        return
    tag = f"-{a.tag}" if a.tag else ""
    outp = Path(a.analysis_dir) / f"{sid}-{a.procedure}{tag}.md"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(text, encoding="utf-8")
    new_id = register_output(a.registry, outp, sid, a.procedure, params)
    print(text)
    print(f"\n→ saved and registered as {new_id}: {outp}\n  cite source rows as {sid}:L<line> and this analysis as {new_id}:L<line>", file=sys.stderr)


def cmd_procedures(a):
    for name, (fn, help_, opts) in PROCS.items():
        print(f"{name:<11} {help_}\n{'':<11} {opts}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", default=os.environ.get("ASSESS_REGISTRY"))
    p.add_argument("--consult-root")
    p.add_argument("--intent", action="append", default=[])
    p.add_argument("--analysis-dir", default=os.environ.get("ASSESS_ANALYSIS_DIR", "analysis"))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("profile"); s.add_argument("src"); s.set_defaults(fn=cmd_profile)
    s = sub.add_parser("procedures"); s.set_defaults(fn=cmd_procedures)
    s = sub.add_parser("run"); s.add_argument("procedure"); s.add_argument("src")
    for o in ("--amount", "--date", "--by", "--key", "--seq", "--cols", "--where", "--other", "--asof", "--period-start", "--period-end", "--cutoff", "--tag"):
        s.add_argument(o)
    s.add_argument("--top", type=int, default=25); s.add_argument("--round", type=float, default=1000)
    s.set_defaults(fn=cmd_run)
    a = p.parse_args()
    if a.consult_root:
        if a.registry:
            p.error("CONSULT mode cannot use a standalone registry (including ASSESS_REGISTRY)")
        a.consult_root = str(Path(a.consult_root).resolve())
        if a.cmd == "run":
            if not a.intent or any(not value.strip() for value in a.intent):
                p.error("integrated analysis requires --intent for genuine capture targets")
            try:
                Path(a.analysis_dir).resolve().relative_to((Path(a.consult_root) / "_synthesis").resolve())
            except ValueError:
                p.error("integrated analysis-dir must be under engagement _synthesis")
            if a.top < 1:
                p.error("--top must be positive")
    if a.cmd in ("profile", "run") and not a.registry and re.match(r"^src-\d{3}$", a.src):
        sys.exit("--registry (or ASSESS_REGISTRY) is required to resolve src ids")
    try:
        a.fn(a)
    except (ValueError, OSError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
