"""Stockage hybride PostgreSQL (Supabase) / SQLite : cours, cartes (SM-2), salons, messages, partages.
Chaque fonction ouvre sa propre connexion : simple et sûr avec Streamlit."""
import json
import os
import random
import sqlite3
import string
from contextlib import contextmanager
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

DB_PATH = os.environ.get("DB_PATH", "data/etude.db")


def _clean_pg_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() != "pgbouncer"
    ]
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return _clean_pg_url(url)
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return _clean_pg_url(st.secrets["DATABASE_URL"])
    except Exception:
        pass
    return None


def _is_pg() -> bool:
    return bool(_get_database_url())


class _CursorAdapter:
    """Adapte le curseur SQLite/psycopg pour garder une API uniforme."""

    def __init__(self, cur, is_pg: bool, last_id=None):
        self._cur = cur
        self._is_pg = is_pg
        self.lastrowid = last_id

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if (row is not None and self._is_pg) else row

    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(r) for r in rows] if self._is_pg else rows


class _ConnAdapter:
    def __init__(self, raw_conn, is_pg: bool):
        self._conn = raw_conn
        self._is_pg = is_pg

    def _adapt_sql(self, sql: str) -> str:
        if not self._is_pg:
            return sql
        q = sql.replace("?", "%s")
        stripped = q.strip()
        upper = stripped.upper()
        if upper.startswith("INSERT INTO ") and "RETURNING" not in upper:
            if not upper.startswith("INSERT INTO ROOMS"):
                q = stripped.rstrip(";") + " RETURNING id"
        return q

    def execute(self, sql: str, params=()):
        cur = self._conn.cursor()
        q = self._adapt_sql(sql)
        cur.execute(q, params)
        last_id = None
        if self._is_pg and q.strip().upper().startswith("INSERT INTO ") and "RETURNING ID" in q.upper():
            res = cur.fetchone()
            if res:
                last_id = res["id"] if isinstance(res, dict) else res[0]
        elif not self._is_pg:
            last_id = cur.lastrowid
        return _CursorAdapter(cur, self._is_pg, last_id=last_id)

    def executemany(self, sql: str, seq_of_params):
        cur = self._conn.cursor()
        q = self._adapt_sql(sql)
        cur.executemany(q, seq_of_params)
        return _CursorAdapter(cur, self._is_pg)

    def executescript(self, script: str):
        if not self._is_pg:
            self._conn.executescript(script)
            return
        cur = self._conn.cursor()
        for stmt in script.split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


@contextmanager
def db():
    url = _get_database_url()
    if url:
        if psycopg is None:
            raise RuntimeError("Installe 'psycopg[binary]' pour utiliser DATABASE_URL avec Supabase.")
        raw = psycopg.connect(url, row_factory=dict_row)
        conn = _ConnAdapter(raw, is_pg=True)
    else:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        raw = sqlite3.connect(DB_PATH, timeout=10)
        raw.row_factory = sqlite3.Row
        conn = _ConnAdapter(raw, is_pg=False)

    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn._conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def init():
    with db() as c:
        if _is_pg():
            c.executescript("""
            CREATE TABLE IF NOT EXISTS decks(
                id SERIAL PRIMARY KEY,
                owner TEXT,
                title TEXT,
                lang TEXT,
                text TEXT,
                pack TEXT DEFAULT '{}',
                created TEXT DEFAULT CURRENT_TIMESTAMP::text
            );
            CREATE TABLE IF NOT EXISTS cards(
                id SERIAL PRIMARY KEY,
                owner TEXT,
                deck_id INTEGER,
                front TEXT,
                back TEXT,
                ease REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                reps INTEGER DEFAULT 0,
                due TEXT
            );
            CREATE TABLE IF NOT EXISTS rooms(
                code TEXT PRIMARY KEY,
                name TEXT,
                subject TEXT,
                created TEXT DEFAULT CURRENT_TIMESTAMP::text
            );
            CREATE TABLE IF NOT EXISTS messages(
                id SERIAL PRIMARY KEY,
                room TEXT,
                author TEXT,
                body TEXT,
                ts TEXT DEFAULT CURRENT_TIMESTAMP::text
            );
            CREATE TABLE IF NOT EXISTS shares(
                id SERIAL PRIMARY KEY,
                room TEXT,
                author TEXT,
                kind TEXT,
                title TEXT,
                payload TEXT,
                ts TEXT DEFAULT CURRENT_TIMESTAMP::text
            );
            """)
        else:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS decks(id INTEGER PRIMARY KEY, owner TEXT, title TEXT, lang TEXT,
                text TEXT, pack TEXT DEFAULT '{}', created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS cards(id INTEGER PRIMARY KEY, owner TEXT, deck_id INTEGER,
                front TEXT, back TEXT, ease REAL DEFAULT 2.5, interval INTEGER DEFAULT 0,
                reps INTEGER DEFAULT 0, due TEXT);
            CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY, name TEXT, subject TEXT,
                created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, room TEXT, author TEXT,
                body TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS shares(id INTEGER PRIMARY KEY, room TEXT, author TEXT,
                kind TEXT, title TEXT, payload TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
            """)


# ---- Cours -------------------------------------------------------------
def add_deck(owner, title, lang, text) -> int:
    with db() as c:
        return c.execute(
            "INSERT INTO decks(owner,title,lang,text) VALUES(?,?,?,?)",
            (owner, title, lang, text),
        ).lastrowid


def list_decks(owner):
    with db() as c:
        return [
            dict(r)
            for r in c.execute(
                "SELECT id,title,lang FROM decks WHERE owner=? ORDER BY id DESC", (owner,)
            ).fetchall()
        ]


def get_deck(deck_id):
    with db() as c:
        r = c.execute("SELECT * FROM decks WHERE id=?", (deck_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["pack"] = json.loads(d["pack"] or "{}")
    return d


def save_section(deck_id, kind, data):
    deck = get_deck(deck_id)
    if not deck:
        return
    deck["pack"][kind] = data
    with db() as c:
        c.execute("UPDATE decks SET pack=? WHERE id=?", (json.dumps(deck["pack"]), deck_id))


# ---- Cartes & révisions ---------------------------------------------------
def add_cards(owner, deck_id, cards):
    today = date.today().isoformat()
    with db() as c:
        c.executemany(
            "INSERT INTO cards(owner,deck_id,front,back,due) VALUES(?,?,?,?,?)",
            [(owner, deck_id, x["front"], x["back"], today) for x in cards],
        )


def due_cards(owner):
    with db() as c:
        return [
            dict(r)
            for r in c.execute(
                "SELECT * FROM cards WHERE owner=? AND due<=? ORDER BY due, id",
                (owner, date.today().isoformat()),
            ).fetchall()
        ]


def update_card(card_id, ease, interval, reps, due):
    with db() as c:
        c.execute(
            "UPDATE cards SET ease=?,interval=?,reps=?,due=? WHERE id=?",
            (ease, interval, reps, due, card_id),
        )


# ---- Salons ---------------------------------------------------------------
def create_room(name, subject) -> str:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    with db() as c:
        c.execute("INSERT INTO rooms(code,name,subject) VALUES(?,?,?)", (code, name, subject))
    return code


def get_room(code):
    with db() as c:
        r = c.execute("SELECT * FROM rooms WHERE code=?", (code.strip().upper(),)).fetchone()
    return dict(r) if r else None


def post_message(room, author, body):
    with db() as c:
        c.execute("INSERT INTO messages(room,author,body) VALUES(?,?,?)", (room, author, body))


def messages(room, limit=60):
    with db() as c:
        rows = c.execute(
            "SELECT author,body,ts FROM messages WHERE room=? ORDER BY id DESC LIMIT ?",
            (room, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def share(room, author, kind, title, payload):
    with db() as c:
        c.execute(
            "INSERT INTO shares(room,author,kind,title,payload) VALUES(?,?,?,?,?)",
            (room, author, kind, title, json.dumps(payload)),
        )


def shares(room):
    with db() as c:
        rows = c.execute("SELECT * FROM shares WHERE room=? ORDER BY id DESC", (room,)).fetchall()
    return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]