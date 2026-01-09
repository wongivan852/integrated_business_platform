#!/bin/bash
#
# Krystal Integrated Business Platform - Startup Script
# Usage: ./start_all_apps.sh [all|main|stripe|crm|status|stop]
#
# Last Updated: 2025-12-02
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
MAIN_PLATFORM_DIR="/home/user/Desktop/integrated_business_platform"
STRIPE_DASHBOARD_DIR="/home/user/stripe-dashboard"
COMPANY_CRM_DIR="/home/user/krystal-company-apps/company_crm_system"

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Check if a port is in use
check_port() {
    local port=$1
    if ss -tlnp | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check service status
check_status() {
    print_msg "$BLUE" "\n=========================================="
    print_msg "$BLUE" "  Platform Status Check"
    print_msg "$BLUE" "==========================================\n"

    # Check Nginx
    if systemctl is-active --quiet nginx; then
        print_msg "$GREEN" "[OK] Nginx (Port 80)"
    else
        print_msg "$RED" "[DOWN] Nginx"
    fi

    # Check PostgreSQL
    if systemctl is-active --quiet postgresql; then
        print_msg "$GREEN" "[OK] PostgreSQL (Port 5432)"
    else
        print_msg "$RED" "[DOWN] PostgreSQL"
    fi

    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_msg "$GREEN" "[OK] Redis (Port 6379)"
    else
        print_msg "$YELLOW" "[?] Redis - May not be running"
    fi

    # Check Main Platform
    if check_port 8080; then
        print_msg "$GREEN" "[OK] Main Platform (Port 8080)"
    else
        print_msg "$RED" "[DOWN] Main Platform (Port 8080)"
    fi

    # Check Stripe Dashboard
    if docker ps --format '{{.Names}}' | grep -q "stripe-dashboard"; then
        print_msg "$GREEN" "[OK] Stripe Dashboard (Docker, Port 8081)"
    else
        print_msg "$RED" "[DOWN] Stripe Dashboard (Docker)"
    fi

    # Check Company CRM
    if docker ps --format '{{.Names}}' | grep -q "company_crm_system_web"; then
        print_msg "$GREEN" "[OK] Company CRM (Docker, Port 8083)"
    else
        print_msg "$RED" "[DOWN] Company CRM (Docker)"
    fi

    print_msg "$BLUE" "\n=========================================="
    print_msg "$BLUE" "  Docker Containers"
    print_msg "$BLUE" "==========================================\n"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not available"

    print_msg "$BLUE" "\n=========================================="
    print_msg "$BLUE" "  Access URLs"
    print_msg "$BLUE" "==========================================\n"
    echo "Main Dashboard:    http://localhost/"
    echo "Admin Panel:       http://localhost/admin/"
    echo "User Manager:      http://localhost/admin-panel/"
    echo "Leave Management:  http://localhost/leave/"
    echo "Expense Claims:    http://localhost/expenses/"
    echo "CRM:               http://localhost/crm/"
    echo "Asset Tracking:    http://localhost/assets/"
    echo "Stripe Dashboard:  http://localhost/stripe/"
    echo ""
}

# Start Main Platform
start_main() {
    print_msg "$YELLOW" "\n[Starting] Main Platform..."

    if check_port 8080; then
        print_msg "$GREEN" "[Already Running] Main Platform on port 8080"
        return 0
    fi

    cd "$MAIN_PLATFORM_DIR"

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    # Start with gunicorn in background
    nohup gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 business_platform.wsgi:application > logs/gunicorn.log 2>&1 &

    sleep 2

    if check_port 8080; then
        print_msg "$GREEN" "[OK] Main Platform started on port 8080"
    else
        print_msg "$RED" "[ERROR] Failed to start Main Platform"
        print_msg "$YELLOW" "Try: python manage.py runserver 0.0.0.0:8080"
    fi
}

# Start Stripe Dashboard
start_stripe() {
    print_msg "$YELLOW" "\n[Starting] Stripe Dashboard..."

    if docker ps --format '{{.Names}}' | grep -q "stripe-dashboard"; then
        print_msg "$GREEN" "[Already Running] Stripe Dashboard"
        return 0
    fi

    cd "$STRIPE_DASHBOARD_DIR"
    docker-compose up -d

    sleep 3

    if docker ps --format '{{.Names}}' | grep -q "stripe-dashboard"; then
        print_msg "$GREEN" "[OK] Stripe Dashboard started"
    else
        print_msg "$RED" "[ERROR] Failed to start Stripe Dashboard"
    fi
}

# Start Company CRM
start_crm() {
    print_msg "$YELLOW" "\n[Starting] Company CRM..."

    if docker ps --format '{{.Names}}' | grep -q "company_crm_system_web"; then
        print_msg "$GREEN" "[Already Running] Company CRM"
        return 0
    fi

    if [ -d "$COMPANY_CRM_DIR" ]; then
        cd "$COMPANY_CRM_DIR"
        docker-compose up -d

        sleep 3

        if docker ps --format '{{.Names}}' | grep -q "company_crm_system_web"; then
            print_msg "$GREEN" "[OK] Company CRM started"
        else
            print_msg "$RED" "[ERROR] Failed to start Company CRM"
        fi
    else
        print_msg "$YELLOW" "[SKIP] Company CRM directory not found"
    fi
}

# Start all services
start_all() {
    print_msg "$BLUE" "\n=========================================="
    print_msg "$BLUE" "  Starting All Platform Services"
    print_msg "$BLUE" "==========================================\n"

    # Ensure nginx is running
    if ! systemctl is-active --quiet nginx; then
        print_msg "$YELLOW" "[Starting] Nginx..."
        sudo systemctl start nginx
    fi

    start_main
    start_stripe
    start_crm

    print_msg "$BLUE" "\n=========================================="
    print_msg "$GREEN" "  Startup Complete!"
    print_msg "$BLUE" "==========================================\n"

    check_status
}

# Stop all services
stop_all() {
    print_msg "$BLUE" "\n=========================================="
    print_msg "$BLUE" "  Stopping All Platform Services"
    print_msg "$BLUE" "==========================================\n"

    # Stop Main Platform (gunicorn)
    print_msg "$YELLOW" "[Stopping] Main Platform..."
    pkill -f "gunicorn.*business_platform" 2>/dev/null || true

    # Stop Stripe Dashboard
    print_msg "$YELLOW" "[Stopping] Stripe Dashboard..."
    cd "$STRIPE_DASHBOARD_DIR" 2>/dev/null && docker-compose down 2>/dev/null || true

    # Stop Company CRM
    if [ -d "$COMPANY_CRM_DIR" ]; then
        print_msg "$YELLOW" "[Stopping] Company CRM..."
        cd "$COMPANY_CRM_DIR" && docker-compose down 2>/dev/null || true
    fi

    print_msg "$GREEN" "\n[OK] All services stopped"
}

# Show help
show_help() {
    echo ""
    echo "Krystal Integrated Business Platform - Startup Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all      Start all services (default)"
    echo "  main     Start Main Platform only"
    echo "  stripe   Start Stripe Dashboard only"
    echo "  crm      Start Company CRM only"
    echo "  status   Check status of all services"
    echo "  stop     Stop all services"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start all services"
    echo "  $0 status       # Check what's running"
    echo "  $0 stripe       # Start only Stripe Dashboard"
    echo ""
}

# Main script logic
case "${1:-all}" in
    all)
        start_all
        ;;
    main)
        start_main
        ;;
    stripe)
        start_stripe
        ;;
    crm)
        start_crm
        ;;
    status)
        check_status
        ;;
    stop)
        stop_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_msg "$RED" "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
