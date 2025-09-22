# CORDRA Identifiers Update Summary

## Changes Made

### 1. Updated `push_to_cordra.py`
Added support for pushing identifier and identifier_type fields to CORDRA for:

#### PublicationCreators (Lines 239-251)
- Added `identifierType` field (e.g., 'orcid', 'isni', 'viaf')
- `identifier` field now contains full resolvable URL (e.g., https://orcid.org/0000-0002-1981-4157)
- Added dynamic field with identifier type name for easier access (e.g., `orcid: "https://orcid.org/..."`

#### PublicationFunders (Lines 340-353)
- Added `identifierType` field (e.g., 'ror', 'fundref', 'isni')
- `identifier` field now contains full resolvable URL (e.g., https://ror.org/01bj3aw27)
- Added dynamic field with identifier type name for easier access (e.g., `ror: "https://ror.org/..."`

#### PublicationOrganizations (Lines 293-306)
- Added conditional support for future identifier fields
- Will automatically include identifier fields when they're added to the model

### 2. Created Test Script
`test_cordra_identifiers.py` - Verifies identifiers are correctly formatted and present

## Data Format in CORDRA

### Creators Example
```json
{
  "familyName": "Kariuki",
  "givenName": "Erastus",
  "fullName": "Erastus Kariuki",
  "identifier": "https://orcid.org/0000-0002-7453-6460",
  "identifierType": "orcid",
  "orcid": "https://orcid.org/0000-0002-7453-6460",
  "role": "Author",
  "parentId": "20.500.14351/..."
}
```

### Funders Example
```json
{
  "name": "Bill & Melinda Gates Foundation",
  "type": "Foundation",
  "funderType": "Private",
  "otherName": "",
  "country": "United States",
  "identifier": "https://ror.org/01bj3aw27",
  "identifierType": "ror",
  "ror": "https://ror.org/01bj3aw27",
  "parentId": "20.500.14351/..."
}
```

### Projects (Unchanged)
```json
{
  "title": "AFRICA PID ALLIANCE DOCiD Example",
  "raidId": "https://app.demo.raid.org.au/raids/10.80368/b1adfb3a",
  "description": "Project description",
  "parentId": "20.500.14351/..."
}
```

## Testing

### 1. Test Specific Publication
```bash
# Test identifiers for a specific publication
python test_cordra_identifiers.py --publication-id 12

# Push to CORDRA with identifiers
python push_to_cordra.py --publication-id 12
```

### 2. Test Recent Publications
```bash
# Check last 5 publications
python test_cordra_identifiers.py

# Push all to CORDRA
python push_to_cordra.py
```

### 3. Verify in Database
```sql
-- Check creators with identifiers
SELECT pc.family_name, pc.given_name, pc.identifier, pc.identifier_type
FROM publication_creators pc
WHERE pc.identifier IS NOT NULL
ORDER BY pc.id DESC;

-- Check funders with identifiers
SELECT pf.name, pf.identifier, pf.identifier_type
FROM publication_funders pf
WHERE pf.identifier IS NOT NULL
ORDER BY pf.id DESC;
```

## Benefits

1. **Resolvable Identifiers**: All identifiers are stored as full URLs
2. **Type Information**: Clear indication of identifier type
3. **Easy Access**: Dynamic fields for quick identifier access
4. **Future-Proof**: Organizations ready for identifier support
5. **CORDRA Integration**: Seamless push of identifier data

## Frontend Requirements

For this to work properly, the frontend needs to send:

### For Creators (✅ Already Working)
- `creators[0][orcid]=0000-0002-7453-6460`
- `creators[0][identifier]=orcid`

### For Funders (❌ Needs Fix)
- `funders[0][ror]=01bj3aw27` (NOT currently being sent)

See `frontend_funder_ror_fix.md` for the required frontend update.

## Cron Job

The push happens automatically via:
- `push_recent_to_cordra.py` - Runs every minute
- Processes publications created in last 2 minutes
- Includes all identifier fields

## Manual Push

To manually push a publication with identifiers:
```bash
python push_to_cordra.py --publication-id 12
```

This will push:
- Main publication metadata
- Files and documents
- **Creators with ORCID identifiers**
- **Funders with ROR identifiers**
- Organizations
- Projects with RAiD