# Individual File/Document Download Statistics Feature

**Implemented:** 2025-11-05

## Overview

This feature adds individual download tracking for each publication file and document, allowing users to see how many times each specific file/document has been downloaded.

---

## What Was Added

### Backend (Flask)

#### 1. New API Endpoints

**File:** [backend/app/routes/analytics.py](backend/app/routes/analytics.py)

**Individual File Stats:**
- `GET /api/publications/files/<file_id>/stats` - Get download count for a specific file
- `GET /api/publications/documents/<document_id>/stats` - Get download count for a specific document

**All Files in Publication:**
- `GET /api/publications/<publication_id>/files-stats` - Get download counts for ALL files and documents in a publication

**Response Format:**
```json
{
  "status": "success",
  "publication_id": 1,
  "files": [
    {
      "id": 1,
      "title": "Research Paper.pdf",
      "file_url": "/uploads/files/paper.pdf",
      "downloads": 15
    }
  ],
  "documents": [
    {
      "id": 1,
      "title": "Dataset.csv",
      "file_url": "/uploads/documents/data.csv",
      "downloads": 8
    }
  ]
}
```

---

### Frontend (Next.js)

#### 1. API Proxy

**File:** [frontend/src/app/api/publications/[id]/files-stats/route.js](frontend/src/app/api/publications/[id]/files-stats/route.js)

Proxies requests to Flask backend to avoid CORS issues.

#### 2. DOCiD Detail Page Updates

**File:** [frontend/src/app/docid/[id]/page.jsx](frontend/src/app/docid/[id]/page.jsx)

**New State:**
```javascript
const [filesStats, setFilesStats] = useState({ files: [], documents: [] });
```

**Fetch Individual Stats:**
- Automatically fetched when page loads (Lines 213-220)
- Refreshed after each download (Lines 702-709)

**Helper Function:**
```javascript
// Get download count for a specific file or document (Lines 652-661)
const getDownloadCount = (itemId, isDocument) => {
  if (isDocument) {
    const doc = filesStats.documents.find(d => d.id === itemId);
    return doc ? doc.downloads : 0;
  } else {
    const file = filesStats.files.find(f => f.id === itemId);
    return file ? file.downloads : 0;
  }
};
```

**Display in Modal:**
Each file/document in the "Publications" and "Documents" modal now shows its individual download count next to the "View File" button (Lines 1399-1421).

---

## Visual Changes

### Before:
```
Publication(s)
Number of Publication(s): 1         [VIEW 👁]
```

### After:
```
Publication(s)
Number of Publication(s): 1         [VIEW 👁]

[In Modal when clicking VIEW:]
1. Research Paper.pdf
   [View File]  [15 downloads]

2. Dataset Analysis.xlsx
   [View File]  [8 downloads]
```

Each file now displays its individual download count in a styled badge next to the download button.

---

## How It Works

### Flow:

1. **Page Load:**
   - Frontend calls `GET /api/publications/{id}/files-stats`
   - Backend queries database for all files/documents and their download counts
   - Frontend stores stats in `filesStats` state

2. **User Clicks "VIEW" on Publications/Documents:**
   - Modal opens showing list of files
   - Each file displays its download count using `getDownloadCount(item.id, isDocument)`

3. **User Downloads a File:**
   - Download is tracked via `POST /api/publications/files/{fileId}/downloads`
   - Stats are refreshed automatically
   - Download count updates in real-time

---

## Testing

### Backend Test Script

**File:** [backend/test_analytics_api.py](backend/test_analytics_api.py)

Run tests:
```bash
cd backend
python test_analytics_api.py
```

New test added:
- `test_get_all_files_stats()` - Tests the individual stats endpoint

### Manual Testing

1. Open DOCiD page: `http://localhost:3000/docid/{docid}`
2. Click "VIEW" button on "Publication(s)" or "Document(s)" section
3. You'll see download counts displayed next to each file
4. Download a file
5. Close and reopen the modal - count should have increased by 1

---

## Database Queries

The backend efficiently queries individual download counts:

```python
# For files
download_count = FileDownloads.query.filter_by(publication_file_id=file_id).count()

# For documents
download_count = FileDownloads.query.filter_by(publication_document_id=doc_id).count()
```

No schema changes were needed - the existing `file_downloads` table supports this!

---

## Benefits

1. **Per-file Analytics** - See which specific files are most popular
2. **Real-time Updates** - Download counts update immediately after each download
3. **User Engagement** - Users can see file popularity
4. **Data-driven Decisions** - Authors can see which content resonates most

---

## Future Enhancements

Possible additions:
- Download history chart (downloads over time)
- Most downloaded files widget
- Export stats to CSV/Excel
- Email alerts when files reach download milestones
- Download velocity (downloads per day/week/month)

---

## Key Files Modified

### Backend:
- [backend/app/routes/analytics.py](backend/app/routes/analytics.py) - Added 3 new endpoints

### Frontend:
- [frontend/src/app/api/publications/[id]/files-stats/route.js](frontend/src/app/api/publications/[id]/files-stats/route.js) - New API proxy
- [frontend/src/app/docid/[id]/page.jsx](frontend/src/app/docid/[id]/page.jsx) - Display stats in modal

### Testing:
- [backend/test_analytics_api.py](backend/test_analytics_api.py) - Added test for new endpoint

---

**Implementation Time:** ~45 minutes
**Status:** ✅ Complete and tested
