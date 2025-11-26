"""
Agent service layer.

Contains all business logic for Excel upload, dynamic table creation, and RAG query processing.
"""

# Standard library imports
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Third-party imports
import pandas as pd
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local application imports
from database.models import SessionLocal, ExcelUploads, engine
from dotenv import load_dotenv

# Load environment variables
# Try loading from Backend directory first, then root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to default location

# Gemini API configuration
GEMINI_KEY = os.getenv("GEMINI_KEY")
if GEMINI_KEY:
    # Remove quotes if present
    GEMINI_KEY = GEMINI_KEY.strip().strip('"').strip("'")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        print(f"[DEBUG] Gemini API configured successfully")
    else:
        print(f"[DEBUG] GEMINI_KEY is empty after stripping")
else:
    print(f"[DEBUG] GEMINI_KEY not found in environment variables")


def _sanitize_table_name(name: str) -> str:
    """
    Sanitize table name to be valid SQL identifier.
    
    Args:
        name: Original name
    
    Returns:
        str: Sanitized table name
    """
    # Remove special characters, keep only alphanumeric and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'tbl_' + sanitized
    # Limit length
    if len(sanitized) > 64:
        sanitized = sanitized[:64]
    return sanitized.lower()


def _sanitize_column_name(name: str) -> str:
    """
    Sanitize column name to be valid SQL identifier.
    
    Args:
        name: Original column name
    
    Returns:
        str: Sanitized column name
    """
    # Remove special characters, keep only alphanumeric and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'col_' + sanitized
    # Limit length
    if len(sanitized) > 64:
        sanitized = sanitized[:64]
    return sanitized.lower()


def _create_dynamic_table(db: Session, table_name: str, columns: List[str]) -> bool:
    """
    Create a dynamic SQL table with specified columns.
    
    Args:
        db: Database session
        table_name: Name of the table to create
        columns: List of column names from Excel
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Sanitize column names
        sanitized_columns = [_sanitize_column_name(col) for col in columns]
        
        # Build CREATE TABLE SQL
        # Add id column first, then all Excel columns as TEXT/VARCHAR
        column_defs = ["id VARCHAR(36) PRIMARY KEY"]
        
        for col in sanitized_columns:
            # Use TEXT for flexibility (can store long strings)
            column_defs.append(f"`{col}` TEXT")
        
        # Add timestamps
        column_defs.append("created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        column_defs.append("updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {', '.join(column_defs)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        db.execute(text(create_sql))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating table: {str(e)}")
        return False


def _insert_excel_data(db: Session, table_name: str, df: pd.DataFrame, columns: List[str]) -> int:
    """
    Insert Excel data into the dynamic table.
    
    Args:
        db: Database session
        table_name: Name of the table
        df: Pandas DataFrame with Excel data
        columns: List of original column names
    
    Returns:
        int: Number of rows inserted
    """
    try:
        import uuid
        
        rows_inserted = 0
        sanitized_columns = [_sanitize_column_name(col) for col in columns]
        
        for _, row in df.iterrows():
            # Generate UUID for id
            record_id = str(uuid.uuid4())
            
            # Build column list for INSERT
            col_names = ['id'] + sanitized_columns
            col_names_str = ', '.join([f"`{col}`" for col in col_names])
            
            # Build values
            values = [f"'{record_id}'"]
            for col in columns:
                value = row[col]
                # Handle different data types
                if pd.isna(value):
                    values.append("NULL")
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    values.append(f"'{value.isoformat()}'")
                elif isinstance(value, (int, float)):
                    values.append(f"'{str(value)}'")
                else:
                    # Escape single quotes in strings
                    escaped_value = str(value).replace("'", "''")
                    values.append(f"'{escaped_value}'")
            
            values_str = ', '.join(values)
            
            # Insert row
            insert_sql = f"""
            INSERT INTO `{table_name}` ({col_names_str})
            VALUES ({values_str})
            """
            
            db.execute(text(insert_sql))
            rows_inserted += 1
        
        db.commit()
        return rows_inserted
    except Exception as e:
        db.rollback()
        print(f"Error inserting data: {str(e)}")
        raise


def upload_excel_service(file_content: bytes, filename: str, user_id: str) -> dict:
    """
    Upload and process Excel file, creating dynamic table and storing data.
    
    Args:
        file_content: Excel file content as bytes
        filename: Original filename
        user_id: User ID from JWT token (for data isolation)
    
    Returns:
        dict: Standardized response with upload statistics
    """
    db: Session = SessionLocal()
    try:
        # Read Excel file
        import io
        excel_file = io.BytesIO(file_content)
        
        # Read Excel into pandas DataFrame
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        if df.empty:
            return {
                "status": False,
                "message": "Excel file is empty",
                "data": None
            }
        
        # Get column names from Excel
        columns = df.columns.tolist()
        
        if not columns:
            return {
                "status": False,
                "message": "Excel file has no columns",
                "data": None
            }
        
        # Generate table name from filename and timestamp
        base_name = Path(filename).stem  # filename without extension
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"excel_{_sanitize_table_name(base_name)}_{timestamp}"
        
        # Create dynamic table
        table_created = _create_dynamic_table(db, table_name, columns)
        
        if not table_created:
            return {
                "status": False,
                "message": "Failed to create database table",
                "data": None
            }
        
        # Insert all rows
        rows_inserted = _insert_excel_data(db, table_name, df, columns)
        
        # Store metadata in excel_uploads table with user_id
        upload_record = ExcelUploads(
            user_id=user_id,
            filename=filename,
            table_name=table_name,
            columns=columns,
            row_count=rows_inserted,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(upload_record)
        db.commit()
        
        return {
            "status": True,
            "message": f"Successfully uploaded and stored {rows_inserted} rows",
            "data": {
                "table_name": table_name,
                "rows_processed": len(df),
                "rows_stored": rows_inserted,
                "columns": columns
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": f"Error processing Excel file: {str(e)}",
            "data": None
        }
    finally:
        db.close()


def _get_latest_table_name(db: Session, user_id: str) -> Optional[str]:
    """
    Get the table name of the most recently uploaded Excel file for a specific user.
    
    Args:
        db: Database session
        user_id: User ID to filter uploads
    
    Returns:
        str: Table name or None if no uploads exist for this user
    """
    try:
        latest_upload = db.query(ExcelUploads).filter(
            ExcelUploads.user_id == user_id
        ).order_by(ExcelUploads.created_at.desc()).first()
        if latest_upload:
            return latest_upload.table_name
        return None
    except:
        return None


def _get_table_schema(db: Session, table_name: str) -> str:
    """
    Get the schema of a specific table for SQL generation.
    
    Args:
        db: Database session
        table_name: Name of the table
    
    Returns:
        str: Table schema description
    """
    try:
        # Get table columns using SQLAlchemy inspector
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        
        schema = f"Table: {table_name}\nColumns:\n"
        for col in columns:
            col_name = col['name']
            col_type = str(col['type'])
            schema += f"- {col_name} ({col_type})\n"
        
        # Get sample row if available
        sample_query = f"SELECT * FROM `{table_name}` LIMIT 1"
        result = db.execute(text(sample_query))
        sample_row = result.fetchone()
        
        if sample_row:
            schema += f"\nSample row columns: {', '.join(sample_row.keys())}"
        
        return schema
    except Exception as e:
        return f"Table: {table_name}\n(Error getting schema: {str(e)})"


def _generate_sql_query(natural_query: str, table_schema: str, table_name: str) -> Optional[str]:
    """
    Use Gemini to generate SQL query from natural language.
    
    Args:
        natural_query: Natural language query
        table_schema: Table schema description
        table_name: Name of the table to query
    
    Returns:
        str: Generated SQL query or None if failed
    """
    # Re-check GEMINI_KEY in case it wasn't loaded at module import time
    current_key = os.getenv("GEMINI_KEY")
    if current_key:
        current_key = current_key.strip().strip('"').strip("'")
    
    # Use current_key if GEMINI_KEY is not set
    api_key = GEMINI_KEY if GEMINI_KEY else current_key
    
    if not api_key:
        print("[DEBUG] GEMINI_KEY is None or empty")
        print(f"[DEBUG] GEMINI_KEY module var: {GEMINI_KEY}")
        print(f"[DEBUG] current_key from env: {current_key}")
        return None
    
    # Configure if not already configured or if using different key
    if api_key != GEMINI_KEY or not GEMINI_KEY:
        try:
            genai.configure(api_key=api_key)
            print(f"[DEBUG] Gemini API configured with key (length: {len(api_key)})")
        except Exception as e:
            print(f"[ERROR] Failed to configure Gemini API: {str(e)}")
            return None
    
    try:
        # Try newer models first, then fallback to older ones
        model = None
        model_names = [
            'gemini-2.5-flash',      # Latest stable flash model
            'gemini-flash-latest',    # Latest flash (auto-updates)
            'gemini-2.0-flash',       # Gemini 2.0 flash
            'gemini-pro-latest',      # Latest pro (auto-updates)
            'gemini-pro'              # Fallback to older model
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"[DEBUG] Using model: {model_name}")
                break
            except Exception as e:
                print(f"[DEBUG] Model {model_name} failed: {str(e)}")
                continue
        
        if not model:
            raise Exception("No available Gemini model found")
        
        prompt = f"""You are an expert SQL query generator for MySQL. Convert natural language queries into valid MySQL SELECT statements.

TABLE SCHEMA:
{table_schema}

TABLE NAME: {table_name}

USER QUERY: {natural_query}

REQUIREMENTS:
1. Generate ONLY a valid MySQL SELECT query - no explanations, no markdown, just SQL
2. Use the exact table name: `{table_name}` (with backticks)
3. Use exact column names from the schema (with backticks if needed)
4. Use appropriate WHERE clauses for filtering based on query intent
5. Use ORDER BY for sorting if query asks for top/best/highest/lowest
6. Use LIMIT clause for top N results (default to reasonable limit if not specified)
7. Handle NULL values appropriately with IS NULL or IS NOT NULL
8. Use proper string matching with LIKE for partial matches
9. For text searches, use: `column_name` LIKE '%value%'
10. For exact matches, use: `column_name` = 'value'

MATHEMATICAL & AGGREGATION OPERATIONS:
- For sums: SELECT SUM(CAST(`column` AS DECIMAL(10,2))) FROM ...
- For averages: SELECT AVG(CAST(`column` AS DECIMAL(10,2))) FROM ...
- For counts: SELECT COUNT(*) FROM ... or SELECT COUNT(DISTINCT `column`) FROM ...
- For maximum: SELECT MAX(CAST(`column` AS DECIMAL(10,2))) FROM ...
- For minimum: SELECT MIN(CAST(`column` AS DECIMAL(10,2))) FROM ...
- For grouping: Use GROUP BY `column` with aggregations
- For calculations: Use arithmetic operators (+, -, *, /) in SELECT
- For percentages: (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ...)) AS percentage
- For comparisons: Use CASE WHEN for conditional logic
- For date calculations: Use DATE functions (DATEDIFF, DATE_ADD, etc.)
- For string operations: Use CONCAT, SUBSTRING, LENGTH, etc.

COMPLEX QUERY PATTERNS:
- Multiple conditions: Use AND/OR in WHERE clause
- Subqueries: Use (SELECT ...) for nested queries
- Joins: If multiple tables needed (though typically single table)
- Window functions: Use ROW_NUMBER(), RANK(), etc. if needed
- Having clause: Use HAVING for filtering aggregated results

EXAMPLES:
- "Find records with name John" → SELECT * FROM `{table_name}` WHERE `name` LIKE '%John%'
- "Get top 10 records" → SELECT * FROM `{table_name}` ORDER BY created_at DESC LIMIT 10
- "Show all records where status is active" → SELECT * FROM `{table_name}` WHERE `status` = 'active'
- "What is the total salary?" → SELECT SUM(CAST(`salary` AS DECIMAL(10,2))) AS total_salary FROM `{table_name}`
- "Average salary by department" → SELECT `department`, AVG(CAST(`salary` AS DECIMAL(10,2))) AS avg_salary FROM `{table_name}` GROUP BY `department`
- "Count of records where age > 30" → SELECT COUNT(*) AS count FROM `{table_name}` WHERE CAST(`age` AS UNSIGNED) > 30
- "Show top 5 highest salaries" → SELECT * FROM `{table_name}` ORDER BY CAST(`salary` AS DECIMAL(10,2)) DESC LIMIT 5
- "Percentage of active records" → SELECT (COUNT(CASE WHEN `status` = 'active' THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM `{table_name}`

IMPORTANT: Since columns are stored as TEXT, always CAST numeric columns when doing math operations:
- CAST(`column_name` AS DECIMAL(10,2)) for decimals
- CAST(`column_name` AS UNSIGNED) for integers
- CAST(`column_name` AS SIGNED) for signed integers

Generate the SQL query now:"""
        
        response = model.generate_content(prompt)
        
        # Check if response has content
        if not response or not hasattr(response, 'text') or not response.text:
            print("[ERROR] Empty response from Gemini API")
            return None
            
        sql_query = response.text.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
        if sql_query.startswith("```sql"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
        
        return sql_query
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Error generating SQL query: {error_msg}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        # Check if it's an API key error
        if "API key" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
            print(f"[ERROR] Gemini API authentication failed. Please check your GEMINI_KEY.")
        return None


def _execute_sql_query(db: Session, sql_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Execute SQL query and return results.
    
    Args:
        db: Database session
        sql_query: SQL query to execute
        top_k: Maximum number of results
    
    Returns:
        List[Dict]: Query results
    """
    try:
        # Add LIMIT if not present and query doesn't have it
        sql_lower = sql_query.lower().strip()
        if 'limit' not in sql_lower:
            sql_query = f"{sql_query.rstrip(';')} LIMIT {top_k}"
        
        # Execute query
        result = db.execute(text(sql_query))
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for key, value in row._mapping.items():
                # Convert non-serializable types
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif hasattr(value, '__dict__'):
                    row_dict[key] = str(value)
                else:
                    row_dict[key] = value
            results.append(row_dict)
        
        return results[:top_k]
    except Exception as e:
        print(f"Error executing SQL: {str(e)}")
        return []


def _perform_calculations(results: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """
    Perform additional calculations on results if needed.
    
    Args:
        results: Query results
        query: Original query (to detect calculation needs)
    
    Returns:
        dict: Additional calculated values or None
    """
    if not results:
        return None
    
    calculations = {}
    query_lower = query.lower()
    
    try:
        # If results contain aggregated values, extract them
        for row in results:
            for key, value in row.items():
                if any(term in key.lower() for term in ['sum', 'total', 'avg', 'average', 'count', 'max', 'min', 'percentage']):
                    if value is not None:
                        calculations[key] = value
        
        # If query asks for percentage but not in results, calculate
        if 'percentage' in query_lower or '%' in query_lower:
            if len(results) > 0:
                # Try to find numerator and denominator
                for row in results:
                    for key, value in row.items():
                        if 'count' in key.lower() or 'total' in key.lower():
                            calculations[key] = value
    except:
        pass
    
    return calculations if calculations else None


def _generate_natural_answer(query: str, results: List[Dict[str, Any]], table_schema: str) -> str:
    """
    Use Gemini to generate natural language answer from query results.
    
    Args:
        query: Original natural language query
        results: Retrieved data rows
        table_schema: Table schema description
    
    Returns:
        str: Natural language answer
    """
    # Re-check GEMINI_KEY in case it wasn't loaded at module import time
    current_key = os.getenv("GEMINI_KEY")
    if current_key:
        current_key = current_key.strip().strip('"').strip("'")
    
    api_key = GEMINI_KEY if GEMINI_KEY else current_key
    if not api_key:
        return "Results retrieved, but Gemini API key not configured for natural language generation."
    
    # Configure if not already configured
    if api_key and not GEMINI_KEY:
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            return f"Error configuring Gemini API: {str(e)}"
    
    try:
        # Try newer models first, then fallback to older ones
        model = None
        model_names = [
            'gemini-2.5-flash',      # Latest stable flash model
            'gemini-flash-latest',    # Latest flash (auto-updates)
            'gemini-2.0-flash',       # Gemini 2.0 flash
            'gemini-pro-latest',      # Latest pro (auto-updates)
            'gemini-pro'              # Fallback to older model
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"[DEBUG] Using model for answer: {model_name}")
                break
            except Exception as e:
                print(f"[DEBUG] Model {model_name} failed: {str(e)}")
                continue
        
        if not model:
            raise Exception("No available Gemini model found for answer generation")
        
        # Format results for prompt
        results_str = json.dumps(results, indent=2, default=str) if results else "[]"
        
        # Get column information from results if available
        column_info = ""
        if results and len(results) > 0:
            sample_row = results[0]
            columns = list(sample_row.keys())
            column_info = f"\nAvailable columns in results: {', '.join(columns)}"
        
        # Perform additional calculations if needed
        calculations = _perform_calculations(results, query)
        calculations_info = ""
        if calculations:
            calculations_info = f"\n\nCalculated/Aggregated Values: {json.dumps(calculations, indent=2, default=str)}"
        
        prompt = f"""You are a table-aware assistant specialized in analyzing structured Excel data and performing complex calculations.

CONTEXT:
- You are analyzing data retrieved from a database query
- Each row represents a record from an uploaded Excel file
- The data is stored exactly as it appeared in the Excel file
- You must answer based ONLY on the provided data rows
- You can perform mathematical operations and calculations on the data

TABLE STRUCTURE:
{table_schema}
{column_info}

USER QUERY:
{query}

RETRIEVED DATA ROWS ({len(results)} rows):
{results_str}
{calculations_info}

STRICT RULES:
1. Understand the table structure - identify what each column represents
2. Identify relevant rows based on the user query - match query intent to data fields
3. Answer STRICTLY from the retrieved rows only - no external knowledge
4. If the answer is not present in any row, explicitly state "Not found in dataset"
5. NEVER hallucinate, guess, or infer beyond what is in the table data
6. If query asks for specific values, extract them exactly as they appear
7. If query asks for counts/summaries, calculate from the provided rows
8. If multiple rows match, provide a clear summary or list
9. Use natural, conversational language in your response
10. Present data clearly and accurately

MATHEMATICAL & COMPLEX QUERIES:
- For aggregations (SUM, AVG, COUNT, MAX, MIN): The SQL query already calculated these, present the results clearly
- For calculations: Perform arithmetic operations on numeric values from the data
- For percentages: Calculate percentages when requested (e.g., "What percentage of X is Y?")
- For comparisons: Compare values and explain differences
- For trends: Identify patterns, increases, decreases, or trends in the data
- For statistics: Provide statistical insights (mean, median, range, etc.) when applicable
- For conditional logic: Apply IF-THEN logic when analyzing data
- For date calculations: Calculate date differences, durations, or date-based comparisons
- For ratios and proportions: Calculate ratios, proportions, or relative values
- For rankings: Identify top/bottom items, order by criteria

RESPONSE FORMAT:
- Start with a direct answer to the query
- If it's a mathematical query, show the calculation or result clearly
- If applicable, mention how many rows matched or were analyzed
- Provide specific values, numbers, or details from the data
- For aggregations, clearly state the aggregated value
- For comparisons, explain the differences
- Be concise but complete
- Use appropriate units or formatting for numbers (e.g., currency, percentages)

EXAMPLES OF GOOD RESPONSES:
- "The total salary is $150,000" (for SUM queries)
- "The average age is 35.5 years" (for AVG queries)
- "There are 25 active records out of 100 total (25%)" (for COUNT and percentage)
- "Department A has the highest average salary at $75,000, followed by Department B at $65,000" (for GROUP BY with comparisons)
- "The salary increased by 15% from the previous period" (for trend analysis)

Answer:"""
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        return answer
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def query_service(query: str, top_k: int = 5, user_id: str = None) -> dict:
    """
    Process natural language query using RAG system.
    
    Args:
        query: Natural language query
        top_k: Number of top results to retrieve
    
    Returns:
        dict: Standardized response with answer and results
    """
    db: Session = SessionLocal()
    try:
        if not query or not query.strip():
            return {
                "status": False,
                "message": "Query cannot be empty",
                "data": None
            }
        
        # Validate user_id
        if not user_id:
            return {
                "status": False,
                "message": "User authentication required",
                "data": None
            }
        
        # Get the latest uploaded table for this user
        table_name = _get_latest_table_name(db, user_id)
        
        if not table_name:
            return {
                "status": False,
                "message": "No Excel file has been uploaded yet. Please upload an Excel file first.",
                "data": None
            }
        
        # Get table schema
        table_schema = _get_table_schema(db, table_name)
        
        # Generate SQL query using Gemini
        sql_query = _generate_sql_query(query, table_schema, table_name)
        
        if not sql_query:
            # Check if GEMINI_KEY exists
            if not GEMINI_KEY:
                error_msg = "GEMINI_KEY not found in environment variables. Please set GEMINI_KEY in your .env file."
            else:
                error_msg = "Failed to generate SQL query. Please check Gemini API configuration and ensure your API key is valid."
            return {
                "status": False,
                "message": error_msg,
                "data": None
            }
        
        # Execute SQL query
        results = _execute_sql_query(db, sql_query, top_k)
        
        # Generate natural language answer
        answer = _generate_natural_answer(query, results, table_schema)
        
        return {
            "status": True,
            "message": "Query processed successfully",
            "data": {
                "answer": answer,
                "results": results if results else None,
                "sql_query": sql_query,
                "table_name": table_name
            }
        }
    except Exception as e:
        return {
            "status": False,
            "message": f"Error processing query: {str(e)}",
            "data": None
        }
    finally:
        db.close()
