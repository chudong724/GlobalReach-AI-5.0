from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeStore:
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
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'general',
                    content TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category)")

    def list_items(self, search: str = "", limit: int = 500) -> list[dict]:
        self.init_db(); q="SELECT * FROM knowledge_items"; params=[]
        if search.strip():
            term=f"%{search.strip()}%"; q += " WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? OR category LIKE ?"; params=[term,term,term,term]
        q += " ORDER BY updated_at DESC LIMIT ?"; params.append(max(1,min(limit,2000)))
        with self.connect() as conn: return [dict(r) for r in conn.execute(q,params).fetchall()]

    def save_item(self, data: dict) -> dict:
        self.init_db(); item_id=str(data.get("id") or uuid.uuid4()); now=_now(); title=str(data.get("title") or "").strip(); category=str(data.get("category") or "general").strip(); content=str(data.get("content") or "").strip(); tags=str(data.get("tags") or "").strip(); active=1 if bool(data.get("active",True)) else 0
        with self.connect() as conn:
            old=conn.execute("SELECT created_at FROM knowledge_items WHERE id=?",(item_id,)).fetchone(); created=old["created_at"] if old else now
            conn.execute("INSERT INTO knowledge_items(id,title,category,content,tags,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,category=excluded.category,content=excluded.content,tags=excluded.tags,active=excluded.active,updated_at=excluded.updated_at",(item_id,title,category,content,tags,active,created,now))
            return dict(conn.execute("SELECT * FROM knowledge_items WHERE id=?",(item_id,)).fetchone())

    def delete_many(self, ids: list[str]) -> int:
        self.init_db(); clean=[str(x).strip() for x in ids if str(x).strip()]
        if not clean:return 0
        marks=",".join(["?"]*len(clean))
        with self.connect() as conn:
            cur=conn.execute(f"DELETE FROM knowledge_items WHERE id IN ({marks})",clean); return int(cur.rowcount or 0)

    def search_context(self, query: str, limit: int = 8) -> list[dict]:
        self.init_db(); terms=[t.strip() for t in str(query or "").replace("/"," ").replace(","," ").split() if len(t.strip())>=2][:8]
        with self.connect() as conn:
            if not terms:
                rows=conn.execute("SELECT * FROM knowledge_items WHERE active=1 ORDER BY updated_at DESC LIMIT ?",(limit,)).fetchall()
            else:
                clauses=[]; params=[]
                for term in terms:
                    like=f"%{term}%"; clauses.append("(title LIKE ? OR content LIKE ? OR tags LIKE ? OR category LIKE ?)"); params.extend([like,like,like,like])
                params.append(limit)
                rows=conn.execute("SELECT * FROM knowledge_items WHERE active=1 AND ("+" OR ".join(clauses)+") ORDER BY updated_at DESC LIMIT ?",params).fetchall()
            return [dict(r) for r in rows]
