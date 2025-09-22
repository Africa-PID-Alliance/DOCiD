# DOCiD Frontend Analysis

## Overview
The frontend is a Next.js 15.2.2 application with React 18, Material-UI, and Redux for state management. It includes internationalization support and OAuth integration.

## Tech Stack
- **Framework**: Next.js 15.2.2 with Turbopack
- **UI Library**: Material-UI v6
- **State Management**: Redux Toolkit with Redux Persist
- **Editor**: TipTap (rich text editor)
- **HTTP Client**: Axios
- **i18n**: next-i18next with support for 6 languages (ar, de, en, fr, pt, sw)
- **Authentication**: OAuth support for ORCID, Google, GitHub

## Key Components

### 1. Assign DOCiD Module (`/src/app/assign-docid/`)
Main workflow for creating publications with DOCiD identifiers.

#### Components:
- **DocIDForm.jsx**: Main form for document metadata
- **CreatorsForm.jsx**: Handles creator/author information with ORCID integration
- **FundersForm.jsx**: Manages funder information with ROR ID integration
- **OrganizationsForm.jsx**: Organization affiliations
- **ProjectForm.jsx**: Project associations with RAiD support
- **PublicationsForm.jsx**: Publication files and metadata
- **DocumentsForm.jsx**: Supporting documents

#### Current Identifier Support:

**✅ Creators (Working)**
- Collects ORCID IDs via `creator.orcidId`
- Sends to backend as `creators[index][orcid]`
- Backend correctly formats as `https://orcid.org/{id}`

**❌ Funders (Needs Fix)**
- Collects ROR IDs via `funder.rorId`
- **NOT sending to backend** - Missing in submission code
- Backend ready to receive as `funders[index][ror]`

### 2. Data Flow

#### Form State Structure:
```javascript
formData = {
  docId: {
    title: '',
    resourceType: '',
    description: '',
    generatedId: ''
  },
  creators: {
    creators: [{
      givenName: '',
      familyName: '',
      orcidId: '',        // ORCID collected here
      identifier_type: 'orcid',
      role: ''
    }]
  },
  funders: {
    funders: [{
      name: '',
      otherName: '',
      type: '',
      country: '',
      rorId: ''           // ROR ID collected but not sent
    }]
  },
  // ... other sections
}
```

### 3. API Integration
- Base URL: Configurable via `NEXT_PUBLIC_API_BASE_URL`
- Default: `https://docid.africapidalliance.org/api/v1`
- Endpoints used:
  - `/ror/get-ror-by-id/{id}` - Fetch ROR details
  - `/ror/search-organization` - Search ROR database
  - `/orcid/get-orcid-by-id/{id}` - Fetch ORCID details
  - `/publications/publish` - Main submission endpoint

### 4. Required Frontend Fix

**File**: `/src/app/assign-docid/page.jsx`
**Line**: ~335-340

**Current Code:**
```javascript
formData.funders.funders.forEach((funder, index) => {
  submitData.append(`funders[${index}][name]`, funder.name);
  submitData.append(`funders[${index}][other_name]`, funder.otherName);
  submitData.append(`funders[${index}][type]`, 1);
  submitData.append(`funders[${index}][country]`, funder.country);
});
```

**Fixed Code:**
```javascript
formData.funders.funders.forEach((funder, index) => {
  submitData.append(`funders[${index}][name]`, funder.name);
  submitData.append(`funders[${index}][other_name]`, funder.otherName);
  submitData.append(`funders[${index}][type]`, 1);
  submitData.append(`funders[${index}][country]`, funder.country);
  
  // Add ROR ID if available
  if (funder.rorId) {
    submitData.append(`funders[${index}][ror]`, funder.rorId);
  }
});
```

### 5. Authentication Flow
- OAuth providers: ORCID, Google, GitHub
- Callback URLs: `/callback/{provider}/`
- Token management via Redux authSlice
- User session persisted with redux-persist

### 6. Internationalization
Supported languages:
- Arabic (ar)
- German (de)
- English (en) - default
- French (fr)
- Portuguese (pt)
- Swahili (sw)

Translation files in `/public/locales/{lang}/common.json`

### 7. Deployment
- PM2 configuration available (`ecosystem.config.js`)
- Scripts: `run.sh`, `restart-dev.sh`
- Build command: `npm run build`
- Start command: `npm start`

## Backend Integration Status

### ✅ Working:
1. **Publication creation** - Basic metadata submission
2. **File uploads** - Publications and documents
3. **Creator ORCID** - Properly sent and stored as resolvable URLs
4. **Organizations** - Name, type, country
5. **Projects** - Title, RAiD ID, description

### ⚠️ Needs Frontend Update:
1. **Funder ROR IDs** - Collected but not sent to backend
2. **Organization identifiers** - No ROR support for organizations yet

### Backend Ready Features:
1. **Funder identifiers** - Can receive and process ROR, FundRef, ISNI
2. **Creator identifiers** - Processes ORCID, ISNI, VIAF
3. **Resolvable URLs** - Automatically formats identifiers as URLs

## Recommendations

### Immediate Actions:
1. **Fix funder ROR submission** - Add the missing append statement
2. **Test the fix** - Verify ROR IDs are saved in database

### Future Enhancements:
1. **Add ROR for organizations** - Similar to funders
2. **Support more identifier types** - ISNI, VIAF for creators
3. **Display identifiers** - Show resolvable URLs in UI
4. **Validation** - Verify identifier formats before submission

## Testing the Fix

After updating the frontend:

1. **Add a funder with ROR**:
   - Use ROR ID: `01bj3aw27` (Gates Foundation)
   - Submit the form

2. **Check backend logs**:
   ```bash
   tail -f /backend/logs/publications.log | grep -i ror
   ```

3. **Verify database**:
   ```sql
   SELECT name, identifier, identifier_type 
   FROM publication_funders 
   WHERE identifier IS NOT NULL;
   ```

Expected result:
```
Bill & Melinda Gates Foundation | https://ror.org/01bj3aw27 | ror
```