# dbg_api.py  ── pull スクショ & キー／マウス入力
import threading, base64, io
import pygame
from fastapi import FastAPI, HTTPException
from PIL import Image
from fastapi_mcp import FastApiMCP
import uvicorn
from typing import Annotated
from pydantic import Field

app = FastAPI()

_screen: pygame.Surface | None = None   # pygame の画面を受け取る

@app.get("/screenshot", operation_id="get_screenshot")
def screenshot():
    """
    get screenshot
    """
    if _screen is None:
        raise HTTPException(503, "Screen not ready")
    raw = pygame.image.tobytes(_screen, "RGB")
    img = Image.frombytes("RGB", _screen.get_size(), raw)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
    return {"jpeg": base64.b64encode(buf.getvalue()).decode()}

@app.post("/input/key")
def key(
    code: Annotated[int, Field(description="ASCII CODE")], 
    down: Annotated[bool, Field(description="True:down, False:up")] = True):
    """
    input key code
    """
    evt_type = pygame.KEYDOWN if down else pygame.KEYUP
    pygame.event.post(pygame.event.Event(evt_type, key=code))
    return {"ok": True}

@app.post("/input/mouse")
def mouse(x: int, y: int, button: int = 1,
          action: Annotated[str, Field(description="down | up | move")] = "down"):
    """
    input mouse
    """
    if action == "move":
        # マウスカーソルを移動（ドラッグ判定も OK）
        pygame.mouse.set_pos((x, y))
        evt_type = pygame.MOUSEMOTION
        pygame.event.post(pygame.event.Event(evt_type, pos=(x, y), rel=(0, 0), buttons=(0, 0, 0)))
    else:
        evt_type = pygame.MOUSEBUTTONDOWN if action == "down" else pygame.MOUSEBUTTONUP
        pygame.event.post(pygame.event.Event(evt_type, pos=(x, y), button=button))
    return {"ok": True}

# ---------- 起動 ---------- #
def _run():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")

def start(screen: pygame.Surface):
    global _screen
    _screen = screen
    threading.Thread(target=_run, daemon=True).start()

mcp = FastApiMCP(
    app,
    name="Dungeon game MCP",
    description="You can cotrol game")
mcp.mount()
