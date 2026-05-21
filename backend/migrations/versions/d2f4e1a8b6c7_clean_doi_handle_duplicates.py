"""clean publications.doi where it's a verbatim copy of document_docid + reverse pub 4185 contamination

Revision ID: d2f4e1a8b6c7
Revises: c3e9b2a17d40
Create Date: 2026-05-21 12:40:00.000000

Background:
- assign-docid was writing the generated DOCiD Handle (20.500.14351/...) into
  Publications.doi. The doi column should hold real CrossRef/DataCite DOIs
  (10.xxxx/...) only. The Handle already lives in document_docid.
- WHERE doi LIKE '20.%' protects Figshare imports that legitimately store a
  real CrossRef DOI in both columns (intentional conflation documented in
  app/routes/figshare.py).
- Additionally undoes the title-search false-positive enrichment that was
  manually accepted onto publication 4185 (JMIR Telehealth paper data).
  Guarded by openalex_id='W2765304416' so re-running this migration on prod
  or KENET where pub 4185 may be a different record (or absent) is a no-op.
"""

from alembic import op


revision = 'd2f4e1a8b6c7'
# Merges two heads that forked off a9f2c1d4e7b8:
#   * b1d4e7f9a2c5_add_curator_review_state_to_publication_enrichments
#   * c3e9b2a17d40_ensure_local_context_audit_log_exists
down_revision = ('c3e9b2a17d40', 'b1d4e7f9a2c5')
branch_labels = None
depends_on = None


def upgrade():
    # Part A: NULL doi where it duplicates the DOCiD Handle.
    op.execute("""
        UPDATE publications
        SET doi = NULL
        WHERE doi IS NOT NULL
          AND doi = document_docid
          AND doi LIKE '20.%'
    """)

    # Part B: Reverse the JMIR title-search false-positive on pub 4185.
    # Targeted by (id, openalex_id) so re-running is safe on other DBs.
    op.execute("""
        UPDATE publications
        SET citation_count = NULL,
            openalex_id = NULL,
            openalex_topics = NULL,
            open_access_status = NULL,
            open_access_url = NULL,
            abstract_text = NULL
        WHERE id = 4185
          AND openalex_id = 'W2765304416'
    """)
    op.execute("""
        DELETE FROM publication_enrichments
        WHERE publication_id = 4185
          AND source_name = 'openalex'
    """)


def downgrade():
    # Irreversible by design: the upgrade only NULLs values that were verbatim
    # duplicates of document_docid, and pub 4185's prior state cannot be
    # reconstructed from the JMIR data we're removing. If rollback is required,
    # restore from a pre-deploy publications-table snapshot.
    pass
