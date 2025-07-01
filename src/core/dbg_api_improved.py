# dbg_api_improved.py ── 改善版 MCP サーバー
import threading
import base64
import io
import logging
from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, Any
from enum import Enum

import pygame
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from PIL import Image
from fastapi_mcp import FastApiMCP
import uvicorn
from pydantic import BaseModel, Field, validator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 定数定義
DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"
MAX_SCREENSHOT_SIZE = (1920, 1080)  # 最大スクリーンショットサイズ
JPEG_QUALITY = 70

# Enumとモデル定義
class MouseAction(str, Enum):
    DOWN = "down"
    UP = "up"
    MOVE = "move"

class ScreenshotResponse(BaseModel):
    jpeg: str
    timestamp: str
    size: tuple[int, int]

class InputResponse(BaseModel):
    ok: bool
    message: str = "Success"
    timestamp: str

class KeyInputRequest(BaseModel):
    code: int = Field(..., description="ASCII code of the key", ge=0, le=255)
    down: bool = Field(True, description="True for key down, False for key up")

class MouseInputRequest(BaseModel):
    x: int = Field(..., description="X coordinate", ge=0)
    y: int = Field(..., description="Y coordinate", ge=0)
    button: int = Field(1, description="Mouse button (1=left, 2=middle, 3=right)", ge=1, le=3)
    action: MouseAction = Field(MouseAction.DOWN, description="Mouse action type")

# FastAPI アプリケーション
app = FastAPI(
    title="Dungeon Game Debug API",
    description="API for debugging and testing the Dungeon game",
    version="1.0.0"
)

# グローバル変数
_screen: Optional[pygame.Surface] = None
_screen_lock = threading.Lock()
_input_history: list[Dict[str, Any]] = []
_max_history = 1000

# ヘルパー関数
def get_timestamp() -> str:
    """現在のタイムスタンプを取得"""
    return datetime.now().isoformat()

def add_to_history(event_type: str, data: Dict[str, Any]) -> None:
    """入力履歴に追加"""
    global _input_history
    _input_history.append({
        "type": event_type,
        "data": data,
        "timestamp": get_timestamp()
    })
    # 履歴サイズの制限
    if len(_input_history) > _max_history:
        _input_history = _input_history[-_max_history:]

# エンドポイント
@app.get("/screenshot", 
         response_model=ScreenshotResponse,
         summary="Get current game screenshot",
         description="Captures the current state of the game screen and returns it as a JPEG image")
def get_screenshot():
    """ゲーム画面のスクリーンショットを取得"""
    with _screen_lock:
        if _screen is None:
            logger.error("Screenshot requested but screen not initialized")
            raise HTTPException(
                status_code=503, 
                detail="Screen not ready. Make sure the game is running."
            )
        
        try:
            # スクリーンサイズの取得
            size = _screen.get_size()
            
            # サイズ制限のチェック
            if size[0] > MAX_SCREENSHOT_SIZE[0] or size[1] > MAX_SCREENSHOT_SIZE[1]:
                logger.warning(f"Screen size {size} exceeds maximum {MAX_SCREENSHOT_SIZE}")
            
            # スクリーンショットの生成
            raw = pygame.image.tobytes(_screen, "RGB")
            img = Image.frombytes("RGB", size, raw)
            
            # JPEG変換
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)
            
            jpeg_data = base64.b64encode(buf.getvalue()).decode()
            
            logger.info(f"Screenshot captured: size={size}")
            
            return ScreenshotResponse(
                jpeg=jpeg_data,
                timestamp=get_timestamp(),
                size=size
            )
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to capture screenshot: {str(e)}"
            )

@app.post("/input/key",
          response_model=InputResponse,
          summary="Send keyboard input",
          description="Simulates keyboard key press or release")
def send_key_input(request: KeyInputRequest):
    """キーボード入力をゲームに送信"""
    try:
        evt_type = pygame.KEYDOWN if request.down else pygame.KEYUP
        event = pygame.event.Event(evt_type, key=request.code)
        pygame.event.post(event)
        
        # 履歴に記録
        add_to_history("key", {
            "code": request.code,
            "down": request.down,
            "char": chr(request.code) if 32 <= request.code <= 126 else f"<{request.code}>"
        })
        
        logger.info(f"Key input: code={request.code}, down={request.down}")
        
        return InputResponse(
            ok=True,
            message=f"Key {'pressed' if request.down else 'released'}: {request.code}",
            timestamp=get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to send key input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send key input: {str(e)}"
        )

@app.post("/input/mouse",
          response_model=InputResponse,
          summary="Send mouse input",
          description="Simulates mouse movement or button clicks")
def send_mouse_input(request: MouseInputRequest):
    """マウス入力をゲームに送信"""
    try:
        # 画面サイズのチェック
        if _screen:
            size = _screen.get_size()
            if request.x >= size[0] or request.y >= size[1]:
                logger.warning(f"Mouse position ({request.x}, {request.y}) is outside screen bounds {size}")
        
        if request.action == MouseAction.MOVE:
            # マウス移動
            pygame.mouse.set_pos((request.x, request.y))
            event = pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=(request.x, request.y),
                rel=(0, 0),
                buttons=(0, 0, 0)
            )
        else:
            # マウスボタン
            evt_type = pygame.MOUSEBUTTONDOWN if request.action == MouseAction.DOWN else pygame.MOUSEBUTTONUP
            event = pygame.event.Event(
                evt_type,
                pos=(request.x, request.y),
                button=request.button
            )
        
        pygame.event.post(event)
        
        # 履歴に記録
        add_to_history("mouse", {
            "x": request.x,
            "y": request.y,
            "button": request.button,
            "action": request.action
        })
        
        logger.info(f"Mouse input: pos=({request.x}, {request.y}), action={request.action}, button={request.button}")
        
        return InputResponse(
            ok=True,
            message=f"Mouse {request.action} at ({request.x}, {request.y})",
            timestamp=get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to send mouse input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send mouse input: {str(e)}"
        )

@app.get("/history",
         summary="Get input history",
         description="Returns the history of recent input events")
def get_input_history(limit: int = Field(100, ge=1, le=1000)):
    """最近の入力履歴を取得"""
    return {
        "history": _input_history[-limit:],
        "total": len(_input_history),
        "limit": limit
    }

@app.get("/status",
         summary="Get server status",
         description="Returns the current status of the debug server")
def get_server_status():
    """サーバーの状態を取得"""
    return {
        "screen_ready": _screen is not None,
        "screen_size": _screen.get_size() if _screen else None,
        "history_count": len(_input_history),
        "timestamp": get_timestamp()
    }

@app.delete("/history",
            response_model=InputResponse,
            summary="Clear input history",
            description="Clears all recorded input history")
def clear_history():
    """入力履歴をクリア"""
    global _input_history
    count = len(_input_history)
    _input_history = []
    logger.info(f"Cleared {count} history entries")
    
    return InputResponse(
        ok=True,
        message=f"Cleared {count} history entries",
        timestamp=get_timestamp()
    )

# ゲームログ統合
try:
    from .game_logger import get_game_logger, LogLevel
    GAME_LOG_ENABLED = True
except ImportError:
    GAME_LOG_ENABLED = False
    logger.warning("Game logger not available")

# ゲームログ関連エンドポイント
if GAME_LOG_ENABLED:
    @app.get("/logs",
             summary="Get game logs",
             description="Retrieves game internal logs with optional filtering")
    def get_game_logs(
        limit: int = Field(100, ge=1, le=1000, description="Maximum number of logs to return"),
        level: Optional[LogLevel] = Field(None, description="Filter by log level"),
        category: Optional[str] = Field(None, description="Filter by category"),
        minutes_ago: Optional[int] = Field(None, ge=1, le=1440, description="Get logs from last N minutes")
    ):
        """ゲーム内部ログを取得"""
        game_logger = get_game_logger()
        
        since = None
        if minutes_ago:
            since = datetime.now() - timedelta(minutes=minutes_ago)
        
        logs = game_logger.get_logs(
            limit=limit,
            level=level.value if level else None,
            category=category,
            since=since
        )
        
        return {
            "logs": logs,
            "count": len(logs),
            "filters": {
                "limit": limit,
                "level": level.value if level else None,
                "category": category,
                "since": since.isoformat() if since else None
            }
        }
    
    @app.get("/logs/stats",
             summary="Get log statistics",
             description="Returns statistics about game logs")
    def get_log_stats():
        """ログ統計を取得"""
        return get_game_logger().get_stats()
    
    @app.get("/logs/search",
             summary="Search game logs",
             description="Search through game logs by message content")
    def search_logs(
        query: str = Field(..., description="Search query"),
        limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    ):
        """ログメッセージを検索"""
        results = get_game_logger().search(query, limit)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    @app.delete("/logs",
                response_model=InputResponse,
                summary="Clear game logs",
                description="Clears all game logs")
    def clear_game_logs():
        """ゲームログをクリア"""
        game_logger = get_game_logger()
        stats = game_logger.get_stats()
        game_logger.clear()
        
        return InputResponse(
            ok=True,
            message=f"Cleared {stats['total_logs']} log entries",
            timestamp=get_timestamp()
        )
    
    @app.post("/logs",
              response_model=InputResponse,
              summary="Add custom log entry",
              description="Manually add a log entry for debugging purposes")
    def add_log_entry(
        message: str = Field(..., description="Log message"),
        level: LogLevel = Field(LogLevel.INFO, description="Log level"),
        category: str = Field("debug", description="Log category")
    ):
        """デバッグ用のログエントリーを手動で追加"""
        game_logger = get_game_logger()
        game_logger.add_log(level.value, f"[MANUAL] {message}", category)
        
        return InputResponse(
            ok=True,
            message=f"Added log entry: {message}",
            timestamp=get_timestamp()
        )

# サーバー起動関数
def _run_server():
    """サーバーを起動"""
    logger.info(f"Starting debug server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT, log_level="warning")

def start(screen: pygame.Surface, port: int = DEFAULT_PORT):
    """
    デバッグサーバーを起動
    
    Args:
        screen: pygame.Surfaceオブジェクト
        port: サーバーポート（デフォルト: 8765）
    """
    global _screen, DEFAULT_PORT
    
    with _screen_lock:
        _screen = screen
    
    DEFAULT_PORT = port
    logger.info(f"Initializing debug server with screen size: {screen.get_size()}")
    
    # サーバーをデーモンスレッドで起動
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    
    logger.info("Debug server thread started")

# MCP設定
mcp = FastApiMCP(
    app,
    name="dungeon-msp",
    description="Dungeon game debugging and testing MCP server"
)
mcp.mount()

# エラーハンドラー
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "timestamp": get_timestamp()
        }
    )