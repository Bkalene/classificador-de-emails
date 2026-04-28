"""
summarizer.py — Gera o relatório diário em Markdown.
"""
import os
import sys
from datetime import datetime
from typing import Any

# Fix encoding para terminal Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "daily_report.md")

CATEGORY_ICONS = {
    "URGENTE": "🔴",
    "IMPORTANTE": "🟡",
    "INFORMATIVO": "🟢",
    "LIXO": "🗑️",
}

CATEGORY_DESCRIPTIONS = {
    "URGENTE": "Requer sua ação hoje",
    "IMPORTANTE": "Leia quando puder",
    "INFORMATIVO": "Pode arquivar",
    "LIXO": "Será movido para a lixeira",
}


def generate_report(classified_emails: list[dict[str, Any]]) -> str:
    """Gera o relatório diário e salva em daily_report.md."""
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")
    total = len(classified_emails)

    # Agrupa por categoria
    groups: dict[str, list] = {cat: [] for cat in CATEGORY_ICONS}
    for email in classified_emails:
        cat = email.get("category", "INFORMATIVO")
        groups.setdefault(cat, []).append(email)

    lines = [
        f"# 📬 Relatório de E-mails — {now}",
        f"\n**Total analisado:** {total} e-mail(s)\n",
    ]

    # Resumo por categoria
    lines.append("## Resumo\n")
    lines.append("| Categoria | Qtd | Ação |")
    lines.append("|-----------|-----|------|")
    for cat, icon in CATEGORY_ICONS.items():
        count = len(groups[cat])
        desc = CATEGORY_DESCRIPTIONS[cat]
        lines.append(f"| {icon} {cat} | {count} | {desc} |")

    lines.append("")

    # Detalhes por categoria (mais importantes primeiro)
    for cat in ["URGENTE", "IMPORTANTE", "INFORMATIVO", "LIXO"]:
        emails_in_cat = groups[cat]
        if not emails_in_cat:
            continue

        icon = CATEGORY_ICONS[cat]
        lines.append(f"\n## {icon} {cat} ({len(emails_in_cat)})\n")

        for i, email in enumerate(emails_in_cat, 1):
            sender = email.get("sender", "Desconhecido")[:50]
            subject = email.get("subject", "(sem assunto)")[:70]
            reason = email.get("reason", "")
            confidence = email.get("confidence", 0)
            date = email.get("date", "")[:16]

            lines.append(f"### {i}. {subject}")
            lines.append(f"- **De:** {sender}")
            lines.append(f"- **Data:** {date}")
            lines.append(f"- **Motivo:** {reason}")
            lines.append(f"- **Confiança:** {confidence:.0%}")
            lines.append(f"- **ID:** `{email.get('id', '')}`")
            lines.append("")

    # Rodapé com instruções
    lines.append("---")
    lines.append("*Execute `python main.py` para aplicar as ações após revisão.*")

    report = "\n".join(lines)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    return report


if __name__ == "__main__":
    # Teste com dados fictícios
    test_emails = [
        {"id": "1", "sender": "chefe@empresa.com", "subject": "Reunião URGENTE amanhã", "date": "Mon, 28 Apr 2026", "category": "URGENTE", "reason": "Requer confirmação hoje", "confidence": 0.95},
        {"id": "2", "sender": "newsletter@tech.com", "subject": "Top 10 artigos da semana", "date": "Mon, 28 Apr 2026", "category": "INFORMATIVO", "reason": "Newsletter automática", "confidence": 0.88},
        {"id": "3", "sender": "promo@loja.com", "subject": "50% OFF hoje só!", "date": "Mon, 28 Apr 2026", "category": "LIXO", "reason": "Promoção não solicitada", "confidence": 0.99},
    ]
    report = generate_report(test_emails)
    print(report.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
    print(f"\n✅ Relatório salvo em: {REPORT_FILE}")
