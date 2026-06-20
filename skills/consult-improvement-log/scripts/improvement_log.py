#!/usr/bin/env python3
"""improvement_log_sync.py

JSON source-of-truth <-> Excel/CSV sync utility for the Improvement Log.

Commands:
  build-xlsx   Build an Excel review workbook from JSON.
  update-json  Merge a CSV review file back into JSON.
  remove       Archive or hard-delete records by ID.

Removal behavior:
  - Safe removal/archive: set record_status=archived, or use remove --archive.
  - Hard delete from CSV: set record_status=deleted_candidate and pass --apply-deletes.
  - Hard delete missing rows: pass --delete-missing to update-json. Use carefully.
  - Hard delete by ID: use remove without --archive.
"""
from __future__ import annotations

import argparse, csv, json, re, shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

DEFAULT_RECORD_FIELDS = [
    "id", "date_identified", "source", "l1_cycle", "l2_process",
    "observation_pain_point", "root_cause", "recommended_action", "impact_type",
    "estimated_impact_benefit", "effort", "priority", "owner", "phase",
    "escalation_status", "process_owner_contacts", "date_updated", "notes_next_step",
    "record_status", "review_status", "requires_human_review", "last_modified_by",
    "last_modified_at", "change_notes",
]
PROTECTED_FIELDS = {"id"}
DATE_FIELDS = {"date_identified", "date_updated"}
BOOL_FIELDS = {"requires_human_review"}
DELETE_STATUSES = {"deleted_candidate", "delete", "deleted", "remove", "removed"}
ARCHIVE_STATUSES = {"archived", "inactive"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_header(header: str) -> str:
    h = str(header or "").strip().replace("\ufeff", "")
    mapping = {
        "ID": "id", "Date Identified": "date_identified", "Source": "source",
        "L1 Cycle": "l1_cycle", "L2 Process": "l2_process",
        "Observation / Pain Point": "observation_pain_point", "Root Cause": "root_cause",
        "Recommended Action": "recommended_action", "Impact Type": "impact_type",
        "Est. Impact / Benefit": "estimated_impact_benefit", "Effort": "effort",
        "Priority": "priority", "Owner": "owner", "Phase": "phase",
        "Escalation Status": "escalation_status", "Process Owner Contact(s)": "process_owner_contacts",
        "Date Updated": "date_updated", "Notes / Next Step": "notes_next_step",
    }
    if h in mapping:
        return mapping[h]
    h = h.replace("/", " ").replace("&", " and ")
    return re.sub(r"[^0-9A-Za-z]+", "_", h).strip("_").lower()


def load_source_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("JSON must be an object with a top-level records list.")
    ids = [r.get("id") for r in data["records"]]
    if any(not x for x in ids):
        raise ValueError("Every record must have a non-empty id.")
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        raise ValueError(f"Duplicate IDs in JSON: {dupes}")
    return data


def field_order(data: Dict[str, Any]) -> List[str]:
    schema_fields = list((data.get("schema", {}).get("fields", {}) or {}).keys())
    record_fields = []
    for rec in data.get("records", []):
        for key in rec:
            if key not in record_fields:
                record_fields.append(key)
    out = []
    for key in DEFAULT_RECORD_FIELDS + schema_fields + record_fields:
        if key not in out:
            out.append(key)
    return out


def clean_value(value: Any, field: str) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    if field in BOOL_FIELDS:
        txt = str(value).strip().lower()
        if txt in {"true", "yes", "y", "1"}: return True
        if txt in {"false", "no", "n", "0"}: return False
        return value
    if field in DATE_FIELDS:
        dt = pd.to_datetime(value, errors="coerce")
        if not pd.isna(dt):
            return dt.date().isoformat()
    return value


def save_json(data: Dict[str, Any], json_path: Path, out_path: Path) -> None:
    data.setdefault("metadata", {})["record_count"] = len(data["records"])
    if out_path.resolve() == json_path.resolve():
        backup = json_path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
        shutil.copy2(json_path, backup)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    check = load_source_json(out_path)
    if check.get("metadata", {}).get("record_count") != len(check["records"]):
        raise ValueError("Validation failed: metadata.record_count does not match records length.")


def build_xlsx(json_path: Path, xlsx_path: Path, active_only: bool = False) -> None:
    data = load_source_json(json_path)
    records = data["records"]
    if active_only:
        records = [r for r in records if str(r.get("record_status", "active")).lower() not in ARCHIVE_STATUSES]
    fields = field_order(data)
    pd.DataFrame([{f: r.get(f) for f in fields} for r in records], columns=fields).to_excel(
        xlsx_path, index=False, sheet_name="Improvement Log", engine="openpyxl"
    )
    wb = load_workbook(xlsx_path)
    ws = wb["Improvement Log"]
    ws.freeze_panes = "A2"
    fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in ws[1]:
        cell.font = Font(bold=True); cell.fill = fill; cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    if ws.max_row >= 2:
        ref = f"A1:{ws.cell(row=ws.max_row, column=ws.max_column).coordinate}"
        tab = Table(displayName="ImprovementLog", ref=ref)
        tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False, showLastColumn=False, showColumnStripes=False)
        ws.add_table(tab)
    widths = {"id":12, "date_identified":15, "source":20, "l1_cycle":24, "l2_process":28,
              "observation_pain_point":60, "root_cause":50, "recommended_action":60,
              "estimated_impact_benefit":42, "notes_next_step":60, "change_notes":40}
    for i, f in enumerate(fields, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = widths.get(f, 22)
    wb.save(xlsx_path)


def read_csv_rows(csv_path: Path) -> List[Dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")
        headers = [normalize_header(h) for h in reader.fieldnames]
        rows = []
        for raw in reader:
            row = {h: raw.get(orig) for orig, h in zip(reader.fieldnames, headers) if h}
            if any(v not in (None, "") for v in row.values()):
                rows.append(row)
        return rows


def update_json(json_path: Path, csv_path: Path, out_path: Path, modified_by: str, apply_deletes: bool, delete_missing: bool) -> Tuple[int,int,int,int,int]:
    data = load_source_json(json_path)
    by_id = {r["id"]: r for r in data["records"]}
    rows = read_csv_rows(csv_path)
    seen, to_delete = set(), set()
    updated = inserted = unchanged = archived = 0
    ts = now_iso()

    for row in rows:
        rec_id = clean_value(row.get("id"), "id")
        if not rec_id:
            raise ValueError("CSV row missing required id.")
        if rec_id in seen:
            raise ValueError(f"Duplicate ID in CSV: {rec_id}")
        seen.add(rec_id)
        clean = {k: clean_value(v, k) for k, v in row.items()}
        status = str(clean.get("record_status") or "").lower()

        if status in DELETE_STATUSES and apply_deletes:
            if rec_id in by_id:
                to_delete.add(rec_id)
            continue

        if rec_id in by_id:
            target = by_id[rec_id]
            before = deepcopy(target)
            for k, v in clean.items():
                if k not in PROTECTED_FIELDS:
                    target[k] = v
            if target != before:
                if status in ARCHIVE_STATUSES:
                    archived += 1
                target["last_modified_by"] = modified_by
                target["last_modified_at"] = ts
                updated += 1
            else:
                unchanged += 1
        else:
            if status in DELETE_STATUSES:
                unchanged += 1
                continue
            clean.setdefault("record_status", "active")
            clean.setdefault("review_status", "needs_review")
            clean.setdefault("requires_human_review", True)
            clean["last_modified_by"] = modified_by
            clean["last_modified_at"] = ts
            data["records"].append(clean)
            by_id[rec_id] = clean
            inserted += 1

    if delete_missing:
        to_delete.update(set(by_id) - seen)

    if to_delete:
        data["records"] = [r for r in data["records"] if r.get("id") not in to_delete]

    data.setdefault("metadata", {})["last_updated_at"] = ts
    data["metadata"]["last_update_source"] = str(csv_path)
    data["metadata"]["last_update_deleted_count"] = len(to_delete)
    save_json(data, json_path, out_path)
    return updated, inserted, unchanged, archived, len(to_delete)


def remove_records(json_path: Path, ids: List[str], out_path: Path, modified_by: str, archive: bool) -> Tuple[int,int]:
    data = load_source_json(json_path)
    ids = set(ids)
    existing = {r["id"] for r in data["records"]}
    missing = len(ids - existing)
    ts = now_iso()
    if archive:
        affected = 0
        for r in data["records"]:
            if r["id"] in ids:
                r["record_status"] = "archived"
                r["requires_human_review"] = False
                r["last_modified_by"] = modified_by
                r["last_modified_at"] = ts
                affected += 1
    else:
        before = len(data["records"])
        data["records"] = [r for r in data["records"] if r["id"] not in ids]
        affected = before - len(data["records"])
    data.setdefault("metadata", {})["last_updated_at"] = ts
    data["metadata"]["last_update_source"] = "remove command"
    save_json(data, json_path, out_path)
    return affected, missing


def main() -> None:
    p = argparse.ArgumentParser(description="Sync Improvement Log JSON with XLSX/CSV, including archive/delete support.")
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build-xlsx")
    b.add_argument("--json", required=True, type=Path); b.add_argument("--xlsx", required=True, type=Path)
    b.add_argument("--active-only", action="store_true", help="Exclude archived/inactive records.")
    u = sub.add_parser("update-json")
    u.add_argument("--json", required=True, type=Path); u.add_argument("--csv", required=True, type=Path); u.add_argument("--out-json", required=True, type=Path)
    u.add_argument("--modified-by", default="csv_update")
    u.add_argument("--apply-deletes", action="store_true", help="Hard-delete rows with record_status=deleted_candidate/delete/deleted/remove/removed.")
    u.add_argument("--delete-missing", action="store_true", help="Hard-delete JSON records absent from the CSV. Use carefully.")
    r = sub.add_parser("remove")
    r.add_argument("--json", required=True, type=Path); r.add_argument("--ids", nargs="+", required=True); r.add_argument("--out-json", required=True, type=Path)
    r.add_argument("--modified-by", default="manual_remove"); r.add_argument("--archive", action="store_true")
    args = p.parse_args()
    if args.command == "build-xlsx":
        build_xlsx(args.json, args.xlsx, args.active_only)
        print(f"Built XLSX: {args.xlsx}")
    elif args.command == "update-json":
        a,b,c,d,e = update_json(args.json, args.csv, args.out_json, args.modified_by, args.apply_deletes, args.delete_missing)
        print(f"Updated JSON: {args.out_json}")
        print(f"Rows updated: {a}; inserted: {b}; unchanged: {c}; archived: {d}; deleted: {e}")
    elif args.command == "remove":
        affected, missing = remove_records(args.json, args.ids, args.out_json, args.modified_by, args.archive)
        print(f"{'Archived' if args.archive else 'Deleted'} records: {affected}; IDs not found: {missing}; output: {args.out_json}")

if __name__ == "__main__":
    main()
