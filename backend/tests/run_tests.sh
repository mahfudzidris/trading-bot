#!/bin/bash
# Test runner for Trading Bot backend
# Usage:
#   ./run_tests.sh           — run once
#   ./run_tests.sh watch     — watch for changes and auto-run
#   ./run_tests.sh coverage  — run with coverage report

set -e
cd "$(dirname "$0")/.."
source ../venv/bin/activate

MODE="${1:-run}"

case "$MODE" in
  run)
    python -m pytest tests/ -v --tb=short "$@"
    ;;
  watch)
    echo "👀 Watching for changes... Tests will auto-run on any .py change"
    python -m pytest_watch tests/ -- --tb=short -v
    ;;
  coverage)
    pip install -q pytest-cov 2>/dev/null || true
    python -m pytest tests/ -v --tb=short --cov=. --cov-report=term --cov-report=html
    echo "📊 Coverage report: open backend/htmlcov/index.html in browser"
    ;;
  quick)
    python -m pytest tests/ -x --tb=short -q "$@"
    ;;
  *)
    echo "Usage: $0 [run|watch|coverage|quick]"
    exit 1
    ;;
esac
