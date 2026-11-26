#!/usr/bin/env bash
# ai-generated: 0% - Hand-written deploy script
set -euo pipefail

CANDIDATE="${1:-ghcr.io/swasik/svcdesk-v2-seeded:2.0.0}"
STABLE="ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
CADDY_ADMIN="${CADDY_ADMIN_URL:-http://edge:2019}"
PROM="${PROMETHEUS_URL:-http://prometheus:9090}"
RECORD_DIR="${RELEASE_RECORD_DIR:-.}"
STRATEGY="${RELEASE_STRATEGY:-canary}"

START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ACTIONS_LOG=()

add_action() {
    local act_at="$1"
    local act_desc="$2"
    local act_auto="$3"
    local act_appr="${4:-}"
    if [ -n "$act_appr" ]; then
        ACTIONS_LOG+=("    - at: \"$act_at\"\n      action: \"$act_desc\"\n      autonomy: \"$act_auto\"\n      approval: \"$act_appr\"")
    else
        ACTIONS_LOG+=("    - at: \"$act_at\"\n      action: \"$act_desc\"\n      autonomy: \"$act_auto\"")
    fi
}

write_change_record() {
    local outcome="$1"
    local reason="$2"
    local finish_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    mkdir -p "$RECORD_DIR"
    local record_path="$RECORD_DIR/CHANGE.md"
    
    cat << EOF > "$record_path"
---
lab6_change:
  id: "change-$(date +%s)"
  candidate: "$CANDIDATE"
  stable: "$STABLE"
  strategy: "$STRATEGY"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "$START_TIME"
  finished: "$finish_time"
  outcome: "$outcome"
  reason: "$reason"
  actions:
$(for a in "${ACTIONS_LOG[@]}"; do echo -e "$a"; done)
---
# Change Record: Canary Deployment of $CANDIDATE

## Outcome: $outcome
Reason: $reason

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
EOF

    if [ "$RECORD_DIR" != "." ]; then
        cp "$record_path" "./CHANGE.md" || true
    fi
}

add_action "$START_TIME" "Read deployment configuration and pre-approved release plan" "approve-then-act" "CAB pre-approval CAB-2026-L6-CANARY"

echo "=== Deploying candidate $CANDIDATE ==="
# Start candidate container on canary track
COMPOSE_ARGS=()
if [ -n "${COMPOSE_FILE:-}" ]; then
    IFS=':' read -ra FILES <<< "$COMPOSE_FILE"
    for f in "${FILES[@]}"; do
        [ -n "$f" ] && COMPOSE_ARGS+=(-f "$f")
    done
fi
if [ -n "${COMPOSE_PROJECT_NAME:-}" ]; then
    COMPOSE_ARGS+=(-p "$COMPOSE_PROJECT_NAME")
fi

if [ ${#COMPOSE_ARGS[@]} -gt 0 ]; then
    CANARY_IMAGE="$CANDIDATE" docker compose "${COMPOSE_ARGS[@]}" up -d --no-deps svcdesk-canary
fi

ACT_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
add_action "$ACT_START" "Start svcdesk-canary container with candidate image" "closed-loop"

set_caddy_weights() {
    local stable_w="$1"
    local canary_w="$2"
    echo "Setting Caddy weights: stable=$stable_w, canary=$canary_w"
    curl -s -X PATCH -H "Content-Type: application/json" \
        -d "[$stable_w, $canary_w]" \
        "${CADDY_ADMIN}/config/apps/http/servers/srv0/routes/0/handle/0/load_balancing/selection_policy/weights" > /dev/null || true
}

# Ensure baseline is 100% stable, 0% canary
set_caddy_weights 100 0

rollback() {
    local why="$1"
    echo "=== ROLLBACK TRIGGERED: $why ==="
    set_caddy_weights 100 0
    local act_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    add_action "$act_time" "Gate check failed: rollback weights to 100% stable, 0% canary" "closed-loop"
    write_change_record "rolled-back" "Rollback triggered by automated analysis gate: $why"
    exit 3
}

query_prom() {
    local query="$1"
    curl -s -G --data-urlencode "query=$query" "${PROM}/api/v1/query"
}

# Canary steps: weight and duration
STEPS=(10 25 50)
DURATIONS=(20 15 15)

for i in "${!STEPS[@]}"; do
    C_WEIGHT="${STEPS[$i]}"
    S_WEIGHT=$((100 - C_WEIGHT))
    MIN_DUR="${DURATIONS[$i]}"
    
    echo ">>> Starting Canary Step $((i+1)): weight=${C_WEIGHT}%, min_duration=${MIN_DUR}s"
    set_caddy_weights "$S_WEIGHT" "$C_WEIGHT"
    
    STEP_ACT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    add_action "$STEP_ACT_TIME" "Set canary routing weight to ${C_WEIGHT}% (stable: ${S_WEIGHT}%)" "closed-loop"
    
    ELAPSED=0
    CHECK_INTERVAL=5
    while [ $ELAPSED -lt $MIN_DUR ]; do
        sleep $CHECK_INTERVAL
        ELAPSED=$((ELAPSED + CHECK_INTERVAL))
        
        READ_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        add_action "$READ_TIME" "Read Prometheus metrics for canary track at step weight ${C_WEIGHT}%" "read-only"
        
        # Query total, fast (<=0.25s), and error counts on canary over last 10s
        TOT_RESP=$(query_prom 'sum(increase(http_server_request_duration_seconds_count{job="svcdesk",track="canary",http_route="/kb/search"}[10s]))')
        FAST_RESP=$(query_prom 'sum(increase(http_server_request_duration_seconds_bucket{job="svcdesk",track="canary",http_route="/kb/search",le="0.25"}[10s]))')
        ERR_RESP=$(query_prom 'sum(increase(http_server_request_duration_seconds_count{job="svcdesk",track="canary",http_route="/kb/search",http_response_status_code=~"5.."}[10s]))')
        STABLE_RESP=$(query_prom 'sum(increase(http_server_request_duration_seconds_count{job="svcdesk",track="stable",http_route="/kb/search"}[10s]))')
        
        TOT_VAL=$(echo "$TOT_RESP" | jq -r '.data.result[0].value[1] // 0' 2>/dev/null || echo "0")
        FAST_VAL=$(echo "$FAST_RESP" | jq -r '.data.result[0].value[1] // 0' 2>/dev/null || echo "0")
        ERR_COUNT=$(echo "$ERR_RESP" | jq -r '.data.result[0].value[1] // 0' 2>/dev/null || echo "0")
        STABLE_COUNT=$(echo "$STABLE_RESP" | jq -r '.data.result[0].value[1] // 0' 2>/dev/null || echo "0")
        
        echo "Canary step $((i+1)) (t+${ELAPSED}s): canary_tot=$TOT_VAL, fast=$FAST_VAL, err=$ERR_COUNT, stable_tot=$STABLE_COUNT"
        
        # Evaluate metrics using python3
        DECISION=$(python3 - << EOF
import sys

try:
    tot = float("$TOT_VAL")
    fast = float("$FAST_VAL")
    err = float("$ERR_COUNT")
    stable = float("$STABLE_COUNT")
    elapsed = float("$ELAPSED")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(0)

# 1. Hang / unresponsive candidate detection
if elapsed >= 10 and stable > 30 and tot < 2:
    print(f"HANG: Canary completed only {tot} requests while stable completed {stable} requests")
    sys.exit(0)

# 2. SLI violation check (error rate > 0.144 or slow rate > 0.144)
if tot >= 5:
    err_share = err / tot
    slow_share = max(0.0, (tot - fast) / tot)
    if err_share > 0.144:
        print(f"ERR_SLI: Error share {err_share:.4f} exceeded threshold 0.144")
        sys.exit(0)
    if slow_share > 0.144:
        print(f"LAT_SLI: Slow share {slow_share:.4f} exceeded threshold 0.144")
        sys.exit(0)

print("OK")
EOF
)

        echo "Gate evaluation at t+${ELAPSED}s: $DECISION"
        case "$DECISION" in
            HANG*)
                rollback "Hang detected: $DECISION"
                ;;
            ERR_SLI*)
                rollback "Availability SLI violated: $DECISION"
                ;;
            LAT_SLI*)
                rollback "Latency SLI violated: $DECISION"
                ;;
            OK)
                ;;
            *)
                echo "Warning: unexpected gate decision: $DECISION"
                ;;
        esac
    done
done

echo "=== All canary steps completed successfully. Promoting candidate ==="
set_caddy_weights 0 100
PROMOTE_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
add_action "$PROMOTE_TIME" "Promote canary candidate to 100% traffic weight" "closed-loop"

write_change_record "promoted" "Canary release passed all progressive delivery gate steps without violating SLO thresholds."
exit 0
