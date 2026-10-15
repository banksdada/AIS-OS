#!/usr/bin/env bash
# Wrapper for the client tracker. Loads the two required env vars from this
# directory and forwards all arguments to client-tracker.py.
#
# Usage:
#   ./scripts/crm.sh list
#   ./scripts/crm.sh add "Client Name" "email@example.com" "Lead"
#   ./scripts/crm.sh stage "Client Name" "Proposal"
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export GOOGLE_CREDENTIALS_PATH="${GOOGLE_CREDENTIALS_PATH:-$SCRIPT_DIR/credentials.json}"
export CLIENT_TRACKER_ID="${CLIENT_TRACKER_ID:-1OuqO9tpzgH-zd9BIGujL_u2dKelSbmMAo_iRtz3gvnY}"

exec python3 "$SCRIPT_DIR/client-tracker.py" "$@"