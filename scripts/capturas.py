"""Gera as capturas de tela de docs/img/ a partir da demonstração fictícia (data/demo/).

Playwright é opcional e só serve para isto (por isso fica fora das dependências do app):
    pip install -e ".[capturas]"
    python scripts/capturas.py
Usa o Chrome instalado; sem ele, rode antes `playwright install chromium`.
Nunca lê o banco real: cria um banco descartável com dados fictícios.
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / "docs" / "img"
PORTA = 8765
CELULAR, COMPUTADOR = {"width": 390, "height": 844}, {"width": 1280, "height": 800}
ORCAMENTOS = [("Transporte", "250"), ("Delivery", "135"), ("Alimentação", "200"), ("Saúde", "100")]


def preparar_banco(caminho: Path) -> dict:
    env = {**os.environ, "FINANCAS_DB": str(caminho), "FINANCAS_OWN_NAMES": "JOAO PEDRO ALMEIDA"}
    py = [sys.executable, "-m", "financas"]
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_demo.py")], check=True, env=env, capture_output=True)
    subprocess.run(py + ["import", *map(str, sorted((RAIZ / "data" / "demo").glob("*.csv")))], check=True, env=env, capture_output=True)
    for cat, valor in ORCAMENTOS:
        subprocess.run(py + ["orcamento", cat, valor], check=True, env=env, capture_output=True)
    return env


def esperar(url: str) -> None:
    for _ in range(50):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.2)
    raise SystemExit("servidor não subiu")


def main() -> None:
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp:
        env = preparar_banco(Path(tmp) / "capturas.db")
        srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "financas.api:app", "--port", str(PORTA)],
                               env=env, cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{PORTA}"
        try:
            esperar(url)
            with sync_playwright() as p:
                try:
                    nav = p.chromium.launch(channel="chrome")
                except Exception:
                    nav = p.chromium.launch()
                erros: list[str] = []

                def pagina(vp, claro=False):
                    pg = nav.new_page(viewport=vp)
                    pg.on("pageerror", lambda e: erros.append(str(e)))
                    pg.goto(url)
                    pg.wait_for_selector(".page .card")
                    if claro:
                        pg.click('[aria-label="Usar tema claro"]')
                    pg.wait_for_timeout(1800)  # animações de entrada
                    return pg

                def ir(pg, rota):
                    pg.evaluate("rota => { location.hash = '#/' + rota }", rota)
                    pg.wait_for_timeout(1500)

                def tirar(pg, nome):
                    pg.screenshot(path=str(IMG / f"{nome}.png"))
                    print("ok", nome)

                for claro in (False, True):
                    sufixo = "-claro" if claro else ""
                    pg = pagina(CELULAR, claro)
                    tirar(pg, f"inicio{sufixo}")
                    ir(pg, "gastos"); tirar(pg, f"gastos{sufixo}")
                    if not claro:
                        pg.mouse.wheel(0, 700); pg.wait_for_timeout(500); tirar(pg, "gastos-categorias")
                    ir(pg, "atividades"); tirar(pg, f"atividades{sufixo}")
                    if not claro:
                        pg.locator("button.tx").first.click(); pg.wait_for_timeout(700); tirar(pg, "categorizar")
                        pg.keyboard.press("Escape")
                        ir(pg, "regras"); tirar(pg, "regras")
                        ir(pg, "fluxo"); tirar(pg, "fluxo")
                    ir(pg, "orcamento"); tirar(pg, f"orcamento{sufixo}")
                    pg.close()

                for claro in (False, True):
                    pg = pagina(COMPUTADOR, claro)
                    tirar(pg, "computador-claro" if claro else "computador")
                    if not claro:
                        ir(pg, "orcamento"); tirar(pg, "computador-orcamento")
                    pg.close()

                nav.close()
                if erros:
                    raise SystemExit(f"erros de JS: {erros}")
        finally:
            srv.terminate()


if __name__ == "__main__":
    main()
