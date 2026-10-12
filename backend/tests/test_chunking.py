import pytest
from app.services.ingestion import IngestionService

def test_markdown_chunking_preserves_headings():
    service = IngestionService(chunk_size=50, overlap=10)
    sample_md = """# Parental Leave Policy
All full-time employees are eligible for up to 16 weeks of fully paid parental leave.
This applies to birth parents, adoptive parents, and foster placements.

# Expense Reimbursement
All business expenses over $50 require prior manager approval.
Receipts must be submitted within 30 days of the expense date via the employee portal.
"""
    chunks, page_count = service.process_file("test.md", sample_md.encode("utf-8"))
    
    assert len(chunks) >= 2
    assert page_count == 1
    headings = [c.section_heading for c in chunks]
    assert "Parental Leave Policy" in headings
    assert "Expense Reimbursement" in headings
    assert any("16 weeks" in c.text for c in chunks)
    assert any("$50" in c.text for c in chunks)

def test_token_overlap():
    service = IngestionService(chunk_size=20, overlap=5)
    text = " ".join([f"Word{i}" for i in range(100)])
    chunks, _ = service.process_file("test.txt", text.encode("utf-8"))
    
    assert len(chunks) > 1
    # Check that adjacent chunks have word overlap
    chunk0_words = chunks[0].text.split()
    chunk1_words = chunks[1].text.split()
    overlap = set(chunk0_words[-5:]).intersection(set(chunk1_words[:10]))
    assert len(overlap) > 0
