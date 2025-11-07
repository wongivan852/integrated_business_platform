#!/bin/bash

# Fix JSX syntax error at line 1247

 

FILE="src/pages/iaicc-2025-project-plan.tsx"

 

echo "🔍 Checking line 1247..."

LINE_1247=$(sed -n '1247p' "$FILE")

echo "Line 1247: $LINE_1247"

echo ""

 

# Check what character is at column 26

CHAR_26=$(echo "$LINE_1247" | cut -c26)

echo "Character at column 26: [$CHAR_26]"

echo ""

 

# Backup

cp "$FILE" "${FILE}.backup"

echo "✅ Backup created"

echo ""

 

# Common fix: Replace > with &gt; in text content

# This is a safe replacement for most cases

echo "🔧 Applying fix..."

 

# Fix line 1247 specifically - replace standalone > with &gt;

# Only between > and < tags in text content

sed -i '1247s/>\([^<{]*\)>\([^<{]*\)</>\1\&gt;\2</g' "$FILE"

 

echo "✅ Fix applied"

echo ""

echo "New line 1247:"

sed -n '1247p' "$FILE"

echo ""

echo "If the error persists, please share line 1247 and I'll provide a manual fix"

 