# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📚 DOCUMENTATION FIRST - READ BEFORE CODING

**CRITICAL:** Before working on any feature, READ these documentation files to avoid wasting time searching:

1. **[API_REFERENCE.md](../API_REFERENCE.md)** - Complete map of all Flask API endpoints
2. **[DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md)** - All database models, relationships, and patterns
3. **[FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)** - Next.js structure, pages, and patterns
4. **[DEVELOPMENT_PATTERNS.md](../DEVELOPMENT_PATTERNS.md)** - Step-by-step guides for common tasks

**These docs eliminate the need to "find what is where" on every new feature. Use them!**

---

## Project Overview

DOCiD is a Flask-based REST API serving as a comprehensive publication and document identifier management platform. It provides persistent identifier (PID) services, metadata management, and scholarly communication tools, with extensive integration to external services including Crossref, CSTR, CORDRA, ROR, ORCID, and Local Contexts.

## Architecture

### Application Structure
- **Flask Application Factory Pattern**: Main app created in `app/__init__.py` with comprehensive extensions
- **Blueprint-based Routing**: 20+ service-specific blueprints in `app/routes/`
- **Service Layer Architecture**: External integrations in `app/service_*.py` files
- **ORM with SQLAlchemy**: Complex relational models with cascading relationships

### Key Architectural Patterns
- **Identifier Management**: Centralized handling of DOIs, DocIDs, Handles, and other PIDs
- **Hierarchical Comments**: Tree-structured commenting system with replies and status management
- **External Service Integration**: Abstracted service connectors with authentication and error handling
- **Publication Lifecycle**: Multi-step workflow from creation to identifier assignment and external registration

## Database Schema

### Core Entities
- **Publications**: Central entity with DocID/DOI assignment, cascading to files, creators, organizations, funders, projects
- **UserAccount**: Comprehensive user management with social auth (Google, ORCID, GitHub)
- **PublicationComments**: Hierarchical commenting with parent-child relationships, status tracking, and like system
- **Reference Tables**: ResourceTypes, CreatorsRoles, FunderTypes, PublicationTypes for controlled vocabularies

### Critical Relationships
- Publications → PublicationCreators (many-to-many with roles)
- Publications → PublicationOrganization (ROR ID integration)
- Publications → PublicationFunders (structured funding information)
- Publications → PublicationComments (hierarchical tree structure)

### 🎯 REFERENCE PATTERNS FOR NEW FEATURES

**When adding new features, ALWAYS use these as templates:**

1. **Comments API** ([routes/comments.py](app/routes/comments.py)) - Perfect example for:
   - Database model with relationships
   - Class methods for business logic
   - Blueprint routes with error handling
   - CRUD operations
   - Frontend API proxy pattern

2. **Publications Model** ([models.py](app/models.py)) - Shows:
   - Cascading relationships
   - Indexes on foreign keys
   - Serialization methods

**See [DEVELOPMENT_PATTERNS.md](../DEVELOPMENT_PATTERNS.md) for step-by-step implementation guides.**

## Development Commands

### Database Operations
```bash
# Database management
python manage.py create-db           # Create all tables
python manage.py seed-db             # Load reference data
python run.py db migrate -m "msg"    # Create migration
python run.py db upgrade             # Apply migrations
python run.py db downgrade           # Rollback migration

# Migration scripts
./run_migrations.sh                  # Apply all pending migrations
./init_migrations.py                 # Initialize migration environment
```

### Server Operations
```bash
# Development server (runs on port 5001)
python run.py

# Production server
gunicorn -c gunicorn.conf.py wsgi:app

# Background services
./setup_cstr_service.sh              # Configure CSTR integration
python push_to_cordra.py             # Sync to CORDRA repository
```

### Testing
```bash
# API testing
python test_comments_api.py          # Comprehensive comments API tests
python test_comments_fetch.py        # Live API endpoint testing
python diagnose_comments_error.py    # Error diagnosis

# Service testing
python test_single_cstr.py           # CSTR integration testing
```

### External Service Management
```bash
# CORDRA operations
python push_recent_to_cordra.py      # Sync recent publications
python update_and_push_to_cordra.py  # Update and sync all

# CSTR operations  
python update_all_cstr_identifiers.py # Batch update CSTR IDs
```

## Key Configuration

### Environment Variables (Required)
```bash
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/docid_db
SECRET_KEY=your_secret_key
CSTR_CLIENT_ID=cstr_client_id
CSTR_SECRET=cstr_secret
CROSSREF_API_URL=crossref_api_endpoint
CROSSREF_API_KEY=crossref_api_key
LC_API_KEY=local_contexts_api_key
```

### Service Dependencies
- **PostgreSQL**: Primary database (required for JSON fields and complex queries)
- **Redis**: Caching and rate limiting (optional but recommended)
- **External APIs**: Crossref, ROR, ORCID, Local Contexts (credentials required)

## API Architecture

### Endpoint Patterns
- **REST Conventions**: Standard HTTP methods with JSON payloads
- **Blueprint Organization**: Service-specific endpoints (`/api/v1/{service}`)
- **Authentication**: JWT-based with social auth integration
- **Documentation**: Swagger/OpenAPI via Flasgger at `/apidocs/`

### Critical API Groups
- **Publications** (`/api/v1/publications`): Core CRUD with metadata management
- **Comments** (`/api/publications/{id}/comments`): Hierarchical commenting system
- **External Services**: Crossref, ROR, ORCID integration endpoints
- **Identifiers**: DOI, DocID, Handle management and resolution

### Server Configuration
- **Default Port**: 5001 (port 5000 conflicts with macOS AirPlay)
- **CORS**: Configured for `localhost:3000` and production domain
- **Rate Limiting**: Applied to authentication and external service endpoints

## External Service Integration

### Service Connectors
- **CORDRA** (`service_codra.py`): Digital object repository with Handle generation
- **Crossref** (`service_crossref.py`): DOI metadata and registration
- **CSTR** (`service_cstr.py`): China Science and Technology Resource platform
- **Identifier Management** (`service_identifiers.py`): Unified PID processing

### Integration Patterns
- **Authentication Token Management**: Automatic token refresh and error handling
- **Batch Processing**: Background jobs for bulk operations
- **Error Handling**: Comprehensive logging and fallback mechanisms
- **Data Transformation**: Service-specific metadata formatting

## Comments System Architecture

### Data Model
- **Hierarchical Structure**: Parent-child relationships for threaded discussions
- **Status Management**: active, edited, deleted, flagged states
- **Moderation**: User vs admin permissions for editing/deletion
- **Engagement**: Like counts and reply threading

### API Endpoints
- **GET /api/publications/{id}/comments**: Retrieve with optional reply inclusion
- **POST /api/publications/{id}/comments**: Create comment or reply
- **PUT /api/comments/{id}**: Edit (author only)
- **DELETE /api/comments/{id}**: Soft delete (author or admin)
- **POST /api/comments/{id}/like**: Toggle like status

## Common Development Patterns

### Error Handling
- **Database Errors**: Rollback transactions and log details
- **External Service Failures**: Fallback mechanisms and retry logic
- **Validation Errors**: Structured JSON error responses
- **Authentication**: JWT validation with proper error messages

### Testing Approach
- **Unit Tests**: Model validation and business logic
- **Integration Tests**: External service connectors
- **API Tests**: Endpoint functionality and error cases
- **Live Testing**: Real API endpoint validation

### Migration Strategy
- **Schema Changes**: Use Alembic migrations for all database changes
- **Data Migration**: Separate scripts for data transformation
- **Production Safety**: Test migrations on staging before production
- **Rollback Plans**: Ensure all migrations are reversible

## Performance Considerations

### Database Optimization
- **Indexes**: Applied to foreign keys and frequently queried fields
- **Query Optimization**: Use SQLAlchemy ORM efficiently, avoid N+1 queries
- **Caching**: Flask-Cache for frequently accessed reference data
- **Connection Pooling**: PostgreSQL connection management

### External Service Management
- **Rate Limiting**: Respect external API limits
- **Caching**: Store external service responses when appropriate
- **Async Processing**: Background jobs for non-critical operations
- **Timeout Handling**: Proper timeout configuration for all external calls