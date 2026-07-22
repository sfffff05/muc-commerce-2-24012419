"""第8天Flask接口测试：覆盖/health、/api/metrics、/api/categories、/api/ask及登录流程。"""

import pytest

from app import app


@pytest.fixture
def client():
    """创建Flask测试客户端，关闭跟踪异常以保持输出整洁。"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _login(client):
    """辅助函数：使用演示账号登录。"""
    return client.post(
        "/login",
        data={"username": "student", "password": "day07"},
        follow_redirects=True,
    )


# ── /health 接口 ──────────────────────────────────────────────


def test_health_returns_ok_without_login(client):
    """测试1：/health不需要登录，返回ok=True和正确的service名称。"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["service"] == "day08-flask-upgrade"


# ── /api/metrics 接口 ────────────────────────────────────────


def test_metrics_requires_login(client):
    """测试2：未登录访问/api/metrics应重定向到登录页。"""
    response = client.get("/api/metrics", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_metrics_returns_four_cards(client):
    """测试3：登录后/api/metrics返回4张指标卡，每张包含label、value、note。"""
    _login(client)
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    metrics = data["metrics"]
    assert len(metrics) == 4
    for card in metrics:
        assert "label" in card
        assert "value" in card
        assert "note" in card
    labels = [card["label"] for card in metrics]
    assert "总用户数" in labels
    assert "流失用户" in labels


# ── /api/categories 接口 ─────────────────────────────────────


def test_categories_filter_by_fashion(client):
    """测试4：登录后用category=Fashion筛选，只返回Fashion一行。"""
    _login(client)
    response = client.get("/api/categories?category=Fashion")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["category"] == "Fashion"
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["偏好品类"] == "Fashion"


def test_categories_default_returns_all(client):
    """测试5：不传category参数时返回全部5个品类。"""
    _login(client)
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["category"] == "全部"
    assert len(data["rows"]) == 5


# ── /api/ask 接口 400 错误 ──────────────────────────────────


def test_ask_empty_question_returns_400(client):
    """测试6：发送空问题时返回400和统一JSON错误结构。"""
    _login(client)
    response = client.post(
        "/api/ask",
        json={"question": ""},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert "answer" in data


def test_ask_valid_question_returns_answer(client):
    """测试7：发送有效问题后返回正常回答。"""
    _login(client)
    response = client.post(
        "/api/ask",
        json={"question": "系统中有多少用户？"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert "5,630" in data["answer"]


# ── 登录流程 ─────────────────────────────────────────────────


def test_login_with_wrong_password(client):
    """测试8：错误密码登录后页面应提示错误信息。"""
    response = client.post(
        "/login",
        data={"username": "student", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"\xe8\xb4\xa6\xe5\x8f\xb7\xe6\x88\x96\xe5\xaf\x86\xe7\xa0\x81\xe9\x94\x99\xe8\xaf\xaf" in response.data
