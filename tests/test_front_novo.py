"""O front (ADR 0021) é servido a partir de web/dist, sem sair da pasta do build."""
import pytest
from fastapi.testclient import TestClient

from financas import api, db


@pytest.fixture
def dist(monkeypatch, tmp_path):
    pasta = tmp_path / "dist"
    (pasta / "assets").mkdir(parents=True)
    (pasta / "index.html").write_text("<title>Arkhe</title>", encoding="utf-8")
    (pasta / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (pasta / "manifest.webmanifest").write_text('{"name": "Arkhe Finance"}', encoding="utf-8")
    (pasta / "icon.svg").write_text("<svg></svg>", encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("fora do dist", encoding="utf-8")
    monkeypatch.setattr(api, "WEB_DIST", pasta)
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "t.db")
    return TestClient(api.app)


def test_serve_index_assets_manifesto_e_icone(dist):
    assert "Arkhe" in dist.get("/").text
    assert dist.get("/assets/app.js").text == "console.log(1)"
    assert dist.get("/manifest.webmanifest").json()["name"] == "Arkhe Finance"
    assert "<svg" in dist.get("/icon.svg").text


def test_api_continua_funcionando_junto_com_o_front(dist):
    assert dist.get("/months").json() == []
    assert dist.get("/categories").status_code == 200


def test_sem_build_explica_o_que_fazer(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "WEB_DIST", tmp_path / "nao-existe")
    r = TestClient(api.app).get("/")
    assert r.status_code == 404
    assert "run.sh" in r.json()["detail"]


def test_arquivo_inexistente_e_404(dist):
    assert dist.get("/assets/nao-existe.js").status_code == 404


def test_nao_sai_da_pasta_do_build(dist):
    for tentativa in ("/assets/..%2fsegredo.txt", "/assets/%2e%2e/segredo.txt", "/assets/..%2f..%2fsegredo.txt"):
        assert "fora do dist" not in dist.get(tentativa).text, tentativa
