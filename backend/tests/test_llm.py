import pytest

from app import llm


def test_json_extracts_from_prose_and_fences():
    assert llm._json('Sure! ```json\n{"sql": "SELECT 1", "chart": {"type": "none"}}\n``` hope that helps')["sql"] == "SELECT 1"
    assert llm._json('{"sql": null}')["sql"] is None
    with pytest.raises(ValueError):
        llm._json("no json here")


def test_question_to_sql_uses_chat(monkeypatch):
    seen = {}

    def fake(system, user, max_tokens, temperature):
        seen.update(user=user, temperature=temperature)
        return 'Here: {"sql": "SELECT name FROM sites", "chart": {"type": "none"}}'

    monkeypatch.setattr(llm, "_chat", fake)
    out = llm.question_to_sql("list sites")
    assert out["sql"] == "SELECT name FROM sites" and seen["temperature"] == 0


def test_groq_needs_key(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "groq")
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        llm._chat("s", "u", 10, 0)
    assert llm._model() == "llama-3.3-70b-versatile"
