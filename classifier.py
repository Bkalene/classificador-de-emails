"""
classifier.py — Classifica e-mails usando Gemini via google-genai SDK.
Categorias: URGENTE | IMPORTANTE | INFORMATIVO | LIXO
"""
import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()

# Modelos em ordem de preferência (fallback automático)
MODELS_PRIORITY = [
    "gemini-2.5-flash",       # melhor custo-beneficio
    "gemini-2.0-flash",       # fallback
    "gemini-2.0-flash-lite",  # fallback leve
]

CATEGORIES = ["URGENTE", "IMPORTANTE", "INFORMATIVO", "LIXO"]

SYSTEM_PROMPT = """Voce e um assistente especialista em organizacao de e-mails pessoais.
Sua tarefa e classificar cada e-mail em UMA das seguintes categorias:

- URGENTE: Requer acao do usuario em ate 24h (pagamentos, reunioes, prazos, respostas urgentes)
- IMPORTANTE: Relevante para o usuario, mas sem prazo imediato (noticias de trabalho, atualizacoes de projetos, e-mails de contatos conhecidos)
- INFORMATIVO: Pode ser lido depois ou ignorado (newsletters, artigos, updates de sistemas, notificacoes automaticas)
- LIXO: Spam, propagandas, promocoes genericas, e-mails nao solicitados

Responda APENAS com um JSON valido no formato:
{
  "category": "URGENTE|IMPORTANTE|INFORMATIVO|LIXO",
  "reason": "Breve justificativa em portugues (max. 100 chars)",
  "confidence": 0.0
}

O campo confidence deve ser um numero entre 0.0 e 1.0."""


def _build_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY nao encontrada no .env")
    return genai.Client(api_key=api_key)


def classify_email(email: dict[str, Any], client: genai.Client | None = None) -> dict[str, Any]:
    """
    Classifica um unico e-mail e retorna a categoria + justificativa.
    Reutiliza o `client` fornecido para evitar multiplas instancias.
    """
    if client is None:
        client = _build_client()

    email_context = (
        f"De: {email.get('sender', '')}\n"
        f"Assunto: {email.get('subject', '')}\n"
        f"Trecho: {email.get('snippet', '')}\n"
        f"Corpo (inicio): {email.get('body', '')[:500]}"
    )

    prompt = f"{SYSTEM_PROMPT}\n\nClassifique este e-mail:\n{email_context}"

    last_error = None
    for model in MODELS_PRIORITY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1),
                )
                break  # sucesso
            except APIError as e:
                error_str = str(e)
                if "429" in error_str or "503" in error_str:
                    wait = (attempt + 1) * 10
                    print(f"    ⚠️  Modelo {model} sobrecarregado (esperando {wait}s e tentando de novo)...")
                    time.sleep(wait)
                    last_error = e
                else:
                    raise
        else:
            # Todos os attempts falharam nesse modelo, tenta proximo
            continue
        break  # modelo funcionou, sai do loop de modelos
    else:
        raise RuntimeError(f"Todos os modelos falharam. Ultimo erro: {last_error}")

    raw = response.text.strip()

    # Remove blocos de codigo markdown se presentes
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        if result.get("category") not in CATEGORIES:
            result["category"] = "INFORMATIVO"
    except json.JSONDecodeError:
        result = {
            "category": "INFORMATIVO",
            "reason": "Erro ao processar - classificado como padrao",
            "confidence": 0.5,
        }

    return {**email, **result}


def classify_all(emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classifica uma lista de e-mails, reutilizando a mesma instancia client."""
    client = _build_client()
    classified = []
    total = len(emails)

    for i, email in enumerate(emails, 1):
        subject = email.get("subject", "")[:50]
        print(f"  [{i}/{total}] Classificando: {subject}...")
        result = classify_email(email, client)
        classified.append(result)

        # Espera 4 segundos para não estourar o limite da API Gratuita (15 req/minuto)
        if i < total:
            time.sleep(4)

    return classified


if __name__ == "__main__":
    test_email = {
        "id": "test123",
        "sender": "chefe@empresa.com",
        "subject": "URGENTE: Reuniao amanha as 9h - confirme presenca",
        "snippet": "Precisamos de sua confirmacao ate hoje as 18h.",
        "body": "Ola, temos uma reuniao importante amanha. Por favor confirme.",
    }
    print("Testando classificador Gemini...")
    result = classify_email(test_email)
    print(f"\nResultado:")
    print(f"  Categoria:  {result['category']}")
    print(f"  Motivo:     {result['reason']}")
    print(f"  Confianca:  {result['confidence']:.0%}")
