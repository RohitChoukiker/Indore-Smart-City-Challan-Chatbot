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


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str = Field(..., description="Natural language answer")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Retrieved data rows")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    table_name: Optional[str] = Field(None, description="Name of the table queried")


class UploadResponse(BaseModel):
    """Response model for Excel upload."""
    table_name: str = Field(..., description="Name of the created database table")
    rows_processed: int = Field(..., description="Number of rows processed")
    rows_stored: int = Field(..., description="Number of rows stored in database")
    columns: List[str] = Field(..., description="List of column names found in Excel")

