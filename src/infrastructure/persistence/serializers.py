"""JSON serialization helpers.

Provides type-safe encoding/decoding for game-specific types that are not
natively JSON-serialisable (``pygame.Rect``, colour tuples, etc.).
"""

import json
from typing import Any, Dict, List, Tuple, Union

import pygame


class GameEncoder(json.JSONEncoder):
    """Extended JSON encoder that handles common game types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, pygame.Rect):
            return {"__type__": "Rect",
                    "x": obj.x, "y": obj.y,
                    "w": obj.w, "h": obj.h}
        if isinstance(obj, pygame.Color):
            return {"__type__": "Color",
                    "r": obj.r, "g": obj.g, "b": obj.b, "a": obj.a}
        if isinstance(obj, (tuple, list)):
            return [self.default(v) if isinstance(v, (pygame.Rect, pygame.Color))
                    else v for v in obj]
        return super().default(obj)


def serializar(obj: Any) -> str:
    """Serialize an object to a JSON string."""
    return json.dumps(obj, cls=GameEncoder, ensure_ascii=False, indent=2)


def desserializar(texto: str) -> Any:
    """Deserialize a JSON string, reconstructing game types."""
    return json.loads(texto, object_hook=_object_hook)


def _object_hook(d: Dict[str, Any]) -> Any:
    """Reconstruct game types from their JSON representation."""
    if "__type__" not in d:
        return d
    tipo = d["__type__"]
    if tipo == "Rect":
        return pygame.Rect(d["x"], d["y"], d["w"], d["h"])
    if tipo == "Color":
        return pygame.Color(d["r"], d["g"], d["b"], d.get("a", 255))
    return d


def salvar_json(caminho: str, dados: Any) -> None:
    """Write data to a JSON file with game-type serialisation."""
    import os
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, cls=GameEncoder, ensure_ascii=False, indent=2)


def carregar_json(caminho: str) -> Any:
    """Read data from a JSON file, reconstructing game types."""
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f, object_hook=_object_hook)
