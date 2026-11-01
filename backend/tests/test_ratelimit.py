from app import ratelimit


def test_per_ip_limit_and_window(monkeypatch):
    monkeypatch.setattr(ratelimit, "PER_IP_LIMIT", 2)
    monkeypatch.setattr(ratelimit, "WINDOW", 100)
    monkeypatch.setattr(ratelimit, "DAILY_LIMIT", 1000)
    ratelimit._hits.clear()
    assert ratelimit.check("1.1.1.1", now=1000) is None
    assert ratelimit.check("1.1.1.1", now=1001) is None
    assert ratelimit.check("1.1.1.1", now=1002) is not None   # third in the window: blocked
    assert ratelimit.check("2.2.2.2", now=1002) is None        # other IP unaffected
    assert ratelimit.check("1.1.1.1", now=1200) is None        # window has passed


def test_daily_cap(monkeypatch):
    monkeypatch.setattr(ratelimit, "PER_IP_LIMIT", 100)
    monkeypatch.setattr(ratelimit, "DAILY_LIMIT", 2)
    ratelimit._hits.clear()
    ratelimit._day.update(start=5000, count=0)
    assert ratelimit.check("a", now=5001) is None
    assert ratelimit.check("b", now=5002) is None
    assert ratelimit.check("c", now=5003) is not None
