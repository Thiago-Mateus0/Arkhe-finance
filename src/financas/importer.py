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
