"""Gera o logo "pedra-chave" do Arkhe Finance (SVG) em web/public/. Determinístico, sem dependência.

Geometria medida na prancha do Thiago (arco de 5 pedras sobre dois pilares), numa caixa de 100 x 84,9:
arco externo de raio 50 em (50, 50); abertura interna de raio 26,7 centrada em (50, 55,9), então o anel é
mais grosso no topo (29) que nas laterais (23). As frestas de 3,4 não são radiais: as da pedra-chave saem de (50, 62) a 15,3 graus da
vertical (a pedra estreita para baixo, como na prancha) e as outras de (50, 55,5) a 53,8 graus. O arco é cortado em y = 53,8 e os pilares começam em 57,2.

Uso: python scripts/gerar_logo.py     (os PNGs saem de: rsvg-convert, ver o fim deste arquivo)
"""
import math
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "web" / "public"
CX = CY = 50
R, r = 50, 26.7
CYI = 55.9  # centro da abertura interna
GAP = 3.4
CORTE_Y, PILAR_Y, ALTURA = 53.8, 57.2, 84.9

TEMAS = {
    "escuro": {"chave": "#22d3ee", "azul": "#5b72f2", "roxo": "#6c5cf0", "fundo": "#0b1220"},
    "claro": {"chave": "#0e7490", "azul": "#3f5bd9", "roxo": "#5148c9", "fundo": "#f3f2ee"},
    "mono": {"chave": "#ffffff", "azul": "#8a8f98", "roxo": "#8a8f98", "fundo": "#0b1220"},
}


# (origem, ângulo a partir da vertical); o ângulo é assinado: negativo é a esquerda
CHAVE = (50.0, 62.0)
LATERAL = (50.0, 55.5)
FRESTAS = [(LATERAL, -53.8), (CHAVE, -15.3), (CHAVE, 15.3), (LATERAL, 53.8)]


def _corta(borda: tuple, centro: tuple[float, float], raio: float) -> tuple[float, float]:
    """Onde a fresta (um raio que sai da origem) encontra o círculo; a origem fica dentro dele."""
    (ox0, oy0), grau = borda
    a = math.radians(grau)
    dx, dy = math.sin(a), -math.cos(a)
    ox, oy = ox0 - centro[0], oy0 - centro[1]
    b = ox * dx + oy * dy
    t = -b + math.sqrt(b * b - (ox * ox + oy * oy - raio * raio))
    return ox0 + t * dx, oy0 + t * dy


def setor(e: tuple, d: tuple) -> str:
    (x1, y1), (x2, y2) = _corta(e, (CX, CY), R), _corta(d, (CX, CY), R)
    (x3, y3), (x4, y4) = _corta(d, (CX, CYI), r), _corta(e, (CX, CYI), r)
    return (f"M{x1:.2f} {y1:.2f}A{R} {R} 0 0 1 {x2:.2f} {y2:.2f}"
            f"L{x3:.2f} {y3:.2f}A{r} {r} 0 0 0 {x4:.2f} {y4:.2f}Z")


def marca(cores: dict, uid: str = "m") -> str:
    """O logo em uma caixa de 100 x 84,9 (use dentro de um <svg viewBox>)."""
    frestas = "".join(
        f'<line x1="{o[0]}" y1="{o[1]}" '
        f'x2="{o[0] + 90 * math.sin(math.radians(g)):.2f}" y2="{o[1] - 90 * math.cos(math.radians(g)):.2f}"/>'
        for o, g in FRESTAS)
    return (
        f'<defs><mask id="{uid}f" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="{ALTURA}">'
        f'<rect width="100" height="{CORTE_Y}" fill="#fff"/>'
        f'<g stroke="#000" stroke-width="{GAP}">{frestas}</g></mask></defs>'
        f'<g mask="url(#{uid}f)">'
        f'<path fill="{cores["roxo"]}" d="{setor((LATERAL, -95), FRESTAS[0])}"/><path fill="{cores["roxo"]}" d="{setor(FRESTAS[3], (LATERAL, 95))}"/>'
        f'<path fill="{cores["azul"]}" d="{setor(FRESTAS[0], FRESTAS[1])}"/><path fill="{cores["azul"]}" d="{setor(FRESTAS[2], FRESTAS[3])}"/>'
        f'<path fill="{cores["chave"]}" d="{setor(FRESTAS[1], FRESTAS[2])}"/></g>'
        f'<rect x="0" y="{PILAR_Y}" width="{CX - r:.1f}" height="{ALTURA - PILAR_Y:.1f}" fill="{cores["roxo"]}"/>'
        f'<rect x="{CX + r:.1f}" y="{PILAR_Y}" width="{CX - r:.1f}" height="{ALTURA - PILAR_Y:.1f}" fill="{cores["roxo"]}"/>'
    )


def logo_svg(tema: str = "escuro") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 {ALTURA}">'
            f'{marca(TEMAS[tema])}</svg>\n')


def icone_svg(escala: float = 0.58, tema: str = "escuro", raio: int = 112) -> str:
    """Ícone quadrado de 512: fundo escuro, logo centralizado. `escala` menor deixa margem para máscara."""
    c = TEMAS[tema]
    w = 512 * escala
    k = w / 100
    x, y = (512 - w) / 2, (512 - ALTURA * k) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<rect width="512" height="512" rx="{raio}" fill="{c["fundo"]}"/>'
            f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})">{marca(c, "i")}</g></svg>\n')


if __name__ == "__main__":
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "logo.svg").write_text(logo_svg("escuro"), encoding="utf-8")
    (PUBLIC / "icon.svg").write_text(icone_svg(0.58), encoding="utf-8")
    (PUBLIC / "icon-maskable.svg").write_text(icone_svg(0.46, raio=0), encoding="utf-8")  # sem cantos: o sistema recorta
    print("gerado em", PUBLIC)
# PNGs (iPhone/Android): rsvg-convert -w 180 web/public/icon.svg -o web/public/icon-180.png  (e 192, 512)
