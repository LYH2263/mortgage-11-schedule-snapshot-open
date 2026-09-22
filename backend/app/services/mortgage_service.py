from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.repositories import loans, runs, settings
import json

def _loads(text):
    try:
        return json.loads(text) if text else {}
    except (TypeError, ValueError):
        return {}

def _summary(row):
    # 摘要取自写入时钉选的 result_json，绝不用现行参数重算
    result = _loads(row.get("result_json"))
    return {"id": row["id"], "kind": row["kind"], "loan_id": row["loan_id"],
            "created_at": row["created_at"],
            "monthly_payment": result.get("monthly_payment"),
            "total_interest": result.get("total_interest")}

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return [_summary(r) for r in runs.list_recent(self._c, limit)]
    def get_run(self, run_id):
        # 钉选打开：返回写入时的输入与结果快照，不按现行本金/利率/期数重算
        row = runs.get(self._c, run_id)
        if row is None:
            return None
        return {"id": row["id"], "kind": row["kind"], "loan_id": row["loan_id"],
                "created_at": row["created_at"],
                "input": _loads(row["input_json"]),
                "result": _loads(row["result_json"])}
    def schedule(self, principal, annual_rate, months, loan_id, persist, preview_rows=12):
        full = equal_payment_schedule(principal, annual_rate, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        rid = None
        if persist:
            rid = runs.insert(self._c, "schedule", {"principal": principal, "annual_rate": annual_rate, "months": months}, out, loan_id)
        return {"run_id": rid, **out}
    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
