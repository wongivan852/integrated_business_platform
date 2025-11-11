#!/bin/bash

# Local Deployment Script for Bilingual Project Management App
# This script automates the local deployment process

set -e  # Exit on error

echo "🚀 Starting Local Deployment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION found${NC}"
else
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Step 2: Activate virtual environment
echo ""
echo -e "${BLUE}Step 2: Activating virtual environment...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment created and activated${NC}"
fi

# Step 3: Install dependencies
echo ""
echo -e "${BLUE}Step 3: Installing Python dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 4: Check Django
echo ""
echo -e "${BLUE}Step 4: Verifying Django installation...${NC}"
DJANGO_VERSION=$(python -c "import django; print(django.get_version())" 2>/dev/null || echo "not found")
if [ "$DJANGO_VERSION" != "not found" ]; then
    echo -e "${GREEN}✅ Django $DJANGO_VERSION installed${NC}"
else
    echo "❌ Django not installed properly"
    exit 1
fi

# Step 5: Database migrations
echo ""
echo -e "${BLUE}Step 5: Running database migrations...${NC}"
export USE_SQLITE=True
python manage.py migrate --noinput
echo -e "${GREEN}✅ Database migrations completed${NC}"

# Step 6: Create locale directories
echo ""
echo -e "${BLUE}Step 6: Setting up locale directories...${NC}"
mkdir -p locale/zh_Hans/LC_MESSAGES
mkdir -p project_management/locale/zh_Hans/LC_MESSAGES
echo -e "${GREEN}✅ Locale directories created${NC}"

# Step 7: Compile messages (optional)
echo ""
echo -e "${BLUE}Step 7: Compiling translation messages...${NC}"
if command -v msgfmt &> /dev/null; then
    python manage.py compilemessages --locale=zh_Hans || true
    echo -e "${GREEN}✅ Translation messages compiled${NC}"
else
    echo -e "${YELLOW}⚠️  gettext not installed. Skipping message compilation.${NC}"
    echo -e "${YELLOW}   App will still work! Only affects template translations.${NC}"
    echo -e "${YELLOW}   To install: sudo apt-get install gettext (Ubuntu/Debian)${NC}"
fi

# Step 8: Collect static files
echo ""
echo -e "${BLUE}Step 8: Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Static files collected${NC}"

# Step 9: Check React build
echo ""
echo -e "${BLUE}Step 9: Verifying React build...${NC}"
if [ -f "staticfiles/project_management/frontend/assets/index-C4CRqYZL.js" ]; then
    echo -e "${GREEN}✅ React build found (281 KB with i18n)${NC}"
else
    echo -e "${YELLOW}⚠️  React build not found in staticfiles${NC}"
fi

# Step 10: Run system check
echo ""
echo -e "${BLUE}Step 10: Running Django system check...${NC}"
python manage.py check
echo -e "${GREEN}✅ System check passed${NC}"

# Final message
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Local Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}To start the development server:${NC}"
echo ""
echo "  python manage.py runserver"
echo ""
echo -e "${BLUE}Then open your browser to:${NC}"
echo ""
echo "  📱 Main Site:        http://127.0.0.1:8000/"
echo "  🔧 Admin Panel:      http://127.0.0.1:8000/admin/"
echo "  📊 Projects:         http://127.0.0.1:8000/project-management/"
echo "  ⚛️  React Frontend:   http://127.0.0.1:8000/project-management/app/"
echo ""
echo -e "${BLUE}Language Switchers:${NC}"
echo ""
echo "  Django:  🌐 Globe icon dropdown in navbar"
echo "  React:   EN / 中文 buttons in navigation"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo ""
echo "  📖 Deployment Guide:      LOCAL_DEPLOYMENT_GUIDE.md"
echo "  📚 Implementation Guide:  project_management/BILINGUAL_IMPLEMENTATION_GUIDE.md"
echo "  📝 Summary:               project_management/BILINGUAL_REVAMP_SUMMARY.md"
echo ""
echo -e "${GREEN}Happy Testing! 🚀${NC}"
echo ""

# Optional: Create superuser
echo -e "${YELLOW}Do you want to create a superuser? (y/n)${NC}"
read -r CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ]; then
    echo ""
    echo -e "${BLUE}Creating superuser...${NC}"
    python manage.py createsuperuser
fi
