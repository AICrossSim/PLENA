#!/bin/bash

# Source the DC install setup
source /mnt/applications/synopsys/2024-25/scripts/SYN_2024.09-SP2_RHELx86.sh

# Synthesis runner script - Handles log redirection automatically
# Usage: ./run_dc.sh

# Set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/outputs/logs"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Display start information
echo "========================================"
echo "Synthesis start time: $(date)"
echo "Working directory: ${SCRIPT_DIR}"
echo "========================================"

# Run DC synthesis and save complete output to run_dc.log
echo "Running DC synthesis..."
dc_shell -f "${SCRIPT_DIR}/dc.tcl" | tee "${LOG_DIR}/run_dc.log"

# Check execution result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ Synthesis completed successfully!"
    echo "📂 Output files location: ${SCRIPT_DIR}/outputs/"
    echo "📝 Complete log: ${LOG_DIR}/run_dc.log"
    echo "📊 Reports: ${SCRIPT_DIR}/outputs/reports/"
    echo "🔍 Netlist: ${SCRIPT_DIR}/outputs/netlist/"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "❌ Synthesis failed!"
    echo "📝 Error log: ${LOG_DIR}/run_dc.log"
    echo "🔧 Check log: ${LOG_DIR}/coprocessor_check.log"
    echo "========================================"
    exit 1
fi 
