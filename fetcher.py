"""
fetcher.py — Busca e-mails das últimas 24h via Gmail API.
"""
import base64
import email
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from googleapiclient.discovery import build

from auth import get_credentials


def _decode_body(payload: dict) -> str:
    """Extrai o texto do corpo do e-mail (preferindo text/plain)."""
    body = ""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    elif mime_type.startswith("multipart"):
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break

    return body[:2000]  # Limita para não estourar tokens do Gemini


def _get_header(headers: list[dict], name: str) -> str:
    """Extrai um header específico da lista de headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_recent_emails(token_file: str, hours: int = 24, max_results: int = 50, unread_only: bool = False) -> list[dict[str, Any]]:
    """
    Busca e-mails recentes.
    Exclui e-mails já na lixeira ou spam.
    """
    creds = get_credentials(token_file)
    service = build("gmail", "v1", credentials=creds)

    # Calcula timestamp de corte
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = f"after:{int(since.timestamp())} -in:trash -in:spam -in:sent"
    
    if unread_only:
        query += " is:unread"

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full",
        ).execute()

        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        email_obj = {
            "id": msg["id"],
            "thread_id": msg_data.get("threadId"),
            "subject": _get_header(headers, "Subject") or "(sem assunto)",
            "sender": _get_header(headers, "From"),
            "date": _get_header(headers, "Date"),
            "snippet": msg_data.get("snippet", ""),
            "body": _decode_body(payload),
            "label_ids": msg_data.get("labelIds", []),
            "token_file": token_file,
            "account_name": os.path.basename(token_file).replace("token_", "").replace(".json", ""),
        }
        emails.append(email_obj)

    return emails


if __name__ == "__main__":
    print("Para testar, use o main.py. O fetcher agora requer um token_file.")
