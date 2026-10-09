"""Gera CSVs 100% fictícios no formato do Nubank para demonstração e portfólio.

Determinístico (semente fixa): rodar de novo produz os mesmos arquivos.
Nada aqui vem de dado real: nomes, empresas e valores são inventados.
    python scripts/gerar_demo.py
"""
import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "demo"
rng = random.Random(42)
NS = uuid.UUID("00000000-0000-0000-0000-00000000f1a4")
DONO = "JOAO PEDRO ALMEIDA"  # usado em FINANCAS_OWN_NAMES na demo

BANCO = "NU PAGAMENTOS - IP (0260) Agência: 1 Conta: 1234567-8"


def pix(tipo: str, nome: str, doc: str = "•••.123.456-••") -> str:
    verbo = "recebida" if tipo == "in" else "enviada"
    return f"Transferência {verbo} pelo Pix - {nome} - {doc} - {BANCO}"


def pix_app(nome: str, cnpj: str) -> str:
    return (f"Transferência enviada pelo Pix via Open Banking - Iniciada por: PagFacil - {nome} - {cnpj}"
            " - BANCO EXEMPLO S.A. Agência: 1 Conta: 99-9")


def fmt_conta(v: float) -> str:
    return f"{v:.2f}"


def fmt_fatura(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def mes_conta(ano: int, mes: int, ate: int) -> list[tuple[date, float, str]]:
    d = lambda dia: date(ano, mes, dia)
    r: list[tuple[date, float, str]] = []
    if ate >= 5:
        r.append((d(5), 3200.00, f"Transferência Recebida - TECNOVA SISTEMAS LTDA - 11.111.111/0001-11 - {BANCO}"))
    # repasses: amigos mandam, o app de pagamentos leva o mesmo valor (às vezes a soma de dois Pix)
    for dia in (2, 6, 9, 13, 16, 20, 24):
        if dia > ate:
            continue
        a, b = rng.choice([10, 15, 20, 25]), rng.choice([10, 20, 30])
        r += [(d(dia), a, pix("in", "LUCAS ANDRADE")), (d(dia), b, pix("in", "BIA CARVALHO")),
              (d(dia), -(a + b), pix_app("LOJA DE INGRESSOS EXEMPLO LTDA", "22.222.222/0001-22"))]
        c = rng.choice([20, 40])
        r += [(d(dia), c, pix("in", "LUCAS ANDRADE")), (d(dia), -c, pix_app("LOJA DE INGRESSOS EXEMPLO LTDA", "22.222.222/0001-22"))]
    if ate >= 7:
        r.append((d(7), -rng.choice([850.00, 900.00]), pix("out", "IMOBILIARIA SOL LTDA", "33.333.333/0001-33")))
    if ate >= 8:
        r.append((d(8), -39.90, pix("out", "PADARIA PAO QUENTE LTDA", "44.444.444/0001-44")))
    if ate >= 10:  # Pix no crédito: entrada fictícia + Pix de saída, mesmo identificador
        r += [(d(10), 120.00, "Valor adicionado na conta por cartão de crédito - Valor adicionado para Pix no Crédito"),
              (d(10), -120.00, pix("out", "BARBEARIA DO ZE LTDA", "55.555.555/0001-55"))]
    if ate >= 12:
        r += [(d(12), -85.00, pix("out", "CARLA MENDES FERREIRA")), (d(12), -40.00, pix("out", "RAFAEL TORRES"))]
    if ate >= 14:
        r.append((d(14), -289.90, pix("out", "SOCIEDADE EDUCACIONAL HORIZONTE LTDA", "66.666.666/0001-66")))
    if ate >= 15:  # transferência entre contas próprias: não é gasto nem receita
        r += [(d(15), -300.00, pix("out", DONO)), (d(15), 300.00, pix("in", DONO))]
    if ate >= 18:
        r.append((d(18), -59.90, pix("out", "ACADEMIA FORMA FISICA LTDA", "77.777.777/0001-77")))
    if ate >= 21:
        r.append((d(21), 150.00, pix("in", "MARIA ALMEIDA")))
    if ate >= 25:
        r.append((d(25), -rng.choice([612.38, 540.10, 705.25]), "Pagamento de fatura"))
    return r


def escrever_conta(nome: str, linhas: list[tuple[date, float, str]], chave: str) -> None:
    with open(OUT / nome, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Data", "Valor", "Identificador", "Descrição"])
        ids: dict[str, str] = {}
        for i, (dia, v, desc) in enumerate(sorted(linhas, key=lambda x: x[0])):
            par = desc.startswith("Valor adicionado na conta") or (dia.day == 10 and abs(v) == 120)
            ident = str(uuid.uuid5(NS, f"{chave}-{dia}-pix-credito" if par else f"{chave}-{i}"))
            w.writerow([dia.strftime("%d/%m/%Y"), fmt_conta(v), ident, desc])


def fatura() -> list[tuple[date, str, float]]:
    r: list[tuple[date, str, float]] = []
    dia, fim = date(2026, 8, 1), date(2026, 10, 8)
    while dia <= fim:
        k = dia.toordinal()
        if k % 2 == 0:
            r.append((dia, rng.choice(["Uber Uber *Trip Help.U", "99*"]), round(rng.uniform(6, 28), 2)))
        if k % 6 == 0:
            r.append((dia, rng.choice(["Ifd*Lanchonete Exemplo", "99Food *Pizzaria"]), round(rng.uniform(22, 64), 2)))
        if k % 17 == 0:
            r.append((dia, "Farmacia Boa Saude", round(rng.uniform(12, 70), 2)))
        if k % 23 == 0:
            r.append((dia, "Recarga de celular", 20.0))
        if dia.day == 11:
            r += [(dia, "Netflix.com", 39.90), (dia, "Spotify", 21.90)]
        if dia.day == 15:
            r.append((dia, "Pix no Crédito - INGRESSOS EXEMPLO", 15.52))
        if k % 29 == 0:
            r.append((dia, "Livraria Cultura Exemplo", round(rng.uniform(45, 120), 2)))
        if dia.day in (17, 18) and dia.month in (8, 9):
            r.append((dia, "Pagamento recebido", -rng.choice([612.38, 540.10])))
        dia += timedelta(days=1)
    r.append((date(2026, 9, 21), "Studio Fotos Pontual", 33.00))
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ano, mes, ate, nome in [(2026, 8, 31, "nubank_conta_2026-08.csv"), (2026, 9, 30, "nubank_conta_2026-09.csv"),
                                (2026, 10, 8, "nubank_conta_2026-10.csv")]:
        escrever_conta(nome, mes_conta(ano, mes, ate), f"{ano}-{mes}")
    with open(OUT / "nubank_fatura_demo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "title", "amount"])
        for dia, titulo, v in sorted(fatura(), key=lambda x: x[0], reverse=True):
            w.writerow([dia.isoformat(), titulo, fmt_fatura(v)])
    print("ok:", ", ".join(sorted(p.name for p in OUT.glob("*.csv"))))


if __name__ == "__main__":
    main()
