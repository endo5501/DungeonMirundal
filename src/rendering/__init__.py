"""レンダリングシステム"""

try:
    from .dungeon_renderer_pygame import DungeonRenderer
except ImportError:
    try:
        from .dungeon_renderer import DungeonRenderer
    except ImportError:
        DungeonRenderer = None

__all__ = [
    "DungeonRenderer"
]