from fastapi import FastAPI, File, UploadFile, HTTPException, StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Optional, List
import os
from PyPDF2 import PdfReader
from sqlalchemy import text, Column, Index
from sqlalchemy.dialects.postgresql import TSVECTOR

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pdf_search")
engine = create_engine(DATABASE_URL)

# Models
class PDFPage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_name: str
    page_number: int
    content: str
    
    # Add SQLAlchemy Column for the TSVECTOR and GIN index
    __table_args__ = (
        Index(
            'idx_page_content_gin',
            text('to_tsvector(\'english\', content)'),
            postgresql_using='gin'
        ),
    )
    
# Create FastAPI app
app = FastAPI(title="PDF Search Service")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Create database tables
SQLModel.metadata.create_all(engine)

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read the PDF file
    contents = await file.read()
    pdf_pages = []
    
    try:
        # Create a temporary file to handle the PDF
        with open("temp.pdf", "wb") as temp_file:
            temp_file.write(contents)
        
        # Parse PDF
        reader = PdfReader("temp.pdf")
        
        # Extract text from each page
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            pdf_page = PDFPage(
                document_name=file.filename,
                page_number=page_num,
                content=text
            )
            pdf_pages.append(pdf_page)
        
        # Store in database
        with Session(engine) as session:
            for page in pdf_pages:
                session.add(page)
            session.commit()
        
        return {
            "message": "PDF uploaded successfully",
            "pages_processed": len(pdf_pages),
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")

@app.get("/search/{query}")
async def search_pdfs(query: str):
    with Session(engine) as session:
        # Use PostgreSQL full-text search with GIN index
        statement = text("""
            SELECT id, document_name, page_number, content
            FROM pdfpage
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) DESC
        """).bindparams(query=query)
        result = session.execute(statement)
        return list(result)

@app.get("/document/{document_name}")
async def get_document_pages(document_name: str) -> List[PDFPage]:
    with Session(engine) as session:
        statement = select(PDFPage).where(PDFPage.document_name == document_name).order_by(PDFPage.page_number)
        return list(session.exec(statement))
