#!/bin/bash
#
# Integrated Business Platform - Simple Startup Script
# Usage: ./start.sh [command]
#
# Commands:
#   start         Start the platform (default)
#   stop          Stop the platform
#   status        Show status
#   migrate       Run migrations
#   seed          Seed app registry
#   shell         Django shell
#   logs          View server output
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PID_FILE="$PROJECT_DIR/.django.pid"
LOG_FILE="$PROJECT_DIR/logs/django.log"
HOST="0.0.0.0"
PORT="8000"

print_msg() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo ""
    print_msg $CYAN "========================================"
    print_msg $CYAN "  Integrated Business Platform"
    print_msg $CYAN "========================================"
    echo ""
}

# Activate virtual environment
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        print_msg $YELLOW "Virtual environment not found. Using system Python."
    fi
}

# Check PostgreSQL
check_postgres() {
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_msg $GREEN "PostgreSQL: Running"
        return 0
    else
        print_msg $YELLOW "PostgreSQL: Not running"
        return 1
    fi
}

# Start PostgreSQL if needed
start_postgres() {
    if ! check_postgres > /dev/null 2>&1; then
        print_msg $YELLOW "Starting PostgreSQL..."
        pg_ctlcluster 16 main start 2>/dev/null || \
        pg_ctlcluster 15 main start 2>/dev/null || \
        pg_ctlcluster 14 main start 2>/dev/null || \
        sudo service postgresql start 2>/dev/null || \
        print_msg $RED "Could not start PostgreSQL. Please start it manually."
        sleep 2
    fi
}

# Start Django server
cmd_start() {
    print_header

    cd "$PROJECT_DIR"
    activate_venv

    # Check if already running
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        print_msg $YELLOW "Platform is already running (PID: $(cat $PID_FILE))"
        cmd_status
        return
    fi

    # Start PostgreSQL
    start_postgres

    # Create logs directory
    mkdir -p "$PROJECT_DIR/logs"

    print_msg $GREEN "Starting Django server..."

    # Start server in background
    nohup python manage.py runserver $HOST:$PORT > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    # Verify it started
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        print_msg $GREEN "Platform started successfully!"
        echo ""
        print_msg $CYAN "Access URLs:"
        echo "  - Local:   http://localhost:$PORT"
        echo "  - Network: http://192.168.0.104:$PORT"
        echo ""
        print_msg $CYAN "Commands:"
        echo "  - View logs: ./start.sh logs"
        echo "  - Stop:      ./start.sh stop"
        echo "  - Status:    ./start.sh status"
    else
        print_msg $RED "Failed to start. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
    fi
}

# Stop server
cmd_stop() {
    print_msg $YELLOW "Stopping platform..."

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            sleep 1
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID
            fi
            print_msg $GREEN "Platform stopped."
        else
            print_msg $YELLOW "Process not running."
        fi
        rm -f "$PID_FILE"
    else
        # Try to find and kill runserver process
        pkill -f "manage.py runserver" 2>/dev/null && \
            print_msg $GREEN "Platform stopped." || \
            print_msg $YELLOW "Platform was not running."
    fi
}

# Show status
cmd_status() {
    print_header

    echo "Service Status:"
    echo ""

    # PostgreSQL
    echo -n "  PostgreSQL:     "
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_msg $GREEN "RUNNING"
    else
        print_msg $RED "STOPPED"
    fi

    # Django
    echo -n "  Django Server:  "
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        print_msg $GREEN "RUNNING (PID: $(cat $PID_FILE))"
    else
        print_msg $RED "STOPPED"
    fi

    # Health check
    echo -n "  Health Check:   "
    if curl -sf http://localhost:$PORT/health/ > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $YELLOW "UNREACHABLE"
    fi

    echo ""
}

# Run migrations
cmd_migrate() {
    cd "$PROJECT_DIR"
    activate_venv

    print_msg $CYAN "Running migrations..."
    python manage.py migrate
    print_msg $GREEN "Migrations complete."
}

# Seed apps
cmd_seed() {
    cd "$PROJECT_DIR"
    activate_venv

    print_msg $CYAN "Seeding app registry..."
    python manage.py seed_apps
    print_msg $GREEN "Seeding complete."
}

# Django shell
cmd_shell() {
    cd "$PROJECT_DIR"
    activate_venv

    python manage.py shell
}

# View logs
cmd_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_msg $CYAN "Showing logs (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        print_msg $YELLOW "No log file found. Start the server first."
    fi
}

# Print usage
print_usage() {
    print_header
    echo "Usage: ./start.sh [command]"
    echo ""
    print_msg $YELLOW "Commands:"
    echo "  start       Start the platform (default)"
    echo "  stop        Stop the platform"
    echo "  restart     Restart the platform"
    echo "  status      Show service status"
    echo "  migrate     Run database migrations"
    echo "  seed        Seed app registry"
    echo "  shell       Open Django shell"
    echo "  logs        View server logs"
    echo ""
    print_msg $YELLOW "Examples:"
    echo "  ./start.sh              # Start platform"
    echo "  ./start.sh status       # Check status"
    echo "  ./start.sh logs         # View logs"
    echo ""
}

# Main
case "${1:-start}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_stop
        sleep 1
        cmd_start
        ;;
    status)
        cmd_status
        ;;
    migrate)
        cmd_migrate
        ;;
    seed)
        cmd_seed
        ;;
    shell)
        cmd_shell
        ;;
    logs)
        cmd_logs
        ;;
    -h|--help|help)
        print_usage
        ;;
    *)
        print_msg $RED "Unknown command: $1"
        print_usage
        exit 1
        ;;
esac
