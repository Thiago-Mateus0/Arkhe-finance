"""Parser do CSV de conta do Nubank: Data,Valor,Identificador,Descrição."""
import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ParsedRow:
    date: str  # ISO yyyy-mm-dd
    amount_cents: int
    source_id: str
    description: str
    counterparty: str
    dedupe_key: str


_PIX = re.compile(
    r"^Transferência (?:recebida|enviada|Recebida)(?: pelo Pix)?(?: via Open Banking - Iniciada por: [^-]+)? - (?P<nome>.+?) - (?:•••|\d)",
    re.IGNORECASE,
)


def counterparty_of(description: str) -> str:
    m = _PIX.match(description)
    return " ".join(m.group("nome").split()).upper() if m else ""


def parse_nubank_conta(content: str | bytes) -> list[ParsedRow]:
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    required = {"Data", "Valor", "Identificador", "Descrição"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError(f"CSV não parece ser de conta Nubank; colunas: {reader.fieldnames}")

    rows: list[ParsedRow] = []
    seen: dict[str, int] = {}
    for rec in reader:
        if not rec["Data"].strip():
            continue
        date = datetime.strptime(rec["Data"].strip(), "%d/%m/%Y").date().isoformat()
        cents = int((Decimal(rec["Valor"].strip()) * 100).to_integral_value())
        desc = rec["Descrição"].strip()
        sid = rec["Identificador"].strip()
        # O ID do Nubank não é único (Pix no crédito repete o ID com sinais opostos),
        # então a chave inclui valor e descrição; o contador cobre linhas idênticas.
        base = f"nubank_conta|{sid}|{cents}|{desc}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        key = hashlib.sha256(f"{base}|{n}".encode()).hexdigest()
        rows.append(ParsedRow(date, cents, sid, desc, counterparty_of(desc), key))
    return rows


def _brl_to_cents(raw: str) -> int:
    """'20,00' -> 2000; '- 180,00' -> -18000; '1.234,56' -> 123456."""
    txt = raw.replace(" ", "").replace(".", "").replace(",", ".")
    return int((Decimal(txt) * 100).to_integral_value())


def detect_format(content: str) -> str:
    header = content.lstrip("\ufeff").splitlines()[0].strip().lower() if content.strip() else ""
    if header.startswith("data,valor,identificador"):
        return "nubank_conta"
    if header == "date,title,amount":
        return "nubank_fatura"
    raise ValueError(f"Formato de CSV não reconhecido (cabeçalho: {header!r})")


def parse_nubank_fatura(content: str | bytes) -> list[ParsedRow]:
    """Fatura do cartão: gasto positivo vira valor negativo (saída); pagamento/estorno vem negativo."""
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    rows: list[ParsedRow] = []
    seen: dict[str, int] = {}
    for rec in csv.DictReader(io.StringIO(content)):
        if not (rec.get("date") or "").strip():
            continue
        date = rec["date"].strip()
        datetime.strptime(date, "%Y-%m-%d")
        title = rec["title"].strip()
        cents = -_brl_to_cents(rec["amount"])
        # Sem identificador: linhas idênticas no mesmo dia são compras distintas (ex.: duas corridas de 4,60).
        base = f"nubank_fatura||{date}|{cents}|{title}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        key = hashlib.sha256(f"{base}|{n}".encode()).hexdigest()
        rows.append(ParsedRow(date, cents, "", title, title.upper(), key))
    return rows
