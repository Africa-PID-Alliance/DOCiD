# CLAUDE.md - Frontend

This file provides guidance to Claude Code when working with the DOCiD frontend.

## 📚 DOCUMENTATION FIRST - READ BEFORE CODING

**CRITICAL:** Before working on any feature, READ these documentation files:

1. **[FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)** - Complete Next.js structure and patterns
2. **[API_REFERENCE.md](../API_REFERENCE.md)** - Backend API endpoints to integrate
3. **[DEVELOPMENT_PATTERNS.md](../DEVELOPMENT_PATTERNS.md)** - Step-by-step implementation guides

---

## Project Overview

Next.js 14+ frontend for DOCiD platform with Material-UI components and Redux state management.

## Quick Reference

### 🎯 REFERENCE PATTERNS

**When adding new features, ALWAYS use these as templates:**

1. **Comments API Proxy** - [src/app/api/publications/[id]/comments/route.js](src/app/api/publications/[id]/comments/route.js)
   - Perfect pattern for Flask API proxy
   - Shows GET and POST handlers
   - Error handling

2. **DOCiD Detail Page** - [src/app/docid/[id]/page.jsx](src/app/docid/[id]/page.jsx)
   - Complex page with multiple API calls
   - State management with hooks
   - Comments integration
   - **⭐ Add view/download counters here**

3. **Assign DOCiD Form** - [src/app/assign-docid/](src/app/assign-docid/)
   - Multi-step form pattern
   - File uploads
   - Form validation

### Technology Stack

- **Framework:** Next.js 14+ (App Router)
- **UI Library:** Material-UI (MUI)
- **State:** Redux + Redux Persist
- **HTTP:** Axios
- **Styling:** MUI sx prop, theme

### Development Commands

```bash
# Install dependencies
npm install

# Run dev server (http://localhost:3000)
npm run dev

# Build production
npm run build

# Start production
npm start
```

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api/v1
```

### Key Files

| File | Purpose |
|------|---------|
| [src/app/layout.jsx](src/app/layout.jsx) | Root layout |
| [src/app/providers.jsx](src/app/providers.jsx) | Redux + Theme providers |
| [src/store/store.js](src/store/store.js) | Redux store config |
| [src/store/slices/userSlice.js](src/store/slices/userSlice.js) | User state |

### User Requirements (from ~/.claude/CLAUDE.md)

- **Declarative variable names** - Always use clear, descriptive names
- **AJAX for interactions** - Use AJAX for buttons, filtering, searching (NOT page reloads)
  - Exception: PDF/Excel reports may use iframe or new window/tab

### Adding New Features

See [DEVELOPMENT_PATTERNS.md](../DEVELOPMENT_PATTERNS.md) for step-by-step guides.

Quick checklist:
1. Create Flask API endpoint (backend)
2. Create Next.js API proxy (frontend/src/app/api/)
3. Update page component to call API
4. Test in browser

### API Proxy Pattern

**ALWAYS** create Next.js API routes to proxy Flask backend:

```javascript
// frontend/src/app/api/your-endpoint/route.js
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function GET(request) {
  const response = await fetch(`${API_BASE_URL}/your-endpoint`);
  const data = await response.json();
  return NextResponse.json(data);
}
```

### Common Patterns

**Fetch data on mount:**
```javascript
useEffect(() => {
  const fetchData = async () => {
    const response = await axios.get('/api/endpoint');
    setData(response.data);
  };
  fetchData();
}, []);
```

**Submit form with AJAX:**
```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  const response = await axios.post('/api/endpoint', formData);
  // Handle response
};
```

**Access Redux state:**
```javascript
const { userInfo, isAuthenticated } = useSelector((state) => state.user);
```

---

**For complete documentation, see [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)**
