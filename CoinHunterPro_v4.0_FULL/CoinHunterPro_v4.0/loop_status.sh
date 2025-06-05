#!/bin/bash

LOCK_FILE="runtime/scheduler.lock"
HEALTH_FILE="runtime/healthcheck.json"

echo "📍 [CoinHunterPro 루프 상태 확인]"

if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    echo "✅ 루프 실행 중 (PID: $PID)"

    if ps -p $PID > /dev/null 2>&1; then
        echo "🟢 PID 유효함 - 프로세스 정상 작동 중"
    else
        echo "🟡 PID는 있지만 실행 중인 프로세스 아님 (비정상 종료 가능성)"
    fi
else
    echo "❌ 루프 비실행 상태 (lock_file 없음)"
fi

if [ -f "$HEALTH_FILE" ]; then
    echo "🩺 헬스 체크 로그:"
    jq '.' "$HEALTH_FILE"
else
    echo "❌ 헬스 체크 파일 없음"
fi

if command -v ps > /dev/null; then
    echo "🧠 현재 루프 프로세스 리소스 사용량:"
    ps -p $PID -o pid,etime,%cpu,%mem,cmd | tail -n +2
else
    echo "⚠️ 'ps' 명령을 찾을 수 없습니다."
fi
