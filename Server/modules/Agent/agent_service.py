import sys
import os
import json
import re
import decimal

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from database.models import SessionLocal, ExcelUploads, engine
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


GEMINI_KEY = os.getenv("GEMINI_KEY")
if GEMINI_KEY:
    GEMINI_KEY = GEMINI_KEY.strip().strip('"').strip("'")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        print(f"[DEBUG] Gemini API configured successfully")
    else:
        print(f"[DEBUG] GEMINI_KEY is empty after stripping")
else:
    print(f"[DEBUG] GEMINI_KEY not found in environment variables")



REQUIRED_COLUMNS = [
    "Circle",
    "Challan Number",
    "Challan Source",
    "Vehicle Number",
    "Challan Date",
    "Challan Place",
    "Latitude Longitude",   
    "Violator Name",
    "Violator Address",
    "Violator Contact",
    "Owner Name",
    "Challan Status",
    "Challan Amount",
    "Vehicle Class",
    "Send To Court Date",
    "Court Name",
    "Offences"
]


def _sanitize_table_name(name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    sanitized = sanitized.strip('_')
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'tbl_' + sanitized
    if len(sanitized) > 64:
        sanitized = sanitized[:64]
    return sanitized.lower()


def _sanitize_column_name(name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    sanitized = sanitized.strip('_')
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'col_' + sanitized
    if len(sanitized) > 64:
        sanitized = sanitized[:64]
    return sanitized.lower()



def _build_column_map(df_columns: List[str]) -> Dict[str, str]:
   
    normalised = {col.strip().lower(): col for col in df_columns}

    col_map: Dict[str, str] = {}
    for req in REQUIRED_COLUMNS:
        key = req.strip().lower()
        if key in normalised:
            col_map[req] = normalised[key] 
        else:
            print(f"[WARNING] Required column not found in file: '{req}'")

    return col_map


def _preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select only the 17 required columns from the dataframe.
    Uses case-insensitive fuzzy matching so that small differences
    in the uploaded file (e.g. extra spaces, different casing) still work.
    """
    col_map = _build_column_map(df.columns.tolist())

    if not col_map:
        print(f"[ERROR] No matching columns found. Available: {df.columns.tolist()}")
        return df  

    
    rename_map = {actual: canonical for canonical, actual in col_map.items()}
    df = df.rename(columns=rename_map)


    found_columns = list(col_map.keys())
    missing = [c for c in REQUIRED_COLUMNS if c not in found_columns]
    if missing:
        print(f"[WARNING] These required columns are missing from the file: {missing}")

    df_filtered = df[found_columns].copy()

    print(f"[INFO] Columns after preprocessing: {df_filtered.columns.tolist()}")
    print(f"[INFO] Rows after preprocessing: {len(df_filtered)}")
    return df_filtered


def _read_csv_with_preprocessing(file_content: bytes, skip_rows: int = 0) -> pd.DataFrame:
    import io

    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None

    for encoding in encodings:
        try:
            csv_file = io.BytesIO(file_content)
            df = pd.read_csv(
                csv_file,
                skiprows=skip_rows,
                header=0,
                encoding=encoding,
                on_bad_lines='skip',
                dtype=str,         
            )
            print(f"[INFO] CSV read successfully with encoding: {encoding}")
            print(f"[INFO] Raw columns: {df.columns.tolist()}")
            print(f"[INFO] Raw rows: {len(df)}")
            break
        except UnicodeDecodeError:
            print(f"[WARNING] Encoding {encoding} failed, trying next...")
            continue
        except Exception as e:
            print(f"[ERROR] CSV read failed with encoding {encoding}: {e}")
            continue

    if df is None:
        raise ValueError("Could not read CSV file with any known encoding.")

    
    df.columns = [str(c).strip() for c in df.columns]

    df = _preprocess_dataframe(df)
    return df



def _read_excel_with_preprocessing(file_content: bytes, file_ext: str) -> pd.DataFrame:
    import io

    excel_file = io.BytesIO(file_content)


    if file_ext == '.xlsx':
        engine_name = 'openpyxl'
    elif file_ext == '.xls':
        engine_name = 'xlrd'
    else:
        engine_name = None  

    try:
        df = pd.read_excel(excel_file, engine=engine_name, dtype=str)
    except Exception as e:
        print(f"[WARNING] Excel read with engine '{engine_name}' failed: {e}. Trying without engine hint.")
        excel_file.seek(0)
        df = pd.read_excel(excel_file, dtype=str)

  
    df.columns = [str(c).strip() for c in df.columns]

    print(f"[INFO] Excel raw columns: {df.columns.tolist()}")
    print(f"[INFO] Excel raw rows: {len(df)}")

    df = _preprocess_dataframe(df)
    return df


def _create_dynamic_table(db: Session, table_name: str, columns: List[str]) -> bool:
    try:
        sanitized_columns = [_sanitize_column_name(col) for col in columns]

        column_defs = ["id VARCHAR(36) PRIMARY KEY"]
        for col in sanitized_columns:
            column_defs.append(f'"{col}" TEXT')
        column_defs.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        column_defs.append('updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

        create_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {', '.join(column_defs)}
        )
        '''
        db.execute(text(create_sql))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating table: {str(e)}")
        return False


def _insert_excel_data(db: Session, table_name: str, df: pd.DataFrame, columns: List[str]) -> int:
    try:
        import uuid

        sanitized_columns = [_sanitize_column_name(col) for col in columns]
        
       
        df_copy = df.copy()
        df_copy.columns = sanitized_columns
        
        df_copy.insert(0, 'id', [str(uuid.uuid4()) for _ in range(len(df_copy))])
     
        df_copy = df_copy.where(pd.notna(df_copy), None)
        
     
        df_copy.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',  
            index=False,           
            chunksize=10000, 
            method='multi'        
        )
        
        print(f"[INFO] Successfully inserted {len(df_copy)} rows into {table_name}")
        return len(df_copy)

    except Exception as e:
        print(f"[ERROR] Insert failed: {str(e)}")
        raise



def upload_excel_service(file_content: bytes, filename: str, user_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        file_ext = Path(filename).suffix.lower()

        if file_ext == '.csv':
            df = _read_csv_with_preprocessing(file_content, skip_rows=0)
        elif file_ext in ['.xlsx', '.xls']:
            df = _read_excel_with_preprocessing(file_content, file_ext)
        else:
            return {
                "status": False,
                "message": f"Unsupported file format: {file_ext}. Only .xlsx, .xls, and .csv are supported.",
                "data": None
            }

        if df.empty:
            return {
                "status": False,
                "message": "File is empty after processing",
                "data": None
            }

        columns = df.columns.tolist()
        if not columns:
            return {
                "status": False,
                "message": "File has no columns after processing",
                "data": None
            }

        base_name = Path(filename).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"excel_{_sanitize_table_name(base_name)}_{timestamp}"

        table_created = _create_dynamic_table(db, table_name, columns)
        if not table_created:
            return {
                "status": False,
                "message": "Failed to create database table",
                "data": None
            }

        rows_inserted = _insert_excel_data(db, table_name, df, columns)

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
            "message": f"Error processing file: {str(e)}",
            "data": None
        }
    finally:
        db.close()


def _get_latest_table_name(db: Session, user_id: str) -> Optional[str]:
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
    try:
        db.rollback()  # ← ADD THIS - clear any failed transaction
        
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)

        schema = f"Table: {table_name}\n\nColumns and Data Types:\n"
        for col in columns:
            col_name = col['name']
            col_type = str(col['type'])
            if col_name not in ['id', 'created_at', 'updated_at']:
                schema += f"- {col_name} ({col_type})\n"

        sample_query = f'SELECT * FROM "{table_name}" LIMIT 3'
        result = db.execute(text(sample_query))
        sample_rows = result.fetchall()

        if sample_rows:
            schema += f"\nSample Data (showing {len(sample_rows)} rows):\n"
            for idx, row in enumerate(sample_rows, 1):
                schema += f"\nRow {idx}:\n"
                for key, value in row._mapping.items():
                    if key not in ['id', 'created_at', 'updated_at']:
                        display_value = str(value)
                        if len(display_value) > 100:
                            display_value = display_value[:100] + "..."
                        schema += f"  {key}: {display_value}\n"

        count_query = f'SELECT COUNT(*) as total_count FROM "{table_name}"'
        count_result = db.execute(text(count_query))
        total_count = count_result.fetchone()[0]
        schema += f"\nTotal Records: {total_count}\n"

        return schema
    except Exception as e:
        db.rollback()  # ← ADD THIS too
        return f"Table: {table_name}\n(Error getting schema: {str(e)})"

def _generate_sql_query(natural_query: str, table_schema: str, table_name: str) -> Optional[str]:
    current_key = os.getenv("GEMINI_KEY")
    if current_key:
        current_key = current_key.strip().strip('"').strip("'")

    api_key = GEMINI_KEY if GEMINI_KEY else current_key

    if not api_key:
        print("[DEBUG] GEMINI_KEY is None or empty")
        return None

    if api_key != GEMINI_KEY or not GEMINI_KEY:
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            print(f"[ERROR] Failed to configure Gemini API: {str(e)}")
            return None

    try:
        model = None
        model_names = [
            'gemini-2.5-flash',
            'gemini-flash-latest',
            'gemini-2.0-flash',
            'gemini-pro-latest',
            'gemini-pro'
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

        prompt = f"""You are an expert SQL query generator specialized in traffic challan and transportation data analysis. Convert natural language queries into precise, optimized PostgreSQL SELECT statements.

TABLE SCHEMA:
{table_schema}

TABLE NAME: `{table_name}`

USER QUERY: {natural_query}

CRITICAL REQUIREMENTS:
1. Generate ONLY valid PostgreSQL SELECT query - no explanations, no markdown, no code blocks, just pure SQL
2. Use exact table name: \"{table_name}\" (with backticks)
3. Use exact column names from schema (with backticks for safety)
4. Analyze query intent deeply - understand what the user REALLY wants
5. Handle complex multi-condition queries with proper AND/OR logic
6. For traffic challan data, recognize common patterns:
   - Amount/Challan Amount: numeric values for fines
   - Location fields: challan_place, latitude_longitude
   - Vehicle fields: vehicle_number, vehicle_class
   - Date/Time fields: challan_date, send_to_court_date

ADVANCED FILTERING & WHERE CLAUSES:
- Multiple conditions: Combine with AND/OR logically
- Partial matches: Use LIKE '%value%' (case-insensitive pattern matching)
- Exact matches: Use = 'value' for precise matching
- Numeric comparisons: Always CAST to DECIMAL for amounts
- Range queries: Use BETWEEN or >= AND <=
- NULL handling: Use IS NULL or IS NOT NULL

MATHEMATICAL & AGGREGATION OPERATIONS:
- Sums: SELECT SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total_amount FROM ...
- Averages: SELECT AVG(CAST(`challan_amount` AS DECIMAL(10,2))) AS avg_amount FROM ...
- Counts: SELECT COUNT(*) AS total_count FROM ...
- Maximum/Minimum: SELECT MAX(CAST(`challan_amount` AS DECIMAL(10,2))) AS max_amount FROM ...
- Grouping: Use GROUP BY with aggregations

SORTING & LIMITING:
- ORDER BY: Use for sorting
- LIMIT: Always include reasonable LIMIT (default 50 if not specified)
- For "top", "highest", "maximum": ORDER BY ... DESC LIMIT N

DATA TYPE HANDLING (CRITICAL):
Since all columns are stored as TEXT, ALWAYS CAST numeric columns:
- Amounts/Money: CAST(`challan_amount` AS DECIMAL(10,2))
- Counts/IDs: CAST(`column` AS UNSIGNED)

Generate the SQL query now (ONLY SQL, no explanations):"""

        response = model.generate_content(prompt)

        if not response or not hasattr(response, 'text') or not response.text:
            print("[ERROR] Empty response from Gemini API")
            return None

        sql_query = response.text.strip()

        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
        if sql_query.startswith("```sql"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query

        return sql_query
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg or 'quota' in error_msg.lower() or 'rate' in error_msg.lower():
            print(f"[WARNING] Gemini rate limit hit, retrying after 25s...")
            import time
            time.sleep(25)
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except:
                return None
        print(f"[ERROR] Error generating SQL query: {error_msg}")
        return None

def _execute_sql_query(db: Session, sql_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    try:
       
        db.rollback() 
        sql_query = sql_query.replace('`', '"')
        
        sql_lower = sql_query.lower().strip()

        is_aggregation = any(keyword in sql_lower for keyword in [
            'sum(', 'avg(', 'count(', 'max(', 'min(',
            'group by', 'having', 'percentage'
        ])

        if not is_aggregation and 'limit' not in sql_lower:
            sql_query = f"{sql_query.rstrip(';')} LIMIT {top_k * 2}"
        elif is_aggregation and 'limit' not in sql_lower:
            sql_query = f"{sql_query.rstrip(';')} LIMIT 100"

        print(f"[DEBUG] Executing SQL: {sql_query}")

        result = db.execute(text(sql_query))
        rows = result.fetchall()

        results = []
        for row in rows:
            row_dict = {}
            for key, value in row._mapping.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif hasattr(value, '__dict__'):
                    row_dict[key] = str(value)
                elif isinstance(value, (int, float)) and value is not None:
                    row_dict[key] = float(value) if isinstance(value, (float, decimal.Decimal)) else int(value)
                else:
                    row_dict[key] = value
            results.append(row_dict)

        if not is_aggregation:
            return results[:top_k]
        return results
    except Exception as e:
        print(f"[ERROR] executing SQL: {str(e)}")
        print(f"[ERROR] SQL Query: {sql_query}")
        return []

def _generate_visualization_data(results: List[Dict[str, Any]], query: str, sql_query: str) -> Optional[Dict[str, Any]]:
    if not results:
        return None

    try:
        sql_lower = sql_query.lower()
        results_lower = query.lower()

        chart_type = "bar_chart"

        if "group by" in sql_lower:
            first_row = results[0]
            keys = list(first_row.keys())

            if len(keys) >= 2:
                category_key = keys[0]
                value_key = keys[1]

                def get_row_value(row, key):
                    if key in row:
                        return row[key]
                    for k, v in row.items():
                        if k.lower() == key.lower():
                            return v
                    return None

                labels = []
                values = []

                for row in results:
                    label_val = get_row_value(row, category_key)
                    labels.append(str(label_val) if label_val is not None else '')

                    val = get_row_value(row, value_key)
                    numeric_val = 0
                    if val is None:
                        numeric_val = 0
                    elif isinstance(val, (int, float)):
                        numeric_val = float(val)
                    elif hasattr(val, '__float__'):
                        try:
                            numeric_val = float(val)
                        except:
                            numeric_val = 0
                    elif isinstance(val, str):
                        try:
                            cleaned = val.replace(',', '').replace('₹', '').replace('$', '').replace(' ', '').strip()
                            numeric_val = float(cleaned) if cleaned else 0
                        except:
                            numeric_val = 0
                    values.append(numeric_val)

                if "percentage" in sql_lower or "%" in results_lower:
                    chart_type = "pie_chart"
                elif "time" in category_key.lower() or "date" in category_key.lower():
                    chart_type = "line_chart"
                else:
                    chart_type = "bar_chart"

                if len(labels) > 0 and len(values) > 0 and any(v > 0 for v in values):
                    return {
                        "chart_type": chart_type,
                        "labels": labels,
                        "values": values,
                        "category_label": category_key.replace('_', ' ').title(),
                        "value_label": value_key.replace('_', ' ').title(),
                        "title": query[:100]
                    }
                return None

        elif any(keyword in sql_lower for keyword in ['sum(', 'avg(', 'count(', 'max(', 'min(']):
            first_row = results[0]
            keys = list(first_row.keys())
            if keys:
                value_key = keys[0]
                value = first_row.get(value_key, 0)
                if isinstance(value, (int, float)):
                    numeric_value = float(value)
                elif isinstance(value, str):
                    try:
                        numeric_value = float(value.replace(',', '').replace('₹', '').strip())
                    except:
                        numeric_value = 0
                else:
                    numeric_value = 0
                return {
                    "chart_type": "single_value",
                    "value": numeric_value,
                    "label": value_key.replace('_', ' ').title(),
                    "title": query[:100]
                }

        if len(results) > 0:
            first_row = results[0]
            keys = list(first_row.keys())
            if len(keys) >= 2:
                labels = [str(row.get(keys[0], '')) for row in results]
                values = []
                for row in results:
                    val = row.get(keys[1], 0)
                    if isinstance(val, (int, float)):
                        values.append(float(val))
                    elif isinstance(val, str):
                        try:
                            values.append(float(val.replace(',', '').replace('₹', '').strip()))
                        except:
                            values.append(0)
                    else:
                        values.append(0)
                return {
                    "chart_type": "bar_chart",
                    "labels": labels,
                    "values": values,
                    "category_label": keys[0].replace('_', ' ').title(),
                    "value_label": keys[1].replace('_', ' ').title(),
                    "title": query[:100]
                }

        return None
    except Exception as e:
        print(f"Error generating visualization data: {str(e)}")
        return None


def _generate_table_data(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not results:
        return None
    try:
        first_row = results[0]
        headers = list(first_row.keys())
        rows = []
        for row in results:
            row_data = []
            for header in headers:
                value = row.get(header, '')
                row_data.append('' if value is None else str(value))
            rows.append(row_data)
        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        print(f"Error generating table data: {str(e)}")
        return None


def _perform_calculations(results: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    if not results:
        return None
    calculations = {}
    query_lower = query.lower()
    try:
        for row in results:
            for key, value in row.items():
                if any(term in key.lower() for term in ['sum', 'total', 'avg', 'average', 'count', 'max', 'min', 'percentage']):
                    if value is not None:
                        calculations[key] = value
    except:
        pass
    return calculations if calculations else None


def _generate_natural_answer(query: str, results: List[Dict[str, Any]], table_schema: str, mode: str = "text") -> str:
    current_key = os.getenv("GEMINI_KEY")
    if current_key:
        current_key = current_key.strip().strip('"').strip("'")

    api_key = GEMINI_KEY if GEMINI_KEY else current_key
    if not api_key:
        return "Results retrieved, but Gemini API key not configured for natural language generation."

    if api_key and not GEMINI_KEY:
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            return f"Error configuring Gemini API: {str(e)}"

    try:
        model = None
        model_names = [
            'gemini-2.5-flash',
            'gemini-flash-latest',
            'gemini-2.0-flash',
            'gemini-pro-latest',
            'gemini-pro'
        ]
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                continue

        if not model:
            raise Exception("No available Gemini model found for answer generation")

        results_str = json.dumps(results, indent=2, default=str) if results else "[]"
        column_info = ""
        if results and len(results) > 0:
            columns = list(results[0].keys())
            column_info = f"\nAvailable columns in results: {', '.join(columns)}"

        calculations = _perform_calculations(results, query)
        calculations_info = ""
        if calculations:
            calculations_info = f"\n\nCalculated/Aggregated Values: {json.dumps(calculations, indent=2, default=str)}"

        if mode == "table":
            prompt = f"""Generate a VERY BRIEF summary (1-2 sentences maximum) for the query results that will be displayed in a table format.
USER QUERY: {query}
NUMBER OF RESULTS: {len(results)}
Generate ONLY a brief 1-2 sentence summary:"""
        else:
            prompt = f"""You are an expert data analyst for traffic challan data.

TABLE STRUCTURE:
{table_schema}
{column_info}

USER QUERY:
{query}

RETRIEVED DATA ROWS ({len(results)} rows):
{results_str}
{calculations_info}

Answer based ONLY on the retrieved data. Be precise, use ₹ for currency, format numbers with commas.
Provide a comprehensive, accurate answer:"""

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
         error_msg = str(e)
         if '429' in error_msg or 'quota' in error_msg.lower() or 'rate' in error_msg.lower():
             return "Server is busy due to high demand. Please wait a moment and try again."
         return "Unable to generate answer. Please try again."
        


def list_files_service(user_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        if not user_id:
            return {"status": False, "message": "User authentication required", "data": None}

        uploads = db.query(ExcelUploads).filter(
            ExcelUploads.user_id == user_id
        ).order_by(ExcelUploads.created_at.desc()).all()

        files = []
        for upload in uploads:
            files.append({
                "id": upload.id,
                "filename": upload.filename,
                "table_name": upload.table_name,
                "columns": upload.columns if isinstance(upload.columns, list) else [],
                "row_count": upload.row_count,
                "created_at": upload.created_at.isoformat() if upload.created_at else None,
                "updated_at": upload.updated_at.isoformat() if upload.updated_at else None
            })

        return {
            "status": True,
            "message": f"Found {len(files)} uploaded file(s)",
            "data": {"files": files, "total_count": len(files)}
        }
    except Exception as e:
        return {"status": False, "message": f"Error listing files: {str(e)}", "data": None}
    finally:
        db.close()


def _drop_table(db: Session, table_name: str) -> bool:
    try:
        drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
        db.execute(text(drop_sql))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error dropping table {table_name}: {str(e)}")
        return False


def delete_file_service(file_id: str, user_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        if not user_id:
            return {"status": False, "message": "User authentication required", "data": None}

        upload = db.query(ExcelUploads).filter(
            ExcelUploads.id == file_id,
            ExcelUploads.user_id == user_id
        ).first()

        if not upload:
            return {"status": False, "message": "File not found or you don't have permission to delete it", "data": None}

        table_name = upload.table_name
        filename = upload.filename

        table_dropped = _drop_table(db, table_name)
        db.delete(upload)
        db.commit()

        return {
            "status": True,
            "message": f"Successfully deleted file '{filename}' and its database table",
            "data": {
                "file_id": file_id,
                "filename": filename,
                "table_name": table_name,
                "table_dropped": table_dropped
            }
        }
    except Exception as e:
        db.rollback()
        return {"status": False, "message": f"Error deleting file: {str(e)}", "data": None}
    finally:
        db.close()


def _get_table_name_by_id_or_latest(db: Session, user_id: str, table_name: Optional[str] = None) -> Optional[str]:
    if table_name:
        upload = db.query(ExcelUploads).filter(
            ExcelUploads.table_name == table_name,
            ExcelUploads.user_id == user_id
        ).first()
        if upload:
            return table_name
        return None
    else:
        return _get_latest_table_name(db, user_id)


def query_service(query: str, top_k: int = 5, user_id: str = None, mode: str = "text", table_name: Optional[str] = None) -> dict:
    db: Session = SessionLocal()
    try:
        if not query or not query.strip():
            return {"status": False, "message": "Query cannot be empty", "data": None}

        if not user_id:
            return {"status": False, "message": "User authentication required", "data": None}

        selected_table_name = _get_table_name_by_id_or_latest(db, user_id, table_name)

        if not selected_table_name:
            if table_name:
                return {
                    "status": False,
                    "message": f"Table '{table_name}' not found or you don't have permission to access it.",
                    "data": None
                }
            else:
                return {
                    "status": False,
                    "message": "No Excel file has been uploaded yet. Please upload an Excel file first.",
                    "data": None
                }

        table_schema = _get_table_schema(db, selected_table_name)
        sql_query = _generate_sql_query(query, table_schema, selected_table_name)

        if not sql_query:
            error_msg = (
                "GEMINI_KEY not configured. Please set GEMINI_KEY in your .env file."
                if not GEMINI_KEY
                else "Server is busy. Please wait a moment and try again."  # ← NAYA
            )
            return {"status": False, "message": error_msg, "data": None}

        results = _execute_sql_query(db, sql_query, top_k)
        answer = _generate_natural_answer(query, results, table_schema, mode)

        response_data = {
            "answer": answer,
            "results": results if results else None,
            "sql_query": sql_query,
            "table_name": selected_table_name,
            "mode": mode
        }

        if mode == "graph":
            visualization_data = _generate_visualization_data(results, query, sql_query)
            if visualization_data:
                response_data["visualization_data"] = visualization_data

        elif mode == "table":
            table_data = _generate_table_data(results)
            if table_data:
                response_data["table_data"] = table_data

        return {
            "status": True,
            "message": "Query processed successfully",
            "data": response_data
        }
    except Exception as e:
        return {"status": False, "message": f"Error processing query: {str(e)}", "data": None}
    finally:
        db.close()