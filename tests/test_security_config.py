import pytest


def test_producao_exige_segredos_distintos_e_longos(monkeypatch):
    monkeypatch.setenv("ECOTECH_ENV", "production")
    monkeypatch.delenv("ECOTECH_SECRET_KEY", raising=False)
    monkeypatch.delenv("ECOTECH_JWT_SECRET", raising=False)

    from flask import Flask

    from ecotech.infrastructure.web import configurar_seguranca

    with pytest.raises(RuntimeError, match="32 caracteres"):
        configurar_seguranca(Flask(__name__))


def test_desenvolvimento_configura_cookies_e_expiracao(monkeypatch):
    monkeypatch.setenv("ECOTECH_ENV", "development")
    monkeypatch.setenv("ECOTECH_JWT_EXPIRACAO_HORAS", "999")
    from flask import Flask

    from ecotech.infrastructure.web import configurar_seguranca

    app = Flask(__name__)
    configurar_seguranca(app)
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["JWT_EXPIRACAO_HORAS"] == 168
