"""
executor.py — Aplica as ações aprovadas no Gmail.
Move e-mails para labels ou envia para a lixeira.
"""
from typing import Any
import os

from googleapiclient.discovery import build

from auth import get_credentials
from memory import save_feedback

# Mapeamento de categoria → nome da label no Gmail
LABEL_NAMES = {
    "URGENTE": "AgentEmail/Urgente",
    "IMPORTANTE": "AgentEmail/Importante",
    "INFORMATIVO": "AgentEmail/Informativo",
}


def _get_or_create_label(service, user_id: str, name: str) -> str:
    """Obtém o ID de uma label existente ou cria uma nova."""
    existing = service.users().labels().list(userId=user_id).execute()
    for label in existing.get("labels", []):
        if label["name"] == name:
            return label["id"]

    # Cria a label (e a parent se necessário)
    new_label = service.users().labels().create(
        userId=user_id,
        body={
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    ).execute()
    return new_label["id"]


def _ensure_labels(service) -> dict[str, str]:
    """Garante que todas as labels necessárias existem e retorna seus IDs."""
    label_ids = {}
    for category, label_name in LABEL_NAMES.items():
        label_ids[category] = _get_or_create_label(service, "me", label_name)
    return label_ids


def execute_actions(
    emails: list[dict[str, Any]],
    original_emails: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Executa as ações no Gmail para cada e-mail aprovado.
    - LIXO → manda para a lixeira
    - Demais → move para a label correspondente

    Salva feedback na memória para aprendizado.
    Retorna contagem de ações por categoria.
    """
    counts: dict[str, int] = {cat: 0 for cat in ["URGENTE", "IMPORTANTE", "INFORMATIVO", "LIXO"]}

    # Cria mapa de ID → categoria original
    original_map = {e["id"]: e.get("category", "INFORMATIVO") for e in original_emails}

    # Agrupa e-mails por token_file (conta)
    grouped_emails = {}
    for email in emails:
        tf = email.get("token_file")
        if tf:
            grouped_emails.setdefault(tf, []).append(email)

    for token_file, acct_emails in grouped_emails.items():
        try:
            creds = get_credentials(token_file)
            service = build("gmail", "v1", credentials=creds)
            label_ids = _ensure_labels(service)
        except Exception as e:
            print(f"  ⚠️  Erro ao conectar na conta {os.path.basename(token_file)}: {e}")
            continue

        for email in acct_emails:
            email_id = email["id"]
        final_cat = email.get("category", "INFORMATIVO")
        original_cat = original_map.get(email_id, final_cat)

        try:
            if final_cat == "LIXO":
                # Move para lixeira
                service.users().messages().trash(
                    userId="me",
                    id=email_id,
                ).execute()
            else:
                # Adiciona label e remove da INBOX para organizar
                label_id = label_ids.get(final_cat)
                if label_id:
                    service.users().messages().modify(
                        userId="me",
                        id=email_id,
                        body={
                            "addLabelIds": [label_id],
                            "removeLabelIds": ["INBOX"],
                        },
                    ).execute()

            counts[final_cat] += 1

            # Salva feedback na memória
            save_feedback(
                email_id=email_id,
                sender=email.get("sender", ""),
                original_category=original_cat,
                final_category=final_cat,
            )

        except Exception as e:
            print(f"  ⚠️  Erro ao processar e-mail {email_id}: {e}")

    return counts
