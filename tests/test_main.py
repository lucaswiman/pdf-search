import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import os
from app.main import app

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def sample_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Page 1
    c.drawString(100, 750, "This is page one with some unique content")
    c.showPage()
    
    # Page 2
    c.drawString(100, 750, "Page two contains searchable text about FastAPI")
    c.showPage()
    
    # Page 3
    c.drawString(100, 750, "The final page talks about PostgreSQL databases")
    c.showPage()
    
    c.save()
    return buffer.getvalue()

def test_pdf_upload_and_search(test_client, sample_pdf):
    # Upload the PDF
    response = test_client.post(
        "/upload/",
        files={"file": ("test.pdf", sample_pdf, "application/pdf")}
    )
    assert response.status_code == 200
    assert response.json()["pages_processed"] == 3
    
    # Test search functionality
    search_terms = [
        ("FastAPI", 1),  # Should find one page
        ("PostgreSQL", 1),  # Should find one page
        ("unique", 1),  # Should find one page
        ("nonexistent", 0),  # Should find no pages
    ]
    
    for term, expected_count in search_terms:
        response = test_client.get(f"/search/{term}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == expected_count
        
        if expected_count > 0:
            # Verify the content contains our search term
            assert any(term.lower() in page["content"].lower() for page in results)
    
    # Test getting all pages of the document
    response = test_client.get("/document/test.pdf")
    assert response.status_code == 200
    assert len(response.json()) == 3
