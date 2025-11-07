#!/bin/bash

# Fix comparison operators in JSX text content WITHOUT breaking HTML tags

 

FILE="src/pages/iaicc-2025-project-plan.tsx"

 

echo "🔧 Applying correct JSX fixes..."

echo ""

 

# Restore from original if available

if [ -f ~/Downloads/iaicc-2025-project-plan.tsx ]; then

    cp ~/Downloads/iaicc-2025-project-plan.tsx "$FILE"

    echo "✅ Restored from original file"

else

    echo "⚠️  Using current file (may have errors)"

fi

 

# Backup

cp "$FILE" "${FILE}.backup.final"

echo "✅ Backup created: ${FILE}.backup.final"

echo ""

 

# Fix ONLY the specific known issues

# Line 1247: Achieve >4.0/5.0

sed -i 's/Achieve >4\.0/Achieve \&gt;4.0/g' "$FILE"

 

# Line 1475: >50+ team members

# Need to be careful - only replace >50+ when it's text content, not in tags

sed -i 's/>>\([0-9]\+\)\+</>>\&gt;\1+</g' "$FILE"

sed -i 's/">\([0-9]\+\)+</">\&gt;\1+</g' "$FILE"

 

# More specific: find patterns like ">50+" in text

sed -i 's/ >50+/ \&gt;50+/g' "$FILE"

sed -i 's/">50+/">\&gt;50+/g' "$FILE"

 

# Fix other common percentage patterns in TEXT only (after tags close)

# Pattern: "sometext >95%" or "sometext <90%"

sed -i 's/ >\([0-9]\+\)%/ \&gt;\1%/g' "$FILE"

sed -i 's/ <\([0-9]\+\)%/ \&lt;\1%/g' "$FILE"

 

# Fix patterns like ">$X" or "<$X"

sed -i 's/ >\$/ \&gt;$/g' "$FILE"

sed -i 's/ <\$/ \&lt;$/g' "$FILE"

 

echo "✅ Applied targeted fixes"

echo ""

 

# Verify specific lines

echo "📝 Checking fixed lines:"

echo ""

echo "Line 1247:"

sed -n '1247p' "$FILE"

echo ""

echo "Line 1475:"

sed -n '1475p' "$FILE"

echo ""

 

echo "✅ Fix complete!"

echo ""

echo "Try: npm run dev"

 