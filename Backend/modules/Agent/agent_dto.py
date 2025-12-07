"""
Agent DTOs (Data Transfer Objects).

Pydantic models for request/response validation in agent endpoints.
"""

# Standard library imports
from typing import Optional, Dict, Any, List

# Third-party imports
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str = Field(..., description="Natural language query about the data")
    top_k: Optional[int] = Field(5, ge=1, le=50, description="Number of top results to retrieve")
    mode: Optional[str] = Field("text", description="Response mode: 'text', 'graph', or 'table'")
    table_name: Optional[str] = Field(None, description="Optional: Specific table name to query. If not provided, uses latest uploaded file.")


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str = Field(..., description="Natural language answer")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Retrieved data rows")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    table_name: Optional[str] = Field(None, description="Name of the table queried")
    mode: Optional[str] = Field(None, description="Response mode used: 'text', 'graph', or 'table'")
    visualization_data: Optional[Dict[str, Any]] = Field(None, description="Structured data for graph visualization (graph mode only)")
    table_data: Optional[Dict[str, Any]] = Field(None, description="Structured table data (table mode only)")


class UploadResponse(BaseModel):
    """Response model for Excel upload."""
    table_name: str = Field(..., description="Name of the created database table")
    rows_processed: int = Field(..., description="Number of rows processed")
    rows_stored: int = Field(..., description="Number of rows stored in database")
    columns: List[str] = Field(..., description="List of column names found in Excel")


class FileInfo(BaseModel):
    """Model for file information."""
    id: str = Field(..., description="File upload record ID")
    filename: str = Field(..., description="Original filename")
    table_name: str = Field(..., description="Database table name")
    columns: List[str] = Field(..., description="List of columns in the file")
    row_count: int = Field(..., description="Number of rows in the file")
    created_at: str = Field(..., description="Upload timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileInfo] = Field(..., description="List of uploaded files")
    total_count: int = Field(..., description="Total number of files")

