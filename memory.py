"""
memory.py — Memória de preferências do usuário.
Aprende com aprovações/rejeições para melhorar classificações futuras.
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.jsonl")


def save_feedback(email_id: str, sender: str, original_category: str, final_category: str) -> None:
    """Salva o feedback do usuário (aprovação ou edição de categoria)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "email_id": email_id,
        "sender": sender,
        "original_category": original_category,
        "final_category": final_category,
        "corrected": original_category != final_category,
    }
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_sender_preferences() -> dict[str, str]:
    """
    Carrega preferências aprendidas por remetente.
    Retorna {sender: most_common_final_category}.
    """
    if not os.path.exists(MEMORY_FILE):
        return {}

    sender_votes: dict[str, dict[str, int]] = {}

    with open(MEMORY_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            sender = entry.get("sender", "")
            category = entry.get("final_category", "")
            if sender and category:
                sender_votes.setdefault(sender, {})
                sender_votes[sender][category] = sender_votes[sender].get(category, 0) + 1

    # Retorna categoria majoritária por remetente
    preferences = {}
    for sender, votes in sender_votes.items():
        preferences[sender] = max(votes, key=votes.get)

    return preferences


def get_stats() -> dict:
    """Retorna estatísticas da memória."""
    if not os.path.exists(MEMORY_FILE):
        return {"total": 0, "corrections": 0}

    total = 0
    corrections = 0
    with open(MEMORY_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                total += 1
                if entry.get("corrected"):
                    corrections += 1

    return {"total": total, "corrections": corrections}
