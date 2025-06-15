#!/bin/bash

# Strict error handling
set -euo pipefail
IFS=$'\n\t'

# Define the red color escape code
RED='\033[0;31m'

# Define the no color escape code
NC='\033[0m' # No Color

# Initialize the global variables
NUM_ERRORS=0
STOP_ON_FIRST_ERROR="yes"

# Check for --stop-on-first-error or -s argument
for arg in "$@";
do
    if [ "$arg" == "--stop-on-first-error" ] || [ "$arg" == "-s" ]; then
        STOP_ON_FIRST_ERROR="yes"
    else
        echo "Unknown argument: $arg"
        exit 1
    fi
done


# Function to echo text in red to stderr and increment NUM_ERRORS
echo_error() {
    echo -e "${RED}$1${NC}" >&2
    NUM_ERRORS=$((NUM_ERRORS + 1))
}


# The .ipython directory gets populated by the root process under Docker, and can cause
# permissions-related issues for none-root scripts/etc running outside of docker.
if [ -d .ipython ]; then
    echo "Tidying up annoying .ipython directory..."
    if ! rm -rf .ipython; then
        echo "Errors removing .ipython directory. I'm going to do it as root user instead!"
        sudo rm -rf .ipython
    fi
fi

# Initialize the global variable NUM_ERRORS
NUM_ERRORS=0

# This function is called by the script when one of the important commands runs a none-zero return code.
function handle_error() {
    echo_error "There was an error!"
    NUM_ERRORS=$((NUM_ERRORS + 1))
    if [ "$STOP_ON_FIRST_ERROR" == "yes" ]; then
        exit 1
    fi
}

# Run unit tests first, to get useful things setup under .venv.
echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests.sh -s || handle_error

# Do the helper script checks over here, because it wants to check the .venv file
# logic (but the .venv might not exist if the previous line has not yet run)
echo "Check helper scripts..."
shellcheck -x scripts/*.sh scripts/_sourced/*.sh || handle_error

# Activate the .venv just setup, to get the correct versions of various testing utils
# available.
VENV_DIR=$(scripts/print_venv_dir.sh)

# shellcheck disable=SC1091
. "$VENV_DIR"/bin/activate

echo "Checking if makemigrations needs to be run..."
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no
RESULT=0
OUTPUT=$(python manage.py makemigrations --dry-run 2>&1) || RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo "'python manage.py makemigrations --dry-run' terminated with exit code $RESULT, and output:"
    echo "$OUTPUT"
    handle_error
else
    if echo "$OUTPUT" | grep -q "No changes detected"; then
        echo "No migrations pending."
    else
        echo "Migrations pending:"
        echo "$OUTPUT"
        echo "Please create the database migrations by running 'scripts/makemigrations.sh'"
        handle_error
    fi
fi

# Run 'black' against the code, it makes some things a bit faster in the pre-commit,
# instead of it taking a long time to run reformats, and then terminate with an
# error message because it reformatted something.
echo "Running Black to reformat code..."
black --line-length 88 . || handle_error

echo "Type checks..."

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

mypy --strict . || handle_error

# Reset variable that we no longer need
unset DATABASE_URL
unset USE_DOCKER

echo "Pylint..."

# Find all Python files in the current directory and subdirectories, excluding hidden directories and migration files
mapfile -t files < <(find . -type f -name "*.py" ! -path "*/.*/*" ! -path "*/migrations/*")

# Run pylint with the dynamically found files
pylint --django-settings-module=config.settings --output-format=colorized --enable-all-extensions "${files[@]}" || handle_error

if [ -f '.pre-commit-config.yaml' ]; then
    echo "Updating pre-commit references..."
    pre-commit autoupdate || handle_error

    echo "Running pre-commit checks 1/2... (only staged files)"
    pre-commit run || handle_error

    echo "Running pre-commit checks 2/2... (all files)"
    pre-commit run --all-files || handle_error
else
    echo "It looks like 'pre-commmit' checks were disabled for this project."
fi

# MOOO SLOWWW
# echo "darglint2..."
# darglint2 "${files[@]}" || handle_error

# Check for security issues:
echo "Check for security issues..."
# The ignored number over here is for a "bad" CVE report, and won't be fixed
# upstream. More info over here:
#   https://github.com/dbt-labs/dbt-core/issues/10250#issuecomment-2210501166
# safety check --ignore 70612 || handle_error
# safety scan

# ---
# safety scan --help
#
# Check for security issues...
#
#  Scans a Python project directory.
#  Example: safety scan to scan the current directory
#
#  Usage: safety [GLOBAL-OPTIONS] scan [OPTIONS]
#
#                                                                     Options
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                           ┃                                                                                                                 ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ ['--target']              │ Define a specific project path to scan. (default: current directory)                                            │
# │                           │                                                                                                                 │
# │                           │ Example: safety scan --target /path/to/project                                                                  │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--output']              │ Set the output format for scan results (default: screen)                                                        │
# │                           │                                                                                                                 │
# │                           │ Example: safety scan --output json                                                                              │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--detailed-output']     │ Enable a verbose scan report for detailed insights (only for screen output)                                     │
# │                           │                                                                                                                 │
# │                           │ Example: safety scan --detailed-output                                                                          │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--save-as']             │ In addition to regular output save the scan results to a json, html, text, or spdx file using: FORMAT FILE_PATH │
# │                           │                                                                                                                 │
# │                           │ Example: safety scan --save-as json results.json                                                                │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--policy-file']         │ Use a local policy file to configure the scan.                                                                  │
# │                           │                                                                                                                 │
# │                           │ Note: Project scan policies defined in Safety Platform will override local policy files                         │
# │                           │                                                                                                                 │
# │                           │ Example: safety scan --policy-file /path/to/policy.yml                                                          │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--apply-fixes']         │ Update packages listed in requirements.txt files to secure versions where possible                              │
# │                           │                                                                                                                 │
# │                           │ Currently supports: requirements.txt files                                                                      │
# │                           │                                                                                                                 │
# │                           │ Note: this will update your requirements.txt file                                                               │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--use-server-matching'] │ Flag to enable using server side vulnerability matching. This just sends data to server for now.                │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--filter']              │ Filter output by specific top-level JSON keys.                                                                  │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--install-completion']  │ Install completion for the current shell.                                                                       │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--show-completion']     │ Show completion for the current shell, to copy it or customize the installation.                                │
# ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--help']                │ Show this message and exit.                                                                                     │
# └───────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
#
#                                                      Global-Options
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                  ┃                                                                                    ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ ['--stage']                      │ Assign a development lifecycle stage to your scan (default: development).          │
# │                                  │                                                                                    │
# │                                  │ This labels the scan and its findings in Safety Platform with this stage.          │
# │                                  │                                                                                    │
# │                                  │ Example: safety --stage production scan                                            │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--key']                        │ The API key required for cicd stage or production stage scans.                     │
# │                                  │                                                                                    │
# │                                  │ For development stage scans unset the API key and authenticate using safety auth.  │
# │                                  │                                                                                    │
# │                                  │ Tip: the API key can also be set using the environment variable: SAFETY_API_KEY    │
# │                                  │                                                                                    │
# │                                  │ Example: safety --key API_KEY scan                                                 │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--proxy-host']                 │ Specify a proxy host for network communications.                                   │
# │                                  │                                                                                    │
# │                                  │ Note: proxy details can be set globally in a config file.                          │
# │                                  │                                                                                    │
# │                                  │ See safety configure --help                                                        │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--proxy-port']                 │ Set the proxy port (default: 80).                                                  │
# │                                  │                                                                                    │
# │                                  │ Note: proxy details can be set globally in a config file.                          │
# │                                  │                                                                                    │
# │                                  │ See safety configure --help                                                        │
# │                                  │                                                                                    │
# │                                  │  Requires: [ proxy_host ]                                                          │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--proxy-protocol']             │ Choose the proxy protocol (default: https).                                        │
# │                                  │                                                                                    │
# │                                  │ Note: proxy details can be set globally in a config file.                          │
# │                                  │                                                                                    │
# │                                  │ See safety configure --help                                                        │
# │                                  │                                                                                    │
# │                                  │  Requires: [ proxy_host ]                                                          │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--disable-optional-telemetry'] │ Opt-out of sending optional telemetry data. Anonymized telemetry data will remain. │
# │                                  │                                                                                    │
# │                                  │ Example: safety --disable-optional-telemetry scan                                  │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--debug']                      │ Enable debug mode for detailed output.                                             │
# │                                  │                                                                                    │
# │                                  │ Example: safety --debug scan                                                       │
# ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
# │ ['--version']                    │ Show the version and exit.                                                         │
# └──────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────┘
#
#  Safety CLI version: 3.5.1
#  Documentation: https://docs.safetycli.com
#
#  Made with love by Safety Cybersecurity
#  https://safetycli.com
#  support@safetycli.com
#
# ---

# Check for out of date packages:
echo "Check for outdated packages..."

# - An older "filelock" is needed by the latest "safety" package
# - An older "regex" is needed by the latest "djlint" package.
# - Ansible and ansible-core held back fpr compatibility with mitogen 0.3.7
# - astroid is currently held back by the latest "pylint" package.
# - I don't know why pydantic_core isn't automatically updating to the latest
#   version at the moment.
scripts/check_outdated_packages.py --ignore filelock,pydantic_core,click,mypy,psutil,pydantic,resolvelib || handle_error

# Done with tools from under the python venv, so deactivate that now.
echo "Deactivate python virtualenv."
deactivate

echo "Running Django's system checks..."
docker compose -f docker-compose.local.yml exec django python manage.py check || handle_error

echo "Unit and functional tests (under docker), with coverage..."
docker compose -f docker-compose.local.yml exec django coverage run --rcfile=.coveragerc -m pytest || handle_error

echo "Coverage report (console)..."
# Run both coverage reports, even if one of them fails, before returning with an exit.
# This is so that we can have both type of output report (terminal, and HTML).
COVERAGE_ERROR=0
docker compose -f docker-compose.local.yml exec django coverage report --rcfile=.coveragerc || COVERAGE_ERROR=1

echo "Coverage report (html)..."
docker compose -f docker-compose.local.yml exec django coverage html --rcfile=.coveragerc || COVERAGE_ERROR=1

# Stop now if there was an error (eg, not enough coverage %) returned by one of the
# coverage report runs
if [ "$COVERAGE_ERROR" != "0" ]; then
    handle_error
fi

STAGING_FQDN=mmm-staging3.ar-ciel.org

# Only deploy to Staging if there are no errors:
if [ $NUM_ERRORS -eq 0 ]; then
    echo "There were no previous errors. Deploying to Staging...."
    scripts/deploy_to_staging.sh || handle_error

    echo "Setting up basic testing data on Staging..."
    ssh root@$STAGING_FQDN docker-compose \
        -f /opt/docker/docker-compose.staging.yml run \
        --rm django \
        python manage.py setup_manual_dev_testing_data || handle_error

    echo "Running headless functional tests against Staging..."
    scripts/functional_tests_against_staging_environment.sh || handle_error
else
    echo "There were errors earlier. Not deploying to Staging"
fi

# Different output at the end depending on if there were errors or not in the logic above.
if [ $NUM_ERRORS -eq 0 ]; then
    # No errors
    echo "Done with all_tests.sh - SUCCESS"

    # And in the case of success, also make some further suggestions:
    echo
    echo "Now that all of my checks look good, you should also manually run these checks in PyCharm:

    1. \`Code\` > \`Analyse Code\` > \`Locate Duplicates\`
    2. \`Code\` > \`Inspect Code\`
"

    echo "After you have done that, and everything looks good, then consider making a git commit."
    echo
else
    # There were errors.
    echo "Done with all_tests.sh - FAILURE. Check the logs above for details."
    exit 1
fi
