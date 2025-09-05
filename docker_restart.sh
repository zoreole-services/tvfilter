#!/bin/bash

# Variables
CONTAINER_NAME="tvfilter"
LOG_FILE="/opt/tvfilter/docker_restart.log"
DOCKER_COMPOSE_CMD="/usr/bin/docker compose"
COMPOSE_DIR="/opt/tvfilter/"  # Directory containing docker-compose.yml
VERBOSE=0



# Parse arguments
while getopts "v" opt; do
  case $opt in
    v) VERBOSE=1 ;;
  esac
done

# Ensure log file exists (create directory and file if needed)
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Logging function
log() {
    if [ "$VERBOSE" -eq 1 ]; then
        echo "$1"
    fi
    echo "$1" >> "$LOG_FILE"
}

# Function to check if the container is running
is_container_running() {
    docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" | grep -q "Up"
}

log "----------------------------------------"
log "[$(date)] START"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log "[$(date)] ERROR: Docker is not running"
    exit 1
fi

# Move to the working directory
cd "$COMPOSE_DIR" || { log "[$(date)] ERROR: Directory not found"; exit 1; }

# Is the container running?
if is_container_running; then
    log "[$(date)] Container $CONTAINER_NAME is running. Restarting..."
    # Restart the container
    $DOCKER_COMPOSE_CMD down >> "$LOG_FILE" 2>&1
    $DOCKER_COMPOSE_CMD up -d >> "$LOG_FILE" 2>&1

    # Final check
    if is_container_running; then
        log "[$(date)] SUCCESS: Container restarted successfully"
    else
        log "[$(date)] ERROR: Container did not start correctly"
        exit 1
    fi
else
    log "[$(date)] Container $CONTAINER_NAME is not running. No action taken."
fi
