import sqlite3
import pytest
from app.services import mortgage_service
from app.services.mortgage_service import MortgageService
from app.engines.amortization import equal_payment_schedule

SCHEMA = """
CREATE TABLE loans(id INTEGER PRIMARY KEY, name TEXT, principal REAL, annual_rate REAL, months INTEGER);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE calc_runs(id INTEGER PRIMARY KEY, kind TEXT, loan_id INTEGER, input_json TEXT, result_json TEXT, created_at TEXT);
"""

@pytest.fixture
def db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    monkeypatch.setattr(mortgage_service, "connect", lambda: conn)
    yield conn
    conn.close()

def run_count(conn):
    return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]

def test_get_run_returns_pinned_snapshot_not_recomputed(db):
    svc = MortgageService()
    written = svc.schedule(1_000_000, 3.5, 360, loan_id=None, persist=True)
    # 现行参数已变：同一贷款如今是另一组本金/利率/期数
    db.execute("INSERT INTO loans(id,name,principal,annual_rate,months) VALUES (1,'现行',500000,6.0,120)")
    opened = svc.get_run(written["run_id"])
    current = equal_payment_schedule(500000, 6.0, 120)
    assert opened["result"]["monthly_payment"] == written["monthly_payment"]
    assert opened["result"]["monthly_payment"] != current["monthly_payment"]
    assert opened["result"]["total_interest"] == written["total_interest"]
    assert opened["result"]["preview"] == written["preview"]
    assert opened["input"] == {"principal": 1_000_000, "annual_rate": 3.5, "months": 360}

def test_get_run_missing_returns_none_and_writes_nothing(db):
    svc = MortgageService()
    before = run_count(db)
    assert svc.get_run(999999) is None
    assert run_count(db) == before

def test_history_summary_comes_from_pinned_result(db):
    svc = MortgageService()
    written = svc.schedule(1_000_000, 3.5, 360, loan_id=None, persist=True)
    item = [i for i in svc.history() if i["id"] == written["run_id"]][0]
    assert item["monthly_payment"] == written["monthly_payment"]
    assert item["total_interest"] == written["total_interest"]
    # 与按其它现行参数重算的结果不同，证明摘要不是现算
    assert item["monthly_payment"] != equal_payment_schedule(500000, 6.0, 120)["monthly_payment"]

def test_schedule_persist_optional(db):
    svc = MortgageService()
    before = run_count(db)
    skipped = svc.schedule(800000, 4.2, 360, loan_id=None, persist=False)
    assert skipped["run_id"] is None
    assert run_count(db) == before
    saved = svc.schedule(800000, 4.2, 360, loan_id=None, persist=True)
    assert saved["run_id"] is not None
    assert run_count(db) == before + 1
