# Database Management Tools

This document explains the different database management scripts available in the DOCiD backend.

## Available Scripts

### 1. clear_non_seeded_tables.py ✅ RECOMMENDED
**Purpose**: Clear all user-generated data while preserving essential lookup data  
**Method**: Uses DELETE statements (no special privileges required)  
**Status**: ✅ Working

```bash
./clear_non_seeded_tables.py
```

**What it preserves**:
- user_accounts (demo user)
- resource_types
- creators_roles
- creators_identifiers
- funder_types
- identifier_types
- publication_types
- pid_lookup

**What it clears**:
- All publication-related tables
- crossref_metadata
- object_datasets
- docid_objects
- object_dataset_types
- user_password_resets
- user_registration_tokens

### 2. truncate_non_seeded_tables.py ⚠️ REQUIRES SUPERUSER
**Purpose**: Same as above but using TRUNCATE statements  
**Method**: Uses TRUNCATE with fallback to DELETE (may require superuser privileges)  
**Status**: ⚠️ May fail due to permission restrictions

```bash
./truncate_non_seeded_tables.py
```

### 3. truncate_all_tables.py 🔴 COMPLETE RESET
**Purpose**: Complete database reset - removes ALL data including seeded data  
**Method**: Uses DELETE statements  
**Status**: ✅ Working

```bash
./truncate_all_tables.py
```

**Warning**: This removes everything including essential lookup data!

## Recommended Workflow

### For Development/Testing
1. Clear user data while keeping lookup data:
   ```bash
   ./clear_non_seeded_tables.py
   ```

### For Complete Reset
1. Clear all data:
   ```bash
   ./truncate_all_tables.py
   ```

2. Reseed essential data:
   ```bash
   python scripts/seed_db.py
   ```

### For Production
- Use `clear_non_seeded_tables.py` to clean user data periodically
- Never use complete reset scripts in production without proper backup

## Why clear_non_seeded_tables.py is Recommended

1. **No special privileges required** - works with standard database user
2. **Safe operation** - preserves essential lookup data
3. **Reliable** - uses DELETE which always works regardless of database permissions
4. **Fast** - processes each table in separate transactions
5. **Verifiable** - shows exactly what was cleared and what was preserved

## Database Verification

After running any cleanup script, you can verify the results by checking the record counts shown in the script output:

```
Seeded tables (should contain data):
  user_accounts: 1 records
  resource_types: 6 records
  creators_roles: 7 records
  ...

Cleared tables (should be empty):
  publication_documents: ✅ Empty
  publications_files: ✅ Empty
  ...
```

## Troubleshooting

### Permission Denied Errors
If you see permission denied errors, use the `clear_non_seeded_tables.py` script instead of the truncate variants.

### Transaction Aborted Errors
This happens when using TRUNCATE without proper privileges. The script will automatically fall back to DELETE, but if you see these errors consistently, switch to `clear_non_seeded_tables.py`.

### Foreign Key Constraint Errors
The scripts process tables in the correct order to avoid foreign key issues. If you still see these errors, check that your database schema matches the expected structure.
