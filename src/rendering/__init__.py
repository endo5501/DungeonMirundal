"""レンダリングシステム"""

# レンダラー初期化定数
PRIMARY_RENDERER = "dungeon_renderer_pygame"
FALLBACK_RENDERER = "dungeon_renderer"

def _import_renderer():
    """レンダラーをインポート"""
    try:
        from .dungeon_renderer_pygame import DungeonRendererPygame
        return DungeonRendererPygame
    except ImportError:
        try:
            from .dungeon_renderer_pygame_backup import DungeonRendererPygame
            return DungeonRendererPygame
        except ImportError:
            return None

DungeonRenderer = _import_renderer()

__all__ = [
    "DungeonRenderer"
]