# Frontend Update Required for ROR ID Support

## Issue
The frontend FundersForm.jsx component collects ROR IDs but doesn't send them to the backend in the submission.

## Current State
- The FundersForm component has a `rorId` field in the `newFunder` state
- ROR IDs are fetched and stored when adding funders
- However, the submission code in `page.jsx` doesn't include the ROR ID

## Required Change in `/src/app/assign-docid/page.jsx`

### Find this code (around line 335-340):
```javascript
formData.funders.funders.forEach((funder, index) => {
  submitData.append(`funders[${index}][name]`, funder.name);
  submitData.append(`funders[${index}][other_name]`, funder.otherName);
  submitData.append(`funders[${index}][type]`, 1);
  submitData.append(`funders[${index}][country]`, funder.country);
});
```

### Replace with:
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

## Alternative: Send with explicit identifier fields
If you want to support multiple identifier types in the future:

```javascript
formData.funders.funders.forEach((funder, index) => {
  submitData.append(`funders[${index}][name]`, funder.name);
  submitData.append(`funders[${index}][other_name]`, funder.otherName);
  submitData.append(`funders[${index}][type]`, 1);
  submitData.append(`funders[${index}][country]`, funder.country);
  
  // Add identifier fields
  if (funder.rorId) {
    submitData.append(`funders[${index}][identifier_type]`, 'ror');
    submitData.append(`funders[${index}][identifier]`, funder.rorId);
  }
});
```

## Backend Support
The backend already supports both formats:
1. `funders[0][ror]=01bj3aw27` - Simple ROR field
2. `funders[0][identifier_type]=ror` & `funders[0][identifier]=01bj3aw27` - Explicit identifier fields

The backend will automatically:
- Detect the ROR ID from either format
- Convert it to a resolvable URL: `https://ror.org/01bj3aw27`
- Store it in the database with `identifier_type='ror'`

## Testing
After making this change, when you add a funder with ROR ID:
1. The ROR ID will be sent to the backend
2. Check the database: `SELECT * FROM publication_funders WHERE identifier IS NOT NULL;`
3. You should see the full ROR URL stored

## File Location
The file that needs to be updated is:
`/Users/ekariz/Projects/AMBAND/DOCiD/frontendv2/docid/src/app/assign-docid/page.jsx`