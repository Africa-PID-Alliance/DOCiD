# DOCiD Development Patterns

**Purpose:** Step-by-step guides for common development tasks to avoid "finding what is where" every time.

---

## Table of Contents

1. [Adding New Feature (Full Stack)](#adding-new-feature-full-stack)
2. [Adding Backend API Endpoint Only](#adding-backend-api-endpoint-only)
3. [Adding Frontend Page Only](#adding-frontend-page-only)
4. [Modifying Existing Feature](#modifying-existing-feature)
5. [Database Migrations](#database-migrations)
6. [Testing New Features](#testing-new-features)

---

## Adding New Feature (Full Stack)

### Example: View & Download Counters

**Reference Pattern:** Mirror the [Comments API](API_REFERENCE.md#-reference-pattern-comments-api)

### Step 1: Plan Database Models

**File:** [backend/app/models.py](backend/app/models.py)

Add new models at the end of the file (before the last class):

```python
class PublicationViews(db.Model):
    """Track DOCiD page views"""
    __tablename__ = 'publication_views'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    publication = db.relationship('Publications', backref=db.backref('views', lazy='dynamic'))
    user = db.relationship('UserAccount', backref=db.backref('viewed_publications', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'user_id': self.user_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }

    @classmethod
    def get_view_count(cls, publication_id):
        """Get total view count for a publication"""
        return cls.query.filter_by(publication_id=publication_id).count()

    @classmethod
    def track_view(cls, publication_id, user_id=None, ip_address=None, user_agent=None):
        """Track a new view"""
        view = cls(
            publication_id=publication_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        db.session.commit()
        return view


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

    def to_dict(self):
        return {
            'id': self.id,
            'publication_file_id': self.publication_file_id,
            'publication_document_id': self.publication_document_id,
            'user_id': self.user_id,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }

    @classmethod
    def get_download_count(cls, publication_id):
        """Get total download count for all files in a publication"""
        from sqlalchemy import or_

        file_downloads = db.session.query(cls).join(
            PublicationFiles, cls.publication_file_id == PublicationFiles.id
        ).filter(PublicationFiles.publication_id == publication_id).count()

        doc_downloads = db.session.query(cls).join(
            PublicationDocuments, cls.publication_document_id == PublicationDocuments.id
        ).filter(PublicationDocuments.publication_id == publication_id).count()

        return file_downloads + doc_downloads

    @classmethod
    def track_download(cls, file_id=None, document_id=None, user_id=None, ip_address=None):
        """Track a new download"""
        download = cls(
            publication_file_id=file_id,
            publication_document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.session.add(download)
        db.session.commit()
        return download
```

### Step 2: Create Database Migration

```bash
cd backend

# Create migration
python run.py db migrate -m "Add view and download tracking tables"

# Review the migration file in backend/migrations/versions/

# Apply migration
python run.py db upgrade
```

### Step 3: Create Flask API Routes

**File:** `backend/app/routes/analytics.py` (create new file)

```python
from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from app import db
from app.models import PublicationViews, FileDownloads, Publications, PublicationFiles, PublicationDocuments

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/publications/<int:publication_id>/views', methods=['POST'])
@cross_origin()
def track_view(publication_id):
    """
    Track a publication view
    ---
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
    """
    try:
        # Verify publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({"status": "error", "message": "Publication not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        # Track view
        view = PublicationViews.track_view(
            publication_id=publication_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return jsonify({
            "status": "success",
            "message": "View tracked",
            "view": view.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking view: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/views/count', methods=['GET'])
@cross_origin()
def get_view_count(publication_id):
    """
    Get view count for a publication
    ---
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
    """
    try:
        count = PublicationViews.get_view_count(publication_id)
        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "view_count": count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting view count: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/files/<int:file_id>/downloads', methods=['POST'])
@cross_origin()
def track_file_download(file_id):
    """
    Track a file download
    ---
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
    """
    try:
        # Verify file exists
        file = PublicationFiles.query.get(file_id)
        if not file:
            return jsonify({"status": "error", "message": "File not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr

        # Track download
        download = FileDownloads.track_download(
            file_id=file_id,
            user_id=user_id,
            ip_address=ip_address
        )

        return jsonify({
            "status": "success",
            "message": "Download tracked",
            "download": download.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking download: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/documents/<int:document_id>/downloads', methods=['POST'])
@cross_origin()
def track_document_download(document_id):
    """
    Track a document download
    ---
    parameters:
      - name: document_id
        in: path
        type: integer
        required: true
    """
    try:
        # Verify document exists
        document = PublicationDocuments.query.get(document_id)
        if not document:
            return jsonify({"status": "error", "message": "Document not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr

        # Track download
        download = FileDownloads.track_download(
            document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )

        return jsonify({
            "status": "success",
            "message": "Download tracked",
            "download": download.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking download: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/downloads/count', methods=['GET'])
@cross_origin()
def get_download_count(publication_id):
    """
    Get download count for all files in a publication
    ---
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
    """
    try:
        count = FileDownloads.get_download_count(publication_id)
        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "download_count": count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting download count: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/stats', methods=['GET'])
@cross_origin()
def get_publication_stats(publication_id):
    """
    Get comprehensive stats for a publication (views, downloads, comments)
    ---
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
    """
    try:
        from app.models import PublicationComments

        view_count = PublicationViews.get_view_count(publication_id)
        download_count = FileDownloads.get_download_count(publication_id)
        comment_count = PublicationComments.query.filter_by(
            publication_id=publication_id,
            status='active'
        ).count()

        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "stats": {
                "views": view_count,
                "downloads": download_count,
                "comments": comment_count
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting publication stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Step 4: Register Blueprint

**File:** [backend/app/__init__.py](backend/app/__init__.py)

Add import (around line 96):
```python
from app.routes.analytics import analytics_bp
```

Add registration (around line 115):
```python
app.register_blueprint(analytics_bp)
```

### Step 5: Create Frontend API Proxy

**File:** `frontend/src/app/api/publications/[id]/views/route.js` (create new file)

```javascript
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';
const ANALYTICS_API_URL = API_BASE_URL.replace('/api/v1', '/api');

export async function POST(request, { params }) {
  const { id } = (await params);
  const body = await request.json();

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error tracking view:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/views/count`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch view count' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching view count:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**File:** `frontend/src/app/api/publications/files/[fileId]/downloads/route.js` (create new file)

```javascript
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';
const ANALYTICS_API_URL = API_BASE_URL.replace('/api/v1', '/api');

export async function POST(request, { params }) {
  const { fileId } = (await params);
  const body = await request.json();

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/files/${fileId}/downloads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error tracking download:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Step 6: Update Frontend Page

**File:** [frontend/src/app/docid/[id]/page.jsx](frontend/src/app/docid/[id]/page.jsx)

Add state for stats (around line 50):
```javascript
const [stats, setStats] = useState({ views: 0, downloads: 0, comments: 0 });
```

Add useEffect to track view and fetch stats (around line 100):
```javascript
useEffect(() => {
  const trackViewAndFetchStats = async () => {
    if (!publicationId) return;

    try {
      // Track view
      await axios.post(`/api/publications/${publicationId}/views`, {
        user_id: userInfo?.user_id || null,
      });

      // Fetch stats
      const statsResponse = await axios.get(`/api/publications/${publicationId}/stats`);
      if (statsResponse.data.status === 'success') {
        setStats(statsResponse.data.stats);
      }
    } catch (error) {
      console.error('Error with analytics:', error);
    }
  };

  trackViewAndFetchStats();
}, [publicationId, userInfo]);
```

Update the view button (replace line 743):
```javascript
<Button startIcon={<VisibilityOutlined />}>{stats.views}</Button>
```

Update the download handler (around line 617):
```javascript
const handleDownloadFile = async (fileId, fileUrl) => {
  try {
    // Track download
    await axios.post(`/api/publications/files/${fileId}/downloads`, {
      user_id: userInfo?.user_id || null,
    });

    // Open file
    const fullUrl = `${API_BASE_URL}${fileUrl}`;
    window.open(fullUrl, '_blank');
  } catch (error) {
    console.error('Error downloading file:', error);
  }
};
```

### Step 7: Test the Feature

```bash
# Terminal 1: Start Flask backend
cd backend
python run.py

# Terminal 2: Start Next.js frontend
cd frontend
npm run dev

# Test:
# 1. Open http://localhost:3000/docid/<some-docid>
# 2. Verify view count increments
# 3. Download a file
# 4. Verify download count increments
```

---

## Adding Backend API Endpoint Only

### Example: Add endpoint to get user statistics

### Step 1: Add route to existing blueprint

**File:** [backend/app/routes/user_profile.py](backend/app/routes/user_profile.py)

```python
@user_profile_bp.route('/<int:user_id>/activity', methods=['GET'])
@cross_origin()
def get_user_activity(user_id):
    """Get user's recent activity"""
    try:
        from app.models import Publications, PublicationComments

        publications = Publications.query.filter_by(user_id=user_id).count()
        comments = PublicationComments.query.filter_by(user_id=user_id).count()

        return jsonify({
            "status": "success",
            "activity": {
                "publications": publications,
                "comments": comments
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Step 2: Test with curl

```bash
curl http://localhost:5001/api/v1/user-profile/1/activity
```

---

## Adding Frontend Page Only

### Example: Add "About Us" page

### Step 1: Create page file

**File:** `frontend/src/app/about-us/page.jsx` (create new)

```javascript
'use client';

import { Container, Typography } from '@mui/material';

export default function AboutUs() {
  return (
    <Container>
      <Typography variant="h2">About Us</Typography>
      <Typography>Content here...</Typography>
    </Container>
  );
}
```

### Step 2: Add navigation link

**File:** [frontend/src/app/layout.jsx](frontend/src/app/layout.jsx)

Add link in header navigation.

---

## Modifying Existing Feature

### Example: Add new field to Publications model

### Step 1: Modify model

**File:** [backend/app/models.py](backend/app/models.py)

```python
class Publications(db.Model):
    # ... existing fields ...
    keywords = db.Column(db.Text, nullable=True)  # NEW FIELD
```

### Step 2: Create migration

```bash
python run.py db migrate -m "Add keywords to publications"
python run.py db upgrade
```

### Step 3: Update API route

**File:** [backend/app/routes/publications.py](backend/app/routes/publications.py)

Update the create/update endpoints to handle the new field.

### Step 4: Update frontend form

**File:** [frontend/src/app/assign-docid/components/PublicationsForm.jsx](frontend/src/app/assign-docid/components/PublicationsForm.jsx)

Add input field for keywords.

---

## Database Migrations

### Create Migration

```bash
cd backend
python run.py db migrate -m "Description of changes"
```

### Review Migration

Check the generated file in `backend/migrations/versions/`

### Apply Migration

```bash
python run.py db upgrade
```

### Rollback Migration

```bash
python run.py db downgrade
```

### Check Migration Status

```bash
python run.py db current
python run.py db history
```

---

## Testing New Features

### Backend Testing

Create test file: `backend/test_analytics_api.py`

```python
import requests
import json

BASE_URL = "http://localhost:5001"

def test_track_view():
    url = f"{BASE_URL}/api/publications/1/views"
    response = requests.post(url, json={"user_id": 1})
    print("Track View:", response.json())
    assert response.status_code == 201

def test_get_view_count():
    url = f"{BASE_URL}/api/publications/1/views/count"
    response = requests.get(url)
    print("View Count:", response.json())
    assert response.status_code == 200

if __name__ == "__main__":
    test_track_view()
    test_get_view_count()
```

Run:
```bash
python test_analytics_api.py
```

### Frontend Testing

1. Open browser dev tools
2. Navigate to the page
3. Check Network tab for API calls
4. Verify response data

---

## Common Pitfalls & Solutions

### Pitfall 1: CORS Errors

**Problem:** API calls from frontend fail with CORS error

**Solution:** Ensure `@cross_origin()` decorator on Flask route

### Pitfall 2: 404 on API Proxy

**Problem:** Next.js API route returns 404

**Solution:** Check file structure: `app/api/path/[param]/route.js`

### Pitfall 3: Migration Fails

**Problem:** `alembic.util.exc.CommandError`

**Solution:**
```bash
# Reset migrations (WARNING: drops all data)
python run.py db downgrade base
python run.py db upgrade
```

### Pitfall 4: Redux State Not Persisting

**Problem:** User state lost on refresh

**Solution:** Check `redux-persist` configuration in `store.js`

---

## Quick Checklist: Adding New Feature

- [ ] **Step 1:** Add database model to `models.py`
- [ ] **Step 2:** Create and run migration
- [ ] **Step 3:** Create Flask route file (e.g., `routes/feature.py`)
- [ ] **Step 4:** Register blueprint in `app/__init__.py`
- [ ] **Step 5:** Create Next.js API proxy (e.g., `app/api/feature/route.js`)
- [ ] **Step 6:** Update frontend page to use new API
- [ ] **Step 7:** Test backend with curl/Postman
- [ ] **Step 8:** Test frontend in browser
- [ ] **Step 9:** Update documentation (this file!)

---

**Last Updated:** 2025-11-05
