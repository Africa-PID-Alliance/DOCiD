# Publication Editing Implementation Plan

## Overview
Implement functionality to allow users to edit their own publications through the frontend, including:
- Adding edit icons to user's publications in the list view
- Creating an edit form page similar to assign-docid
- Adding backend API endpoints for updating publications

## Backend Implementation

### 1. New API Endpoints in `/Users/ekariz/Projects/AMBAND/DOCiD/backend/app/routes/publications.py`

#### 1.1 GET Endpoint for Edit Form Data (CREATE NEW)
- **Endpoint**: `/api/v1/publications/get-publication/{id}?user_id={user_id}`
- **Purpose**: Retrieve publication data for editing with all related data
- **Response**: Include publications, creators, organizations, funders, projects, files
- **Security**: Ensure only the publication owner can access this data
- **Authorization**: Validate user owns the publication before returning data

#### 1.2 PUT/PATCH Endpoint for Publication Updates (CREATE NEW)
- **Endpoint**: `/api/v1/publications/update-publication/{id}` or `/publish-update`
- **Method**: PUT or PATCH
- **Purpose**: Update existing publication data
- **Validation**: 
  - Verify user owns the publication
  - Validate all required fields
  - Handle file uploads if needed
  - Maintain data integrity with related tables (creators, organizations, funders, etc.)

### 2. Database Considerations
- **Audit Trail**: ✅ **REQUIRED** - Create audit trail model and table with migration
- **Updated Fields**: Add updated_at timestamp and updated_by fields to publications table
- **Related Data**: Handle updates to:
  - PublicationCreators
  - PublicationOrganization
  - PublicationFunders
  - PublicationProjects
  - File attachments

### 2.1 Audit Trail Model Design
```python
class PublicationAuditTrail(db.Model):
    __tablename__ = 'publication_audit_trail'
    
    id = db.Column(db.Integer, primary_key=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'UPDATE', 'CREATE', 'DELETE'
    field_name = db.Column(db.String(100))  # Field that was changed
    old_value = db.Column(db.Text)  # Previous value (JSON for complex objects)
    new_value = db.Column(db.Text)  # New value (JSON for complex objects)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # User's IP address
    user_agent = db.Column(db.Text)  # Browser/client information
    
    # Relationships
    publication = db.relationship('Publication', backref='audit_entries')
    user = db.relationship('UserAccount', backref='audit_actions')
```

### 2.2 Database Migration Requirements
- **New Table**: Create `publication_audit_trail` table
- **Publications Table**: Add `updated_at` and `updated_by` columns
- **Migration Script**: Use Alembic to create migration file
- **Indexes**: Add indexes on `publication_id`, `user_id`, and `timestamp` for performance

## Frontend Implementation

### 3. Modify List Publications Page (`http://localhost:3000/list-docids`)

#### 3.1 Add Edit Icon/Button
- **Location**: Each publication row/card where user is the owner
- **Condition**: Only show for publications belonging to the current user
- **Action**: Navigate to `/edit-docid/{id}` route

#### 3.2 User Ownership Check
- **Implementation**: Compare current user ID with publication owner
- **Data Source**: Ensure publication list API returns owner information

### 4. Create Edit Publication Page

#### 4.1 New Route: `/edit-docid/[id]`
- **File**: Create new Next.js page component
- **Base Template**: Clone from `/assign-docid` page
- **Modifications**:
  - Pre-populate form fields with existing publication data
  - Change form title to "Edit Publication"
  - Update submit button text to "Update Publication"
  - Handle different form states (loading, error, success)

#### 4.2 Form Components
- **Reuse Existing**: Leverage existing form components from assign-docid
- **Data Fetching**: Call the GET endpoint to populate initial values
- **Form Validation**: Apply same validation rules as creation form
- **Submit Handler**: Call the update API endpoint instead of create

### 5. API Integration

#### 5.1 Frontend API Calls
- **Get Publication**: Fetch publication data for editing
- **Update Publication**: Submit updated publication data
- **Error Handling**: Handle validation errors, permission errors, network errors
- **Success Handling**: Redirect to publication view or list after successful update

## Environment Configuration

### 6. Environment Variables

#### Backend (.env)
```bash
# API Base Configuration
API_BASE_URL=http://127.0.0.1:5001
API_VERSION=v1

# Frontend URLs (for CORS and redirects)
FRONTEND_BASE_URL=http://localhost:3000
```

#### Frontend (.env.local or .env)
```bash
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:5001
NEXT_PUBLIC_API_VERSION=v1

# Frontend Base URL
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

### 7. API URL Construction

#### Backend
- Use `os.environ.get('API_BASE_URL')` for internal API references
- Construct URLs dynamically: `f"{API_BASE_URL}/api/{API_VERSION}/publications"`

#### Frontend
- Use `process.env.NEXT_PUBLIC_API_BASE_URL` for API calls
- Construct URLs: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/${process.env.NEXT_PUBLIC_API_VERSION}/publications`

## Technical Specifications

### 8. Files to Create/Modify

#### Backend Files
- **Modify**: `/Users/ekariz/Projects/AMBAND/DOCiD/backend/app/routes/publications.py`
  - Add update endpoint
  - Add proper authorization checks  
  - Handle partial updates
  - Implement audit trail logging
- **Modify**: `/Users/ekariz/Projects/AMBAND/DOCiD/backend/app/models.py`
  - Add PublicationAuditTrail model
  - Add updated_at and updated_by fields to Publications model
- **Create**: Database migration file using Alembic
  - `python run.py db migrate -m "Add publication audit trail and updated fields"`
  - `python run.py db upgrade`

#### Frontend Files (Need to identify exact paths)
- **Create**: Edit publication page (`/edit-docid/[id].js` or similar)
- **Modify**: List publications component (add edit icon)
- **Modify**: API service files (add update publication function)
- **Modify**: Navigation/routing configuration
- **Create/Modify**: Environment configuration file (`.env.local` or `.env`)
- **Modify**: API utility functions to use environment variables

#### Configuration Files
- **Backend**: Update `.env` file with API and frontend URL variables
- **Frontend**: Create/update `.env.local` with backend API configuration
- **Both**: Ensure no hardcoded URLs remain in codebase

### 7. Notification System
- **Success Notifications**: Show success message after successful publication update
- **Error Notifications**: Display error messages for validation failures or server errors
- **Toast Notifications**: Use Material-UI Snackbar/Toast for user feedback
- **Modal Confirmations**: Confirm before significant changes (like file deletions)

### 8. Workflow State Management
- **Editable States**: Allow editing for `draft` and `published` publications
- **Restricted States**: Block editing for `archived`, `rejected`, `deleted` publications
- **Frontend**: Show edit icon only for publications in editable states
- **Backend**: Validate publication state before allowing updates
- **Status Transitions**: Track state changes in audit trail

### 9. Security Considerations
- **Authorization**: ✅ **CONFIRMED** - Only publication owners can edit their own publications (no admin override)
- **User Ownership Check**: Compare `user_id` from JWT token with publication owner
- **State Validation**: Verify publication is in editable state before allowing changes
- **Input Validation**: Validate all form inputs on both frontend and backend
- **CSRF Protection**: Ensure proper CSRF token handling
- **File Upload Security**: Validate file types, sizes, and scan for malicious content

### 9. User Experience Flow
1. User visits `${NEXT_PUBLIC_BASE_URL}/list-docids`
2. User sees edit icon on their publications
3. User clicks edit icon → navigates to `${NEXT_PUBLIC_BASE_URL}/edit-docid/{id}`
4. System fetches publication data from `${NEXT_PUBLIC_API_BASE_URL}/api/${NEXT_PUBLIC_API_VERSION}/publications/get-publication/{id}`
5. Form pre-populates with existing data
6. User modifies desired fields
7. User submits form to `${NEXT_PUBLIC_API_BASE_URL}/api/${NEXT_PUBLIC_API_VERSION}/publications/update-publication/{id}`
8. System validates and updates publication
9. User receives confirmation and/or redirects to updated publication

### 10. Implementation Best Practices
- **No Hardcoded URLs**: All URLs must be constructed from environment variables
- **Environment Variable Validation**: Check for required environment variables on app startup
- **Fallback Values**: Consider default values for development environments
- **Documentation**: Update README with required environment variables

## Questions for Clarification

1. **Frontend Framework**: ✅ **ANSWERED** - Next.js 15.2.2 with App Router, Material-UI components, React 18.2.0, Redux Toolkit for state management
2. **Existing API**: ✅ **ANSWERED** - No API exists, create it
3. **File Editing**: ✅ **ANSWERED** - YES, users should be able to upload new files or modify existing file attachments  
4. **Field Restrictions**: ✅ **ANSWERED** - Allow editing all fields for now
5. **Permissions**: ✅ **ANSWERED** - Only user will be required to edit their publication as of now
6. **Workflow State**: ✅ **ANSWERED** - Use common patterns: Allow editing drafts and published publications, restrict editing for archived/rejected states
7. **Notification**: ✅ **ANSWERED** - Notify user when publication is edited
8. **Audit Trail**: ✅ **ANSWERED** - Add an audit trail model and table and migrate it

## Frontend Framework Analysis

Based on examination of `/Users/ekariz/Projects/AMBAND/DOCiD/frontendv2/docid07aug25/`:

### Framework Details
- **Framework**: Next.js 15.2.2 with App Router structure
- **UI Library**: Material-UI (@mui/material v6.4.7)
- **State Management**: Redux Toolkit (@reduxjs/toolkit v2.7.0) with Redux Persist
- **HTTP Client**: Axios for API calls
- **Rich Text Editor**: TipTap for content editing

### Key Frontend Files Structure
- **List Page**: `/src/app/list-docids/page.jsx` - Main publications listing page
- **Assign Page**: `/src/app/assign-docid/page.jsx` - Multi-step form for creating publications
- **API Routes**: `/src/app/api/publications/` - Frontend API route handlers
- **Components**: `/src/app/assign-docid/components/` - Reusable form components
- **Utils**: `/src/utils/docidUtils.js` - URL and utility functions

### Current User Authentication
- Uses Redux state: `const { user, isAuthenticated } = useSelector((state) => state.auth)`
- User object contains: `user.id`, `user.name`, etc.
- Authentication check redirects to `/login` if not authenticated

### Current Publication Ownership Check
The list page shows all publications but needs modification to:
1. Compare `user.id` with publication owner
2. Show edit icon only for owned publications
3. Route to `/edit-docid/{id}` when clicked

## Next Steps
1. Clarify any unclear requirements
2. Examine existing codebase structure
3. Implement backend endpoints first
4. Test backend endpoints
5. Implement frontend components
6. Integration testing
7. User acceptance testing