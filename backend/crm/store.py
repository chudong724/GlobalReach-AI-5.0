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
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crm_contacts (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL DEFAULT '',
                    contact_name TEXT NOT NULL DEFAULT '',
                    job_title TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    website TEXT NOT NULL DEFAULT '',
                    country TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '',
                    linkedin TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'new',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_email ON crm_contacts(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_company ON crm_contacts(company_name)")

    def list_contacts(self, search: str = "", limit: int = 1000) -> list[dict]:
        self.init_db()
        query = "SELECT * FROM crm_contacts"
        params: list[object] = []
        if search.strip():
            q = f"%{search.strip()}%"
            query += " WHERE company_name LIKE ? OR contact_name LIKE ? OR email LIKE ? OR website LIKE ? OR country LIKE ?"
            params.extend([q, q, q, q, q])
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(max(1, min(limit, 5000)))
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def upsert_contact(self, data: dict) -> dict:
        self.init_db()
        values = {k: str(data.get(k, "") or "").strip() for k in CRM_COLUMNS}
        contact_id = str(data.get("id") or uuid.uuid4())
        now = _now()
        with self.connect() as conn:
            existing = None
            if values["email"]:
                existing = conn.execute("SELECT id, created_at FROM crm_contacts WHERE lower(email)=lower(?) LIMIT 1", (values["email"],)).fetchone()
            if existing:
                contact_id = existing["id"]
                created_at = existing["created_at"]
            else:
                created_at = now
            cols = ["id"] + CRM_COLUMNS + ["created_at", "updated_at"]
            row = [contact_id] + [values[k] for k in CRM_COLUMNS] + [created_at, now]
            placeholders = ",".join(["?"] * len(cols))
            updates = ",".join([f"{c}=excluded.{c}" for c in CRM_COLUMNS + ["updated_at"]])
            conn.execute(
                f"INSERT INTO crm_contacts ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}",
                row,
            )
            result = conn.execute("SELECT * FROM crm_contacts WHERE id=?", (contact_id,)).fetchone()
            return dict(result)

    def delete_many(self, ids: list[str]) -> int:
        self.init_db()
        clean = [str(x).strip() for x in ids if str(x).strip()]
        if not clean:
            return 0
        marks = ",".join(["?"] * len(clean))
        with self.connect() as conn:
            cur = conn.execute(f"DELETE FROM crm_contacts WHERE id IN ({marks})", clean)
            return int(cur.rowcount or 0)

    def import_csv(self, raw: bytes) -> dict:
        text = raw.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        imported = 0
        skipped = 0
        for row in reader:
            normalized = {k: row.get(k, "") for k in CRM_COLUMNS}
            if not any(str(v or "").strip() for v in normalized.values()):
                skipped += 1
                continue
            self.upsert_contact(normalized)
            imported += 1
        return {"imported": imported, "skipped": skipped}

    def export_csv(self, contacts: list[dict] | None = None) -> str:
        contacts = contacts if contacts is not None else self.list_contacts(limit=5000)
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=["id"] + CRM_COLUMNS + ["created_at", "updated_at"])
        writer.writeheader()
        for item in contacts:
            writer.writerow({k: item.get(k, "") for k in writer.fieldnames})
        return "\ufeff" + out.getvalue()


def csv_template() -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=CRM_COLUMNS)
    writer.writeheader()
    writer.writerow({
        "company_name": "Example Importer Ltd",
        "contact_name": "Jane Smith",
        "job_title": "Purchasing Manager",
        "email": "jane@example.com",
        "phone": "+1 555 0100",
        "website": "https://example.com",
        "country": "United States",
        "city": "Los Angeles",
        "linkedin": "https://linkedin.com/in/example",
        "source": "Trade Show",
        "status": "new",
        "priority": "high",
        "notes": "Interested in OEM/ODM",
    })
    return "\ufeff" + out.getvalue()
