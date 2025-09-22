INSERT INTO publications (
    id,
    user_id,
    document_docid,
    document_title,
    document_description,
    avatar,
    owner,
    timestamp,
    resource_type_id,
    publication_poster_url,
    doi,
    published
) VALUES
(
    2,                                     -- id (optional if auto-increment)
    2,                                  -- user_id (ForeignKey to user_accounts.user_id)
    '20.500.14351/834ce32a04333cd91d4b',                   -- document_docid (unique DocID for the publication)
    'Sample Document Title',               -- document_title
    'This is a sample document description for testing.', -- document_description
    'https://example.com/avatar.png',      -- avatar (URL or path to the avatar)
    'John Doe',                            -- owner (owner of the publication)
    EXTRACT(EPOCH FROM NOW()),             -- timestamp (current UNIX timestamp)
    1,                                     -- resource_type_id (ForeignKey to resource_types.id)
    'https://example.com/poster.png',      -- publication_poster_url (URL to the poster)
    '20.500.14351/834ce32a04333cd91d4b',                      -- doi (unique DOI for the publication)
    NOW()                                  -- published (current datetime)
);
