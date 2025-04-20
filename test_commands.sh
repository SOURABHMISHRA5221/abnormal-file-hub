#!/bin/bash

# Script to test all management commands in sequence
# Run this once Docker is available and the containers are running

echo "======================================================"
echo "Testing File Storage Management Commands"
echo "======================================================"
echo

# Function to wait for user input before proceeding
continue_prompt() {
    echo
    read -p "Press Enter to continue to next step..."
    echo
}

# Step 1: Clean and generate test data
echo "Step 1: Generating test data (5 unique files, 10 duplicates)"
echo "------------------------------------------------------"
./run_management_commands.sh generate --unique=5 --duplicates=10 --clean
continue_prompt

# Step 2: Analyze storage
echo "Step 2: Basic storage analysis"
echo "------------------------------------------------------"
./run_management_commands.sh analyze
continue_prompt

# Step 3: Detailed analysis
echo "Step 3: Detailed storage analysis"
echo "------------------------------------------------------"
./run_management_commands.sh analyze --detail
continue_prompt

# Step 4: Check what would be deleted in dry run
echo "Step 4: Check what would be deleted (dry run)"
echo "------------------------------------------------------"
./run_management_commands.sh delete --dry-run
continue_prompt

# Step 5: Generate more test data
echo "Step 5: Adding more test data (3 unique, 7 duplicates)"
echo "------------------------------------------------------"
./run_management_commands.sh generate --unique=3 --duplicates=7
continue_prompt

# Step 6: Another analysis
echo "Step 6: Updated storage analysis"
echo "------------------------------------------------------"
./run_management_commands.sh analyze
continue_prompt

# Step 7: Delete duplicates (real deletion)
echo "Step 7: Deleting duplicate files"
echo "------------------------------------------------------"
./run_management_commands.sh delete
continue_prompt

# Step 8: Final analysis
echo "Step 8: Final storage analysis after deletion"
echo "------------------------------------------------------"
./run_management_commands.sh analyze --detail

echo
echo "======================================================"
echo "Test sequence completed"
echo "======================================================" 