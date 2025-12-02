#!/bin/bash
#
# Integrated Business Platform - Unified Startup Manager
# Usage: ./platform.sh [command] [options]
#
# Commands:
#   start         Start production services
#   start:dev     Start development services
#   stop          Stop all services
#   restart       Restart all services
#   status        Show service status
#   logs          View logs (all services)
#   logs [svc]    View logs for specific service
#   health        Check health of all services
#   migrate       Run database migrations
#   shell         Open Django shell
#   bash          Open bash in web container
#   build         Build Docker images
#   clean         Remove containers and volumes
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="integrated_business_platform"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE_PROD="docker-compose.yml"
COMPOSE_FILE_DEV="docker-compose.dev.yml"

# Default mode
MODE="prod"

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Print header
print_header() {
    echo ""
    print_msg $CYAN "========================================"
    print_msg $CYAN "  Integrated Business Platform Manager"
    print_msg $CYAN "========================================"
    echo ""
}

# Print usage
print_usage() {
    print_header
    echo "Usage: ./platform.sh [command] [options]"
    echo ""
    print_msg $YELLOW "Commands:"
    echo "  start              Start production services (nginx + gunicorn)"
    echo "  start:dev          Start development services (Django runserver)"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  restart:dev        Restart development services"
    echo "  status             Show service status"
    echo "  logs               View logs (all services)"
    echo "  logs [service]     View logs for specific service (web, db, redis, nginx)"
    echo "  health             Check health of all services"
    echo "  migrate            Run database migrations"
    echo "  makemigrations     Create new migrations"
    echo "  collectstatic      Collect static files"
    echo "  shell              Open Django shell"
    echo "  bash               Open bash in web container"
    echo "  build              Build Docker images"
    echo "  build:nocache      Build images without cache"
    echo "  clean              Remove containers and volumes"
    echo "  clean:all          Remove everything including images"
    echo ""
    print_msg $YELLOW "Examples:"
    echo "  ./platform.sh start           # Start production"
    echo "  ./platform.sh start:dev       # Start development"
    echo "  ./platform.sh logs web        # View web service logs"
    echo "  ./platform.sh health          # Check all services health"
    echo ""
}

# Get compose file based on mode
get_compose_file() {
    if [ "$MODE" = "dev" ]; then
        echo "$COMPOSE_FILE_DEV"
    else
        echo "$COMPOSE_FILE_PROD"
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        print_msg $RED "Error: Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if docker-compose is available
check_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_msg $RED "Error: Neither docker-compose nor docker compose is available."
        exit 1
    fi
}

# Start services
cmd_start() {
    local compose_file=$(get_compose_file)
    print_msg $GREEN "Starting services in $MODE mode..."
    print_msg $BLUE "Using: $compose_file"

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$compose_file" up -d

    echo ""
    print_msg $GREEN "Services started successfully!"
    echo ""

    # Show access URLs
    if [ "$MODE" = "prod" ]; then
        print_msg $CYAN "Access URLs:"
        echo "  - Platform:  http://192.168.0.104:8080"
        echo "  - Platform:  http://localhost:8080"
        echo "  - Direct:    http://localhost:8000"
    else
        print_msg $CYAN "Access URLs:"
        echo "  - Platform:  http://localhost:8000"
        echo "  - Admin:     http://localhost:8000/admin/"
    fi
    echo ""

    # Show status
    cmd_status
}

# Stop services
cmd_stop() {
    print_msg $YELLOW "Stopping services..."

    cd "$PROJECT_DIR"

    # Stop both prod and dev if running
    if [ -f "$COMPOSE_FILE_PROD" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE_PROD" down 2>/dev/null || true
    fi
    if [ -f "$COMPOSE_FILE_DEV" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE_DEV" down 2>/dev/null || true
    fi

    print_msg $GREEN "Services stopped."
}

# Restart services
cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

# Show status
cmd_status() {
    print_msg $CYAN "Service Status:"
    echo ""

    cd "$PROJECT_DIR"

    # Check production services
    if [ -f "$COMPOSE_FILE_PROD" ]; then
        echo "Production services:"
        $COMPOSE_CMD -f "$COMPOSE_FILE_PROD" ps 2>/dev/null || echo "  Not running"
    fi

    # Check development services
    if [ -f "$COMPOSE_FILE_DEV" ]; then
        echo ""
        echo "Development services:"
        $COMPOSE_CMD -f "$COMPOSE_FILE_DEV" ps 2>/dev/null || echo "  Not running"
    fi
}

# View logs
cmd_logs() {
    local service=$1
    local compose_file=$(get_compose_file)

    cd "$PROJECT_DIR"

    if [ -n "$service" ]; then
        print_msg $CYAN "Showing logs for: $service"
        $COMPOSE_CMD -f "$compose_file" logs -f "$service"
    else
        print_msg $CYAN "Showing all logs (Ctrl+C to exit)"
        $COMPOSE_CMD -f "$compose_file" logs -f
    fi
}

# Health check
cmd_health() {
    print_msg $CYAN "Checking service health..."
    echo ""

    local all_healthy=true

    # Check web service
    echo -n "Web service:    "
    if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $RED "UNHEALTHY"
        all_healthy=false
    fi

    # Check database
    echo -n "Database:       "
    if docker exec ${PROJECT_NAME}-db-1 pg_isready -U postgres > /dev/null 2>&1 || \
       docker exec ${PROJECT_NAME}_db_1 pg_isready -U postgres > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $RED "UNHEALTHY"
        all_healthy=false
    fi

    # Check Redis
    echo -n "Redis:          "
    if docker exec ${PROJECT_NAME}-redis-1 redis-cli ping > /dev/null 2>&1 || \
       docker exec ${PROJECT_NAME}_redis_1 redis-cli ping > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $RED "UNHEALTHY"
        all_healthy=false
    fi

    # Check Nginx (production only)
    echo -n "Nginx:          "
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $YELLOW "NOT RUNNING (dev mode?)"
    fi

    # Check Django health endpoint
    echo -n "Django app:     "
    if curl -sf http://localhost:8000/health/db/ > /dev/null 2>&1; then
        print_msg $GREEN "HEALTHY"
    else
        print_msg $YELLOW "CHECKING..."
    fi

    echo ""

    if [ "$all_healthy" = true ]; then
        print_msg $GREEN "All core services are healthy!"
    else
        print_msg $RED "Some services are unhealthy. Check logs with: ./platform.sh logs"
    fi
}

# Run migrations
cmd_migrate() {
    local compose_file=$(get_compose_file)
    print_msg $CYAN "Running database migrations..."

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$compose_file" exec web python manage.py migrate --noinput

    print_msg $GREEN "Migrations completed."
}

# Make migrations
cmd_makemigrations() {
    local compose_file=$(get_compose_file)
    local app=$1
    print_msg $CYAN "Creating migrations..."

    cd "$PROJECT_DIR"
    if [ -n "$app" ]; then
        $COMPOSE_CMD -f "$compose_file" exec web python manage.py makemigrations "$app"
    else
        $COMPOSE_CMD -f "$compose_file" exec web python manage.py makemigrations
    fi

    print_msg $GREEN "Migrations created."
}

# Collect static files
cmd_collectstatic() {
    local compose_file=$(get_compose_file)
    print_msg $CYAN "Collecting static files..."

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$compose_file" exec web python manage.py collectstatic --noinput

    print_msg $GREEN "Static files collected."
}

# Open Django shell
cmd_shell() {
    local compose_file=$(get_compose_file)
    print_msg $CYAN "Opening Django shell..."

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$compose_file" exec web python manage.py shell
}

# Open bash in container
cmd_bash() {
    local compose_file=$(get_compose_file)
    local service=${1:-web}
    print_msg $CYAN "Opening bash in $service container..."

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$compose_file" exec "$service" /bin/bash || \
    $COMPOSE_CMD -f "$compose_file" exec "$service" /bin/sh
}

# Build images
cmd_build() {
    local no_cache=$1
    local compose_file=$(get_compose_file)
    print_msg $CYAN "Building Docker images..."

    cd "$PROJECT_DIR"

    if [ "$no_cache" = "nocache" ]; then
        $COMPOSE_CMD -f "$compose_file" build --no-cache
    else
        $COMPOSE_CMD -f "$compose_file" build
    fi

    print_msg $GREEN "Build completed."
}

# Clean up
cmd_clean() {
    local all=$1
    print_msg $YELLOW "Cleaning up..."

    cd "$PROJECT_DIR"

    # Stop and remove containers
    $COMPOSE_CMD -f "$COMPOSE_FILE_PROD" down -v 2>/dev/null || true
    $COMPOSE_CMD -f "$COMPOSE_FILE_DEV" down -v 2>/dev/null || true

    if [ "$all" = "all" ]; then
        print_msg $YELLOW "Removing images..."
        docker rmi ${PROJECT_NAME}_web 2>/dev/null || true
        docker rmi ${PROJECT_NAME}-web 2>/dev/null || true
    fi

    print_msg $GREEN "Cleanup completed."
}

# Main entry point
main() {
    check_docker
    check_compose

    case "$1" in
        start)
            MODE="prod"
            cmd_start
            ;;
        start:dev)
            MODE="dev"
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            MODE="prod"
            cmd_restart
            ;;
        restart:dev)
            MODE="dev"
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$2"
            ;;
        health)
            cmd_health
            ;;
        migrate)
            cmd_migrate
            ;;
        makemigrations)
            cmd_makemigrations "$2"
            ;;
        collectstatic)
            cmd_collectstatic
            ;;
        shell)
            cmd_shell
            ;;
        bash)
            cmd_bash "$2"
            ;;
        build)
            cmd_build
            ;;
        build:nocache)
            cmd_build "nocache"
            ;;
        clean)
            cmd_clean
            ;;
        clean:all)
            cmd_clean "all"
            ;;
        -h|--help|help|"")
            print_usage
            ;;
        *)
            print_msg $RED "Unknown command: $1"
            print_usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
