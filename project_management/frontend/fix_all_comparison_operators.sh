#!/bin/bash

# Fix all comparison operators in JSX text content

 

FILE="src/pages/iaicc-2025-project-plan.tsx"

 

echo "🔧 Fixing all comparison operators in JSX..."

echo ""

 

# Backup

cp "$FILE" "${FILE}.backup.$(date +%s)"

echo "✅ Backup created"

echo ""

 

# Fix all common patterns of comparison operators in text

# Pattern: >number or <number in text content

 

# Fix >4.0 and similar patterns

sed -i 's/>4\.0/\&gt;4.0/g' "$FILE"

sed -i 's/<4\.0/\&lt;4.0/g' "$FILE"

 

# Fix >95% and similar percentage comparisons

sed -i 's/>95%/\&gt;95%/g' "$FILE"

sed -i 's/<95%/\&lt;95%/g' "$FILE"

sed -i 's/>90%/\&gt;90%/g' "$FILE"

sed -i 's/<90%/\&lt;90%/g' "$FILE"

sed -i 's/>80%/\&gt;80%/g' "$FILE"

sed -i 's/<80%/\&lt;80%/g' "$FILE"

 

# Fix >X and <X patterns where X is a number

sed -i 's/>\([0-9]\)/\&gt;\1/g' "$FILE"

sed -i 's/<\([0-9]\)/\&lt;\1/g' "$FILE"

 

# Fix >= and <=

sed -i 's/>=\([0-9]\)/\&gt;=\1/g' "$FILE"

sed -i 's/<=\([0-9]\)/\&lt;=\1/g' "$FILE"

 

echo "✅ Applied fixes for comparison operators"

echo ""

 

# Check if there are any remaining issues

echo "🔍 Checking for remaining issues..."

ISSUES=$(grep -n "[^{]>[0-9]\|[^{]<[0-9]" "$FILE" | grep -v "className\|style\|key\|id\|=" || true)

 

if [ -n "$ISSUES" ]; then

    echo "⚠️  Potential remaining issues:"

    echo "$ISSUES"

else

    echo "✅ No obvious issues found"

fi

 

echo ""

echo "📝 Lines that were modified:"

grep -n "&gt;\|&lt;" "$FILE" | head -20

 

echo ""

echo "✅ Fix complete! Try running: npm run dev"

 