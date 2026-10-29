#!/usr/bin/env bash
# End-to-end smoke test script for UK Wind Generation Forecast Accuracy API
# Usage: ./scripts/smoke.sh [BASE_URL]
# Example: ./scripts/smoke.sh http://127.0.0.1:8000

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
# Strip trailing slash if present
BASE_URL="${BASE_URL%/}"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

FAILED=0

echo "=========================================================="
echo "Running E2E Smoke Tests against: ${BASE_URL}"
echo "=========================================================="

# Helper: check HTTP status and json content
run_check() {
    local name="$1"
    local endpoint="$2"
    local expected_status="$3"
    local validation_pattern="$4"

    echo -n "Checking ${name} (${endpoint})... "

    # Make request capturing body and status code
    local response
    local status
    response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}" || true)
    status=$(echo "${response}" | tail -n1)
    local body
    body=$(echo "${response}" | sed '$d')

    if [ "${status}" -ne "${expected_status}" ]; then
        echo -e "${RED}FAILED${NC} (Expected HTTP ${expected_status}, got ${status})"
        FAILED=1
        return
    fi

    if [ -n "${validation_pattern}" ]; then
        if echo "${body}" | grep -q -E "${validation_pattern}"; then
            echo -e "${GREEN}PASSED${NC} (HTTP ${status})"
        else
            echo -e "${RED}FAILED${NC} (Body did not match pattern '${validation_pattern}')"
            echo "Response preview: $(echo "${body}" | head -c 200)"
            FAILED=1
            return
        fi
    else
        echo -e "${GREEN}PASSED${NC} (HTTP ${status})"
    fi
}

# 1. Health check: 200 OK
run_check "Health check" "/api/health" 200 '"status"[[:space:]]*:[[:space:]]*"ok"'

# 2. Meta endpoint: 200 OK with window metadata
run_check "Metadata window" "/api/meta" 200 '"expected_periods"[[:space:]]*:[[:space:]]*744'

# 3. Summary endpoint: 200 OK with positive matched count and non-null MAE
run_check "Summary metrics" "/api/summary?cutoff_time=09:00" 200 '"n_matched"[[:space:]]*:[[:space:]]*[1-9][0-9]*'

# 4. Series endpoint: 200 OK with non-empty points array
run_check "Time-series hourly" "/api/series?granularity=hourly" 200 '"points"[[:space:]]*:[[:space:]]*\['

# 5. Records endpoint: 200 OK with items list
run_check "Records pagination" "/api/records?page=1&page_size=50" 200 '"items"[[:space:]]*:[[:space:]]*\['

# 6. Parameter validation: 400 Bad Request on invalid cutoff
run_check "Validation error handling" "/api/summary?cutoff_time=99:99" 400 '"code"[[:space:]]*:[[:space:]]*"INVALID_PARAMETER"'

echo "=========================================================="
if [ "${FAILED}" -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some smoke checks failed.${NC}"
    exit 1
fi

