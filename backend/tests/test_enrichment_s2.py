"""Semantic Scholar batch enrichment must be DOI-only.

Guards the fix that removed the title-search fallback: title matching applied the
first search hit directly, which could write the WRONG paper's citation count /
abstract onto a DOCiD and would run S2 against every DOI-less record (flooding the
1 req/s rate limit).
"""
from types import SimpleNamespace

import pytest

from enrich_metadata import enrich_with_semantic_scholar, SOURCE_REGISTRY


class _NoTitleSearchClient:
    """Fails loudly if the batch ever falls back to title search."""

    def __init__(self, paper_by_doi=None):
        self._paper_by_doi = paper_by_doi

    def get_paper_by_doi(self, doi):
        return self._paper_by_doi

    def search_papers_by_title(self, title):  # pragma: no cover - must NOT be called
        raise AssertionError("Batch S2 must be DOI-only; title search must not run")


class _Mapper:
    def extract_enrichment(self, paper):
        return {
            'citation_count': paper.get('citationCount'),
            'influential_citation_count': paper.get('influentialCitationCount'),
            'semantic_scholar_id': paper.get('paperId'),
            'abstract': paper.get('abstract'),
        }


def _pub(doi=None, title="Some Title"):
    return SimpleNamespace(
        doi=doi, document_title=title,
        citation_count=None, influential_citation_count=None,
        semantic_scholar_id=None, abstract_text=None,
    )


def test_s2_registered_as_doi_only():
    assert SOURCE_REGISTRY['semantic_scholar']['require_doi'] is True


def test_s2_no_doi_is_skipped_without_title_search():
    status, reason, raw = enrich_with_semantic_scholar(_pub(doi=None), _NoTitleSearchClient(), _Mapper())
    assert status == 'skipped'
    assert reason == 'no_valid_doi'
    assert raw is None


def test_s2_doi_present_but_no_match_is_not_found():
    client = _NoTitleSearchClient(paper_by_doi=None)
    status, reason, raw = enrich_with_semantic_scholar(_pub(doi='10.1/x'), client, _Mapper())
    assert status == 'not_found'


def test_s2_doi_match_enriches_and_writes_fields():
    paper = {'paperId': 'abc', 'citationCount': 42, 'influentialCitationCount': 5, 'abstract': 'A.'}
    pub = _pub(doi='10.1/x')
    status, reason, raw = enrich_with_semantic_scholar(pub, _NoTitleSearchClient(paper_by_doi=paper), _Mapper())
    assert status == 'enriched'
    assert pub.semantic_scholar_id == 'abc'
    assert pub.citation_count == 42
    assert pub.abstract_text == 'A.'
