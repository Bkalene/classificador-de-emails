"""
auth.py — Autenticação OAuth2 com Gmail API.
Execute este arquivo UMA VEZ para gerar o token.json.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Permissões necessárias: leitura + modificação de labels/lixeira
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")


def get_credentials(token_file: str) -> Credentials:
    """Retorna credenciais válidas a partir do arquivo de token especificado."""
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "credentials.json não encontrado!\n"
                    "Baixe em: https://console.cloud.google.com → APIs → Gmail API → Credenciais"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds


if __name__ == "__main__":
    import sys
    # Fix encoding para terminal Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        
    print("🔐 Configuração de Múltiplas Contas Gmail")
    print("Digite um apelido para a conta que vai autenticar (ex: pessoal, trabalho, kalene)")
    nome_conta = input("> Apelido: ").strip().lower()
    
    if not nome_conta:
        print("❌ Nome inválido.")
        sys.exit(1)
        
    token_path = os.path.join(BASE_DIR, f"token_{nome_conta}.json")
    print(f"\nIniciando autenticação para gerar {os.path.basename(token_path)}...")
    creds = get_credentials(token_path)
    print(f"✅ Autenticação concluída! {os.path.basename(token_path)} gerado com sucesso.")
