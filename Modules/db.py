"""
Reusable MySQL connection for the Blockchained application database.

Credentials are read from the project's `.env` (git-ignored):

    MYSQL_HOST=127.0.0.1
    MYSQL_PORT=3306
    MYSQL_USER=<user>
    MYSQL_PASS=<password>
    MYSQL_DB=blockchained_dev_2

Why not plain `load_dotenv()`? With no arguments python-dotenv resolves the
`.env` relative to the *calling* file, so a script living outside the project
(e.g. a scratch dir) silently gets no credentials and falls back to the OS
username. This module always points at the project root explicitly.

Usage
-----
    from db import query, cursor, describe, tables

    rows = query("SELECT BuildingID, Name FROM buildings LIMIT 5")

    with cursor() as cur:                 # connection closed automatically
        cur.execute("SELECT COUNT(*) AS n FROM buildings")
        print(cur.fetchone()["n"])
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

_REQUIRED = ("MYSQL_USER", "MYSQL_PASS", "MYSQL_DB")


def get_config(**overrides) -> dict:
    """Build connection kwargs from .env, with optional overrides."""
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    missing = [k for k in _REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing {', '.join(missing)} in {ENV_PATH}. "
            "Add MYSQL_HOST/MYSQL_PORT/MYSQL_USER/MYSQL_PASS/MYSQL_DB."
        )
    cfg = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASS"),
        "database": os.getenv("MYSQL_DB"),
    }
    cfg.update(overrides)
    return cfg


def connect(cursorclass=DictCursor, **overrides) -> pymysql.connections.Connection:
    """Open a new connection. Caller is responsible for closing it."""
    return pymysql.connect(
        **get_config(**overrides),
        cursorclass=cursorclass,
        charset="utf8mb4",
        connect_timeout=5,
    )


@contextmanager
def connection(**kwargs):
    """Context-managed connection."""
    conn = connect(**kwargs)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def cursor(**kwargs):
    """Context-managed cursor (opens and closes its own connection)."""
    with connection(**kwargs) as conn:
        with conn.cursor() as cur:
            yield cur


def query(sql: str, params=None) -> list[dict]:
    """Run a SELECT and return all rows as dicts."""
    with cursor() as cur:
        cur.execute(sql, params or ())
        return list(cur.fetchall())


def tables() -> list[str]:
    """List table names in the configured database."""
    with cursor(cursorclass=pymysql.cursors.Cursor) as cur:
        cur.execute("SHOW TABLES")
        return [r[0] for r in cur.fetchall()]


def describe(table: str) -> list[dict]:
    """DESCRIBE a table. Table name is validated to avoid SQL injection."""
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Unsafe table name: {table!r}")
    return query(f"DESCRIBE `{table}`")


def row_count(table: str) -> int:
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Unsafe table name: {table!r}")
    with cursor(cursorclass=pymysql.cursors.Cursor) as cur:
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        return cur.fetchone()[0]


if __name__ == "__main__":
    cfg = get_config()
    print(f"Connecting to {cfg['database']} at {cfg['host']}:{cfg['port']} "
          f"as {cfg['user']} ...")
    with connection() as conn:
        print("OK — server", conn.get_server_info())
    names = tables()
    print(f"{len(names)} tables: {', '.join(names)}")
