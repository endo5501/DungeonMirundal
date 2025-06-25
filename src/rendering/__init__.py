"""レンダリングシステム"""

# レンダラー初期化定数
PRIMARY_RENDERER = "dungeon_renderer_pygame"
FALLBACK_RENDERER = "dungeon_renderer"

def _import_renderer():
    """レンダラーをインポート"""
    try:
        from .dungeon_renderer_pygame import DungeonRenderer
        return DungeonRenderer
    except ImportError:
        try:
            from .dungeon_renderer import DungeonRenderer
            return DungeonRenderer
        except ImportError:
            return None

DungeonRenderer = _import_renderer()

__all__ = [
    "DungeonRenderer"
]