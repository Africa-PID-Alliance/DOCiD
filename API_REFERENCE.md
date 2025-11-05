# DOCiD API Reference

**Quick Navigation:** This document maps ALL Flask API endpoints to avoid endless searching.

## Blueprint Registration Summary

All blueprints are registered in [backend/app/__init__.py](backend/app/__init__.py#L79-L116)

| Blueprint | URL Prefix | File | Purpose |
|-----------|-----------|------|---------|
| `auth_bp` | `/api/v1/auth` | [auth.py](backend/app/routes/auth.py) | Authentication & JWT tokens |
| `datacite_bp` | `/api/v1/datacite` | [datacite.py](backend/app/routes/datacite.py) | DataCite DOI services |
| `docid_bp` | `/api/v1/docid` | [docid.py](backend/app/routes/docid.py) | DOCiD identifier operations |
| `crossref_bp` | `/api/v1/crossref` | [crossref.py](backend/app/routes/crossref.py) | Crossref metadata services |
| `ror_bp` | `/api/v1/ror` | [ror.py](backend/app/routes/ror.py) | ROR organization lookup |
| `raid_bp` | `/api/v1/raid` | [raid.py](backend/app/routes/raid.py) | RAiD identifier services |
| `orcid_bp` | `/api/v1/orcid` | [orcid.py](backend/app/routes/orcid.py) | ORCID researcher lookup |
| `cordoi_bp` | `/api/v1/cordoi` | [cordoi.py](backend/app/routes/cordoi.py) | CORDRA DOI services |
| `publications_bp` | `/api/v1/publications` | [publications.py](backend/app/routes/publications.py) | Publications CRUD |
| `arks_bp` | `/api/v1/arks` | [arks.py](backend/app/routes/arks.py) | ARK identifier services |
| `cstr_bp` | `/api/v1/cstr` | [cstr.py](backend/app/routes/cstr.py) | CSTR identifier integration |
| `smtp_bp` | `/api/v1/smtp` | [smtp.py](backend/app/routes/smtp.py) | Email services |
| `uploads_bp` | `/uploads` | [uploads.py](backend/app/routes/uploads.py) | Static file serving |
| `doi_bp` | `/doi` | [doi.py](backend/app/routes/doi.py) | DOI resolution |
| `localcontexts_bp` | `/api/v1/localcontexts` | [localcontexts.py](backend/app/routes/localcontexts.py) | Local Contexts integration |
| `docs_bp` | `/docs` | [docs.py](backend/app/routes/docs.py) | Documentation endpoints |
| `comments_bp` | *(no prefix)* | [comments.py](backend/app/routes/comments.py) | **Comments API - REFERENCE PATTERN** |
| `user_profile_bp` | `/api/v1/user-profile` | [user_profile.py](backend/app/routes/user_profile.py) | User profile management |

---

## 🎯 REFERENCE PATTERN: Comments API

**File:** [backend/app/routes/comments.py](backend/app/routes/comments.py)

The comments API is our **GOLD STANDARD** for implementing new features. Use it as a template.

### Endpoints

| Method | Endpoint | Purpose | Code Location |
|--------|----------|---------|---------------|
| `GET` | `/api/publications/<id>/comments` | Fetch all comments | Line ~25 |
| `POST` | `/api/publications/<id>/comments` | Create new comment | Line ~80 |
| `PUT` | `/api/comments/<id>` | Edit comment (author only) | Line ~150 |
| `DELETE` | `/api/comments/<id>` | Delete comment (soft delete) | Line ~200 |
| `POST` | `/api/comments/<id>/like` | Toggle like on comment | Line ~250 |
| `POST` | `/api/comments/<id>/reply` | Reply to comment | Line ~300 |
| `GET` | `/api/comments/stats/<id>` | Get comment statistics | Line ~350 |

### Key Patterns from Comments API

```python
# 1. Blueprint structure
comments_bp = Blueprint('comments', __name__)

# 2. CORS enabled
@comments_bp.route('/api/publications/<int:publication_id>/comments', methods=['GET'])
@cross_origin()
def get_comments(publication_id):
    pass

# 3. Error handling
try:
    # Operation
    db.session.commit()
    return jsonify({"status": "success"}), 201
except Exception as e:
    db.session.rollback()
    current_app.logger.error(f"Error: {str(e)}")
    return jsonify({"status": "error", "message": str(e)}), 500

# 4. Using model class methods
comments = PublicationComments.get_publication_comments(publication_id)
```

---

## 📚 Publications API

**File:** [backend/app/routes/publications.py](backend/app/routes/publications.py)

Core CRUD operations for publications (the main entity in DOCiD).

### Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `GET` | `/api/v1/publications` | List all publications | No |
| `GET` | `/api/v1/publications/<id>` | Get single publication | No |
| `POST` | `/api/v1/publications` | Create publication | Yes (JWT) |
| `PUT` | `/api/v1/publications/<id>` | Update publication | Yes (JWT) |
| `DELETE` | `/api/v1/publications/<id>` | Delete publication | Yes (JWT) |
| `GET` | `/api/v1/publications/user/<user_id>` | Get user's publications | No |
| `GET` | `/api/v1/publications/drafts` | Get draft publications | Yes (JWT) |
| `POST` | `/api/v1/publications/<id>/publish` | Publish draft | Yes (JWT) |

**Related Models:**
- [Publications](backend/app/models.py) (main table)
- [PublicationFiles](backend/app/models.py) (file attachments)
- [PublicationDocuments](backend/app/models.py) (documents)
- [PublicationCreators](backend/app/models.py) (authors)
- [PublicationOrganization](backend/app/models.py) (affiliations)

---

## 🔐 Authentication API

**File:** [backend/app/routes/auth.py](backend/app/routes/auth.py)

JWT-based authentication with social auth support (Google, ORCID, GitHub).

### Endpoints

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| `POST` | `/api/v1/auth/login` | Login with credentials | Access + Refresh tokens |
| `POST` | `/api/v1/auth/register` | Register new user | User account |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | New access token |
| `POST` | `/api/v1/auth/google` | Google OAuth login | Access + Refresh tokens |
| `POST` | `/api/v1/auth/orcid` | ORCID OAuth login | Access + Refresh tokens |
| `POST` | `/api/v1/auth/github` | GitHub OAuth login | Access + Refresh tokens |
| `POST` | `/api/v1/auth/logout` | Logout (invalidate token) | Success message |
| `GET` | `/api/v1/auth/verify` | Verify JWT token | User info |

**Token Configuration:** [backend/app/__init__.py](backend/app/__init__.py#L49-L52)
- Access token: 24 hours (86400 seconds)
- Refresh token: 30 days (2592000 seconds)

---

## 👤 User Profile API

**File:** [backend/app/routes/user_profile.py](backend/app/routes/user_profile.py)

User profile management and statistics.

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/user-profile/<user_id>` | Get user profile |
| `PUT` | `/api/v1/user-profile/<user_id>` | Update profile |
| `GET` | `/api/v1/user-profile/<user_id>/publications` | User's publications list |
| `GET` | `/api/v1/user-profile/<user_id>/stats` | User statistics |

---

## 📤 Uploads & File Serving

**File:** [backend/app/routes/uploads.py](backend/app/routes/uploads.py)

Static file serving for uploaded documents and files.

### Endpoints

| Method | Endpoint | Purpose | Notes |
|--------|----------|---------|-------|
| `GET` | `/uploads/<path:filename>` | Serve uploaded file | Direct file download |

**Configuration:**
- Upload directory: `backend/uploads/`
- Files stored in subdirectories by type
- Served via Flask's `send_from_directory()`

**Related Models:**
- `PublicationFiles.file_url` → Points to uploads directory
- `PublicationDocuments.file_url` → Points to uploads directory

---

## 🔍 External Service Integration APIs

### ROR (Research Organization Registry)

**File:** [backend/app/routes/ror.py](backend/app/routes/ror.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/ror/search?query=<name>` | Search organizations |
| `GET` | `/api/v1/ror/<ror_id>` | Get organization by ROR ID |

### ORCID

**File:** [backend/app/routes/orcid.py](backend/app/routes/orcid.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/orcid/search?query=<name>` | Search researchers |
| `GET` | `/api/v1/orcid/<orcid_id>` | Get researcher profile |

### Crossref

**File:** [backend/app/routes/crossref.py](backend/app/routes/crossref.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/crossref/register` | Register DOI with Crossref |
| `GET` | `/api/v1/crossref/metadata/<doi>` | Get DOI metadata |

### Local Contexts

**File:** [backend/app/routes/localcontexts.py](backend/app/routes/localcontexts.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/localcontexts/projects` | List LC projects |
| `GET` | `/api/v1/localcontexts/labels` | Get TK/BC labels |

---

## 🔑 Identifier Resolution

### DOI Resolution

**File:** [backend/app/routes/doi.py](backend/app/routes/doi.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/doi/<doi_suffix>` | Resolve DOI (redirect) |

### DOCiD Operations

**File:** [backend/app/routes/docid.py](backend/app/routes/docid.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/docid/generate` | Generate new DOCiD |
| `GET` | `/api/v1/docid/<docid>` | Resolve DOCiD |

**Root-level DOCiD route:** [backend/app/routes/docid_root.py](backend/app/routes/docid_root.py)
- `GET /docid/<docid>` → Frontend redirection

---

## 📊 API Documentation

**Swagger UI:** Available at `/apidocs/` when server is running

**Configuration:** [backend/app/__init__.py](backend/app/__init__.py#L30-L41)

---

## 🚀 Adding New Endpoints - Quick Checklist

When adding a new feature (like view/download counters):

1. **Create Blueprint** (e.g., `analytics.py`)
   ```python
   analytics_bp = Blueprint('analytics', __name__)
   ```

2. **Define Routes** (mirror comments.py pattern)
   ```python
   @analytics_bp.route('/api/publications/<int:id>/views', methods=['POST'])
   @cross_origin()
   def track_view(id):
       # Implementation
   ```

3. **Register Blueprint** in [backend/app/__init__.py](backend/app/__init__.py)
   ```python
   from app.routes.analytics import analytics_bp
   app.register_blueprint(analytics_bp)
   ```

4. **Create Database Model** in [backend/app/models.py](backend/app/models.py)

5. **Run Migration**
   ```bash
   python run.py db migrate -m "Add analytics tables"
   python run.py db upgrade
   ```

6. **Test Endpoints**
   ```bash
   python test_analytics_api.py
   ```

---

## ⚡ Performance & Caching

- **Flask-Caching** enabled: 5-minute timeout for reference data
- **Connection Pooling** via SQLAlchemy
- **CORS** configured for `localhost:3000` and production

---

## 📝 Common Error Responses

All endpoints follow this error format:

```json
{
  "status": "error",
  "message": "Detailed error message"
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad request / validation error
- `401` - Unauthorized
- `404` - Not found
- `500` - Server error
