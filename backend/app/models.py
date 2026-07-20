import time
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, DateTime, Enum, Boolean, event
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app import db

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")
 
class UserAccount(db.Model):
    """
    User account model with adjusted VARCHAR sizes for optimized storage.
    """
    __tablename__ = "user_accounts"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    social_id = db.Column(db.String(100), nullable=True)  # Reduced from 800
    user_name = db.Column(db.String(50), nullable=False)  # Username (50 should be sufficient)
    full_name = db.Column(db.String(100), nullable=False)  # Full name
    email = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # Login type (google, facebook, etc.)
    avator = db.Column(db.String(255), nullable=True)  # Profile avator URL, 255 characters for URLs
    logo_url = db.Column(db.String(500), nullable=True)  # User-specific custom logo URL
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False) #datetime.utcnow for consistent timestamp 
    affiliation = db.Column(db.String(100), nullable=True)  # Organization or affiliation
    role = db.Column(db.String(50), nullable=True)  # Role (e.g., admin, user)
    first_time = db.Column(db.Integer, default=1)  # Flag indicating first login
    orcid_id = db.Column(db.String(50), nullable=True)
    ror_id = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    linkedin_profile_link = db.Column(db.String(255), nullable=True)  # Reduced URL length to 255
    facebook_profile_link = db.Column(db.String(255), nullable=True)
    x_profile_link = db.Column(db.String(255), nullable=True)  # Formerly Twitter
    instagram_profile_link = db.Column(db.String(255), nullable=True)
    github_profile_link = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Custom location string
    date_joined = db.Column(DateTime, default=datetime.utcnow, nullable=False)  # Join date
    password = db.Column(db.String(255), nullable=True)  # Hashed password
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_types.id'), nullable=True, index=True)

    # Define relationships
    publications = relationship('Publications', back_populates='user_account', cascade="all, delete-orphan", foreign_keys='Publications.user_id')
    account_type = relationship('AccountTypes', backref='users')

    def validate_user_id(user_id):
        """
        Validates the provided user ID.
        Args:
            user_id: The user ID to validate.
        Returns:
            The user ID if valid, otherwise returns None.
        """
        if user_id:
            try:
                if not isinstance(user_id, int):
                    return None
                user = UserAccount.query.get(user_id)
                return user
            except (ValueError, TypeError):
                return None
        return None

    def serialize(self):
        return {
            "user_id": self.user_id,
            "social_id": self.social_id,
            "user_name": self.user_name,
            "full_name": self.full_name,
            "email": self.email,
            "type": self.type,
            "avator": self.avator,
            "logo_url": self.logo_url,
            "timestamp": self.timestamp,
            "affiliation": self.affiliation,
            "role": self.role,
            "first_time": self.first_time,
            "orcid_id": self.orcid_id,
            "ror_id": self.ror_id,
            "country": self.country,
            "city": self.city,
            "linkedin_profile_link": self.linkedin_profile_link,
            "facebook_profile_link": self.facebook_profile_link,
            "x_profile_link": self.x_profile_link,
            "instagram_profile_link": self.instagram_profile_link,
            "github_profile_link": self.github_profile_link,
            "location": self.location,
            "date_joined": self.date_joined.isoformat()
        }

    def __repr__(self):
        return f"<UserAccount(user_id={self.user_id}, email='{self.email}', user_name='{self.user_name}')>"
   
class RegistrationTokens(db.Model):
    """
    Model for registration tokens used for user registration and verification.
    """
    __tablename__ = "user_registration_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False)  # Email associated with the registration token
    token = Column(String(255), nullable=False, unique=True)  # Unique registration token
    expires_at = Column(DateTime, nullable=False)  # Expiration datetime of the token

    def __init__(self, email, token, expires_at):
        self.email = email
        self.token = token
        self.expires_at = expires_at

    def is_expired(self):
        """
        Checks if the token has expired.
        Returns:
            bool: True if the token is expired, False otherwise.
        """
        return datetime.utcnow() > self.expires_at

    def serialize(self):
        """
        Serializes the registration token data for easy JSON conversion.
        Returns:
            dict: Dictionary containing the token data.
        """
        return {
            "id": self.id,
            "email": self.email,
            "token": self.token,
            "expires_at": self.expires_at.isoformat()
        }

    def __repr__(self):
        return f"<RegistrationTokens(id={self.id}, email='{self.email}', token='{self.token}', expires_at='{self.expires_at}')>"
     
 
class PasswordResets(db.Model):
    """
    Model for managing password reset requests.
    """

    __tablename__ = "user_password_resets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False, index=True)  # Index added for faster lookups
    token = Column(String(255), unique=True, nullable=False)  
    expires_at = Column(DateTime, nullable=False)  
    type = Column(Enum("password_reset", "account_verification", name="reset_type_enum"), nullable=False)

    def __init__(self, email, token, expires_at, type):
        self.email = email
        self.token = token
        self.expires_at = expires_at
        self.type = type

    def is_expired(self):
        """
        Checks if the token has expired.
        Returns:
            bool: True if the token is expired, False otherwise.
        """
        return datetime.utcnow() > self.expires_at
    
    def is_token_valid(token):
        reset_entry = PasswordResets.query.filter_by(token=token).first()
        return reset_entry and not reset_entry.is_expired()


    def serialize(self):
        """
        Serializes the password reset data for JSON responses.
        Returns:
            dict: Dictionary containing the password reset data.
        """
        return {
            "id": self.id,
            "email": self.email,
            "token": self.token,
            "expires_at": self.expires_at.isoformat(),
            "type": self.type
        }

    def __repr__(self):
        return (
            f"<PasswordResets(id={self.id}, email='{self.email}', "
            f"token='{self.token}', expires_at='{self.expires_at}', type='{self.type}')>"
        )
 
class DocIDObject(db.Model):
    """
    DocID Object
    """

    __tablename__ = "docid_objects"

    object_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    object_docid = db.Column(db.Integer, unique=True, nullable=False)
    object_title = db.Column(db.String(100), nullable=False)
    object_description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user_accounts.user_id"))
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)


class ObjectDataset(db.Model):
    """
    Object dataset
    """

    __tablename__ = "object_datasets"

    object_dataset_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True, nullable=False
    )
    object_dataset_name = db.Column(db.String(100), nullable=False)
    object_dataset_description = db.Column(db.String(100), nullable=False)
    datacite_doi = db.Column(db.String(100), nullable=False)
    object_dataset_title = db.Column(db.String(100), nullable=False)
    docid_doi = db.Column(db.Integer, db.ForeignKey("docid_objects.object_docid"))
    object_dataset_type = db.Column(
        db.Integer, db.ForeignKey("object_dataset_types.object_dataset_type_id")
    )


class ObjectDataSetType(db.Model):
    """
    Object dataset types lookup table
    """

    __tablename__ = "object_dataset_types"

    object_dataset_type_id = db.Column(db.Integer, primary_key=True)
    object_dataset_type_name = db.Column(db.String(100), nullable=False)
    object_dataset_type_description = db.Column(db.String(100), nullable=False)


class DocIdLookup(db.Model):
    """
    DocId lookup
    """

    __tablename__ = "pid_lookup"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    pid = db.Column(db.Text, nullable=False, unique=True)
    pid_reserved = db.Column(db.Boolean, nullable=False, default=False)
    pid_reserved_date = db.Column(db.DateTime, default=datetime.utcnow)
    # pid_reserved_by = initdb.Column(initdb.Integer, initdb.ForeignKey('app_user.user_id'))
    pid_assigned = db.Column(db.Boolean, nullable=False, default=False)
    pid_assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    # pid_assigned_by = initdb.Column(initdb.Integer, initdb.ForeignKey('app_user.user_id'))
    # docid_doi = initdb.Column(initdb.Integer, initdb.ForeignKey('docid_object.object_docid'))

class ResourceTypes(db.Model):
    __tablename__ = 'resource_types'

    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)
    default_poster_url = db.Column(db.String(500), nullable=True)  # fallback card image when publication.publication_poster_url is empty

    def validate_resource_type(resource_type_id):
        """
        Validates the existence of the provided resource type in the database.

        Args:
            data: A dictionary containing the publication data.

        Returns:
            The resource type object if found, otherwise None.
        """
        
        if resource_type_id:
          try:
            # Validate if resource_type_id is an integer
            if not isinstance(resource_type_id, int):
                return None
            # Assuming resourceType represents an ID (modify if needed)
            resource_type = ResourceTypes.query.get(resource_type_id)
            return resource_type
          except (ValueError, TypeError):
            return None
        else:
            return None
     
    def __repr__(self):
     return f"<ResourceTypes(id={self.id}, resource_type='{self.resource_type}')>"


class AccountTypes(db.Model):
    __tablename__ = 'account_types'

    id = db.Column(db.Integer, primary_key=True)
    account_type_name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<AccountTypes(id={self.id}, account_type_name='{self.account_type_name}')>"


class CreatorsRoles(db.Model):
    __tablename__ = 'creators_roles'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.String(50), nullable=False, unique=True)
    role_name = db.Column(db.String(100), nullable=False)


    def validate_creators_role(creators_role_id):
        """
        Validates the existence of the provided creators role in the database.

        Args:
            data: A dictionary containing the creators role data.

        Returns:
            The creators role object if found, otherwise None.
        """
        
        print(f"creators_role_id={creators_role_id}")

        if creators_role_id:
          try:
            # Validate if creators_role_id is an string
            if not isinstance(creators_role_id, str):
                return None
            # Assuming creators_roles represents an ID (modify if needed)
            creators_role = CreatorsRoles.query.filter_by(role_id=creators_role_id).first()

            if creators_role is None:
             return None
            else:
             return creators_role

          except (ValueError, TypeError):
            return None
        else:
            return None

class creatorsIdentifiers(db.Model):
    __tablename__ = 'creators_identifiers'

    id = db.Column(db.Integer, primary_key=True)
    identifier_name = db.Column(db.String(80), nullable=False)

    def validate_creators_role(creators_identifier_id):
        """
        Validates the existence of the provided Identifiers role in the database.

        Args:
            data: A dictionary containing the Identifiers role data.

        Returns:
            The creators Identifiers object if found, otherwise None.
        """

        if creators_identifier_id:
          try:
            # Validate if creators_role_id is an string
            if not isinstance(creators_identifier_id, str):
                return None
            # Assuming creators_roles represents an ID (modify if needed)
            creators_identifier = creatorsIdentifiers.query.filter_by(id=creators_identifier_id).first()

            if creators_identifier is None:
             return None
            else:
             return creators_identifier

          except (ValueError, TypeError):
            return None
        else:
            return None

class FunderTypes(db.Model):
    __tablename__ = 'funder_types'

    id = db.Column(db.Integer, primary_key=True)
    funder_type_name = db.Column(db.String(100), nullable=False)

    def validate_funder_type(funder_type_id):
        """
        Validates the existence of the provided funder types in the database.

        Args:
            data: A dictionary containing the funder  types data.

        Returns:
            The funder type object if found, otherwise None.
        """

        if funder_type_id:
          try:
            # Validate if funder_type_id is an integer
            if not isinstance(funder_type_id, int):
                return None
            # Assuming funder_type represents an ID (modify if needed)
            funder_type = FunderTypes.query.get(funder_type_id)
            return funder_type
          except (ValueError, TypeError):
            return None
        else:
            return None

class PublicationTypes(db.Model):
    __tablename__ = 'publication_types'

    id = db.Column(db.Integer, primary_key=True)
    publication_type_name = db.Column(db.String(50), nullable=False)

    def validate_publication_type(publication_type_id):
        """
        Validates the existence of the provided publication types in the database.

        Args:
            data: A dictionary containing the publication  types data.

        Returns:
            The publication type object if found, otherwise None.
        """

        if publication_type_id:
          try:
            # Validate if publication_type_id is an integer
            if not isinstance(publication_type_id, int):
                return None
            # Assuming publication_type represents an ID (modify if needed)
            publication_type = PublicationTypes.query.get(publication_type_id)
            return publication_type
          except (ValueError, TypeError):
            return None
        else:
            return None

class PublicationIdentifierTypes(db.Model):
    __tablename__ = 'identifier_types'

    id = db.Column(db.Integer, primary_key=True)
    identifier_type_name = db.Column(db.String(50), nullable=False)


    def validate_identifier_type(identifier_type_id):
        """
        Validates the existence of the provided identifier types in the database.

        Args:
            data: A dictionary containing the identifier  types data.

        Returns:
            The identifier type object if found, otherwise None.
        """

        if identifier_type_id:
          try:
            # Validate if identifier_type_id is an integer
            if not isinstance(identifier_type_id, int):
                return None
            # Assuming identifier_type represents an ID (modify if needed)
            identifier_type = PublicationIdentifierTypes.query.get(identifier_type_id)
            return identifier_type
          except (ValueError, TypeError):
            return None
        else:
            return None


class Publications(db.Model):
    """
    Publications model
    """
    __tablename__ = 'publications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_accounts.user_id'), nullable=False, index=True)
    document_docid = Column(String(255), nullable=True, unique=True, index=True)  # Primary resolvable identifier (DOI or minted DOCiD handle)
    document_title = Column(String(255), nullable=False)
    document_description = Column(Text)
    avatar = Column(String(255))
    owner = Column(String(255))
    timestamp = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))  # Use UNIX timestamp as default
    resource_type_id = Column(Integer, ForeignKey('resource_types.id'), nullable=False, index=True)
    publication_poster_url = Column(String(255))
    doi = Column(String(50), nullable=True)
    handle_url = Column(String(500), nullable=True)  # Full resolvable URL for DSpace/repository handles
    collection_name = Column(String(500), nullable=True)  # DSpace collection name (e.g., "City Centre & Atlantic Seaboard")
    published = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('user_accounts.user_id'), nullable=True, index=True)

    # External repository links
    figshare_article_id = Column(String(50), nullable=True, unique=True, index=True)  # Figshare article ID (unique for idempotent imports)
    figshare_url = Column(String(500), nullable=True)  # Full Figshare URL
    ojs_submission_id = Column(String(50), nullable=True, index=True)  # OJS submission ID
    ojs_url = Column(String(500), nullable=True)  # Full OJS article URL

    # CORDRA sync tracking
    cordra_synced = Column(Boolean, default=False)  # Track if pushed to CORDRA
    cordra_synced_at = Column(DateTime, nullable=True)  # When it was synced
    cordra_status = Column(String(20), nullable=False, default='PENDING', index=True)  # SKIPPED|PENDING|MINTED|FAILED
    cordra_error = Column(Text, nullable=True)  # Error message if minting failed
    cordra_object_id = Column(String(128), nullable=True, index=True)  # Cordra object ID after minting

    # Versioning
    parent_id = Column(Integer, ForeignKey('publications.id', ondelete='SET NULL'), nullable=True, index=True)
    version_number = Column(Integer, nullable=True, default=None)

    # Metadata enrichment fields
    citation_count = Column(Integer, nullable=True)
    influential_citation_count = Column(Integer, nullable=True)
    open_access_status = Column(String(20), nullable=True)  # gold|green|hybrid|bronze|closed
    open_access_url = Column(String(500), nullable=True)
    openalex_topics = Column(JSON_DOCUMENT, nullable=True)  # [{name, score}]
    openalex_id = Column(String(100), nullable=True)
    semantic_scholar_id = Column(String(100), nullable=True)
    abstract_text = Column(Text, nullable=True)
    openaire_id = Column(String(100), nullable=True)
    lens_patent_id = Column(String(50), nullable=True, index=True)
    lens_scholar_id = Column(String(50), nullable=True, index=True)

    # Soft-delete (tombstone) — keep handle resolving after retirement
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(Integer, ForeignKey('user_accounts.user_id'), nullable=True)
    deletion_reason = Column(Text, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    # Relationships
    user_account = relationship('UserAccount', back_populates='publications', foreign_keys=[user_id])
    updated_by_user = relationship('UserAccount', foreign_keys=[updated_by])
    resource_type = relationship('ResourceTypes', foreign_keys=[resource_type_id])
    publications_files = relationship('PublicationFiles', back_populates='publication', cascade="all, delete-orphan")
    publication_documents = relationship('PublicationDocuments', back_populates='publication', cascade="all, delete-orphan")
    publication_creators = relationship('PublicationCreators', back_populates='publication', cascade="all, delete-orphan")
    publication_organizations = relationship('PublicationOrganization', back_populates='publication', cascade="all, delete-orphan")
    publication_funders = relationship('PublicationFunders', back_populates='publication', cascade="all, delete-orphan")
    publication_projects = relationship('PublicationProjects', back_populates='publication', cascade="all, delete-orphan")
    parent_publication = relationship('Publications', remote_side='Publications.id', foreign_keys=[parent_id], backref='versions')

    def __repr__(self):
        return f"<Publications(id={self.id}, document_title='{self.document_title}', doi='{self.doi}')>"

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

    # Integrity / checksum fields (see docs/checksum-integrity-implementation-plan.md)
    checksum = Column(String(64), nullable=True)  # hex SHA-256 of stored file bytes
    checksum_algorithm = Column(String(20), nullable=True)  # e.g. 'SHA-256'
    file_size = Column(BigInteger, nullable=True)  # bytes
    checksum_status = Column(String(30), nullable=True)  # pending|verified|external_not_supported|missing_bytes|failed
    checksum_error = Column(Text, nullable=True)  # last error when status=failed
    checksum_generated_at = Column(DateTime, nullable=True)  # when the hash was computed
    checksum_last_checked_at = Column(DateTime, nullable=True)  # when it was last (re)verified

    # Relationships
    publication = relationship('Publications', back_populates='publications_files')

    def __repr__(self):
        return f"<PublicationFiles(id={self.id}, title='{self.title}', publication_id={self.publication_id})>"

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
    rrid = Column(String(100), nullable=True)  # Optional RRID e.g. "RRID:SCR_012345"

    # Integrity / checksum fields (see docs/checksum-integrity-implementation-plan.md)
    checksum = Column(String(64), nullable=True)  # hex SHA-256 of stored file bytes
    checksum_algorithm = Column(String(20), nullable=True)  # e.g. 'SHA-256'
    file_size = Column(BigInteger, nullable=True)  # bytes
    checksum_status = Column(String(30), nullable=True)  # pending|verified|external_not_supported|missing_bytes|failed
    checksum_error = Column(Text, nullable=True)  # last error when status=failed
    checksum_generated_at = Column(DateTime, nullable=True)  # when the hash was computed
    checksum_last_checked_at = Column(DateTime, nullable=True)  # when it was last (re)verified

    # Relationships
    publication = relationship('Publications', back_populates='publication_documents')

    def __repr__(self):
        return f"<PublicationDocuments(id={self.id}, title='{self.title}', publication_id={self.publication_id})>"

class PublicationCreators(db.Model):
    """
    Creators related to publications
    """
    __tablename__ = 'publication_creators'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    family_name = Column(String(255), nullable=False)
    given_name = Column(String(255))
    identifier = Column(String(500))  # Stores the full resolvable URL (e.g., https://orcid.org/0000-0002-1981-4157)
    identifier_type = Column(String(50))  # Stores the type (e.g., 'orcid', 'isni', 'viaf')
    role_id = Column(String(255), nullable=False)
    affiliation = Column(String(500), nullable=True)

    # Relationships
    publication = relationship('Publications', back_populates='publication_creators')

    def __repr__(self):
        return f"<PublicationCreators(id={self.id}, family_name='{self.family_name}', publication_id={self.publication_id})>"


class NationalIdResearcher(db.Model):
    """
    Registry of researchers identified by National ID or Passport Number.
    Acts as a local researcher database (mirror of ORCID for non-ORCID researchers).
    """
    __tablename__ = 'national_id_researchers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    national_id_number = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, server_default=db.func.now())
    updated_at = Column(DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('national_id_number', 'country', name='uq_national_id_country'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'national_id_number': self.national_id_number,
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<NationalIdResearcher(id={self.id}, name='{self.name}', country='{self.country}')>"


class PublicationOrganization(db.Model):
    """
    Organizations related to publications
    """
    __tablename__ = 'publication_organizations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    other_name = Column(String(255))
    country = Column(String(255))
    identifier = Column(String(500))  # Primary resolvable URL (back-compat — usually the ROR or first PID)
    identifier_type = Column(String(50))  # Type for `identifier` (e.g., 'ror', 'grid', 'isni', 'ringgold')
    # Cross-reference identifiers — Ringgold lookup returns both, store both losslessly.
    ringgold_id = Column(String(50), nullable=True, index=True)
    isni = Column(String(50), nullable=True, index=True)
    rrid = Column(String(100), nullable=True)  # Optional RRID e.g. "RRID:SCR_012345"

    # Relationships
    publication = relationship('Publications', back_populates='publication_organizations')

    def __repr__(self):
        return f"<PublicationOrganization(id={self.id}, name='{self.name}', publication_id={self.publication_id})>"


class Tenant(db.Model):
    """
    Per-client branding config. Each row controls one subdomain's visual
    identity (logo, title, colors, footer). All tenants share the same
    underlying data — this is PURE whitelabel, not data scoping.

    Resolved at request time by the Next.js frontend middleware, which
    parses the Host header (e.g. `stellenbosch.africapidalliance.test`
    locally or `stellenbosch.africapidalliance.org` in prod), extracts
    the first dot-segment as the slug, and fetches config from
    GET /api/v1/tenants/<slug>.
    """
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)

    # Visual assets — URLs relative to Next.js /public dir or absolute
    logo_url = Column(String(500), nullable=True)
    logo_dark_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    og_image_url = Column(String(500), nullable=True)

    # Colors (hex strings, e.g. "#780000"). NULL = inherit default theme.
    primary_color = Column(String(9), nullable=True)
    primary_color_dark = Column(String(9), nullable=True)
    accent_color = Column(String(9), nullable=True)

    # Copy overrides (all optional, fall back to default DOCiD copy)
    page_title = Column(String(255), nullable=True)
    page_description = Column(Text, nullable=True)
    hero_tagline = Column(String(500), nullable=True)
    footer_copyright = Column(String(255), nullable=True)

    # Contact overrides
    contact_email = Column(String(255), nullable=True)
    email_from_name = Column(String(255), nullable=True)

    # Extensibility without migrations
    feature_flags = Column(JSON_DOCUMENT, nullable=True)

    # Lifecycle
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            'slug': self.slug,
            'display_name': self.display_name,
            'logo_url': self.logo_url,
            'logo_dark_url': self.logo_dark_url,
            'favicon_url': self.favicon_url,
            'og_image_url': self.og_image_url,
            'primary_color': self.primary_color,
            'primary_color_dark': self.primary_color_dark,
            'accent_color': self.accent_color,
            'page_title': self.page_title,
            'page_description': self.page_description,
            'hero_tagline': self.hero_tagline,
            'footer_copyright': self.footer_copyright,
            'contact_email': self.contact_email,
            'email_from_name': self.email_from_name,
            'feature_flags': self.feature_flags or {},
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f"<Tenant(id={self.id}, slug='{self.slug}', display_name='{self.display_name}')>"


class PublicationFunders(db.Model):
    """
    Funders related to publications
    """
    __tablename__ = 'publication_funders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    funder_type_id = Column(Integer, ForeignKey('funder_types.id'), nullable=False, index=True)
    other_name = Column(String(255))
    country = Column(String(255))
    identifier = Column(String(500))  # Stores the full resolvable URL (e.g., https://ror.org/01ej9dk98)
    identifier_type = Column(String(50))  # Stores the type (e.g., 'ror', 'fundref', 'isni')

    # Relationships
    publication = relationship('Publications', back_populates='publication_funders')

    def __repr__(self):
        return f"<PublicationFunders(id={self.id}, name='{self.name}', publication_id={self.publication_id})>"

class PublicationProjects(db.Model):
    """
    Projects related to publications
    """
    __tablename__ = 'publication_projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey('publications.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    raid_id = Column(String(255))  # Keep for backward compatibility
    identifier = Column(String(500))  # Stores the full resolvable URL (e.g., https://app.demo.raid.org.au/raids/10.80368/b1adfb3a)
    identifier_type = Column(String(50))  # Stores the type (e.g., 'raid')

    # Relationships
    publication = relationship('Publications', back_populates='publication_projects')

    def __repr__(self):
        return f"<PublicationProjects(id={self.id}, title='{self.title}', publication_id={self.publication_id})>"
        
        

class CrossrefMetadata(db.Model):
    __tablename__ = 'crossref_metadata'

    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(512), nullable=False)
    authors = db.Column(db.Text, nullable=True)  # Storing authors as a comma-separated string or JSON.
    publisher = db.Column(db.String(255), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    resource_url = db.Column(db.String(512), nullable=True)
    journal_full_title = db.Column(db.String(512), nullable=True)
    journal_issn = db.Column(db.String(32), nullable=True)
    deposit_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    def __repr__(self):
        return f"<CrossrefMetadata(doi='{self.doi}', title='{self.title}')>"

    def to_dict(self):
        return {
            'doi': self.doi,
            'title': self.title,
            'authors': self.authors,
            'publisher': self.publisher,
            'publication_date': self.publication_date,
            'resource_url': self.resource_url,
            'journal_full_title': self.journal_full_title,
            'journal_issn': self.journal_issn,
            'deposit_date': self.deposit_date
        }


class PublicationComments(db.Model):
    """
    Model for storing comments on publications
    """
    __tablename__ = 'publication_comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=False, index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('publication_comments.id'), nullable=True, index=True)
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50), default='general')  # general, review, question, suggestion
    status = db.Column(db.String(20), default='active')  # active, edited, deleted, flagged
    is_edited = db.Column(db.Boolean, default=False)
    edit_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    publication = db.relationship('Publications', backref=db.backref('comments', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('UserAccount', backref=db.backref('comments', lazy='dynamic'))
    parent_comment = db.relationship('PublicationComments', remote_side=[id], backref='replies')
    
    def __repr__(self):
        return f"<PublicationComment(id={self.id}, publication_id={self.publication_id}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert comment to dictionary for API responses"""
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_avatar': self.user.avator if self.user else None,
            'parent_comment_id': self.parent_comment_id,
            'comment_text': self.comment_text,
            'comment_type': self.comment_type,
            'status': self.status,
            'is_edited': self.is_edited,
            'edit_count': self.edit_count,
            'likes_count': self.likes_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'replies_count': len(self.replies) if self.replies else 0
        }
    
    @classmethod
    def get_publication_comments(cls, publication_id, include_replies=True):
        """Get all comments for a publication"""
        if include_replies:
            return cls.query.filter_by(publication_id=publication_id, status='active').order_by(cls.created_at.desc()).all()
        else:
            # Get only top-level comments (no parent)
            return cls.query.filter_by(publication_id=publication_id, parent_comment_id=None, status='active').order_by(cls.created_at.desc()).all()
    
    @classmethod
    def add_comment(cls, publication_id, user_id, comment_text, comment_type='general', parent_comment_id=None):
        """Add a new comment to a publication"""
        comment = cls(
            publication_id=publication_id,
            user_id=user_id,
            comment_text=comment_text,
            comment_type=comment_type,
            parent_comment_id=parent_comment_id
        )
        db.session.add(comment)
        db.session.commit()
        return comment
    
    def edit_comment(self, new_text):
        """Edit an existing comment"""
        self.comment_text = new_text
        self.is_edited = True
        self.edit_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def delete_comment(self, soft_delete=True):
        """Delete a comment (soft delete by default)"""
        if soft_delete:
            self.status = 'deleted'
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()
    
    def increment_likes(self):
        """Increment the likes count for a comment"""
        self.likes_count += 1
        db.session.commit()
        return self.likes_count


class PublicationDrafts(db.Model):
    """
    Draft storage for assign-docid form - allows users to save and continue later.
    Supports multiple drafts per user (one per resource type).
    """
    __tablename__ = 'publication_drafts'
    __table_args__ = (
        db.UniqueConstraint('email', 'resource_type_id', name='uq_publication_drafts_email_resource_type'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    resource_type_id = db.Column(db.Integer, db.ForeignKey('resource_types.id'), nullable=False, index=True)
    form_data = db.Column(db.JSON, nullable=False)  # Complete form state as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to ResourceTypes
    resource_type = db.relationship('ResourceTypes', backref='drafts')

    def __repr__(self):
        return f"<PublicationDrafts(id={self.id}, email='{self.email}', resource_type_id={self.resource_type_id})>"

    def to_dict(self):
        """Serialize draft for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'resource_type_id': self.resource_type_id,
            'resource_type_name': self.resource_type.resource_type if self.resource_type else None,
            'form_data': self.form_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def save_draft(cls, email, resource_type_id, form_data):
        """Save or update draft data for user and resource type combination"""
        draft = cls.query.filter_by(email=email, resource_type_id=resource_type_id).first()

        if draft:
            # Update existing draft
            draft.form_data = form_data
            draft.updated_at = datetime.utcnow()
        else:
            # Create new draft
            draft = cls(email=email, resource_type_id=resource_type_id, form_data=form_data)
            db.session.add(draft)

        db.session.commit()
        return draft

    @classmethod
    def get_draft(cls, email, resource_type_id):
        """Get specific draft for user and resource type"""
        return cls.query.filter_by(email=email, resource_type_id=resource_type_id).first()

    @classmethod
    def get_all_drafts_by_email(cls, email):
        """Get all drafts for a user"""
        return cls.query.filter_by(email=email).order_by(cls.updated_at.desc()).all()

    @classmethod
    def delete_draft(cls, email, resource_type_id):
        """Delete specific draft after successful submission"""
        draft = cls.query.filter_by(email=email, resource_type_id=resource_type_id).first()
        if draft:
            db.session.delete(draft)
            db.session.commit()
            return True
        return False

    @classmethod
    def get_user_drafts_count(cls):
        """Get total count of drafts (for admin purposes)"""
        return cls.query.count()


class PidMintAudit(db.Model):
    """Immutable security audit record for PID namespace write attempts."""

    __tablename__ = 'pid_mint_audit'
    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'operation', 'idempotency_key',
            name='uq_pid_mint_audit_actor_operation_key',
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user_accounts.user_id'),
        nullable=False,
        index=True,
    )
    operation = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)
    idempotency_key = db.Column(db.String(128), nullable=False)
    request_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    payload_sha256 = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_progress', index=True)
    response_status = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    identifier = db.Column(db.String(255), nullable=True, index=True)
    error_code = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('UserAccount', backref='pid_mint_audits')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation': self.operation,
            'resource_type': self.resource_type,
            'idempotency_key': self.idempotency_key,
            'request_id': self.request_id,
            'payload_sha256': self.payload_sha256,
            'status': self.status,
            'response_status': self.response_status,
            'identifier': self.identifier,
            'error_code': self.error_code,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class MutationAudit(db.Model):
    """Append-only audit event for every state-changing HTTP request."""

    __tablename__ = 'mutation_audit'

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )
    request_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    user_role = db.Column(db.String(50), nullable=True)
    method = db.Column(db.String(10), nullable=False)
    endpoint = db.Column(db.String(255), nullable=True)
    path = db.Column(db.String(500), nullable=False)
    payload_sha256 = db.Column(db.String(64), nullable=False)
    response_status = db.Column(db.Integer, nullable=False, index=True)
    outcome = db.Column(db.String(20), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


@event.listens_for(MutationAudit, 'before_update')
@event.listens_for(MutationAudit, 'before_delete')
def _prevent_mutation_audit_changes(mapper, connection, target):
    raise ValueError('mutation_audit records are immutable')


class PublicationAuditTrail(db.Model):
    """
    Audit trail for tracking changes to publications
    """
    __tablename__ = 'publication_audit_trail'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    field_name = db.Column(db.String(100))  # Field that was changed (null for CREATE/DELETE)
    old_value = db.Column(db.Text)  # Previous value (JSON for complex objects)
    new_value = db.Column(db.Text)  # New value (JSON for complex objects)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))  # User's IP address (IPv4/IPv6)
    user_agent = db.Column(db.Text)  # Browser/client information
    
    # Relationships
    publication = db.relationship('Publications', backref='audit_entries')
    user = db.relationship('UserAccount', backref='audit_actions')
    
    def __repr__(self):
        return f"<PublicationAuditTrail(id={self.id}, publication_id={self.publication_id}, action='{self.action}', user_id={self.user_id})>"
    
    @classmethod
    def log_change(cls, publication_id, user_id, action, field_name=None, old_value=None, new_value=None, ip_address=None, user_agent=None):
        """
        Log a change to the audit trail
        
        Args:
            publication_id (int): ID of the publication
            user_id (int): ID of the user making the change
            action (str): Action performed ('CREATE', 'UPDATE', 'DELETE')
            field_name (str, optional): Name of the field changed
            old_value (str, optional): Previous value
            new_value (str, optional): New value
            ip_address (str, optional): User's IP address
            user_agent (str, optional): User's browser/client info
        """
        audit_entry = cls(
            publication_id=publication_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(audit_entry)
        db.session.commit()
        return audit_entry
    
    @classmethod
    def get_publication_history(cls, publication_id, limit=50):
        """
        Get audit history for a publication
        
        Args:
            publication_id (int): ID of the publication
            limit (int): Maximum number of entries to return
            
        Returns:
            List of audit entries ordered by timestamp (newest first)
        """
        return cls.query.filter_by(publication_id=publication_id)\
                      .order_by(cls.timestamp.desc())\
                      .limit(limit)\
                      .all()
    
    def serialize(self):
        """Serialize audit entry for JSON responses"""
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'user_id': self.user_id,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }


class PublicationViews(db.Model):
    """
    Track DOCiD page views for analytics
    """
    __tablename__ = 'publication_views'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    publication = db.relationship('Publications', backref=db.backref('views', lazy='dynamic'))
    user = db.relationship('UserAccount', backref=db.backref('viewed_publications', lazy='dynamic'))

    def __repr__(self):
        return f"<PublicationViews(id={self.id}, publication_id={self.publication_id}, viewed_at='{self.viewed_at}')>"

    def to_dict(self):
        """Serialize view record for JSON responses"""
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'user_id': self.user_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }

    @classmethod
    def get_view_count(cls, publication_id):
        """
        Get total view count for a publication

        Args:
            publication_id (int): ID of the publication

        Returns:
            int: Total number of views
        """
        return cls.query.filter_by(publication_id=publication_id).count()

    @classmethod
    def track_view(cls, publication_id, user_id=None, ip_address=None, user_agent=None):
        """
        Track a new view

        Args:
            publication_id (int): ID of the publication
            user_id (int, optional): ID of the user viewing (null for anonymous)
            ip_address (str, optional): IP address of the viewer
            user_agent (str, optional): Browser/client information

        Returns:
            PublicationViews: Created view record
        """
        view = cls(
            publication_id=publication_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        db.session.commit()
        return view


class FileDownloads(db.Model):
    """
    Track file downloads for analytics
    """
    __tablename__ = 'file_downloads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_file_id = db.Column(db.Integer, db.ForeignKey('publications_files.id'), nullable=True, index=True)
    publication_document_id = db.Column(db.Integer, db.ForeignKey('publication_documents.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    publication_file = db.relationship('PublicationFiles', backref=db.backref('downloads', lazy='dynamic'))
    publication_document = db.relationship('PublicationDocuments', backref=db.backref('downloads', lazy='dynamic'))
    user = db.relationship('UserAccount', backref=db.backref('downloaded_files', lazy='dynamic'))

    def __repr__(self):
        return f"<FileDownloads(id={self.id}, file_id={self.publication_file_id}, document_id={self.publication_document_id})>"

    def to_dict(self):
        """Serialize download record for JSON responses"""
        return {
            'id': self.id,
            'publication_file_id': self.publication_file_id,
            'publication_document_id': self.publication_document_id,
            'user_id': self.user_id,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }

    @classmethod
    def get_download_count(cls, publication_id):
        """
        Get total download count for all files in a publication

        Args:
            publication_id (int): ID of the publication

        Returns:
            int: Total number of downloads
        """
        file_downloads_count = db.session.query(cls).join(
            PublicationFiles, cls.publication_file_id == PublicationFiles.id
        ).filter(PublicationFiles.publication_id == publication_id).count()

        document_downloads_count = db.session.query(cls).join(
            PublicationDocuments, cls.publication_document_id == PublicationDocuments.id
        ).filter(PublicationDocuments.publication_id == publication_id).count()

        return file_downloads_count + document_downloads_count

    @classmethod
    def track_download(cls, file_id=None, document_id=None, user_id=None, ip_address=None):
        """
        Track a new download

        Args:
            file_id (int, optional): ID of the publication file
            document_id (int, optional): ID of the publication document
            user_id (int, optional): ID of the user downloading (null for anonymous)
            ip_address (str, optional): IP address of the downloader

        Returns:
            FileDownloads: Created download record
        """
        download = cls(
            publication_file_id=file_id,
            publication_document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.session.add(download)
        db.session.commit()
        return download


class RinggoldInstitution(db.Model):
    """
    Local cache of Ringgold institution data for African institutions.
    Enables fast local searches without API calls.
    Data sourced from Ringgold data export for African countries.
    """
    __tablename__ = 'ringgold_institutions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ringgold_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False, index=True)
    country = db.Column(db.String(100), nullable=False, index=True)
    city = db.Column(db.String(200), nullable=True)
    post_code = db.Column(db.String(50), nullable=True)
    administrative_area_level_1 = db.Column(db.String(200), nullable=True)
    administrative_area_level_2 = db.Column(db.String(200), nullable=True)
    administrative_area_level_3 = db.Column(db.String(200), nullable=True)
    isni = db.Column(db.String(20), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RinggoldInstitution(ringgold_id={self.ringgold_id}, name='{self.name}', country='{self.country}')>"

    def to_dict(self):
        """Serialize institution for JSON responses (matching Ringgold API format)"""
        return {
            'ringgold_id': self.ringgold_id,
            'name': self.name,
            'country': self.country,
            'locality': self.city,
            'city': self.city,
            'post_code': self.post_code,
            'admin_area_level_1': self.administrative_area_level_1,
            'admin_area_level_2': self.administrative_area_level_2,
            'admin_area_level_3': self.administrative_area_level_3,
            'country_code': self.get_country_code(),
            'ISNI': self.isni
        }

    def get_country_code(self):
        """Convert country name to ISO 2-letter code"""
        country_codes = {
            'South Africa': 'ZA', 'Nigeria': 'NG', 'Egypt': 'EG', 'Kenya': 'KE',
            'Algeria': 'DZ', 'Uganda': 'UG', 'Ghana': 'GH', 'Ethiopia': 'ET',
            'Morocco': 'MA', 'Tanzania, United Republic of': 'TZ', 'Tunisia': 'TN',
            'Zimbabwe': 'ZW', 'Cameroon': 'CM', 'Zambia': 'ZM', 'Botswana': 'BW',
            'Rwanda': 'RW', 'Sudan': 'SD', 'Mauritius': 'MU', 'Mozambique': 'MZ',
            'Malawi': 'MW', 'Senegal': 'SN', 'Namibia': 'NA', 'Libya': 'LY',
            'Reunion': 'RE', 'Congo, Democratic Republic of the': 'CD',
            'Burkina Faso': 'BF', "Cote d'Ivoire": 'CI', 'Angola': 'AO',
            'Madagascar': 'MG', 'Benin': 'BJ', 'Somalia': 'SO', 'Lesotho': 'LS',
            'Eswatini': 'SZ', 'Sierra Leone': 'SL', 'Togo': 'TG', 'Mali': 'ML',
            'Liberia': 'LR', 'South Sudan': 'SS', 'Seychelles': 'SC', 'Guinea': 'GN',
            'Burundi': 'BI', 'Gabon': 'GA', 'Gambia': 'GM', 'Eritrea': 'ER',
            'Mauritania': 'MR', 'Niger': 'NE', 'Cape Verde': 'CV', 'Chad': 'TD',
            'Djibouti': 'DJ', 'Congo, Republic of the': 'CG',
            'Central African Republic': 'CF', 'Guinea-Bissau': 'GW', 'Comoros': 'KM',
            'Saint Helena, Ascension and Tristan da Cunha': 'SH', 'Mayotte': 'YT',
            'Equatorial Guinea': 'GQ', 'Sao Tome and Principe': 'ST'
        }
        return country_codes.get(self.country, '')

    @classmethod
    def search(cls, query, country=None, limit=20, offset=0):
        """
        Search institutions by name with optional country filter

        Args:
            query (str): Search query for institution name
            country (str, optional): Country name or code to filter by
            limit (int): Maximum results to return
            offset (int): Offset for pagination

        Returns:
            tuple: (list of institutions, total count)
        """
        search_filter = cls.name.ilike(f'%{query}%')

        if country:
            # Support both country name and country code
            country_upper = country.strip().upper()
            if len(country_upper) == 2:
                # It's a country code, convert to name
                code_to_country = {v: k for k, v in {
                    'South Africa': 'ZA', 'Nigeria': 'NG', 'Egypt': 'EG', 'Kenya': 'KE',
                    'Algeria': 'DZ', 'Uganda': 'UG', 'Ghana': 'GH', 'Ethiopia': 'ET',
                    'Morocco': 'MA', 'Tanzania, United Republic of': 'TZ', 'Tunisia': 'TN',
                    'Zimbabwe': 'ZW', 'Cameroon': 'CM', 'Zambia': 'ZM', 'Botswana': 'BW',
                    'Rwanda': 'RW', 'Sudan': 'SD', 'Mauritius': 'MU', 'Mozambique': 'MZ',
                    'Malawi': 'MW', 'Senegal': 'SN', 'Namibia': 'NA', 'Libya': 'LY',
                    'Reunion': 'RE', 'Congo, Democratic Republic of the': 'CD',
                    'Burkina Faso': 'BF', "Cote d'Ivoire": 'CI', 'Angola': 'AO',
                    'Madagascar': 'MG', 'Benin': 'BJ', 'Somalia': 'SO', 'Lesotho': 'LS',
                    'Eswatini': 'SZ', 'Sierra Leone': 'SL', 'Togo': 'TG', 'Mali': 'ML',
                    'Liberia': 'LR', 'South Sudan': 'SS', 'Seychelles': 'SC', 'Guinea': 'GN',
                    'Burundi': 'BI', 'Gabon': 'GA', 'Gambia': 'GM', 'Eritrea': 'ER',
                    'Mauritania': 'MR', 'Niger': 'NE', 'Cape Verde': 'CV', 'Chad': 'TD',
                    'Djibouti': 'DJ', 'Congo, Republic of the': 'CG',
                    'Central African Republic': 'CF', 'Guinea-Bissau': 'GW', 'Comoros': 'KM',
                    'Saint Helena, Ascension and Tristan da Cunha': 'SH', 'Mayotte': 'YT',
                    'Equatorial Guinea': 'GQ', 'Sao Tome and Principe': 'ST'
                }.items()}
                country_name = code_to_country.get(country_upper)
                if country_name:
                    search_filter = db.and_(search_filter, cls.country == country_name)
            else:
                # It's a country name
                search_filter = db.and_(search_filter, cls.country.ilike(f'%{country}%'))

        total = cls.query.filter(search_filter).count()
        institutions = cls.query.filter(search_filter).offset(offset).limit(limit).all()

        return institutions, total

    @classmethod
    def get_by_ringgold_id(cls, ringgold_id):
        """Get institution by Ringgold ID"""
        return cls.query.filter_by(ringgold_id=ringgold_id).first()

    @classmethod
    def get_by_isni(cls, isni):
        """Get institution by ISNI"""
        clean_isni = ''.join(filter(str.isdigit, str(isni)))
        return cls.query.filter_by(isni=clean_isni).first()


class DSpaceMapping(db.Model):
    """
    Tracks mapping between DSpace items and DOCiD publications for integration
    """
    __tablename__ = 'dspace_mappings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # DSpace identifiers
    dspace_handle = db.Column(db.String(255), unique=True, nullable=False, index=True)
    dspace_uuid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    dspace_url = db.Column(db.String(500))  # Full DSpace instance URL

    # DOCiD reference
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Sync tracking
    sync_status = db.Column(db.String(50), default='synced')  # synced, pending, error, conflict
    last_sync_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Change detection (for incremental sync - skip unchanged items)
    dspace_metadata_hash = db.Column(db.String(64), index=True)  # MD5 hash of DSpace metadata
    docid_metadata_hash = db.Column(db.String(64))   # MD5 hash of DOCiD metadata

    # Error tracking
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)

    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    publication = db.relationship('Publications', backref=db.backref('dspace_mapping', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<DSpaceMapping {self.dspace_handle} -> Publication {self.publication_id}>'

    def to_dict(self):
        """Serialize DSpace mapping for JSON responses"""
        return {
            'id': self.id,
            'dspace_handle': self.dspace_handle,
            'dspace_uuid': self.dspace_uuid,
            'dspace_url': self.dspace_url,
            'publication_id': self.publication_id,
            'sync_status': self.sync_status,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ==============================================================================
# Local Contexts Integration Models
# Per DocID_Local_Contexts_Tech_Documentation.md Section 5
# ==============================================================================

class LocalContextType:
    """Context type constants for Local Contexts labels and notices"""
    TK_LABEL = 'TK_LABEL'      # Traditional Knowledge Label
    BC_LABEL = 'BC_LABEL'      # Biocultural Label
    NOTICE = 'NOTICE'          # Notice (e.g., Open to Collaborate, Attribution)
    
    VALID_TYPES = [TK_LABEL, BC_LABEL, NOTICE]
    
    @classmethod
    def is_valid(cls, context_type):
        return context_type in cls.VALID_TYPES


class LocalContext(db.Model):
    """
    Cached Local Contexts labels and notices from Local Contexts Hub.
    
    DocID stores references + cached metadata only.
    All authoritative label data remains external.
    
    Per Section 5.1: doc_local_contexts table
    """
    __tablename__ = 'local_contexts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    external_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    context_type = db.Column(db.String(50), nullable=False)  # TK_LABEL, BC_LABEL, NOTICE
    
    # Cached metadata (verbatim from Local Contexts Hub)
    title = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    community_name = db.Column(db.String(255), nullable=True)
    source_url = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)  # Label/Notice icon URL
    
    # Status tracking
    is_active = db.Column(db.Boolean, default=True)  # False if deleted from Hub
    is_authoritative = db.Column(db.Boolean, default=False)
    needs_review = db.Column(db.Boolean, default=False)  # Flag for admin review on mismatch
    
    # Sync tracking
    cached_at = db.Column(db.DateTime, nullable=True)
    last_sync_attempt = db.Column(db.DateTime, nullable=True)
    sync_error = db.Column(db.Text, nullable=True)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    publication_contexts = db.relationship('PublicationLocalContext', back_populates='local_context', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<LocalContext {self.external_id} ({self.context_type})>'

    def serialize(self):
        """Serialize for JSON responses"""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'context_type': self.context_type,
            'title': self.title,
            'summary': self.summary,
            'community_name': self.community_name,
            'source_url': self.source_url,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'is_authoritative': self.is_authoritative,
            'needs_review': self.needs_review,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_by_external_id(cls, external_id):
        """Get cached context by external ID"""
        return cls.query.filter_by(external_id=external_id).first()

    @classmethod
    def get_or_create(cls, external_id, context_type, **kwargs):
        """Get existing or create new cached context"""
        context = cls.get_by_external_id(external_id)
        if context:
            return context, False
        
        if not LocalContextType.is_valid(context_type):
            raise ValueError(f"Invalid context_type: {context_type}. Must be one of {LocalContextType.VALID_TYPES}")
        
        context = cls(external_id=external_id, context_type=context_type, **kwargs)
        db.session.add(context)
        return context, True


class PublicationLocalContext(db.Model):
    """
    Links publications to Local Contexts labels/notices.
    
    Per Section 5.1: doc_documents_local_contexts table
    """
    __tablename__ = 'publication_local_contexts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id', ondelete='CASCADE'), nullable=False, index=True)
    local_context_id = db.Column(db.Integer, db.ForeignKey('local_contexts.id', ondelete='CASCADE'), nullable=False, index=True)
    project_external_id = db.Column(db.String(255), nullable=True, index=True)

    display_order = db.Column(db.Integer, default=0)
    attached_at = db.Column(db.DateTime, default=datetime.utcnow)
    attached_by = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True)

    # Relationships
    publication = db.relationship('Publications', backref=db.backref('local_contexts', cascade='all, delete-orphan'))
    local_context = db.relationship('LocalContext', back_populates='publication_contexts')
    user = db.relationship('UserAccount', foreign_keys=[attached_by])

    # Two partial unique indexes — the same item can be attached under different
    # projects but never duplicated within the same project (or as a legacy
    # NULL-project attachment).
    __table_args__ = (
        db.Index(
            'uq_plc_item_no_project',
            'publication_id', 'local_context_id',
            unique=True,
            postgresql_where=db.text('project_external_id IS NULL'),
        ),
        db.Index(
            'uq_plc_item_with_project',
            'publication_id', 'local_context_id', 'project_external_id',
            unique=True,
            postgresql_where=db.text('project_external_id IS NOT NULL'),
        ),
    )

    def __repr__(self):
        return f'<PublicationLocalContext pub={self.publication_id} context={self.local_context_id} project={self.project_external_id}>'

    def serialize(self):
        """Serialize for JSON responses"""
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'project_external_id': self.project_external_id,
            'local_context': self.local_context.serialize() if self.local_context else None,
            'display_order': self.display_order,
            'attached_at': self.attached_at.isoformat() if self.attached_at else None,
            'attached_by': self.attached_by
        }


class LocalContextAuditLog(db.Model):
    """
    Audit log for Local Contexts attach/detach operations.
    
    Per Section 11: Log all attach/detach operations
    """
    __tablename__ = 'local_context_audit_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # What happened
    action = db.Column(db.String(50), nullable=False)  # ATTACH, DETACH, SYNC, MARK_INACTIVE
    
    # References
    publication_id = db.Column(db.Integer, nullable=True, index=True)
    local_context_id = db.Column(db.Integer, nullable=True, index=True)
    external_id = db.Column(db.String(255), nullable=True)
    
    # Who did it
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True)
    
    # Details
    details = db.Column(db.Text, nullable=True)  # JSON with additional info
    ip_address = db.Column(db.String(45), nullable=True)
    
    # When
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('UserAccount', foreign_keys=[user_id])

    def __repr__(self):
        return f'<LocalContextAuditLog {self.action} at {self.created_at}>'

    def serialize(self):
        return {
            'id': self.id,
            'action': self.action,
            'publication_id': self.publication_id,
            'local_context_id': self.local_context_id,
            'external_id': self.external_id,
            'user_id': self.user_id,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def log(cls, action, publication_id=None, local_context_id=None, external_id=None,
            user_id=None, details=None, ip_address=None):
        """Create an audit log entry"""
        import json
        log_entry = cls(
            action=action,
            publication_id=publication_id,
            local_context_id=local_context_id,
            external_id=external_id,
            user_id=user_id,
            details=json.dumps(details) if isinstance(details, dict) else details,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        return log_entry


# ==============================================================================
# RRID (Research Resource Identifier) Integration Model
# Dedicated association table for RRID attachments to publications and organizations
# ==============================================================================

class DocidRrid(db.Model):
    """
    RRID (Research Resource Identifier) attachment model.

    Links RRIDs to publications and organizations via polymorphic entity_type/entity_id.
    No SQLAlchemy relationship() declarations — polymorphic entity_id prevents clean FK
    relationships. Query by ID using class methods instead.
    """
    ALLOWED_ENTITY_TYPES = frozenset({'publication', 'organization', 'document'})

    __tablename__ = 'docid_rrids'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(50), nullable=False)  # 'publication' or 'organization'
    entity_id = db.Column(db.Integer, nullable=False)  # matches publications.id or publication_organizations.id
    rrid = db.Column(db.String(50), nullable=False)  # RRID curie format e.g. RRID:SCR_012345
    rrid_name = db.Column(db.String(500), nullable=True)  # facility/resource name from SciCrunch
    rrid_description = db.Column(db.Text, nullable=True)  # resource description
    rrid_resource_type = db.Column(db.String(100), nullable=True)  # e.g. 'core facility', 'software'
    rrid_url = db.Column(db.String(500), nullable=True)  # resource URL
    resolved_json = db.Column(JSON_DOCUMENT, nullable=True)  # cached resolver metadata (normalized subset only)
    last_resolved_at = db.Column(db.DateTime, nullable=True)  # when resolver cache was last refreshed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'rrid', name='uq_docid_rrids_entity_rrid'),
        db.Index('ix_docid_rrids_entity_lookup', 'entity_type', 'entity_id'),
    )

    def __repr__(self):
        return f"<DocidRrid(id={self.id}, entity={self.entity_type}:{self.entity_id}, rrid='{self.rrid}')>"

    def serialize(self):
        """Serialize RRID record for JSON responses"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'rrid': self.rrid,
            'rrid_name': self.rrid_name,
            'rrid_description': self.rrid_description,
            'rrid_resource_type': self.rrid_resource_type,
            'rrid_url': self.rrid_url,
            'resolved_json': self.resolved_json,
            'last_resolved_at': self.last_resolved_at.isoformat() if self.last_resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_rrids_for_entity(cls, entity_type, entity_id):
        """
        Get all RRIDs attached to a specific entity.

        Args:
            entity_type (str): 'publication' or 'organization'
            entity_id (int): ID of the entity

        Returns:
            list: List of DocidRrid instances ordered by created_at descending
        """
        return cls.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_rrid(cls, rrid_value):
        """
        Look up a record by RRID curie value.

        Args:
            rrid_value (str): RRID curie e.g. 'RRID:SCR_012345'

        Returns:
            DocidRrid or None: First matching record
        """
        return cls.query.filter_by(rrid=rrid_value).first()


class PublicationEnrichment(db.Model):
    """
    Tracks per-publication, per-source enrichment status for idempotency.
    Each record represents one enrichment attempt from a specific source.
    """
    __tablename__ = 'publication_enrichments'
    __table_args__ = (
        db.UniqueConstraint('publication_id', 'source_name', name='uq_publication_source_enrichment'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id', ondelete='CASCADE'), nullable=False, index=True)
    source_name = db.Column(db.String(50), nullable=False, index=True)  # openalex|unpaywall|semantic_scholar|openaire
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending|enriched|not_found|error|skipped
    enriched_at = db.Column(db.DateTime, nullable=True)
    raw_response = db.Column(JSON_DOCUMENT, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    review_status = db.Column(db.String(20), nullable=True, index=True)  # accepted|pending_review|rejected|NULL
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publication = db.relationship('Publications', backref=db.backref('enrichments', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<PublicationEnrichment(id={self.id}, pub={self.publication_id}, source='{self.source_name}', status='{self.status}')>"

    def serialize(self):
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'source_name': self.source_name,
            'status': self.status,
            'enriched_at': self.enriched_at.isoformat() if self.enriched_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class EnrichmentRun(db.Model):
    """
    Tracks each cron execution of the enrichment/harvest pipeline for auditability and resumability.
    """
    __tablename__ = 'enrichment_runs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    run_type = db.Column(db.String(50), nullable=False, index=True)  # harvest|enrich
    source_name = db.Column(db.String(50), nullable=False, index=True)  # openalex|unpaywall|semantic_scholar|openaire|dspace|figshare|ojs
    status = db.Column(db.String(20), nullable=False, default='running')  # running|completed|failed|interrupted
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    publications_processed = db.Column(db.Integer, default=0)
    publications_enriched = db.Column(db.Integer, default=0)
    publications_skipped = db.Column(db.Integer, default=0)
    publications_failed = db.Column(db.Integer, default=0)
    error_summary = db.Column(db.Text, nullable=True)
    last_processed_publication_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<EnrichmentRun(id={self.id}, type='{self.run_type}', source='{self.source_name}', status='{self.status}')>"

    def serialize(self):
        return {
            'id': self.id,
            'run_type': self.run_type,
            'source_name': self.source_name,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'publications_processed': self.publications_processed,
            'publications_enriched': self.publications_enriched,
            'publications_skipped': self.publications_skipped,
            'publications_failed': self.publications_failed,
            'error_summary': self.error_summary,
        }


class HarvestSource(db.Model):
    """
    Stores connection details for institutional repository sources.
    Each university/repository has its own entry with DSpace version,
    API type, authentication credentials (encrypted), and harvest schedule.
    """
    __tablename__ = 'harvest_sources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    ui_base_url = db.Column(db.String(500), nullable=True)  # UI URL when different from API (e.g. ir.unilag.edu.ng vs api-ir.unilag.edu.ng)
    dspace_version = db.Column(db.String(20), nullable=True)
    api_type = db.Column(db.String(20), nullable=False)  # legacy|modern|figshare|ojs
    auth_required = db.Column(db.Boolean, default=False)
    encrypted_username = db.Column(db.Text, nullable=True)
    encrypted_password = db.Column(db.Text, nullable=True)
    owner_name = db.Column(db.String(255), nullable=False)
    owner_email = db.Column(db.String(255), nullable=True, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id', ondelete='SET NULL'), nullable=True, index=True)
    harvest_frequency = db.Column(db.String(20), default='weekly')  # daily|weekly|biweekly|monthly
    is_active = db.Column(db.Boolean, default=True)
    last_harvested_at = db.Column(db.DateTime, nullable=True)
    total_items_synced = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    owner_user = relationship('UserAccount', foreign_keys=[owner_user_id])
    field_mappings = relationship(
        'HarvestSourceFieldMapping',
        back_populates='source',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<HarvestSource(id={self.id}, name='{self.name}', api_type='{self.api_type}')>"

    def resolve_owner(self):
        """Look up owner_user_id from owner_email (case-insensitive).

        Sets self.owner_user_id when a matching UserAccount exists and returns it.
        Called automatically by the before_insert/before_update event below and
        defensively at the start of each harvest run.
        """
        if not self.owner_email:
            return self.owner_user_id
        user = UserAccount.query.filter(
            db.func.lower(UserAccount.email) == self.owner_email.lower()
        ).first()
        if user:
            self.owner_user_id = user.user_id
        return self.owner_user_id

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'base_url': self.base_url,
            'ui_base_url': self.ui_base_url,
            'dspace_version': self.dspace_version,
            'api_type': self.api_type,
            'auth_required': self.auth_required,
            'owner_name': self.owner_name,
            'owner_email': self.owner_email,
            'owner_user_id': self.owner_user_id,
            'harvest_frequency': self.harvest_frequency,
            'is_active': self.is_active,
            'last_harvested_at': self.last_harvested_at.isoformat() if self.last_harvested_at else None,
            'total_items_synced': self.total_items_synced,
        }


@event.listens_for(HarvestSource, 'before_insert')
@event.listens_for(HarvestSource, 'before_update')
def _harvest_source_resolve_owner(mapper, connection, target):
    """Auto-resolve owner_user_id from owner_email on any insert/update."""
    if target.owner_email and not target.owner_user_id:
        result = connection.execute(
            db.text("SELECT user_id FROM user_accounts WHERE LOWER(email) = LOWER(:e) LIMIT 1"),
            {"e": target.owner_email},
        ).first()
        if result:
            target.owner_user_id = result[0]


class HarvestSourceFieldMapping(db.Model):
    """
    Per-source metadata field mappings. Maps DOCiD fields to DSpace/repository
    metadata fields. Priority determines which source field is tried first
    when multiple fields can provide the same DOCiD field value.
    """
    __tablename__ = 'harvest_source_field_mappings'
    __table_args__ = (
        db.UniqueConstraint('harvest_source_id', 'docid_field', 'source_field',
                            name='uq_source_docid_field_mapping'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    harvest_source_id = db.Column(
        db.Integer,
        db.ForeignKey('harvest_sources.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    docid_field = db.Column(db.String(100), nullable=False)   # doi, document_title, etc.
    source_field = db.Column(db.String(200), nullable=False)  # dc.identifier.other, dc.title, etc.
    priority = db.Column(db.Integer, default=0)               # higher = tried first

    source = relationship('HarvestSource', back_populates='field_mappings')

    def __repr__(self):
        return f"<FieldMapping(source_id={self.harvest_source_id}, {self.docid_field} <- {self.source_field}, pri={self.priority})>"


class PublicationExternalEdge(db.Model):
    """
    A typed edge from a DOCiD publication to an external identifier.
    Covers citations (cites / cited_by), patent family membership, and
    scholar-to-patent links via a single unified table.
    relation values: 'cites' | 'cited_by' | 'patent_family_member'
                     | 'patent_cites_paper' | 'paper_cited_by_patent'
    object_id_kind:  'doi' | 'patent_number' | 'lens_patent_id'
                     | 'oclc' | 'isbn' | 'arxiv_id'
    source_name:     'opencitations' | 'semantic_scholar' | 'lens_org'
    """
    __tablename__ = 'publication_external_edges'
    __table_args__ = (
        db.UniqueConstraint(
            'publication_id', 'relation', 'object_id_kind', 'object_id', 'source_name',
            name='uq_publication_external_edge',
        ),
        db.Index('ix_publication_external_edges_object', 'object_id_kind', 'object_id'),
        db.Index('ix_publication_external_edges_relation', 'publication_id', 'relation'),
    )

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_id = db.Column(
        db.Integer,
        db.ForeignKey('publications.id', ondelete='CASCADE'),
        nullable=False,
    )
    object_id_kind = db.Column(db.String(20), nullable=False)
    object_id      = db.Column(db.String(255), nullable=False)
    object_label   = db.Column(db.String(500), nullable=True)
    relation       = db.Column(db.String(40), nullable=False)
    source_name    = db.Column(db.String(50), nullable=False)
    confidence     = db.Column(db.String(20), nullable=True)
    raw_metadata   = db.Column(JSON_DOCUMENT, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publication = db.relationship('Publications', backref=db.backref('external_edges', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<PublicationExternalEdge(pub={self.publication_id}, {self.relation}, {self.object_id_kind}:{self.object_id}, src={self.source_name})>"

    def serialize(self):
        return {
            'id': self.id,
            'publication_id': self.publication_id,
            'object_id_kind': self.object_id_kind,
            'object_id': self.object_id,
            'object_label': self.object_label,
            'relation': self.relation,
            'source_name': self.source_name,
            'confidence': self.confidence,
            'raw_metadata': self.raw_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HarvestState(db.Model):
    """
    Per-endpoint OAI-PMH harvest state. Tracks checkpoints and concurrency.
    The COALESCE-based unique index (endpoint, metadata_prefix, COALESCE(set_spec,''))
    is created in the alembic migration because SQLAlchemy declarative does not
    support expression-based unique indexes.
    in_progress is set atomically via a conditional UPDATE so parallel workers
    cannot both claim the lock.
    """
    __tablename__ = 'harvest_state'
    __table_args__ = (
        db.Index('ix_harvest_state_endpoint', 'endpoint'),
    )

    id                    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    endpoint              = db.Column(db.String(500), nullable=False)
    metadata_prefix       = db.Column(db.String(50), nullable=False)
    set_spec              = db.Column(db.String(255), nullable=True)
    granularity           = db.Column(db.String(40), nullable=True)
    last_success_from     = db.Column(db.DateTime, nullable=True)
    last_success_until    = db.Column(db.DateTime, nullable=True)
    last_resumption_token = db.Column(db.String(500), nullable=True)
    in_progress           = db.Column(db.Boolean, default=False, nullable=False)
    in_progress_since     = db.Column(db.DateTime, nullable=True)
    last_run_at           = db.Column(db.DateTime, nullable=True)
    last_run_status       = db.Column(db.String(20), nullable=True)
    last_error_message    = db.Column(db.Text, nullable=True)
    consecutive_failures  = db.Column(db.Integer, default=0)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at            = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HarvestState(id={self.id}, endpoint='{self.endpoint}', prefix='{self.metadata_prefix}', in_progress={self.in_progress})>"

    def serialize(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'metadata_prefix': self.metadata_prefix,
            'set_spec': self.set_spec,
            'last_success_from': self.last_success_from.isoformat() if self.last_success_from else None,
            'last_success_until': self.last_success_until.isoformat() if self.last_success_until else None,
            'in_progress': self.in_progress,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'consecutive_failures': self.consecutive_failures,
        }


class HarvestStagingRecord(db.Model):
    """
    Staging table for OAI-PMH harvested records awaiting DOCiD matching.
    Unmatched records sit in status='unmatched' until a curator reviews them.
    The (endpoint, oai_identifier) unique constraint makes replays idempotent.
    """
    __tablename__ = 'harvest_staging_records'
    __table_args__ = (
        db.UniqueConstraint('endpoint', 'oai_identifier', name='uq_harvest_staging_endpoint_id'),
        db.Index('ix_harvest_staging_status', 'status'),
        db.Index('ix_harvest_staging_oai_datestamp', 'oai_datestamp'),
    )

    id                     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    endpoint               = db.Column(db.String(500), nullable=False)
    oai_identifier         = db.Column(db.String(255), nullable=False)
    oai_datestamp          = db.Column(db.DateTime, nullable=False)
    is_deleted             = db.Column(db.Boolean, default=False, nullable=False)
    raw_xml                = db.Column(db.Text, nullable=True)
    normalised             = db.Column(JSON_DOCUMENT, nullable=True)
    matched_publication_id = db.Column(
        db.Integer,
        db.ForeignKey('publications.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    match_method           = db.Column(db.String(50), nullable=True)
    status                 = db.Column(db.String(20), default='new', nullable=False)
    retry_count            = db.Column(db.Integer, default=0)
    last_error_message     = db.Column(db.Text, nullable=True)
    created_at             = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at             = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matched_publication = db.relationship('Publications', foreign_keys=[matched_publication_id])

    def __repr__(self):
        return f"<HarvestStagingRecord(id={self.id}, oai='{self.oai_identifier}', status='{self.status}')>"

    def serialize(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'oai_identifier': self.oai_identifier,
            'oai_datestamp': self.oai_datestamp.isoformat() if self.oai_datestamp else None,
            'is_deleted': self.is_deleted,
            'matched_publication_id': self.matched_publication_id,
            'match_method': self.match_method,
            'status': self.status,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
