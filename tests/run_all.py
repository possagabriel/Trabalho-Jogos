"""Roda toda a suite de testes standalone, arquivo por arquivo.

Cada arquivo de teste funciona de forma independente (headless, com
INCARNATE_DATA_DIR temporario), entao basta executa-los em subprocessos:

    python tests/run_all.py
"""

import os
import subprocess
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS = [
    "test_theme_geometry_smooth.py",
    "test_settings_save_shop.py",
    "test_weapons_powerups.py",
    "test_player.py",
    "test_enemies_bosses.py",
    "test_scenarios_particles.py",
    "test_menu_scene.py",
    "test_menu.py",
    "test_interacao.py",
    "test_core.py",
    "test_hud.py",
    "test_layout.py",
    "smoke_test.py",
]


def main():
    falhas = 0
    for arquivo in ARQUIVOS:
        caminho = os.path.join(PASTA, arquivo)
        print(f"== {arquivo} ==")
        try:
            resultado = subprocess.run(
                [sys.executable, caminho], capture_output=True, text=True)
            print(resultado.stdout.strip().splitlines()[-1])
            if resultado.returncode != 0:
                falhas += 1
                print(resultado.stderr)
        except FileNotFoundError:
            falhas += 1
            print("arquivo nao encontrado")
    print(f"\n{'FALHAS' if falhas else 'TODOS'} "
          f"({len(ARQUIVOS) - falhas}/{len(ARQUIVOS)} arquivos ok)")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())