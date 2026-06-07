"""
Tests for DedupFilter — run with: pytest tests/test_dedup.py -v
"""
import pytest
from datetime import datetime
from agents.watcher import CircularDoc
from agents.dedup import DedupFilter, InMemoryDedupStore, DedupResult


def make_doc(url="https://rbi.org.in/circular/1", title="Test Circular", regulator="RBI"):
    return CircularDoc(
        url=url, title=title, regulator=regulator,
        published_at=datetime.utcnow(), raw_text="Some circular text here...", source="rss"
    )


@pytest.fixture
def dedup():
    return DedupFilter(store=InMemoryDedupStore())


class TestUrlHashDedup:
    def test_first_doc_not_duplicate(self, dedup):
        doc = make_doc()
        assert dedup.check(doc).is_duplicate is False

    def test_same_url_is_duplicate_after_mark(self, dedup):
        doc = make_doc()
        dedup.mark_seen(doc)
        result = dedup.check(doc)
        assert result.is_duplicate is True
        assert result.reason == "url_hash"

    def test_different_url_not_duplicate(self, dedup):
        doc1 = make_doc(url="https://rbi.org.in/1", title="KYC Master Direction")
        doc2 = make_doc(url="https://rbi.org.in/2", title="FEMA Regulations Update")
        dedup.mark_seen(doc1)
        assert dedup.check(doc2).is_duplicate is False


class TestTitleHashDedup:
    def test_same_title_different_url_is_duplicate(self, dedup):
        doc1 = make_doc(url="https://rbi.org.in/1", title="KYC Master Direction Update")
        doc2 = make_doc(url="https://rbi.org.in/2", title="KYC Master Direction Update")
        dedup.mark_seen(doc1)
        result = dedup.check(doc2)
        assert result.is_duplicate is True
        assert result.reason == "title_hash"

    def test_title_normalization_strips_circular_number(self, dedup):
        doc1 = make_doc(url="https://rbi.org.in/1", title="RBI/2023-24/83 KYC Norms")
        doc2 = make_doc(url="https://rbi.org.in/2", title="RBI/2024-25/83 KYC Norms")
        dedup.mark_seen(doc1)
        # Different year in circular number — should still be caught as duplicate
        result = dedup.check(doc2)
        assert result.is_duplicate is True

    def test_different_titles_not_duplicate(self, dedup):
        doc1 = make_doc(url="https://rbi.org.in/1", title="KYC Master Direction")
        doc2 = make_doc(url="https://rbi.org.in/2", title="FEMA Regulations Update")
        dedup.mark_seen(doc1)
        assert dedup.check(doc2).is_duplicate is False


class TestBatchFilter:
    def test_intra_batch_dedup(self, dedup):
        # Two docs with same URL in same batch (two feeds emitting same circular)
        doc = make_doc(url="https://rbi.org.in/1")
        docs = [doc, doc]
        unique = dedup.filter_batch(docs)
        assert len(unique) == 1

    def test_batch_vs_existing(self, dedup):
        existing = make_doc(url="https://rbi.org.in/1", title="KYC Master Direction")
        dedup.mark_seen(existing)

        new_docs = [
            make_doc(url="https://rbi.org.in/1", title="KYC Master Direction"),  # duplicate
            make_doc(url="https://rbi.org.in/2", title="FEMA Regulations Update"),  # new
        ]
        unique = dedup.filter_batch(new_docs)
        assert len(unique) == 1
        assert unique[0].url == "https://rbi.org.in/2"

    def test_empty_batch(self, dedup):
        assert dedup.filter_batch([]) == []
