#!/bin/bash

# Source the DC install setup
source /mnt/applications/synopsys/2024-25/scripts/SYN_2024.09-SP2_RHELx86.sh

# RTL Debug script runner
# Usage: bash ./run_debug.sh

# Set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/outputs/logs"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Display start information
echo "========================================"
echo "RTL Debug start time: $(date)"
echo "Working directory: ${SCRIPT_DIR}"
echo "========================================"

# Run RTL debug and save complete output to debug.log
echo "Running RTL Debug..."
dc_shell -f "${SCRIPT_DIR}/debug.tcl" | tee "${LOG_DIR}/debug.log"

# Check execution result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ RTL Debug completed!"
    echo "📝 Debug log: ${LOG_DIR}/debug.log"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "❌ RTL Debug failed!"
    echo "📝 Error log: ${LOG_DIR}/debug.log"
    echo "========================================"
    exit 1
fi 