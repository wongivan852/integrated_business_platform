#!/bin/bash

# Fix common JSX syntax errors in TSX files

 

echo "🔧 Fixing JSX syntax errors..."

 

FILE="$HOME/Desktop/integrated_business_platform/project_management/frontend/src/pages/iaicc-2025-project-plan.tsx"

 

if [ ! -f "$FILE" ]; then

    echo "❌ File not found: $FILE"

    exit 1

fi

 

echo "📄 Original file backed up to: ${FILE}.backup"

cp "$FILE" "${FILE}.backup"

 

# Show the error area

echo ""

echo "🔍 Lines around error (1245-1250):"

sed -n '1245,1250p' "$FILE"

echo ""

 

# Common fixes for JSX syntax errors:

# 1. Fix comparison operators in text content

# 2. Fix unclosed tags

# 3. Escape special characters

 

# Replace common issues

sed -i 's/\([^{]\)>\([^}]\)/\1\&gt;\2/g' "$FILE"  # Replace standalone > with &gt;

sed -i 's/\([^{]\)<\([^}]\)/\1\&lt;\2/g' "$FILE"  # Replace standalone < with &lt;

 

echo "✅ Applied automatic fixes"

echo ""

echo "If the error persists, please run:"

echo "  nano +1247 $FILE"

echo ""

echo "And manually fix the issue at line 1247, column 26"

echo ""

echo "Common fixes:"

echo "  - Wrap comparisons in {}: {value > 0}"

echo "  - Use &gt; instead of >"

echo "  - Use &lt; instead of <"

echo "  - Check for unclosed tags"

 