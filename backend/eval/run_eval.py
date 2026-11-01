"""Run the 25-question eval:  python -m eval.run_eval [--only 1,5,9] [--json results.json]

For each question: run the reference SQL, ask the LLM pipeline for SQL, execute it through the
same guard + read-only path the app uses, and compare results (see eval/compare.py).
Two scores are reported:
  strict   - exact same columns and values as the reference
  lenient  - extra columns are allowed (the headline score)
Also reports accuracy by difficulty, plus every failure with both SQL strings.
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

from sqlalchemy import text

from app import llm
from app.db import engine
from app.qa import run_readonly
from app.sql_guard import UnsafeSQL
from eval.compare import lenient_match, strict_match
from eval.questions import QUESTIONS


def reference(sql):
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(sql)).fetchall()]


def run(only=None):
    results = []
    for q in QUESTIONS:
        if only and q["id"] not in only:
            continue
        ordered = q.get("ordered", False)
        expected = reference(q["sql"])
        entry = dict(id=q["id"], difficulty=q["difficulty"], question=q["q"], ref_sql=q["sql"],
                     generated_sql=None, passed=False, passed_strict=False, error=None)
        t0 = time.time()
        try:
            plan = llm.question_to_sql(q["q"])
            entry["generated_sql"] = plan.get("sql")
            _, rows, _, _ = run_readonly(plan["sql"])
            entry["passed"] = lenient_match(rows, expected, ordered)
            entry["passed_strict"] = strict_match(rows, expected, ordered)
            if not entry["passed"]:
                entry["expected"], entry["got"] = [list(r) for r in expected[:5]], rows[:5]
        except UnsafeSQL as e:
            entry["error"] = f"blocked by guard: {e}"
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {str(e).splitlines()[0]}"
        entry["seconds"] = round(time.time() - t0, 1)
        results.append(entry)
        print(f"[{'PASS' if entry['passed'] else 'FAIL'}] Q{q['id']:>2} {q['q']}")
    return results


def report(results):
    n = len(results)
    ok, ok_strict = sum(r["passed"] for r in results), sum(r["passed_strict"] for r in results)
    model = os.environ.get("LLM_MODEL") or llm._model()
    print(f"\nModel: {llm.PROVIDER}/{model}")
    print(f"Accuracy (extra columns allowed): {ok}/{n} = {100 * ok / n:.0f}%")
    print(f"Accuracy (strict, exact columns): {ok_strict}/{n} = {100 * ok_strict / n:.0f}%")
    by = defaultdict(lambda: [0, 0])
    for r in results:
        by[r["difficulty"]][1] += 1
        by[r["difficulty"]][0] += r["passed"]
    for d in sorted(by):
        print(f"  difficulty {d}: {by[d][0]}/{by[d][1]}")
    for r in results:
        if not r["passed"]:
            print(f"\n--- FAILED Q{r['id']}: {r['question']}")
            print("reference:", r["ref_sql"])
            print("generated:", r["generated_sql"])
            if r["error"]:
                print("error:", r["error"])
            else:
                print("expected:", r.get("expected"), "\ngot:     ", r.get("got"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated question ids")
    ap.add_argument("--json", help="write full results to this file")
    a = ap.parse_args()
    res = run({int(x) for x in a.only.split(",")} if a.only else None)
    report(res)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=2, default=str)
    sys.exit(0 if all(r["passed"] for r in res) else 1)
