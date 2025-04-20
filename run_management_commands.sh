#!/bin/bash

# Script to run various management commands for the file storage application

# Function to show help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  generate       Generate test data"
    echo "  analyze        Analyze storage usage"
    echo "  delete         Delete duplicate files"
    echo "  help           Show this help message"
    echo
    echo "Options for 'generate':"
    echo "  --unique=N     Number of unique files to create (default: 10)"
    echo "  --duplicates=N Number of duplicate files to create (default: 20)"
    echo "  --size=N       Base size of files in bytes (default: 1024)"
    echo "  --clean        Clean existing test data before creating new files"
    echo
    echo "Options for 'analyze':"
    echo "  --detail       Show detailed analysis by file type"
    echo "  --min-duplicates=N Minimum number of duplicates to include in report (default: 1)"
    echo
    echo "Options for 'delete':"
    echo "  --dry-run      Show what would be deleted without performing the actual deletion"
    echo
    echo "Examples:"
    echo "  $0 generate --unique=5 --duplicates=10 --clean"
    echo "  $0 analyze --detail"
    echo "  $0 delete --dry-run"
}

# Check if Docker is running
check_docker() {
    docker info > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if containers are running
check_containers() {
    CONTAINER_RUNNING=$(docker-compose ps | grep backend | grep Up)
    if [ -z "$CONTAINER_RUNNING" ]; then
        echo "Starting containers..."
        docker-compose up -d
        
        # Wait for containers to be ready
        echo "Waiting for containers to be ready..."
        sleep 5
    fi
}

# Execute management command
run_command() {
    CMD="docker-compose exec backend python manage.py $*"
    echo "Running: $CMD"
    echo "---------------------------------"
    eval $CMD
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    generate)
        check_docker
        check_containers
        run_command generate_test_data "$@"
        ;;
    analyze)
        check_docker
        check_containers
        run_command analyze_storage "$@"
        ;;
    delete)
        check_docker
        check_containers
        run_command delete_duplicates "$@"
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit 0 