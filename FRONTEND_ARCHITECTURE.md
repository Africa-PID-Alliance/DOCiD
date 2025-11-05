# DOCiD Frontend Architecture Reference

**Quick Navigation:** Complete map of Next.js frontend to avoid searching.

**Framework:** Next.js 14+ with App Router
**UI Library:** Material-UI (MUI)
**State Management:** Redux + Redux Persist
**HTTP Client:** Axios

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Key Pages & Routes](#key-pages--routes)
3. [API Proxy Pattern](#api-proxy-pattern)
4. [State Management](#state-management)
5. [Component Patterns](#component-patterns)
6. [Common Operations](#common-operations)
7. [Development Commands](#development-commands)

---

## Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router (pages)
│   │   ├── api/                      # API proxy routes (⭐ IMPORTANT)
│   │   │   └── publications/
│   │   │       └── [id]/
│   │   │           └── comments/
│   │   │               └── route.js  # ⭐ REFERENCE PATTERN
│   │   ├── docid/
│   │   │   └── [id]/
│   │   │       └── page.jsx          # ⭐ DOCiD detail page (views/downloads)
│   │   ├── assign-docid/
│   │   │   ├── page.jsx              # Main assignment page
│   │   │   └── components/           # Form components
│   │   ├── list-docids/
│   │   │   └── page.jsx              # Publications list
│   │   ├── my-account/
│   │   │   └── MyAccountPage.jsx     # User profile page
│   │   ├── login/
│   │   │   └── LoginPage.jsx         # Authentication page
│   │   ├── layout.jsx                # Root layout (header, footer)
│   │   └── providers.jsx             # Redux + Theme providers
│   ├── components/                   # Shared components
│   ├── store/                        # Redux store configuration
│   │   ├── store.js                  # Store setup
│   │   └── slices/
│   │       └── userSlice.js          # User state slice
│   └── utils/                        # Utility functions
├── public/                           # Static assets
└── package.json                      # Dependencies
```

---

## Key Pages & Routes

### 1. DOCiD Detail Page ⭐

**Route:** `/docid/[id]`
**File:** [frontend/src/app/docid/[id]/page.jsx](frontend/src/app/docid/[id]/page.jsx)

**Purpose:** Display single DOCiD with metadata, files, comments

**⚠️ THIS IS WHERE VIEW COUNTER GOES**

#### Key Features:
- Displays DOCiD metadata (title, authors, description)
- Shows attached files and documents for download
- Comments section with replies
- View, like, and share buttons
- **Line 743:** View counter placeholder `<Button startIcon={<VisibilityOutlined />}>0</Button>`

#### State Management:
```javascript
const [publicationData, setPublicationData] = useState(null);
const [publicationId, setPublicationId] = useState(null);
const [comments, setComments] = useState([]);
const [isLoading, setIsLoading] = useState(true);
```

#### API Calls:
```javascript
// Fetch publication data
useEffect(() => {
  const fetchPublication = async () => {
    const response = await axios.get(`/api/publications/${publicationId}`);
    setPublicationData(response.data);
  };
  fetchPublication();
}, [publicationId]);

// Fetch comments
useEffect(() => {
  const fetchComments = async () => {
    const response = await axios.get(`/api/publications/${publicationId}/comments`);
    setComments(response.data);
  };
  if (publicationId) fetchComments();
}, [publicationId]);
```

#### File Download Function (Line 617):
```javascript
const handleDownloadFile = (fileUrl) => {
  const fullUrl = `${API_BASE_URL}${fileUrl}`;
  window.open(fullUrl, '_blank');

  // ⚠️ ADD DOWNLOAD TRACKING HERE
};
```

---

### 2. Assign DOCiD Page

**Route:** `/assign-docid`
**File:** [frontend/src/app/assign-docid/page.jsx](frontend/src/app/assign-docid/page.jsx)

**Purpose:** Multi-step form for creating new publications

#### Components:
- [DocIDForm.jsx](frontend/src/app/assign-docid/components/DocIDForm.jsx) - Basic metadata
- [PublicationsForm.jsx](frontend/src/app/assign-docid/components/PublicationsForm.jsx) - Publication details
- [CreatorsForm.jsx](frontend/src/app/assign-docid/components/CreatorsForm.jsx) - Authors/contributors
- [OrganizationsForm.jsx](frontend/src/app/assign-docid/components/OrganizationsForm.jsx) - Affiliations
- [FundersForm.jsx](frontend/src/app/assign-docid/components/FundersForm.jsx) - Funding info
- [DocumentsForm.jsx](frontend/src/app/assign-docid/components/DocumentsForm.jsx) - File uploads
- [ProjectForm.jsx](frontend/src/app/assign-docid/components/ProjectForm.jsx) - Project info

#### Pattern:
- Stepper UI (Material-UI Stepper)
- Form validation
- Multi-part file uploads
- Progress tracking

---

### 3. List DOCiDs Page

**Route:** `/list-docids`
**File:** [frontend/src/app/list-docids/page.jsx](frontend/src/app/list-docids/page.jsx)

**Purpose:** Browse all publications with search and filters

#### Features:
- Pagination
- Search by title/author
- Filter by type/date
- Card grid layout

---

### 4. My Account Page

**Route:** `/my-account`
**File:** [frontend/src/app/my-account/MyAccountPage.jsx](frontend/src/app/my-account/MyAccountPage.jsx)

**Purpose:** User profile management and publications

#### Features:
- Edit profile information
- View user publications
- Statistics dashboard
- Account settings

---

### 5. Authentication Pages

**Login:** [frontend/src/app/login/LoginPage.jsx](frontend/src/app/login/LoginPage.jsx)
- Email/password login
- Social auth buttons (Google, ORCID, GitHub)

**Register:** [frontend/src/app/register/page.jsx](frontend/src/app/register/page.jsx)
- User registration form
- Email verification

**OAuth Callbacks:**
- [frontend/src/app/callback/google/page.jsx](frontend/src/app/callback/google/page.jsx)
- [frontend/src/app/callback/orcid/page.jsx](frontend/src/app/callback/orcid/page.jsx)
- [frontend/src/app/callback/github/page.jsx](frontend/src/app/callback/github/page.jsx)

---

## API Proxy Pattern ⭐

**CRITICAL:** Next.js API routes act as a proxy to the Flask backend to avoid CORS issues.

### Reference Implementation: Comments API

**File:** [frontend/src/app/api/publications/[id]/comments/route.js](frontend/src/app/api/publications/[id]/comments/route.js)

```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

// Remove /api/v1 for non-versioned endpoints (like comments)
const COMMENTS_API_URL = API_BASE_URL.replace('/api/v1', '/api');

// GET handler
export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await fetch(`${COMMENTS_API_URL}/publications/${id}/comments`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch comments' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST handler
export async function POST(request, { params }) {
  const { id } = (await params);
  const body = await request.json();

  try {
    const response = await fetch(`${COMMENTS_API_URL}/publications/${id}/comments`, {
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
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Pattern for New API Proxies

For view/download counters, create:

1. **View Counter:**
   - File: `frontend/src/app/api/publications/[id]/views/route.js`
   - Endpoint: `POST /api/publications/[id]/views`

2. **Download Counter:**
   - File: `frontend/src/app/api/publications/files/[fileId]/downloads/route.js`
   - Endpoint: `POST /api/publications/files/[fileId]/downloads`

---

## State Management

### Redux Store Setup

**File:** [frontend/src/store/store.js](frontend/src/store/store.js)

```javascript
import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import userReducer from './slices/userSlice';

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['user'], // Persist user state
};

const persistedReducer = persistReducer(persistConfig, userReducer);

export const store = configureStore({
  reducer: {
    user: persistedReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export const persistor = persistStore(store);
```

### User Slice

**File:** [frontend/src/store/slices/userSlice.js](frontend/src/store/slices/userSlice.js)

```javascript
import { createSlice } from '@reduxjs/toolkit';

const userSlice = createSlice({
  name: 'user',
  initialState: {
    userInfo: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
  },
  reducers: {
    setUser: (state, action) => {
      state.userInfo = action.payload.user;
      state.accessToken = action.payload.access_token;
      state.refreshToken = action.payload.refresh_token;
      state.isAuthenticated = true;
    },
    logout: (state) => {
      state.userInfo = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
    },
    updateTokens: (state, action) => {
      state.accessToken = action.payload.access_token;
    },
  },
});

export const { setUser, logout, updateTokens } = userSlice.actions;
export default userSlice.reducer;
```

### Using Redux in Components

```javascript
import { useSelector, useDispatch } from 'react-redux';
import { setUser, logout } from '@/store/slices/userSlice';

function MyComponent() {
  const dispatch = useDispatch();
  const { userInfo, isAuthenticated } = useSelector((state) => state.user);

  const handleLogin = (userData) => {
    dispatch(setUser(userData));
  };

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <div>
      {isAuthenticated ? (
        <p>Welcome, {userInfo.full_name}</p>
      ) : (
        <p>Please log in</p>
      )}
    </div>
  );
}
```

---

## Component Patterns

### 1. Page Component Structure

```javascript
'use client'; // Required for client-side interactivity

import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import axios from 'axios';

export default function MyPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated } = useSelector((state) => state.user);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/endpoint');
        setData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) return <CircularProgress />;

  return (
    <Container>
      {/* Content */}
    </Container>
  );
}
```

### 2. Form Component Pattern

```javascript
'use client';

import { useState } from 'react';
import { TextField, Button } from '@mui/material';
import axios from 'axios';

export default function MyForm() {
  const [formData, setFormData] = useState({
    field1: '',
    field2: '',
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post('/api/endpoint', formData);
      console.log('Success:', response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <TextField
        name="field1"
        value={formData.field1}
        onChange={handleChange}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

### 3. AJAX Pattern (Per User Instructions)

**⚠️ User Requirement:** Always use AJAX for page interactions (buttons, filtering, searching)

```javascript
// ✅ CORRECT - AJAX request
const handleFilter = async (filterValue) => {
  try {
    const response = await axios.get(`/api/publications?filter=${filterValue}`);
    setFilteredData(response.data);
  } catch (error) {
    console.error('Error:', error);
  }
};

// ❌ INCORRECT - Page reload
const handleFilter = (filterValue) => {
  window.location.href = `/publications?filter=${filterValue}`;
};
```

**Exception:** PDF/Excel reports may use iframe or new window/tab

---

## Common Operations

### 1. Track Page View (ADD THIS)

```javascript
// In DOCiD detail page useEffect
useEffect(() => {
  const trackView = async () => {
    try {
      await axios.post(`/api/publications/${publicationId}/views`, {
        // Optionally send user info, IP handled by backend
      });
    } catch (error) {
      console.error('Error tracking view:', error);
    }
  };

  if (publicationId) {
    trackView();
  }
}, [publicationId]);
```

### 2. Track File Download (ADD THIS)

```javascript
const handleDownloadFile = async (fileId, fileUrl) => {
  try {
    // Track download
    await axios.post(`/api/publications/files/${fileId}/downloads`);

    // Open file
    const fullUrl = `${API_BASE_URL}${fileUrl}`;
    window.open(fullUrl, '_blank');
  } catch (error) {
    console.error('Error tracking download:', error);
  }
};
```

### 3. Fetch and Display Comments

```javascript
const [comments, setComments] = useState([]);

useEffect(() => {
  const fetchComments = async () => {
    try {
      const response = await axios.get(`/api/publications/${publicationId}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  if (publicationId) {
    fetchComments();
  }
}, [publicationId]);
```

### 4. Post Comment

```javascript
const handlePostComment = async (commentText) => {
  try {
    const response = await axios.post(`/api/publications/${publicationId}/comments`, {
      user_id: userInfo.user_id,
      comment_text: commentText,
      comment_type: 'general',
    });

    // Refresh comments
    setComments([...comments, response.data]);
  } catch (error) {
    console.error('Error posting comment:', error);
  }
};
```

---

## Development Commands

```bash
# Install dependencies
npm install

# Run development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

---

## Environment Variables

**File:** `frontend/.env.local`

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api/v1
```

**Usage in code:**
```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';
```

---

## Material-UI (MUI) Components

Commonly used MUI components:

```javascript
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
```

**Icons:**
```javascript
import {
  VisibilityOutlined,
  ThumbUpOutlined,
  ShareOutlined,
  DownloadOutlined,
  CommentOutlined,
} from '@mui/icons-material';
```

---

## File Upload Pattern

```javascript
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    console.log('File uploaded:', response.data.file_url);
  } catch (error) {
    console.error('Upload error:', error);
  }
};
```

---

## Quick Reference: Where to Find Things

| What | File |
|------|------|
| DOCiD detail page ⭐ | [frontend/src/app/docid/[id]/page.jsx](frontend/src/app/docid/[id]/page.jsx) |
| Comments API proxy ⭐ | [frontend/src/app/api/publications/[id]/comments/route.js](frontend/src/app/api/publications/[id]/comments/route.js) |
| Redux store | [frontend/src/store/store.js](frontend/src/store/store.js) |
| User state slice | [frontend/src/store/slices/userSlice.js](frontend/src/store/slices/userSlice.js) |
| Root layout | [frontend/src/app/layout.jsx](frontend/src/app/layout.jsx) |
| Providers | [frontend/src/app/providers.jsx](frontend/src/app/providers.jsx) |
| Login page | [frontend/src/app/login/LoginPage.jsx](frontend/src/app/login/LoginPage.jsx) |
| Assign DOCiD | [frontend/src/app/assign-docid/page.jsx](frontend/src/app/assign-docid/page.jsx) |

---

**Last Updated:** 2025-11-05
**Framework:** Next.js 14+ (App Router)
