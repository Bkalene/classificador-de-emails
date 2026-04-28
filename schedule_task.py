"""
schedule_task.py — Cria tarefa agendada no Windows Task Scheduler.
Executa o Email Agent diariamente às 8h.
"""
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")
TASK_NAME = "EmailAgentDiario"


def create_scheduled_task(hour: int = 8, minute: int = 0) -> None:
    """Cria ou atualiza a tarefa agendada no Windows Task Scheduler."""

    # Remove tarefa existente silenciosamente
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )

    time_str = f"{hour:02d}:{minute:02d}"

    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", f'"{PYTHON_EXE}" "{MAIN_SCRIPT}"',
        "/SC", "DAILY",
        "/ST", time_str,
        "/RL", "HIGHEST",
        "/F",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Tarefa '{TASK_NAME}' criada com sucesso!")
        print(f"   Execução diária às {time_str}")
        print(f"   Script: {MAIN_SCRIPT}")
        print(f"\n   Para verificar: schtasks /Query /TN {TASK_NAME}")
        print(f"   Para remover:   schtasks /Delete /TN {TASK_NAME} /F")
    else:
        print(f"❌ Erro ao criar tarefa:\n{result.stderr}")
        print("\nTente executar como Administrador:")
        print(f"  python schedule_task.py")


if __name__ == "__main__":
    print("⏰ Configurando execução diária do Email Agent...")
    hour = int(input("Horário de execução (hora, 0-23) [padrão: 8]: ").strip() or "8")
    minute = int(input("Minutos (0-59) [padrão: 0]: ").strip() or "0")
    create_scheduled_task(hour=hour, minute=minute)
