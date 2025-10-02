#!/bin/bash

###############################################################################
# SSO Deployment Script
# Deploys SSO system to integrated business platform
#
# Usage:
#   ./deploy_sso.sh
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header "SSO DEPLOYMENT FOR INTEGRATED BUSINESS PLATFORM"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Must run this script from integrated_business_platform directory"
    exit 1
fi

# Step 1: Install dependencies
print_header "Step 1: Installing Dependencies"
print_info "Installing SSO requirements..."

if pip install djangorestframework-simplejwt==5.3.0 PyJWT==2.8.0; then
    print_success "Dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Step 2: Check environment variables
print_header "Step 2: Checking Environment Variables"

if [ -z "$SSO_SECRET_KEY" ]; then
    print_warning "SSO_SECRET_KEY not set in environment"
    print_info "Generating random SSO secret key..."

    SSO_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    print_success "Generated SSO_SECRET_KEY: $SSO_SECRET_KEY"

    # Add to .env file
    if [ -f ".env" ]; then
        echo "" >> .env
        echo "# SSO Configuration" >> .env
        echo "SSO_SECRET_KEY=$SSO_SECRET_KEY" >> .env
        print_success "Added SSO_SECRET_KEY to .env file"
    else
        print_warning ".env file not found, please create it manually"
    fi
else
    print_success "SSO_SECRET_KEY is set"
fi

# Step 3: Create migrations
print_header "Step 3: Creating Database Migrations"

print_info "Creating SSO migrations..."
if python manage.py makemigrations sso; then
    print_success "SSO migrations created"
else
    print_error "Failed to create migrations"
    exit 1
fi

# Step 4: Run migrations
print_header "Step 4: Running Database Migrations"

print_info "Applying migrations..."
if python manage.py migrate; then
    print_success "Migrations applied"
else
    print_error "Failed to apply migrations"
    exit 1
fi

# Step 5: Test SSO module
print_header "Step 5: Testing SSO Module"

print_info "Testing SSO imports..."
if python manage.py shell << EOF
from sso.models import SSOToken, SSOSession, SSOAuditLog
from sso.utils import SSOTokenManager
from sso.serializers import SSOUserSerializer
print("✓ All SSO modules loaded successfully")
EOF
then
    print_success "SSO module tests passed"
else
    print_error "SSO module tests failed"
    exit 1
fi

# Step 6: Collect static files
print_header "Step 6: Collecting Static Files"

print_info "Collecting static files..."
if python manage.py collectstatic --noinput; then
    print_success "Static files collected"
else
    print_warning "Static files collection had warnings (may be okay)"
fi

# Step 7: Display next steps
print_header "SSO DEPLOYMENT COMPLETE!"

print_success "SSO system deployed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Restart the application server:"
echo "     systemctl restart business-platform"
echo ""
echo "  2. Test SSO endpoints:"
echo "     curl -X POST http://localhost:8000/api/sso/token/ \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"username\":\"admin\",\"password\":\"your_password\"}'"
echo ""
echo "  3. Configure secondary apps using the guide:"
echo "     cat ../SSO_INTEGRATION_GUIDE.md"
echo ""
print_warning "IMPORTANT: Use the SAME SSO_SECRET_KEY in ALL applications!"
echo "  SSO_SECRET_KEY=$SSO_SECRET_KEY"
echo ""
print_success "Deployment complete! Check logs for any issues."
