# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Manie's Maintenance Manager** is a Django web application for coordinating maintenance jobs between Manie (a maintenance contractor) and commercial property management clients (agents). The system tracks the complete job lifecycle from initial request through completion and payment.

## Architecture

### Core Django Apps
- **`jobs/`** - Primary job management functionality with status-driven workflow
- **`users/`** - Extended user management with role-based permissions (`is_agent`, `is_manie`)
- **`contrib/sites/`** - Django sites framework customization

### Key Architectural Patterns
- **Status-driven workflow**: Jobs progress through defined states (PENDING_INSPECTION → INSPECTION_COMPLETED → QUOTE_UPLOADED → etc.)
- **Role-based access control**: Three user types (Admin, Manie, Agents) with different permissions
- **Secure file handling**: Uses `django-private-storage` for PDFs/images with permission-based access
- **Auto-incrementing job numbers**: Per-agent job numbering system

### Technology Stack
- Django 5.0.8 with PostgreSQL (SQLite for unit tests)
- `django-allauth` for authentication
- `django-private-storage` for secure file uploads
- Bootstrap 5 + `django-crispy-forms` for UI
- Docker containerization for all environments

## Development Commands

### Environment Setup
```bash
# Setup Python version and virtual environment
scripts/setup_venv_dir.sh

# Build and start all Docker containers
scripts/build_and_start_containers.sh

# Populate database with test data
scripts/setup_manual_testing_data_in_db.sh
```

### Testing Commands
```bash
# Fast unit tests (SQLite, outside Docker, with parallelization)
scripts/unit_tests.sh

# Selenium functional tests (requires Docker containers running)
scripts/functional_tests.sh

# Complete test suite + linting + staging deployment
scripts/all_tests.sh
```

### Django Management
```bash
# Standard Django commands (inside Docker)
docker compose -f docker-compose.local.yml exec django python manage.py <command>

# Create migrations
scripts/makemigrations.sh

# Access shell
docker compose -f docker-compose.local.yml exec django python manage.py shell
```

### Quality Assurance
```bash
# Type checking
mypy manies_maintenance_manager

# Linting and formatting
ruff check . --fix
black --line-length 88 .

# Security scanning
safety check --ignore 70612
```

## Testing Architecture

### Unit Tests
- Run outside Docker using SQLite in-memory database for speed
- Parallel execution with `pytest-xdist` when no recent failures
- Located in `*/tests/` directories within each app
- Use factory-boy for test data generation

### Functional Tests
- Selenium WebDriver tests running against Chrome in Docker
- VNC access available on port 5900 (password: 'secret') for debugging
- Located in `manies_maintenance_manager/functional_tests/`
- Automatically save screenshots on failures

### CI/CD Workflow
- `scripts/all_tests.sh` runs complete validation pipeline
- Automatically deploys to staging environment on success
- Includes unit tests, functional tests, linting, security checks, and type checking

## Configuration

### Settings Structure
- `config/settings/base.py` - Common settings
- `config/settings/local.py` - Development environment
- `config/settings/production.py` - Production environment
- `config/settings/test.py` - Testing configuration

### Environment Variables
```bash
DATABASE_URL=sqlite://:memory:  # For fast unit tests
USE_DOCKER=no                   # When running outside containers
TEST_USER_PASSWORD=<password>   # For functional tests
```

## Development Workflow

### Typical Development Process
1. Run `scripts/unit_tests.sh` for fast feedback during development
2. Use `scripts/setup_manual_testing_data_in_db.sh` to populate test data for manual testing
3. Run `scripts/functional_tests.sh` to test browser interactions
4. Run `scripts/all_tests.sh` before committing (includes full validation + staging deployment)

### Docker Environments
- **Local**: `docker-compose.local.yml` - Django, PostgreSQL, Mailpit, Chrome
- **Staging**: `docker-compose.staging.yml` - Pre-production environment
- **Production**: `docker-compose.production.yml` - With Traefik reverse proxy

### Email Testing
- Local development uses Mailpit container
- Access email interface at `http://127.0.0.1:8025`
- All outgoing emails captured for testing

## Code Quality Standards

### Linting Configuration
- **ruff**: Primary linter with extensive rule set
- **pylint**: Additional code analysis with Django plugin
- **black**: Code formatting (88 character line length)
- **mypy**: Static type checking with Django plugin

### Pre-commit Hooks
- Automatic code formatting and linting
- Security vulnerability scanning
- Import sorting and other code quality checks

## File Upload Security

The application handles sensitive documents (quotes, invoices, payment proofs) using `django-private-storage`:
- Files stored outside web-accessible directory
- Permission-based access control
- Separate handling for different document types

## Performance Considerations

- Unit tests optimized with SQLite in-memory database
- Parallel test execution when possible
- `django-zen-queries` for query optimization
- Separate test database configuration for speed

## Deployment

### Staging Environment
- Automatically deployed after successful `scripts/all_tests.sh` run
- Uses separate staging configuration
- Functional tests run against staging after deployment

### Production Deployment
```bash
# Deploy to production (manual)
scripts/deploy_to_prod.sh
```
