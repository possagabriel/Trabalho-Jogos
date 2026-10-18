"""INCARNATE - Entre na Fenda.

Ponto de entrada do jogo e das rotinas de diagnóstico/distribuição.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def executar_smoke_test() -> int:
    """Inicializa, simula e salva três quadros sem abrir uma janela real."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    with tempfile.TemporaryDirectory(prefix="incarnate_smoke_") as dados:
        os.environ["INCARNATE_DATA_DIR"] = dados
        import pygame

        from src.core.application import Application

        jogo = Application().jogo
        for _ in range(3):
            jogo.loop_controller.atualizar()
            jogo.render_controller.desenhar()
        jogo._salvar_tudo()
        pygame.quit()
    return 0


def _transferir_save(argumentos: list[str]) -> int | None:
    """Exporta ou importa o progresso quando solicitado pela linha de comando."""
    for opcao in ("--export-save", "--import-save"):
        if opcao not in argumentos:
            continue
        indice = argumentos.index(opcao)
        try:
            destino = Path(argumentos[indice + 1]).expanduser().resolve()
        except IndexError:
            print(f"Informe um arquivo depois de {opcao}.", file=sys.stderr)
            return 2

        from src.core.settings import Configuracoes
        from src.domain.systems.profile_service import ProfileService
        from src.infrastructure.persistence.profile_repository import JsonProfileRepository

        settings = Configuracoes()
        service = ProfileService(JsonProfileRepository(), settings["limite_perfis"],
                                 settings["limite_nome_perfil"])
        service.migrate_legacy()
        try:
            if opcao == "--export-save":
                if service.select_last() is None:
                    raise ValueError("Selecione um perfil no jogo antes de exportar")
                concluido = service.export_active(destino)
            else:
                service.import_file(destino)
                concluido = True
        except (OSError, ValueError, KeyError) as exc:
            print(f"Não foi possível processar o progresso: {exc}", file=sys.stderr)
            return 1
        if not concluido:
            print(f"Não foi possível processar o progresso em {destino}.", file=sys.stderr)
            return 1
        acao = "exportado para" if opcao == "--export-save" else "importado de"
        print(f"Progresso {acao} {destino}")
        return 0
    return None


def cli(argumentos: list[str] | None = None) -> int:
    """Executa o jogo ou uma operação administrativa portátil."""
    argumentos = list(sys.argv[1:] if argumentos is None else argumentos)
    if "--smoke-test" in argumentos:
        return executar_smoke_test()
    resultado = _transferir_save(argumentos)
    if resultado is not None:
        return resultado

    from src.core.application import main

    main()
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
