"""A publication's files and documents always load in the order they were added.

Postgres returns an UPDATEd row after the untouched ones when a query has no
ORDER BY, so after editing one file the edit page showed a different file in
that spot. SQLite (used here) doesn't reorder rows, so the reorder itself
can't be reproduced in this suite; these tests pin the ORDER BY that prevents it.
"""

from sqlalchemy.dialects import postgresql

from app import db
from app.models import PublicationDocuments, PublicationFiles, Publications


def _compiled_edit_page_query():
    query = Publications.query.options(
        db.joinedload(Publications.publications_files),
        db.joinedload(Publications.publication_documents),
    ).filter_by(id=1)
    return str(query.statement.compile(dialect=postgresql.dialect()))


def test_files_load_in_id_order():
    order_by = Publications.publications_files.property.order_by
    assert [column.key for column in order_by] == ["id"]
    assert order_by[0].table is PublicationFiles.__table__


def test_documents_load_in_id_order():
    order_by = Publications.publication_documents.property.order_by
    assert [column.key for column in order_by] == ["id"]
    assert order_by[0].table is PublicationDocuments.__table__


def test_the_edit_page_query_sends_the_order_to_postgres():
    sql = _compiled_edit_page_query()
    assert "ORDER BY publications_files_1.id, publication_documents_1.id" in sql
