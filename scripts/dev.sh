#!/usr/bin/env bash
# Development startup helper script

case "$1" in
  backend)
    cd backend && uvicorn app.main:app --reload --port 8000
    ;;
  frontend)
    cd frontend && npm run dev
    ;;
  *)
    echo "Usage: ./scripts/dev.sh [frontend|backend]"
    exit 1
    ;;
esac
