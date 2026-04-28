"""
main.py — Ponto de entrada do Email Agent.
Orquestra: Fetch → Classify → Summarize → Approve → Execute
"""
import sys
import os
import glob
from datetime import datetime

# Fix encoding para terminal Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel

from fetcher import fetch_recent_emails
from classifier import classify_all
from summarizer import generate_report, REPORT_FILE
from approval import run_approval
from executor import execute_actions
from memory import get_stats

console = Console()


def print_banner() -> None:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    console.print(Panel.fit(
        f"[bold cyan]📧 Email Agent[/bold cyan] [dim]powered by Gemini[/dim]\n"
        f"[dim]Executando em: {now}[/dim]",
        border_style="cyan"
    ))
    console.print()


def print_step(step: int, total: int, description: str) -> None:
    console.print(f"[bold cyan][{step}/{total}][/bold cyan] {description}")


def print_done(counts: dict) -> None:
    lines = ["[bold green]✅ Ações executadas com sucesso![/bold green]\n"]
    for cat, count in counts.items():
        if count > 0:
            lines.append(f"  • {cat}: {count} e-mail(s)")
    console.print(Panel("\n".join(lines), border_style="green"))

    stats = get_stats()
    console.print(
        f"\n[dim]📊 Memória: {stats['total']} e-mails processados, "
        f"{stats['corrections']} correções aprendidas[/dim]"
    )


def main() -> None:
    print_banner()

    # Passo 1: Buscar e-mails para todas as contas conectadas
    token_files = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "token_*.json"))
    if not token_files:
        console.print("[bold red]❌ Nenhuma conta configurada![/bold red]")
        console.print("[yellow]👉 Rode `python auth.py` para adicionar suas contas.[/yellow]")
        sys.exit(1)

    print_step(1, 4, f"Buscando e-mails em {len(token_files)} conta(s)...")
    
    all_emails = []
    for token_file in token_files:
        account_name = os.path.basename(token_file).replace("token_", "").replace(".json", "")
        console.print(f"   [dim]Buscando conta: {account_name}[/dim]")
        try:
            # Busca e-mails para esta conta
            emails = fetch_recent_emails(token_file=token_file, hours=24*30, max_results=30, unread_only=True)
            all_emails.extend(emails)
        except Exception as e:
            console.print(f"   [red]Erro na conta {account_name}: {e}[/red]")

    if not all_emails:
        console.print("\n[yellow]📭 Nenhum e-mail novo encontrado nas suas contas. Até amanhã![/yellow]")
        return

    console.print(f"   [green]→ {len(all_emails)} e-mail(s) encontrado(s) no total[/green]\n")

    # ── Passo 2: Classificar com Gemini ────────────────────────────────────
    print_step(2, 4, "Classificando com Gemini...")
    classified = classify_all(all_emails)
    console.print(f"   [green]→ Classificação concluída[/green]\n")

    # ── Passo 3: Gerar relatório ────────────────────────────────────────────
    print_step(3, 4, "Gerando relatório diário...")
    generate_report(classified)
    console.print(f"   [green]→ Relatório salvo em: {REPORT_FILE}[/green]\n")

    # ── Passo 4: Aprovação do usuário ───────────────────────────────────────
    print_step(4, 4, "Aguardando sua aprovação...\n")
    final_emails, approved = run_approval(classified)

    if not approved:
        console.print("\n[dim]Relatório disponível em:[/dim] " + REPORT_FILE)
        console.print("[dim]Execute novamente quando quiser aplicar as ações.[/dim]")
        return

    # ── Execução das ações ──────────────────────────────────────────────────
    console.print("[bold]Aplicando ações no Gmail...[/bold]")
    counts = execute_actions(final_emails, classified)
    print_done(counts)
    console.print(f"\n[dim]📄 Relatório completo: {REPORT_FILE}[/dim]")


if __name__ == "__main__":
    main()
