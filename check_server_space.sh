#!/bin/bash
# Space Check Script for 54.160.147.118
# Run this on the server to check if there's enough space

echo "========================================="
echo "🔍 Server Disk Space Analysis"
echo "========================================="
echo ""

# 1. Overall disk usage
echo "📊 Overall Disk Usage:"
df -h | grep -E "Filesystem|/$|/home"
echo ""

# 2. Available space in GB
AVAILABLE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "💾 Available Space: ${AVAILABLE}GB"
echo ""

# 3. Existing projects
echo "📁 Existing Projects:"
if [ -d "/var/www" ]; then
    du -sh /var/www/* 2>/dev/null
fi
if [ -d "/opt" ]; then
    du -sh /opt/* 2>/dev/null
fi
if [ -d "/home/aipenpaladm" ]; then
    du -sh /home/aipenpaladm/* 2>/dev/null
fi
echo ""

# 4. Required space
REQUIRED=2
echo "📦 This Project Needs: ${REQUIRED}GB"
echo ""

# 5. Assessment
if [ "$AVAILABLE" -gt "$REQUIRED" ]; then
    echo "✅ SUFFICIENT SPACE AVAILABLE"
    echo "   You have ${AVAILABLE}GB free, project needs ${REQUIRED}GB"
    echo "   Safe to proceed with deployment!"
else
    echo "⚠️ INSUFFICIENT SPACE"
    echo "   You have ${AVAILABLE}GB free, project needs ${REQUIRED}GB"
    echo "   Need to free up space or upgrade storage"
fi
echo ""

# 6. Memory check
echo "🧠 Memory Status:"
free -h | grep -E "Mem|Swap"
echo ""

# 7. Top space consumers
echo "📈 Top 10 Space Consumers:"
du -h --max-depth=1 /home/aipenpaladm 2>/dev/null | sort -hr | head -10
echo ""

echo "========================================="
echo "✅ Analysis Complete"
echo "========================================="

