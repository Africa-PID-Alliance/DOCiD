# DOCiD™ System Documentation

## Overview
DOCiD™ (Digital Object Collective Identifier) is a digital content management and identification system that provides a workflow for creating, managing, and publishing digital objects with unique identifiers.

## System Workflow

The DOCiD system follows a 6-step progressive workflow:

### Step 1: DOCID™ (Initial Setup)
- System entry point for creating a new DOCID record
- Marked with a green checkmark when completed

### Step 2: Publications
- **Purpose**: Define and categorize the publication type
- **Publication Types Available**:
  - Article
  - Book Chapter
  - Chapter
  - Proceeding
  - Monograph
  - Preprint
  - Edited Book
  - Seminar
  - Research Chapter
  - Review Article
  - Book Review
  - Conference Abstract
  - Letter To Editor
  - Editorial
  - Other Book Content
  - Correction Erratum
- **Interface**: Dropdown selection with search capability
- Users select the appropriate publication type for their content

### Step 3: Documents
- **Purpose**: Upload and manage publication files
- **Document Type Categories**:

  **Multimedia Content:**
  - **Video** - Supported formats: .mp4, .mov, .avi, .mkv
  - **Audio** - Supported formats: .mp3, .wav, .ogg, .m4a
  - **Image** - Supported formats: .jpg, .jpeg, .png, .webp
  - **Gif** - Supported format: .gif

  **Data & Research:**
  - **Datasets** - Supported formats: .csv, .xlsx, .json, .xml

  **Publications:**
  - **Article** - Supported formats: .pdf, .doc, .docx
  - **Book Chapter** - Supported formats: .pdf, .doc, .docx
  - **Chapter** - Supported formats: .pdf, .doc, .docx
  - **Proceeding** - Supported formats: .pdf, .doc, .docx
  - **Monograph** - Supported formats: .pdf, .doc, .docx
  - **Preprint** - Supported formats: .pdf, .doc, .docx
  - **Edited Book** - Supported formats: .pdf, .doc, .docx
  - **Seminar** - Supported formats: .pdf, .doc, .docx
  - **Research Chapter** - Supported formats: .pdf, .doc, .docx
  - **Review Article** - Supported formats: .pdf, .doc, .docx

- **Upload Interface**:
  - Document Type selection dropdown with file format hints
  - **Upload 4 Files** button for batch file upload
  - Maximum file size: 100MB per file
  - Multiple file upload support (up to 4 files simultaneously)

- **File Management**:
  - Uploaded files display with:
    - File icon indicator
    - Full filename with timestamp (e.g., "Screenshot 2025-08-15 at 07-22-34 Animal Health Records WRTI BioAtlas.png")
    - File size display (e.g., "396.4 KB")
  - Action buttons:
    - **Preview** - View uploaded file
    - **Remove** - Delete uploaded file

- **Metadata Fields**:
  - **Title** - Required field for document title (e.g., "test image")
  - **Description** - Text area for detailed description (e.g., "image desc")
  - **Identifier Type** - Dropdown selection (default: "APA Handle ID")
  - **Generated Identifier** - Auto-generated unique identifier (e.g., "20.500.14351/b1f26969fdec417b55c6")

- **Additional Features**:
  - **Add Another Document** button - Add multiple documents in sequence
  - Form validation before proceeding
  - Back/Next navigation buttons
  - Session saving capability

### Step 4: Creators
- **Purpose**: Add author/creator information and manage contributors
- **Initial State**:
  - Empty creators list with "No creators added yet" message
  - Green "Add" button in top-right corner

- **Add Creator Modal**:
  - Two-tab interface:
    - **ORCID ID Tab**: Primary creator identification method
    - **ORCID Details Tab**: View and edit creator information

- **ORCID Integration**:
  - **ORCID ID Entry**:
    - Input field for ORCID identifier (format: 0000-0002-1981-4157)
    - "Search ORCID" button to retrieve creator details
    - "Get ORCID ID" link for users without ORCID

  - **Retrieved Information**:
    - Full Name (auto-populated)
    - Family Name (e.g., "Česnutytė")
    - Given Name (e.g., "Eglė")
    - ORCID ID (validated format)
    - Affiliation (e.g., "No institution found" if not available)
    - Identifier Type dropdown (default: ORCID)

- **Role Assignment**:
  - Required field with dropdown selection
  - Available roles:
    - Innovator
    - Director
    - Researcher
    - Principal Investigator
    - Librarian
    - Vice Chancellor
    - Deputy Vice Chancellor

- **Creator Management**:
  - **Creator List Display**:
    - Sequential numbering (Creator 1, Creator 2, etc.)
    - Displays: Given Name, Family Name, ORCID ID, Affiliation, Role
    - Delete button (trash icon) for each creator
  - **Multiple Creators**:
    - Add unlimited creators using the "Add" button
    - Each creator card shows all relevant information
  - **Edit Capability**:
    - Click on creator card to edit details
    - Modal allows modification of all fields

- **Form Actions**:
  - "Add Creator" button to save and add to list
  - X button to close modal without saving
  - Form validation ensures required fields are filled

### Step 5: Organizations
- **Purpose**: Manage organizational associations and affiliations
- **Initial State**:
  - Empty organizations list with "No organizations added yet" message
  - Green "Add" button in top-right corner

- **Add Organization Modal**:
  - Two-tab interface:
    - **ROR ID Tab**: Primary organization identification method
    - **ROR Details Tab**: View and edit organization information

- **ROR Integration** (Research Organization Registry):
  - **Method 1: ROR ID Search**
    - Input field for ROR ID (e.g., "00dzfmv17")
    - "Search ROR" button to retrieve organization details
    - "Get ROR ID" link for organizations without ROR

  - **Method 2: Manual Search**
    - Organization Name field (e.g., "Bill Gates Foundation")
    - Country field with dropdown/autocomplete (e.g., "USA")
    - "Search ROR" button to find matching organizations
    - "Get ROR ID" link for manual registration

- **Organization Details**:
  - **Retrieved/Entered Information**:
    - Organization Name (e.g., "Training Centre in Communication")
    - ROR ID (e.g., "00dzfmv17")
    - Country (e.g., "Kenya")
    - Organization Type (optional field)
    - Other Organization Name (alternative names)

- **Organization Management**:
  - **Organization List Display**:
    - Sequential numbering (Organization 1, Organization 2, etc.)
    - Card format showing:
      - Organization Name
      - ROR ID
      - Country
      - Organization Type (shows "N/A" if not specified)
    - Delete button (trash icon) for each organization

  - **Multiple Organizations**:
    - Add unlimited organizations using the "Add" button
    - Each organization card displays all relevant information
    - Cards are expandable/editable

- **Form Actions**:
  - "Add Organization" button to save and add to list
  - X button to close modal without saving
  - Form validation for required fields
  - Clear visual feedback with red X when closing details

### Step 6: Funders
- **Purpose**: Add funding information and grant details for the publication/research
- **Initial State**:
  - Empty funders list with "No funders added yet" message
  - Green "Add" button in top-right corner

- **Add Funder Modal**:
  - Two-tab interface:
    - **ROR ID Tab**: Primary funder identification method
    - **ROR Details Tab**: View and edit funder information

- **Funder Search Methods**:

  **Method 1: ROR ID Direct Entry**
  - Input field accepts:
    - ROR ID only (e.g., "00dzfmv17")
    - Full ROR URL (e.g., "https://ror.org/00dzfmv17")
  - "Search ROR" button retrieves funder details
  - "Get ROR ID" link for funders without ROR

  **Method 2: Name and Country Search**
  - Organization Name field (e.g., "BILL & MELIDA GATES FOUNDATION")
  - Country dropdown/text field (e.g., "USA")
  - "Search ROR" button to find matching funders
  - System searches ROR database for matches

- **Funder Details** (ROR Details Tab):
  - **Retrieved/Entered Information**:
    - Organization Name (e.g., "Gates Foundation", "Training Centre in Communication")
    - ROR ID (e.g., "0456r8d26", "https://ror.org/00dzfmv17")
    - Country (e.g., "United States", "Kenya")
    - Organization Type (auto-populated as "Funder")
    - Other Organization Name (alternative names, e.g., "TCC Africa")

- **Funder Management**:
  - **Funder List Display**:
    - Sequential numbering (Funder 1, Funder 2, etc.)
    - Card format showing:
      - Organization Name
      - ROR ID
      - Country
      - Organization Type (displays "Funder")
    - Delete button (trash icon) for each funder

  - **Multiple Funders**:
    - Add unlimited funders using the "Add" button
    - Each funder card displays all relevant information
    - Support for multiple funding sources per publication

- **Form Actions**:
  - "Add Funder" button to save and add to list
  - X button to close modal without saving
  - Form validation ensures required fields
  - Red X indicator when closing details tab without saving

### Step 7: Projects
- **Purpose**: Link publications to related projects and research initiatives
- **Navigation**:
  - "Assign ID" button replaces "Next" button to complete the workflow

- **Add Project Modal**:
  - Single input interface for RAID URL
  - Supports Research Activity Identifier (RAiD) system

- **Project Integration**:
  - **RAID URL Entry**:
    - Input field for full RAID URL (e.g., "https://app.demo.raid.org.au/raids/10.80368/b1adfb3a")
    - "Find Project" button to retrieve project details
    - "GET RAID ID" link for projects without RAID

  - **Project Discovery**:
    - System searches RAID database using provided URL
    - Success message: "✓ Project found!" when match located
    - Auto-populates project details from RAID system

- **Project Information**:
  - **Retrieved Details**:
    - Title (e.g., "AFRICA PID ALLIANCE DOCID Example_RAID title added by Erastus... 06:55:17")
    - Description (e.g., "DOiD Description text added by Erastus...123")
    - Both fields are read-only when retrieved from RAID
    - Fields display full project metadata

- **Project Management**:
  - **Project List Display**:
    - Sequential numbering (Project 1, Project 2, etc.)
    - Card format showing:
      - Project Title (full title from RAID)
      - Project Description (complete description text)
    - Delete button (trash icon) for each project
    - Large text area for description to accommodate detailed project information

  - **Multiple Projects**:
    - Add unlimited projects using the "Add" button
    - Each project card displays full information
    - Support for linking to multiple research projects

- **Form Actions**:
  - "Add Project" button to save and add to list
  - X button to close modal without saving
  - "GET RAID ID" link for manual registration

- **Workflow Completion**:
  - **Assign ID** button becomes active after completing all steps
  - Clicking "Assign ID" triggers submission confirmation
  - Completes the publication registration process
  - Links all metadata, files, creators, organizations, funders, and projects

## Final Submission Process

### Confirmation Dialog
- **Trigger**: Clicking "Assign ID" button
- **Warning Icon**: Orange triangle alert symbol
- **Message**: "Are you sure?" with "Do you want to submit this publication?"
- **Actions**:
  - **No** button - Returns to edit mode
  - **Yes** button - Proceeds with submission

### Success Confirmation
- **Success Modal**:
  - Green checkmark icon
  - "Success" heading
  - Message: "Publication added Successfully"
  - **OK** button to proceed to DOCIDs list

## Post-Submission: DOCIDs List View

### Main Dashboard
- **URL**: http://localhost:3000/list-docids
- **Header**: "Digital Object Container Identifiers"
- **Tagline**: "Browse and search through registered DOCIDs. Find, explore, and collaborate on digital objects across different domains."

### Search and Filter
- **Search Bar**: "Search by title..." with magnifying glass icon
- **Filter Dropdown**: "Filter by Res.Types" for resource type filtering
- **Assign DocID Button**: Top-right button to start new DOCID creation

### DOCID Cards Display
Each published DOCID appears as a card showing:
- **Author Avatar**: Circle with initials (e.g., "E" for E. Kariz)
- **Author Name** and **Publication Date**
- **DOCID Logo**: Large DOCiD™ branding
- **Resource Type Tag**: (e.g., #Indigenous Knowledge, #Patent)
- **Title**: Publication title
- **Engagement Metrics**:
  - Likes (thumbs up icon with count)
  - Comments (comment icon with count)
  - Views (eye icon with count)

### Top Publications Sidebar
- **Section**: "Top Publications"
- Lists recent publications with:
  - Author avatar
  - Publication date
  - Title
  - Resource type hashtag

## Single DOCID View

### Publication Details Page
When clicking on a DOCID card, users see:

**Header Section**:
- Author name and publication date
- Three-dot menu for additional options
- Title of publication
- Full DOCID identifier (e.g., "DOCID: 20.500.14351/b23a80ce9b1a6ef21588")
- DOCiD™ logo with tagline

**Description Section**:
- Full description text

**Engagement Bar**:
- Like button with count
- Comment count (e.g., "1")
- View count
- Share button

**Metadata Sections** (with VIEW buttons):
- **Publication(s)**: Number of publications
- **Document(s)**: Number of documents
- **Creator(s)**: Number of creators
- **Organizations**: Number of organizations
- **Funders**: Number of funders
- **Project(s)**: Number of projects

### Comments Section
- **Header**: "Comment(s) (1)"
- **Comment Display**:
  - Commenter avatar and name
  - Timestamp (e.g., "29/09/2025 04:46:23")
  - "hello" sample comment
  - Reply button
- **Post Comment**:
  - Text area: "Share your thoughts..."
  - "Post Comment" button

### Related DOCIDs
- Section showing related publications
- Allows discovery of similar content

## Navigation Features

- **Progress Indicator**: Visual workflow showing current step with highlighted circles
- **Back/Next Buttons**: Navigate between workflow steps
- **Save Draft**: Option to save progress (shown as "Saved 07:34:19")
- **Draft Management**: Ability to load from previous session

## User Interface Elements

### Header
- Home navigation
- DOCIDs menu
- About DOCID™ section
- User profile with theme toggle (dark/light mode)
- Timestamp display

### Form Validation
- Required fields marked with asterisks (*)
- Real-time validation feedback
- Auto-save functionality

## Technical Features

1. **Unique Identifier Generation**
   - Automatic generation of persistent identifiers
   - Format: 20.500.[institution]/[unique-hash]
   - Ensures global uniqueness and persistence

2. **File Management**
   - Multi-file upload support
   - File size display
   - Preview capabilities
   - Remove functionality

3. **Metadata Capture**
   - Structured metadata fields
   - Rich text descriptions
   - Controlled vocabularies for resource types

4. **Session Management**
   - Draft saving
   - Session restoration
   - Progress tracking

## Best Practices

1. Complete all required fields before proceeding to next step
2. Upload files in supported formats only
3. Provide descriptive titles and descriptions
4. Select appropriate publication types and resource categories
5. Save drafts regularly to prevent data loss

## System Benefits

- Standardized digital object identification
- Persistent URLs for citations
- Comprehensive metadata management
- Support for various publication types
- Multi-format file support
- Collaborative features through organizations and projects
- Funding acknowledgment capabilities