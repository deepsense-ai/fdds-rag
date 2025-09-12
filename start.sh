#!/bin/bash

set -e

# Colors for better output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} ${WHITE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} ${WHITE}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} ${WHITE}$1${NC}"
}

print_error() {
    echo -e "${RED}✗${NC} ${WHITE}$1${NC}"
}

print_header() {
    echo -e "\n${PURPLE}════════════════════════════════════════${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════${NC}\n"
}

# Function to generate random API key
generate_random_key() {
    openssl rand -hex 32
}

# Default values
DETACHED=false
JAEGER_ENABLED=false
WITH_INGEST=false
INGEST_FILE=""
PORT="8000"
HOST="0.0.0.0"
ENV_FILE=""
DATA_MOUNT_PATH="./app-data"
declare -a ENV_VARS=()

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --detached              Run in detached mode"
    echo "  --jaeger                    Enable Jaeger tracing"
    echo "  --with-ingest               Run ingestion service"
    echo "  --with-ingest-file FILE     Run ingestion with custom PDF file"
    echo "  --port PORT                 Set API port (default: 8000)"
    echo "  --host HOST                 Set API host (default: 0.0.0.0)"
    echo "  --data-path PATH            Set data mount path (default: ./app-data)"
    echo "  --env-file FILE             Load environment variables from file"
    echo "  -e, --env KEY=VALUE         Set environment variable"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --with-ingest --port 9000"
    echo "  $0 --with-ingest-file custom-pdfs.txt --detached"
    echo "  $0 --data-path /custom/data --with-ingest"
    echo "  $0 --env-file .env.prod -e DEBUG=true"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detached)
            DETACHED=true
            shift
            ;;
        --jaeger)
            JAEGER_ENABLED=true
            shift
            ;;
        --with-ingest)
            WITH_INGEST=true
            shift
            ;;
        --with-ingest-file)
            if [[ -n "$2" && "$2" != -* ]]; then
                WITH_INGEST=true
                INGEST_FILE="$2"
                shift 2
            else
                print_error "Error: --with-ingest-file requires a filename"
                exit 1
            fi
            ;;
        --port)
            if [[ -n "$2" && "$2" != -* ]]; then
                PORT="$2"
                shift 2
            else
                print_error "Error: --port requires a port number"
                exit 1
            fi
            ;;
        --host)
            if [[ -n "$2" && "$2" != -* ]]; then
                HOST="$2"
                shift 2
            else
                print_error "Error: --host requires a host address"
                exit 1
            fi
            ;;
        --data-path)
            if [[ -n "$2" && "$2" != -* ]]; then
                DATA_MOUNT_PATH="$2"
                shift 2
            else
                print_error "Error: --data-path requires a path"
                exit 1
            fi
            ;;
        --env-file)
            if [[ -n "$2" && "$2" != -* ]]; then
                ENV_FILE="$2"
                shift 2
            else
                print_error "Error: --env-file requires a filename"
                exit 1
            fi
            ;;
        -e|--env)
            if [[ -n "$2" && "$2" != -* ]]; then
                ENV_VARS+=("$2")
                shift 2
            else
                print_error "Error: -e/--env requires KEY=VALUE format"
                exit 1
            fi
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
done

print_header "🚀 FDDS RAG System Startup"

# Handle OpenAI API key - check environment first, then existing file
OPENAI_API_KEY=""

# Check if OPENAI_API_KEY is already set in environment
if [ -n "$OPENAI_API_KEY" ]; then
    print_success "Using OpenAI API key from environment"
elif [ -f "docker/fdds/fdds.env" ]; then
    EXISTING_OPENAI_KEY=$(grep "^OPENAI_API_KEY=" docker/fdds/fdds.env 2>/dev/null | cut -d'=' -f2- || echo "")
    if [ -n "$EXISTING_OPENAI_KEY" ]; then
        OPENAI_API_KEY="$EXISTING_OPENAI_KEY"
        KEY_ENDING="${EXISTING_OPENAI_KEY: -10}"
        print_success "Using existing OpenAI API key ending with: ...$KEY_ENDING"
    fi
fi

# If still no key found, check env file or prompt
if [ -z "$OPENAI_API_KEY" ] && [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- || echo "")
    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "Using OpenAI API key from $ENV_FILE"
    fi
fi

# Check env vars array for OpenAI key
for env_var in "${ENV_VARS[@]}"; do
    if [[ "$env_var" == OPENAI_API_KEY=* ]]; then
        OPENAI_API_KEY="${env_var#OPENAI_API_KEY=}"
        print_success "Using OpenAI API key from command line"
        break
    fi
done

# If still no key, prompt user
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OpenAI API key not found in environment or existing files"
    echo -n "Please enter your OpenAI API key: "
    read -r OPENAI_API_KEY

    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "Error: OpenAI API key cannot be empty"
        exit 1
    fi
fi

# Prepare environment variables
print_info "Preparing environment configuration..."

# Base environment variables
QD_KEY=$(generate_random_key)
ENV_VARS_COMPOSE=(
    "OPENAI_API_KEY=$OPENAI_API_KEY"
    "NEPTUNE_API_KEY=$(generate_random_key)"
    "QDRANT__SERVICE__API_KEY=$QD_KEY"
    "QDRANT_API_KEY=$QD_KEY"
    "JAEGER_ENABLED=$JAEGER_ENABLED"
    "QDRANT_URL=http://qdrant"
    "QDRANT_INGEST_URL=http://qdrant"
    "DATA_MOUNT_PATH=$DATA_MOUNT_PATH"
)

# Add custom environment variables from file
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    print_info "Loading environment variables from $ENV_FILE"
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            ENV_VARS_COMPOSE+=("$line")
        fi
    done < "$ENV_FILE"
fi

# Add custom environment variables from command line
for env_var in "${ENV_VARS[@]}"; do
    ENV_VARS_COMPOSE+=("$env_var")
done

print_success "Environment configuration prepared"

# Prepare docker compose command
COMPOSE_FILE="docker/fdds/docker-compose.yml"
DOCKER_COMPOSE_CMD="docker compose -f $COMPOSE_FILE"

# Handle profiles
PROFILES=""
if [ "$JAEGER_ENABLED" = true ]; then
    PROFILES="--profile jaeger"
    print_info "Jaeger tracing will be enabled"
fi

# Prepare data directory
print_info "Preparing data directory: $DATA_MOUNT_PATH"
mkdir -p "$DATA_MOUNT_PATH"

# Create .env file in data directory
ENV_FILE_PATH="$DATA_MOUNT_PATH/.env"
print_info "Creating environment file: $ENV_FILE_PATH"

# Write all environment variables to .env file
cat > "$ENV_FILE_PATH" << EOF
# Generated by start.sh on $(date)
$(printf '%s\n' "${ENV_VARS_COMPOSE[@]}")
EOF

print_success "Environment file created with ${#ENV_VARS_COMPOSE[@]} variables"

# Handle ingestion
if [ "$WITH_INGEST" = true ]; then
    PROFILES="$PROFILES --profile ingestion"
    print_info "Ingestion service will be included"

    if [ -n "$INGEST_FILE" ]; then
        if [ ! -f "$INGEST_FILE" ]; then
            print_error "Error: Ingestion file '$INGEST_FILE' not found"
            exit 1
        fi
        print_info "Using custom ingestion file: $INGEST_FILE"
        cp "$INGEST_FILE" "$DATA_MOUNT_PATH/pdfs.txt"
        print_success "Custom PDF list copied to $DATA_MOUNT_PATH/pdfs.txt"
    else
        # Copy default pdfs file if it exists
        if [ -f "data/pdfs.txt" ]; then
            cp "data/pdfs.txt" "$DATA_MOUNT_PATH/pdfs.txt"
            print_success "Default PDF list copied to $DATA_MOUNT_PATH/pdfs.txt"
        else
            print_warning "No default pdfs.txt found, ingestion may fail if no pdfs.txt exists in data directory"
        fi
    fi
else
    print_info "Ingestion service will be skipped"
fi

# Update docker-compose command to use the env file
DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD --env-file $ENV_FILE_PATH"

print_header "🐳 Starting Docker Services"

# Show configuration summary
print_info "Configuration Summary:"
echo "  • API Port: $PORT"
echo "  • API Host: $HOST"
echo "  • Data Mount Path: $DATA_MOUNT_PATH"
echo "  • Detached Mode: $DETACHED"
echo "  • Jaeger Enabled: $JAEGER_ENABLED"
echo "  • Ingestion Enabled: $WITH_INGEST"
if [ -n "$INGEST_FILE" ]; then
    echo "  • Custom Ingestion File: $INGEST_FILE"
fi
if [ -n "$ENV_FILE" ]; then
    echo "  • Environment File: $ENV_FILE"
fi
if [ ${#ENV_VARS[@]} -gt 0 ]; then
    echo "  • Custom Environment Variables: ${#ENV_VARS[@]} set"
fi
echo ""

# Run docker compose
if [ "$DETACHED" = true ]; then
    print_info "Starting services in detached mode..."
    eval "$DOCKER_COMPOSE_CMD $PROFILES up -d"
    if [ $? -eq 0 ]; then
        print_success "Services started successfully in detached mode"
        print_info "API will be available at: http://$HOST:$PORT"
        if [ "$JAEGER_ENABLED" = true ]; then
            print_info "Jaeger UI available at: http://localhost:16686"
        fi
        print_info "Qdrant dashboard available at: http://localhost:6333/dashboard"
        print_info ""
        print_info "Use 'docker compose -f $COMPOSE_FILE logs -f' to view logs"
        print_info "Use 'docker compose -f $COMPOSE_FILE down' to stop services"
    else
        print_error "Failed to start services"
        exit 1
    fi
else
    print_info "Starting services in foreground mode..."
    print_info "Press Ctrl+C to stop all services"
    print_info ""
    eval "$DOCKER_COMPOSE_CMD $PROFILES up"
fi
