"""
approval.py — Interface CLI de aprovação do relatório diário.
O usuário revisa e confirma antes de qualquer ação no Gmail.
"""
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

CATEGORY_STYLES = {
    "URGENTE": "bold red",
    "IMPORTANTE": "bold yellow",
    "INFORMATIVO": "bold green",
    "LIXO": "dim",
}

CATEGORY_ICONS = {
    "URGENTE": "🔴",
    "IMPORTANTE": "🟡",
    "INFORMATIVO": "🟢",
    "LIXO": "🗑️ ",
}

VALID_CATEGORIES = ["URGENTE", "IMPORTANTE", "INFORMATIVO", "LIXO"]


def _print_header(total: int) -> None:
    console.print(Panel.fit(
        f"[bold cyan]📬 Email Agent — Relatório Diário[/bold cyan]\n"
        f"[dim]{total} e-mail(s) para revisar[/dim]",
        border_style="cyan"
    ))
    console.print()


def _print_summary_table(emails: list[dict[str, Any]]) -> None:
    table = Table(title="Resumo por Categoria", box=box.ROUNDED, show_header=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Categoria", width=14)
    table.add_column("De", width=30)
    table.add_column("Assunto", width=45)
    table.add_column("Confiança", width=10)

    for i, email in enumerate(emails, 1):
        cat = email.get("category", "INFORMATIVO")
        style = CATEGORY_STYLES.get(cat, "")
        icon = CATEGORY_ICONS.get(cat, "")
        confidence = email.get("confidence", 0)
        conf_str = f"{confidence:.0%}"

        table.add_row(
            str(i),
            f"{icon}{cat}",
            email.get("sender", "")[:28],
            email.get("subject", "")[:43],
            conf_str,
            style=style,
        )

    console.print(table)
    console.print()


def _print_commands() -> None:
    console.print(Panel(
        "[bold]Comandos disponíveis:[/bold]\n\n"
        "  [cyan]s[/cyan]        → Aprovar TUDO e executar ações\n"
        "  [cyan]n[/cyan]        → Cancelar (nenhuma ação será feita)\n"
        "  [cyan]e N CAT[/cyan]  → Editar categoria do e-mail N (ex: e 3 IMPORTANTE)\n"
        "  [cyan]v N[/cyan]      → Ver detalhes do e-mail N\n"
        "  [cyan]?[/cyan]        → Mostrar esta ajuda",
        title="Ajuda",
        border_style="dim",
    ))


def _view_email(emails: list[dict[str, Any]], index: int) -> None:
    if index < 1 or index > len(emails):
        console.print(f"[red]E-mail #{index} não existe.[/red]")
        return

    email = emails[index - 1]
    cat = email.get("category", "INFORMATIVO")
    icon = CATEGORY_ICONS.get(cat, "")
    style = CATEGORY_STYLES.get(cat, "")

    console.print(Panel(
        f"[bold]De:[/bold] {email.get('sender', '')}\n"
        f"[bold]Assunto:[/bold] {email.get('subject', '')}\n"
        f"[bold]Data:[/bold] {email.get('date', '')}\n"
        f"[bold]Categoria:[/bold] [{style}]{icon}{cat}[/{style}]\n"
        f"[bold]Motivo:[/bold] {email.get('reason', '')}\n"
        f"[bold]Confiança:[/bold] {email.get('confidence', 0):.0%}\n\n"
        f"[bold]Trecho:[/bold]\n{email.get('snippet', '')}",
        title=f"E-mail #{index}",
        border_style=style if style else "white",
    ))


def run_approval(emails: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    """
    Exibe o resumo e aguarda aprovação do usuário.
    Retorna (emails_com_categorias_finais, aprovado).
    """
    emails = [dict(e) for e in emails]  # cópia para não mutar originais

    _print_header(len(emails))
    _print_summary_table(emails)
    _print_commands()

    approved = False

    while True:
        try:
            cmd = console.input("\n[bold cyan]> Comando:[/bold cyan] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Cancelado.[/yellow]")
            return emails, False

        if cmd == "s":
            console.print("\n[bold green]✅ Aprovado! Aplicando ações no Gmail...[/bold green]\n")
            approved = True
            break

        elif cmd == "n":
            console.print("\n[yellow]⏸️  Cancelado. Nenhuma ação foi feita.[/yellow]\n")
            break

        elif cmd == "?":
            _print_commands()

        elif cmd.startswith("v "):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                _view_email(emails, int(parts[1]))
            else:
                console.print("[red]Uso: v N (ex: v 2)[/red]")

        elif cmd.startswith("e "):
            parts = cmd.upper().split()
            if len(parts) == 3 and parts[1].isdigit() and parts[2] in VALID_CATEGORIES:
                idx = int(parts[1]) - 1
                if 0 <= idx < len(emails):
                    old_cat = emails[idx]["category"]
                    emails[idx]["category"] = parts[2]
                    console.print(f"[green]✏️  E-mail #{idx+1}: {old_cat} → {parts[2]}[/green]")
                    _print_summary_table(emails)
                else:
                    console.print(f"[red]E-mail #{parts[1]} não existe.[/red]")
            else:
                console.print(f"[red]Uso: e N CATEGORIA (ex: e 3 IMPORTANTE)[/red]")
                console.print(f"[dim]Categorias: {', '.join(VALID_CATEGORIES)}[/dim]")

        else:
            console.print("[red]Comando inválido. Digite '?' para ajuda.[/red]")

    return emails, approved
