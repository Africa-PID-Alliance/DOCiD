# Model Changes Summary for Handle/DOI Support

## Changes Made to `/Users/ekariz/Projects/AMBAND/DOCiD/backend/app/models.py`

### 1. PublicationFiles Model (Lines 477-501)

**Added Fields:**
```python
handle_identifier = Column(String(100), nullable=True)  # Handle for CORDRA
external_identifier = Column(String(100), nullable=True)  # DOI from DataCite/Crossref
external_identifier_type = Column(String(50), nullable=True)  # Type of external identifier (DOI, etc.)
```

**Complete Updated Model:**
```python
class PublicationFiles(db.Model):
    """
    Files related to publications
    """
    __tablename__ = 'publications_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    publication_type_id = Column(Integer, ForeignKey('publication_types.id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_url = Column(String(255), nullable=False)
    identifier = Column(String(100), nullable=False)
    generated_identifier = Column(String(100), nullable=False)
    handle_identifier = Column(String(100), nullable=True)  # Handle for CORDRA
    external_identifier = Column(String(100), nullable=True)  # DOI from DataCite/Crossref
    external_identifier_type = Column(String(50), nullable=True)  # Type of external identifier (DOI, etc.)

    # Relationships
    publication = relationship('Publications', back_populates='publications_files')

    def __repr__(self):
        return f"<PublicationFiles(id={self.id}, title='{self.title}', publication_id={self.publication_id})>"
```

### 2. PublicationDocuments Model (Lines 503-526)

**Added Fields:**
```python
handle_identifier = Column(String(100), nullable=True)  # Handle for CORDRA
external_identifier = Column(String(100), nullable=True)  # DOI from DataCite/Crossref
external_identifier_type = Column(String(50), nullable=True)  # Type of external identifier (DOI, etc.)
```

**Complete Updated Model:**
```python
class PublicationDocuments(db.Model):
    """
    Documents related to publications
    """
    __tablename__ = 'publication_documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    publication_type_id = Column(Integer, ForeignKey('publication_types.id'), nullable=False)
    file_url = Column(String(255), nullable=False)
    identifier_type_id = Column(Integer, ForeignKey('identifier_types.id'), nullable=True)
    generated_identifier = Column(String(255), nullable=True)
    identifier_cstr = Column(String(100), nullable=True)
    handle_identifier = Column(String(100), nullable=True)  # Handle for CORDRA
    external_identifier = Column(String(100), nullable=True)  # DOI from DataCite/Crossref
    external_identifier_type = Column(String(50), nullable=True)  # Type of external identifier (DOI, etc.)

    # Relationships
    publication = relationship('Publications', back_populates='publication_documents')

    def __repr__(self):
        return f"<PublicationDocuments(id={self.id}, title='{self.title}', publication_id={self.publication_id})>"
```

## Purpose of New Fields

1. **handle_identifier**: Stores the Handle identifier that is used for CORDRA integration
2. **external_identifier**: Stores external identifiers like DOIs from DataCite or Crossref
3. **external_identifier_type**: Stores the type of external identifier (e.g., "DOI", "ARK", etc.)

## Usage Pattern

When a publication file or document has an identifier:
- If it's a DOI (e.g., `10.70001/3030-53-3821`), the system:
  - Generates a Handle for CORDRA
  - Stores the DOI in `external_identifier`
  - Sets `external_identifier_type` to "DOI"
  - Uses the Handle in `handle_identifier` for CORDRA

- If it's already a Handle (e.g., `20.500.12345/abc123`), the system:
  - Stores it in `handle_identifier`
  - Leaves `external_identifier` and `external_identifier_type` as NULL
  - Uses it directly for CORDRA