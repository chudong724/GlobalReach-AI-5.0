from __future__ import annotations

import csv
import io
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

CRM_COLUMNS = [
    "company_name", "contact_name", "job_title", "email", "phone", "website",
    "country", "city", "linkedin", "source", "status", "priority", "notes",
    "deal_stage", "lead_score", "email_verification", "last_contacted_at", "next_follow_up_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _score_contact(data: dict) -> int:
    score = 10
    if str(data.get("company_name", "")).strip(): score += 10
    if str(data.get("website", "")).strip(): score += 12
    if str(data.get("email", "")).strip(): score += 18
    if str(data.get("phone", "")).strip(): score += 8
    if str(data.get("linkedin", "")).strip(): score += 8
    if str(data.get("contact_name", "")).strip(): score += 8
    if str(data.get("job_title", "")).strip(): score += 8
    if str(data.get("country", "")).strip(): score += 5
    priority = str(data.get("priority", "normal")).lower()
    if priority == "high": score += 8
    elif priority == "low": score -= 3
    verification = str(data.get("email_verification", "unknown")).lower()
    if verification == "valid": score += 5
    elif verification in {"invalid", "risky"}: score -= 10
    return max(0, min(100, score))


class CRMStore:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crm_contacts (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL DEFAULT '', contact_name TEXT NOT NULL DEFAULT '',
                    job_title TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '',
                    website TEXT NOT NULL DEFAULT '', country TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '',
                    linkedin TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'new',
                    priority TEXT NOT NULL DEFAULT 'normal', notes TEXT NOT NULL DEFAULT '',
                    deal_stage TEXT NOT NULL DEFAULT 'new', lead_score INTEGER NOT NULL DEFAULT 0,
                    email_verification TEXT NOT NULL DEFAULT 'unknown', last_contacted_at TEXT NOT NULL DEFAULT '',
                    next_follow_up_at TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )
            """)
            existing = {r[1] for r in conn.execute("PRAGMA table_info(crm_contacts)").fetchall()}
            migrations = {
                "deal_stage": "TEXT NOT NULL DEFAULT 'new'",
                "lead_score": "INTEGER NOT NULL DEFAULT 0",
                "email_verification": "TEXT NOT NULL DEFAULT 'unknown'",
                "last_contacted_at": "TEXT NOT NULL DEFAULT ''",
                "next_follow_up_at": "TEXT NOT NULL DEFAULT ''",
            }
            for name, ddl in migrations.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE crm_contacts ADD COLUMN {name} {ddl}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_email ON crm_contacts(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_company ON crm_contacts(company_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_stage ON crm_contacts(deal_stage)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_score ON crm_contacts(lead_score)")

    def list_contacts(self, search: str = "", limit: int = 1000, stage: str = "") -> list[dict]:
        self.init_db()
        where, params = [], []
        if search.strip():
            q = f"%{search.strip()}%"
            where.append("(company_name LIKE ? OR contact_name LIKE ? OR email LIKE ? OR website LIKE ? OR country LIKE ?)")
            params.extend([q, q, q, q, q])
        if stage.strip():
            where.append("deal_stage=?")
            params.append(stage.strip())
        query = "SELECT * FROM crm_contacts"
        if where: query += " WHERE " + " AND ".join(where)
        query += " ORDER BY lead_score DESC, updated_at DESC LIMIT ?"
        params.append(max(1, min(limit, 5000)))
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get_contacts(self, ids: list[str]) -> list[dict]:
        self.init_db()
        clean = [str(x).strip() for x in ids if str(x).strip()]
        if not clean: return []
        marks = ",".join(["?"] * len(clean))
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(f"SELECT * FROM crm_contacts WHERE id IN ({marks})", clean).fetchall()]

    def upsert_contact(self, data: dict) -> dict:
        self.init_db()
        values = {k: str(data.get(k, "") or "").strip() for k in CRM_COLUMNS}
        values["status"] = values["status"] or "new"
        values["priority"] = values["priority"] or "normal"
        values["deal_stage"] = values["deal_stage"] or "new"
        values["email_verification"] = values["email_verification"] or "unknown"
        supplied_score = str(data.get("lead_score", "") or "").strip()
        values["lead_score"] = supplied_score if supplied_score.isdigit() else str(_score_contact(values))
        contact_id = str(data.get("id") or uuid.uuid4())
        now = _now()
        with self.connect() as conn:
            existing = None
            if values["email"]:
                existing = conn.execute("SELECT id, created_at FROM crm_contacts WHERE lower(email)=lower(?) LIMIT 1", (values["email"],)).fetchone()
            if existing:
                contact_id, created_at = existing["id"], existing["created_at"]
            else:
                created_at = now
            cols = ["id"] + CRM_COLUMNS + ["created_at", "updated_at"]
            row = [contact_id] + [values[k] for k in CRM_COLUMNS] + [created_at, now]
            placeholders = ",".join(["?"] * len(cols))
            updates = ",".join([f"{c}=excluded.{c}" for c in CRM_COLUMNS + ["updated_at"]])
            conn.execute(f"INSERT INTO crm_contacts ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}", row)
            return dict(conn.execute("SELECT * FROM crm_contacts WHERE id=?", (contact_id,)).fetchone())

    def update_email_verification(self, contact_id: str, status: str) -> None:
        self.init_db()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM crm_contacts WHERE id=?", (contact_id,)).fetchone()
            if not row: return
            data = dict(row); data["email_verification"] = status
            conn.execute(
                "UPDATE crm_contacts SET email_verification=?, lead_score=?, updated_at=? WHERE id=?",
                (status, _score_contact(data), _now(), contact_id),
            )

    def rescore(self, ids: list[str] | None = None) -> int:
        self.init_db()
        with self.connect() as conn:
            if ids:
                marks = ",".join(["?"] * len(ids)); rows = conn.execute(f"SELECT * FROM crm_contacts WHERE id IN ({marks})", ids).fetchall()
            else: rows = conn.execute("SELECT * FROM crm_contacts").fetchall()
            for row in rows:
                data = dict(row); conn.execute("UPDATE crm_contacts SET lead_score=?, updated_at=? WHERE id=?", (_score_contact(data), _now(), data["id"]))
            return len(rows)

    def pipeline_summary(self) -> dict:
        self.init_db()
        with self.connect() as conn:
            stages = {r["deal_stage"]: int(r["n"]) for r in conn.execute("SELECT deal_stage, COUNT(*) n FROM crm_contacts GROUP BY deal_stage")}
            total = int(conn.execute("SELECT COUNT(*) FROM crm_contacts").fetchone()[0])
            avg = float(conn.execute("SELECT COALESCE(AVG(lead_score),0) FROM crm_contacts").fetchone()[0])
            valid = int(conn.execute("SELECT COUNT(*) FROM crm_contacts WHERE email_verification='valid'").fetchone()[0])
        return {"total": total, "average_score": round(avg, 1), "verified_emails": valid, "stages": stages}

    def delete_many(self, ids: list[str]) -> int:
        self.init_db(); clean = [str(x).strip() for x in ids if str(x).strip()]
        if not clean: return 0
        marks = ",".join(["?"] * len(clean))
        with self.connect() as conn:
            cur = conn.execute(f"DELETE FROM crm_contacts WHERE id IN ({marks})", clean); return int(cur.rowcount or 0)

    def import_csv(self, raw: bytes) -> dict:
        text = raw.decode("utf-8-sig", errors="replace"); reader = csv.DictReader(io.StringIO(text)); imported = skipped = 0
        for row in reader:
            normalized = {k: row.get(k, "") for k in CRM_COLUMNS}
            if not any(str(v or "").strip() for v in normalized.values()): skipped += 1; continue
            self.upsert_contact(normalized); imported += 1
        return {"imported": imported, "skipped": skipped}

    def export_csv(self, contacts: list[dict] | None = None) -> str:
        contacts = contacts if contacts is not None else self.list_contacts(limit=5000)
        out = io.StringIO(); fields = ["id"] + CRM_COLUMNS + ["created_at", "updated_at"]
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        for item in contacts: writer.writerow({k: item.get(k, "") for k in fields})
        return "\ufeff" + out.getvalue()


def csv_template() -> str:
    out = io.StringIO(); writer = csv.DictWriter(out, fieldnames=CRM_COLUMNS); writer.writeheader()
    writer.writerow({"company_name":"Example Importer Ltd","contact_name":"Jane Smith","job_title":"Purchasing Manager","email":"jane@example.com","phone":"+1 555 0100","website":"https://example.com","country":"United States","city":"Los Angeles","linkedin":"https://linkedin.com/in/example","source":"Trade Show","status":"new","priority":"high","notes":"Interested in OEM/ODM","deal_stage":"new","lead_score":"","email_verification":"unknown","last_contacted_at":"","next_follow_up_at":""})
    return "\ufeff" + out.getvalue()
