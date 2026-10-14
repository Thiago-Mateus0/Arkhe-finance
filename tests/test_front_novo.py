"""O app novo (ADR 0021) é servido em /novo a partir de web/dist, sem sair da pasta."""
from fastapi.testclient import TestClient

from financas import api


def _cliente(monkeypatch, tmp_path, com_build=True):
    dist = tmp_path / "dist"
    if com_build:
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<title>novo</title>", encoding="utf-8")
        (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("fora do dist", encoding="utf-8")
    monkeypatch.setattr(api, "WEB_DIST", dist)
    return TestClient(api.app)


def test_serve_index_e_assets(monkeypatch, tmp_path):
    c = _cliente(monkeypatch, tmp_path)
    assert "novo" in c.get("/novo").text
    assert "novo" in c.get("/novo/").text
    assert c.get("/novo/assets/app.js").text == "console.log(1)"


def test_sem_build_explica_o_que_fazer(monkeypatch, tmp_path):
    c = _cliente(monkeypatch, tmp_path, com_build=False)
    r = c.get("/novo")
    assert r.status_code == 404
    assert "run.sh" in r.json()["detail"]


def test_arquivo_inexistente_e_404_e_nao_a_pagina(monkeypatch, tmp_path):
    c = _cliente(monkeypatch, tmp_path)
    assert c.get("/novo/assets/nao-existe.js").status_code == 404


def test_nao_sai_da_pasta_do_build(monkeypatch, tmp_path):
    c = _cliente(monkeypatch, tmp_path)
    for tentativa in ("/novo/..%2fsegredo.txt", "/novo/%2e%2e/segredo.txt", "/novo/assets/..%2f..%2fsegredo.txt"):
        r = c.get(tentativa)
        assert "fora do dist" not in r.text, tentativa


def test_app_antigo_continua_em_raiz(monkeypatch, tmp_path):
    c = _cliente(monkeypatch, tmp_path)
    assert c.get("/").status_code == 200
