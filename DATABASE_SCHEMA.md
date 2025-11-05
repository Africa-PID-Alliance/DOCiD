# DOCiD Database Schema Reference

**Quick Navigation:** Complete map of all database models to avoid searching.

**File:** [backend/app/models.py](backend/app/models.py)

---

## Table of Contents

1. [Core Entities](#core-entities)
2. [Reference/Lookup Tables](#referencelookup-tables)
3. [Publication-Related Tables](#publication-related-tables)
4. [User Management Tables](#user-management-tables)
5. [External Service Tables](#external-service-tables)
6. [Audit & Tracking Tables](#audit--tracking-tables)
7. [Quick Relationship Map](#quick-relationship-map)
8. [Database Migration Commands](#database-migration-commands)

---

## Core Entities

### 1. Publications

**Table:** `publications`
**File Location:** [models.py:446-478](backend/app/models.py#L446-L478)

Central entity for all DOCiD publications.

```python
class Publications(db.Model):
    __tablename__ = 'publications'
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Primary key |
| `user_id` | Integer | FK → user_accounts.user_id, Indexed | Publication owner |
| `document_docid` | String(255) | NOT NULL | DOCiD identifier |
| `document_title` | String(255) | NOT NULL | Publication title |
| `doi` | String(50) | NOT NULL | DOI identifier |
| `published` | DateTime | Default: utcnow | Publication date |
| `updated_at` | DateTime | Auto-update | Last modification |

**Relationships (with cascade delete):**
- `publications_files` → PublicationFiles
- `publication_documents` → PublicationDocuments
- `publication_creators` → PublicationCreators
- `publication_organization` → PublicationOrganization
- `publication_funders` → PublicationFunders
- `publication_projects` → PublicationProjects
- `comments` → PublicationComments
- `audit_trail` → PublicationAuditTrail

**Used By:**
- Publications API: [routes/publications.py](backend/app/routes/publications.py)
- Comments API: [routes/comments.py](backend/app/routes/comments.py)

---

### 2. UserAccount

**Table:** `user_accounts`
**File Location:** [models.py:7-85](backend/app/models.py#L7-L85)

User authentication and profile data.

```python
class UserAccount(db.Model):
    __tablename__ = "user_accounts"
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | Integer | PK, Auto | Primary key |
| `social_id` | String(100) | NULL | OAuth provider ID |
| `user_name` | String(50) | NOT NULL | Username |
| `full_name` | String(100) | NOT NULL | Full name |
| `email` | String(100) | UNIQUE, NOT NULL | Email address |
| `type` | String(20) | NOT NULL | Auth type (google, orcid, github, local) |
| `avator` | String(255) | NULL | Profile image URL |
| `timestamp` | DateTime | Default: utcnow | Account creation |
| `affiliation` | String(100) | NULL | Organization affiliation |
| `role` | String(50) | NULL | User role (admin, user) |
| `first_time` | Integer | Default: 1 | First login flag |
| `orcid_id` | String(50) | NULL | ORCID identifier |
| `ror_id` | String(50) | NULL | ROR organization ID |
| `country` | String(50) | NULL | Country |
| `city` | String(50) | NULL | City |
| `linkedin_profile_link` | String(255) | NULL | LinkedIn URL |
| `facebook_profile_link` | String(255) | NULL | Facebook URL |
| `x_profile_link` | String(255) | NULL | X (Twitter) URL |
| `instagram_profile_link` | String(255) | NULL | Instagram URL |
| `github_profile_link` | String(255) | NULL | GitHub URL |
| `location` | String(100) | NULL | Custom location |
| `date_joined` | DateTime | Default: utcnow | Join date |
| `password` | String(255) | NULL | Hashed password (for local auth) |

**Relationships:**
- `publications` → Publications (cascade delete)

**Methods:**
- `validate_user_id(user_id)` - Validates and retrieves user
- `serialize()` - Returns JSON-safe dict

**Used By:**
- Auth API: [routes/auth.py](backend/app/routes/auth.py)
- User Profile API: [routes/user_profile.py](backend/app/routes/user_profile.py)

---

## Reference/Lookup Tables

These are **controlled vocabulary** tables populated by `seed-db` command.

### 3. ResourceTypes

**Table:** `resource_types`
**File Location:** [models.py:246-278](backend/app/models.py#L246-L278)

Defines types of resources (e.g., Dataset, Software, Text).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `type_general` | String(50) | General category |
| `type` | String(255) | Specific type name |

**Seed Data:** ~30 resource types from DataCite schema

---

### 4. CreatorsRoles

**Table:** `creators_roles`
**File Location:** [models.py:280-317](backend/app/models.py#L280-L317)

Contributor roles (Author, Editor, DataCurator, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `role` | String(100) | Role name |

**Seed Data:** ~20 roles from CRediT taxonomy

---

### 5. FunderTypes

**Table:** `funder_types`
**File Location:** [models.py:354-382](backend/app/models.py#L354-L382)

Types of funders (Government, Foundation, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `type` | String(100) | Funder type |

---

### 6. PublicationTypes

**Table:** `publication_types`
**File Location:** [models.py:384-412](backend/app/models.py#L384-L412)

Publication categories (Journal Article, Conference Paper, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `type` | String(100) | Publication type |

---

### 7. PublicationIdentifierTypes

**Table:** `publication_identifier_types`
**File Location:** [models.py:414-444](backend/app/models.py#L414-L444)

Identifier schemes (DOI, ARK, Handle, CSTR, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `identifier_type` | String(50) | Identifier scheme name |

---

## Publication-Related Tables

### 8. PublicationFiles

**Table:** `publications_files`
**File Location:** [models.py:480-504](backend/app/models.py#L480-L504)

File attachments for publications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `file_url` | String(255) | NOT NULL | Path to uploaded file |
| `file_size` | Integer | NULL | File size in bytes |
| `file_type` | String(50) | NULL | MIME type |
| `uploaded_at` | DateTime | Default: utcnow | Upload timestamp |

**Relationships:**
- `publication` ← Publications

**⚠️ Important for Download Counter:**
- This table stores file paths
- Track downloads per `file_id`
- File served via [routes/uploads.py](backend/app/routes/uploads.py)

---

### 9. PublicationDocuments

**Table:** `publication_documents`
**File Location:** [models.py:506-529](backend/app/models.py#L506-L529)

Document attachments (PDFs, Word docs, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `document_type` | String(50) | NULL | Document category |
| `file_url` | String(255) | NOT NULL | Path to document |
| `file_size` | Integer | NULL | File size in bytes |
| `uploaded_at` | DateTime | Default: utcnow | Upload timestamp |

**Relationships:**
- `publication` ← Publications

**⚠️ Important for Download Counter:**
- Similar to PublicationFiles
- Both tables need download tracking

---

### 10. PublicationCreators

**Table:** `publication_creators`
**File Location:** [models.py:531-549](backend/app/models.py#L531-L549)

Authors and contributors for publications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `creator_name` | String(255) | NOT NULL | Creator's name |
| `creator_role` | Integer | FK → creators_roles.id | Role (Author, Editor, etc.) |
| `orcid_id` | String(50) | NULL | ORCID identifier |
| `affiliation` | String(255) | NULL | Institution |

**Relationships:**
- `publication` ← Publications
- `role_details` ← CreatorsRoles

---

### 11. PublicationOrganization

**Table:** `publication_organization`
**File Location:** [models.py:551-570](backend/app/models.py#L551-L570)

Organization affiliations for publications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `organization_name` | String(255) | NOT NULL | Organization name |
| `ror_id` | String(100) | NULL | ROR identifier |

**Relationships:**
- `publication` ← Publications

---

### 12. PublicationFunders

**Table:** `publication_funders`
**File Location:** [models.py:572-592](backend/app/models.py#L572-L592)

Funding information for publications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `funder_name` | String(255) | NOT NULL | Funder name |
| `funder_type` | Integer | FK → funder_types.id | Funder category |
| `grant_number` | String(100) | NULL | Grant/Award number |

**Relationships:**
- `publication` ← Publications
- `type_details` ← FunderTypes

---

### 13. PublicationProjects

**Table:** `publication_projects`
**File Location:** [models.py:594-614](backend/app/models.py#L594-L614)

Projects associated with publications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Parent publication |
| `project_name` | String(255) | NOT NULL | Project name |
| `project_id` | String(100) | NULL | Project identifier |

**Relationships:**
- `publication` ← Publications

---

## User Management Tables

### 14. RegistrationTokens

**Table:** `user_registration_tokens`
**File Location:** [models.py:87-126](backend/app/models.py#L87-L126)

Email verification tokens for user registration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `email` | String(100) | NOT NULL | User email |
| `token` | String(255) | UNIQUE, NOT NULL | Verification token |
| `expires_at` | DateTime | NOT NULL | Token expiration |

---

### 15. PasswordResets

**Table:** `password_resets`
**File Location:** [models.py:128-178](backend/app/models.py#L128-L178)

Password reset tokens.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `user_id` | Integer | FK → user_accounts.user_id | User requesting reset |
| `token` | String(255) | UNIQUE, NOT NULL | Reset token |
| `created_at` | DateTime | Default: utcnow | Token creation |
| `expires_at` | DateTime | NOT NULL | Token expiration |
| `used` | Boolean | Default: False | Token used flag |

---

## External Service Tables

### 16. DocIDObject

**Table:** `docid_object`
**File Location:** [models.py:180-193](backend/app/models.py#L180-L193)

Legacy DOCiD object storage.

---

### 17. CrossrefMetadata

**Table:** `crossref_metadata`
**File Location:** [models.py:616-645](backend/app/models.py#L616-L645)

Cached Crossref metadata responses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `doi` | String(100) | UNIQUE, NOT NULL | DOI identifier |
| `metadata_json` | JSON | NOT NULL | Crossref response |
| `cached_at` | DateTime | Default: utcnow | Cache timestamp |

---

## Audit & Tracking Tables

### 18. PublicationComments ⭐

**Table:** `publication_comments`
**File Location:** [models.py:647-740](backend/app/models.py#L647-L740)

**⭐ REFERENCE PATTERN** - Use this as template for new features!

Hierarchical commenting system with likes and moderation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto | Primary key |
| `publication_id` | Integer | FK → publications.id, Indexed | Parent publication |
| `user_id` | Integer | FK → user_accounts.user_id, Indexed | Comment author |
| `parent_comment_id` | Integer | FK → self.id, NULL | Parent comment (for replies) |
| `comment_text` | Text | NOT NULL | Comment content |
| `comment_type` | Enum | 'general'/'review'/'question' | Comment category |
| `status` | Enum | 'active'/'edited'/'deleted'/'flagged' | Comment state |
| `likes_count` | Integer | Default: 0 | Number of likes |
| `created_at` | DateTime | Default: utcnow, Indexed | Creation time |
| `updated_at` | DateTime | Auto-update | Last edit time |

**Relationships:**
- `publication` ← Publications
- `user` ← UserAccount
- `parent_comment` ← PublicationComments (self-referencing)
- `replies` → PublicationComments (self-referencing)

**Class Methods:**
```python
PublicationComments.get_publication_comments(publication_id, include_replies=True)
PublicationComments.add_comment(publication_id, user_id, comment_text, comment_type='general')
```

**Instance Methods:**
```python
comment.to_dict()  # Returns JSON-safe dictionary with replies
```

**Used By:**
- Comments API: [routes/comments.py](backend/app/routes/comments.py)

---

### 19. PublicationDrafts

**Table:** `publication_drafts`
**File Location:** [models.py:742-793](backend/app/models.py#L742-L793)

Draft publications before publishing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `user_id` | Integer | FK → user_accounts.user_id | Draft owner |
| `draft_data` | JSON | NOT NULL | Serialized draft content |
| `created_at` | DateTime | Default: utcnow | Draft creation |
| `updated_at` | DateTime | Auto-update | Last modification |
| `status` | Enum | 'draft'/'submitted'/'published' | Draft state |

---

### 20. PublicationAuditTrail

**Table:** `publication_audit_trail`
**File Location:** [models.py:795-878](backend/app/models.py#L795-L878)

Tracks all changes to publications for compliance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `publication_id` | Integer | FK → publications.id | Modified publication |
| `user_id` | Integer | FK → user_accounts.user_id | User who made change |
| `action` | Enum | 'created'/'updated'/'deleted' | Action type |
| `changes` | JSON | NULL | Old vs new values |
| `timestamp` | DateTime | Default: utcnow | Action timestamp |

---

## Quick Relationship Map

### Publications (Center of Universe)

```
UserAccount (user_id)
    ↓
Publications (id) ← ────────────────┐
    ├── PublicationFiles             │
    ├── PublicationDocuments          │ All with
    ├── PublicationCreators           │ CASCADE DELETE
    ├── PublicationOrganization       │
    ├── PublicationFunders            │
    ├── PublicationProjects           │
    ├── PublicationComments ⭐        │
    └── PublicationAuditTrail ────────┘
```

### Comments (Hierarchical)

```
Publications (id)
    ↓
PublicationComments (id)
    ├── parent_comment_id → PublicationComments.id (self-referencing)
    ├── user_id → UserAccount.user_id
    └── replies → PublicationComments[] (children)
```

---

## 🎯 Pattern for New Features: View & Download Counters

Based on the **PublicationComments** pattern, here's what you need:

### New Models to Add

```python
class PublicationViews(db.Model):
    """Track DOCiD page views"""
    __tablename__ = 'publication_views'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # For deduplication
    user_agent = db.Column(db.Text, nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    publication = db.relationship('Publications', backref=db.backref('views', lazy='dynamic'))
    user = db.relationship('UserAccount', backref=db.backref('viewed_publications', lazy='dynamic'))

class FileDownloads(db.Model):
    """Track file downloads"""
    __tablename__ = 'file_downloads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_file_id = db.Column(db.Integer, db.ForeignKey('publications_files.id'), nullable=True, index=True)
    publication_document_id = db.Column(db.Integer, db.ForeignKey('publication_documents.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    publication_file = db.relationship('PublicationFiles', backref=db.backref('downloads', lazy='dynamic'))
    publication_document = db.relationship('PublicationDocuments', backref=db.backref('downloads', lazy='dynamic'))
    user = db.relationship('UserAccount', backref=db.backref('downloaded_files', lazy='dynamic'))
```

---

## Database Migration Commands

**Location:** [backend/CLAUDE.md:38-51](backend/CLAUDE.md#L38-L51)

```bash
# Create all tables (first time)
python manage.py create-db

# Load reference data (ResourceTypes, CreatorsRoles, etc.)
python manage.py seed-db

# Create migration after model changes
python run.py db migrate -m "Add view and download tracking tables"

# Apply migrations
python run.py db upgrade

# Rollback migration
python run.py db downgrade

# Apply all pending migrations
./run_migrations.sh
```

---

## Database Configuration

**Connection String:** Set in `.env`
```bash
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/docid_db
```

**Required:** PostgreSQL (for JSON field support)

**Indexes:** Applied automatically on:
- Foreign keys
- Frequently queried fields (`publication_id`, `user_id`, `created_at`)

---

## Quick Reference: Where to Find Things

| What | File | Line Range |
|------|------|------------|
| All models | [models.py](backend/app/models.py) | Full file |
| User auth model | [models.py](backend/app/models.py) | 7-85 |
| Publications model | [models.py](backend/app/models.py) | 446-478 |
| Comments model ⭐ | [models.py](backend/app/models.py) | 647-740 |
| File attachments | [models.py](backend/app/models.py) | 480-504, 506-529 |
| Reference tables | [models.py](backend/app/models.py) | 246-444 |

---

**Last Updated:** 2025-11-05
**Total Models:** 20 database models
