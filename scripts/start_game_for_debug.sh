#!/bin/bash
# デバッグ用ゲーム起動スクリプト
# APIサーバーの起動を待機し、準備完了後に制御を返す
# デバッグ時の詳細ログを有効にしてゲーム内の状況を把握可能にする

# カラー出力の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログファイルとPIDファイル
LOG_FILE="game_debug.log"
PID_FILE="game_debug.pid"
API_PORT=8765
MAX_WAIT_SECONDS=10

echo -e "${YELLOW}Starting game for debug session...${NC}"

# 既存のプロセスチェック
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}Game is already running (PID: $OLD_PID)${NC}"
        echo -e "${GREEN}Debug API ready at http://localhost:$API_PORT${NC}"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# ゲームを起動（INFOレベルのログを有効化）
echo -e "Starting game process with INFO logging..."
export DUNGEON_LOG_LEVEL=INFO
uv run python main.py > "$LOG_FILE" 2>&1 &
GAME_PID=$!
echo $GAME_PID > "$PID_FILE"

echo -e "Game started with PID: $GAME_PID"
echo -e "Waiting for API server on port $API_PORT..."

# APIサーバーの起動を待機
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $((MAX_WAIT_SECONDS * 10)) ]; do
    if curl -s "http://localhost:$API_PORT/screenshot" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Debug API is ready!${NC}"
        echo -e "${GREEN}Game is running (PID: $GAME_PID)${NC}"
        echo -e "${GREEN}API endpoint: http://localhost:$API_PORT${NC}"
        echo -e "${YELLOW}Debug log file: $LOG_FILE (INFO level enabled)${NC}"
        echo -e "${YELLOW}To view logs in real-time: tail -f $LOG_FILE${NC}"
        exit 0
    fi
    sleep 0.1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    
    # 進捗表示
    if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
        echo -n "."
    fi
done

# タイムアウト
echo -e "\n${RED}✗ API server failed to start within $MAX_WAIT_SECONDS seconds${NC}"
echo -e "${YELLOW}Check the log file: $LOG_FILE${NC}"
tail -20 "$LOG_FILE"
exit 1