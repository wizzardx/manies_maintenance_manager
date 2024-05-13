#!/bin/bash
set -e

# Variables
TEMPLATE_REPO="gh:cookiecutter/cookiecutter-django"
NEW_TEMPLATE_DIR="/tmp/new_template_project"
ORIGINAL_TEMPLATE_BRANCH="original_template"
CURRENT_PROJECT_DIR="$(pwd)"
NEW_TEMPLATE_BRANCH="updated_template"

# Step 0: Tidy up previous runs
echo "Tidying up from previous runs..."
git checkout main
rm -rf /home/david/.cookiecutters/cookiecutter-django
rm -rf "$NEW_TEMPLATE_DIR"
git branch -D new_template || true
git remote remove new_template || true
git branch -D $NEW_TEMPLATE_BRANCH || true

# Step 1: Create a new project using the latest Cookiecutter template
echo "Creating a new project using the latest Cookiecutter template..."
cookiecutter --replay $TEMPLATE_REPO --output-dir $NEW_TEMPLATE_DIR

# Step 2: Initialize and commit new template
echo "Initializing Git in the new template directory and committing all files..."
cd $NEW_TEMPLATE_DIR/manies_maintenance_manager
git init
git add .
git commit -m "Initial commit of new template"

# Step 3: Add as a remote and fetch
echo "Adding new template as a remote and fetching it..."
cd "$CURRENT_PROJECT_DIR"
git remote add new_template $NEW_TEMPLATE_DIR/manies_maintenance_manager
git fetch new_template

# Step 4: Create branch for updated template
echo "Creating a new branch for the updated template..."
git checkout -b $NEW_TEMPLATE_BRANCH new_template/main

# Step 5: Switch to original template branch
echo "Switching to the original template branch..."
git checkout $ORIGINAL_TEMPLATE_BRANCH

# Step 6: Generate diffs and find common files
echo "Generating diffs and finding common files..."
git diff $ORIGINAL_TEMPLATE_BRANCH $NEW_TEMPLATE_BRANCH > /tmp/template_changes.diff
git diff $ORIGINAL_TEMPLATE_BRANCH main > /tmp/main_changes.diff
grep -oP '(?<=^--- a/|^\+\+\+ b/).*' /tmp/main_changes.diff | sort | uniq > /tmp/sorted_unique_main_files.txt
grep -oP '(?<=^--- a/|^\+\+\+ b/).*' /tmp/template_changes.diff | sort | uniq > /tmp/sorted_unique_template_files.txt
comm -12 /tmp/sorted_unique_main_files.txt /tmp/sorted_unique_template_files.txt > /tmp/common_files.txt

# Step 7: Open Meld for each common file
echo "Opening Meld for each common file..."
git checkout main
while read -r file; do
    meld "$NEW_TEMPLATE_DIR/manies_maintenance_manager/$file" "$CURRENT_PROJECT_DIR/$file"
done < /tmp/common_files.txt

# Cleanup
echo "Cleaning up..."
git remote remove new_template
git branch -D $NEW_TEMPLATE_BRANCH
