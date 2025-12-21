
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


def _create_dynamic_table(db: Session, table_name: str, columns: List[str]) -> bool:
    try:
        sanitized_columns = [_sanitize_column_name(col) for col in columns]
        
        column_defs = ["id VARCHAR(36) PRIMARY KEY"]
        
        for col in sanitized_columns:
            column_defs.append(f"`{col}` TEXT")
        
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
  
    try:
        import uuid
        
        rows_inserted = 0
        sanitized_columns = [_sanitize_column_name(col) for col in columns]
        
        for _, row in df.iterrows():
          
            record_id = str(uuid.uuid4())
            
           
            col_names = ['id'] + sanitized_columns
            col_names_str = ', '.join([f"`{col}`" for col in col_names])
            
         
            values = [f"'{record_id}'"]
            for col in columns:
                value = row[col]
               
                if pd.isna(value):
                    values.append("NULL")
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    values.append(f"'{value.isoformat()}'")
                elif isinstance(value, (int, float)):
                    values.append(f"'{str(value)}'")
                else:
                 
                    escaped_value = str(value).replace("'", "''")
                    values.append(f"'{escaped_value}'")
            
            values_str = ', '.join(values)
            
           
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


def _preprocess_csv_data(df: pd.DataFrame) -> pd.DataFrame:
   
    required_columns = [
        "Challan Number",
        "Challan Source",
        "Vehicle Number",
        "Challan Date",
        "Challan Place",
        "Latitue Longtitue", 
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
    
  
    available_columns = df.columns.tolist()
    missing_columns = [col for col in required_columns if col not in available_columns]
    
    if missing_columns:
        print(f"[WARNING] Missing columns in CSV: {missing_columns}")
        print(f"[INFO] Available columns: {available_columns}")
       
        required_columns = [col for col in required_columns if col in available_columns]
    
   
    df_filtered = df[required_columns].copy()
    
    return df_filtered


def _read_csv_with_preprocessing(file_content: bytes, skip_rows: int = 7) -> pd.DataFrame:
   
    import io
    
    csv_file = io.BytesIO(file_content)
    
   
    try:
      
        df = pd.read_csv(
            csv_file,
            skiprows=skip_rows, 
            header=0, 
            encoding='utf-8',
            on_bad_lines='skip' 
        )
    except TypeError:
       
        try:
            df = pd.read_csv(
                csv_file,
                skiprows=skip_rows,
                header=0,
                encoding='utf-8',
                error_bad_lines=False,  # Old parameter name
                warn_bad_lines=False
            )
        except TypeError:
           
            df = pd.read_csv(
                csv_file,
                skiprows=skip_rows,
                header=0,
                encoding='utf-8'
            )
    
  
    df = _preprocess_csv_data(df)
    
    return df


def upload_excel_service(file_content: bytes, filename: str, user_id: str) -> dict:
    
    db: Session = SessionLocal()
    try:
        import io
        
       
        file_ext = Path(filename).suffix.lower()
        
       
        if file_ext == '.csv':
           
            df = _read_csv_with_preprocessing(file_content, skip_rows=7)
        elif file_ext in ['.xlsx', '.xls']:
         
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(excel_file, engine='openpyxl')
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
       
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        
        schema = f"Table: {table_name}\n\nColumns and Data Types:\n"
        for col in columns:
            col_name = col['name']
            col_type = str(col['type'])
            
            if col_name not in ['id', 'created_at', 'updated_at']:
                schema += f"- {col_name} ({col_type})\n"
        
      
        sample_query = f"SELECT * FROM `{table_name}` LIMIT 3"
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
        
      
        count_query = f"SELECT COUNT(*) as total_count FROM `{table_name}`"
        count_result = db.execute(text(count_query))
        total_count = count_result.fetchone()[0]
        schema += f"\nTotal Records: {total_count}\n"
        
        return schema
    except Exception as e:
        return f"Table: {table_name}\n(Error getting schema: {str(e)})"


def _generate_sql_query(natural_query: str, table_schema: str, table_name: str) -> Optional[str]:
    
    current_key = os.getenv("GEMINI_KEY")
    if current_key:
        current_key = current_key.strip().strip('"').strip("'")
    
  
    api_key = GEMINI_KEY if GEMINI_KEY else current_key
    
    if not api_key:
        print("[DEBUG] GEMINI_KEY is None or empty")
        print(f"[DEBUG] GEMINI_KEY module var: {GEMINI_KEY}")
        print(f"[DEBUG] current_key from env: {current_key}")
        return None
    
   
    if api_key != GEMINI_KEY or not GEMINI_KEY:
        try:
            genai.configure(api_key=api_key)
            print(f"[DEBUG] Gemini API configured with key (length: {len(api_key)})")
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
        
        prompt = f"""You are an expert SQL query generator specialized in traffic challan and transportation data analysis. Convert natural language queries into precise, optimized MySQL SELECT statements.

TABLE SCHEMA:
{table_schema}

TABLE NAME: `{table_name}`

USER QUERY: {natural_query}

CRITICAL REQUIREMENTS:
1. Generate ONLY valid MySQL SELECT query - no explanations, no markdown, no code blocks, just pure SQL
2. Use exact table name: `{table_name}` (with backticks)
3. Use exact column names from schema (with backticks for safety)
4. Analyze query intent deeply - understand what the user REALLY wants
5. Handle complex multi-condition queries with proper AND/OR logic
6. For traffic challan data, recognize common patterns:
   - Amount/Challan Amount: numeric values for fines
   - Location fields: Street Name, Locality Name, City Name
   - Vehicle fields: Vehicle Name, Vehicle Number, Mode of Transport
   - Date/Time fields: if present, use for filtering and sorting

ADVANCED FILTERING & WHERE CLAUSES:
- Multiple conditions: Combine with AND/OR logically
  Example: "challans above 1000 in Indore for cars" → WHERE CAST(`challan_amount` AS DECIMAL(10,2)) > 1000 AND `city_name` LIKE '%Indore%' AND (`vehicle_name` LIKE '%car%' OR `mode_of_transport` LIKE '%car%')
- Partial matches: Use LIKE '%value%' (case-insensitive pattern matching)
- Exact matches: Use = 'value' for precise matching
- Numeric comparisons: Always CAST to DECIMAL for amounts, UNSIGNED for counts
- Range queries: Use BETWEEN or >= AND <=
- NULL handling: Use IS NULL or IS NOT NULL
- Case-insensitive: Use LOWER() or UPPER() if needed: LOWER(`column`) LIKE LOWER('%value%')

MATHEMATICAL & AGGREGATION OPERATIONS (CRITICAL FOR CHALLAN DATA):
- Sums: SELECT SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total_amount FROM ...
- Averages: SELECT AVG(CAST(`challan_amount` AS DECIMAL(10,2))) AS avg_amount FROM ...
- Counts: SELECT COUNT(*) AS total_count FROM ... or COUNT(DISTINCT `column`) for unique values
- Maximum/Minimum: SELECT MAX(CAST(`challan_amount` AS DECIMAL(10,2))) AS max_amount FROM ...
- Grouping: Use GROUP BY with aggregations for breakdowns by location, vehicle type, etc.
- Percentages: (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `{table_name}`)) AS percentage
- Ratios: Calculate ratios between different groups
- Cumulative sums: Use window functions if needed
- Statistical functions: STDDEV, VARIANCE when applicable

COMPLEX QUERY PATTERNS FOR TRAFFIC CHALLAN ANALYSIS:
1. CROSS-QUERIES (Multiple conditions across different dimensions):
   - "Show challans above 1000 rupees in Indore city for cars" 
     → WHERE CAST(`challan_amount` AS DECIMAL(10,2)) > 1000 AND `city_name` LIKE '%Indore%' AND (`vehicle_name` LIKE '%car%' OR `mode_of_transport` LIKE '%car%')
   
2. AGGREGATION BY MULTIPLE DIMENSIONS:
   - "Total challan amount by city and vehicle type"
     → SELECT `city_name`, `vehicle_name`, SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total FROM ... GROUP BY `city_name`, `vehicle_name`
   
3. TOP-N WITH CONDITIONS:
   - "Top 10 highest challans in Mumbai"
     → SELECT * FROM ... WHERE `city_name` LIKE '%Mumbai%' ORDER BY CAST(`challan_amount` AS DECIMAL(10,2)) DESC LIMIT 10
   
4. COMPARATIVE ANALYSIS:
   - "Compare total challans between two cities"
     → Use GROUP BY with CASE WHEN or UNION
   
5. PERCENTAGE & PROPORTION QUERIES:
   - "What percentage of challans are above 5000?"
     → SELECT (COUNT(CASE WHEN CAST(`challan_amount` AS DECIMAL(10,2)) > 5000 THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM ...
   
6. TREND ANALYSIS:
   - "Average challan amount by locality"
     → SELECT `locality_name`, AVG(CAST(`challan_amount` AS DECIMAL(10,2))) AS avg_amount FROM ... GROUP BY `locality_name` ORDER BY avg_amount DESC

SORTING & LIMITING:
- ORDER BY: Use for sorting (DESC for highest, ASC for lowest)
- LIMIT: Always include reasonable LIMIT (default 50 if not specified, but respect user's "top N" requests)
- For "top", "highest", "maximum": ORDER BY ... DESC LIMIT N
- For "bottom", "lowest", "minimum": ORDER BY ... ASC LIMIT N

COLUMN NAME MAPPING (Common traffic challan fields):
- Amount/Challan Amount: Look for columns with "amount", "challan", "fine", "penalty"
- Location: "street", "locality", "city", "area", "location"
- Vehicle: "vehicle", "transport", "mode", "type"
- Vehicle Number: "number", "registration", "plate"

DATA TYPE HANDLING (CRITICAL):
Since all columns are stored as TEXT, ALWAYS CAST numeric columns:
- Amounts/Money: CAST(`column` AS DECIMAL(10,2))
- Counts/IDs: CAST(`column` AS UNSIGNED) or CAST(`column` AS SIGNED)
- For comparisons: CAST both sides if comparing numbers
- For calculations: CAST all numeric operands

EXAMPLES FOR TRAFFIC CHALLAN QUERIES:
1. "Show all challans above 1000 rupees"
   → SELECT * FROM `{table_name}` WHERE CAST(`challan_amount` AS DECIMAL(10,2)) > 1000

2. "Total challan amount collected"
   → SELECT SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total_amount FROM `{table_name}`

3. "Average challan amount by city"
   → SELECT `city_name`, AVG(CAST(`challan_amount` AS DECIMAL(10,2))) AS avg_amount FROM `{table_name}` GROUP BY `city_name` ORDER BY avg_amount DESC

4. "Top 5 highest challans in Indore"
   → SELECT * FROM `{table_name}` WHERE `city_name` LIKE '%Indore%' ORDER BY CAST(`challan_amount` AS DECIMAL(10,2)) DESC LIMIT 5

5. "Count of challans by vehicle type"
   → SELECT `vehicle_name`, COUNT(*) AS count FROM `{table_name}` GROUP BY `vehicle_name` ORDER BY count DESC

6. "Challans between 500 and 2000 rupees for cars in Mumbai"
   → SELECT * FROM `{table_name}` WHERE CAST(`challan_amount` AS DECIMAL(10,2)) BETWEEN 500 AND 2000 AND (`vehicle_name` LIKE '%car%' OR `mode_of_transport` LIKE '%car%') AND `city_name` LIKE '%Mumbai%'

7. "What percentage of challans are above 5000?"
   → SELECT (COUNT(CASE WHEN CAST(`challan_amount` AS DECIMAL(10,2)) > 5000 THEN 1 END) * 100.0 / COUNT(*)) AS percentage FROM `{table_name}`

8. "Total amount collected by each locality"
   → SELECT `locality_name`, SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total_amount FROM `{table_name}` GROUP BY `locality_name` ORDER BY total_amount DESC

9. "Compare total challans between Indore and Mumbai"
   → SELECT `city_name`, COUNT(*) AS total_count, SUM(CAST(`challan_amount` AS DECIMAL(10,2))) AS total_amount FROM `{table_name}` WHERE `city_name` LIKE '%Indore%' OR `city_name` LIKE '%Mumbai%' GROUP BY `city_name`

10. "Show challans for specific vehicle number"
    → SELECT * FROM `{table_name}` WHERE `vehicle_number` LIKE '%ABC123%'

QUERY GENERATION RULES:
- If query asks for specific values, include them in SELECT
- If query asks for aggregations, use appropriate aggregation functions
- If query asks for comparisons, structure query to enable comparison
- If query has multiple conditions, combine them logically with AND/OR
- Always consider the full context of the query, not just keywords
- For "show me", "list", "display": Use SELECT * or specific columns
- For "how many", "count": Use COUNT(*)
- For "total", "sum": Use SUM()
- For "average", "mean": Use AVG()
- For "highest", "maximum", "top": Use MAX() or ORDER BY DESC
- For "lowest", "minimum", "bottom": Use MIN() or ORDER BY ASC

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
        print(f"[ERROR] Error generating SQL query: {error_msg}")
        print(f"[ERROR] Error type: {type(e).__name__}")
       
        if "API key" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
            print(f"[ERROR] Gemini API authentication failed. Please check your GEMINI_KEY.")
        return None


def _execute_sql_query(db: Session, sql_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
  
    try:
        sql_lower = sql_query.lower().strip()
        
     
        is_aggregation = any(keyword in sql_lower for keyword in [
            'sum(', 'avg(', 'count(', 'max(', 'min(', 
            'group by', 'having', 'percentage'
        ])
        
        
        if not is_aggregation and 'limit' not in sql_lower:
         
            sql_query = f"{sql_query.rstrip(';')} LIMIT {top_k * 2}"
        elif is_aggregation and 'limit' not in sql_lower:
           
            sql_query = f"{sql_query.rstrip(';')} LIMIT 100"
        
       
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
        print(f"Error executing SQL: {str(e)}")
        print(f"SQL Query: {sql_query}")
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
            
            print(f"[DEBUG] GROUP BY detected. Keys: {keys}")
            print(f"[DEBUG] First row sample: {first_row}")
            
            
            if len(keys) >= 2:
                category_key = keys[0]
                value_key = keys[1] if len(keys) > 1 else keys[0]
                
                print(f"[DEBUG] Using category_key={category_key}, value_key={value_key}")
                
               
                def get_row_value(row, key):
                  
                    if key in row:
                        return row[key]
                  
                    for k, v in row.items():
                        if k.lower() == key.lower():
                            return v
                   
                    key_normalized = key.replace(' ', '_').replace('-', '_').lower()
                    for k, v in row.items():
                        k_normalized = k.replace(' ', '_').replace('-', '_').lower()
                        if k_normalized == key_normalized:
                            return v
                    return None
                
              
                labels = []
                values = []
                
                for idx, row in enumerate(results):
                    
                    label_val = get_row_value(row, category_key)
                    if label_val is None:
                        label_val = row.get(category_key, '') 
                    labels.append(str(label_val) if label_val is not None else '')
                    
                  
                    val = get_row_value(row, value_key)
                    if val is None:
                        val = row.get(value_key, 0)  
                    
                   
                    print(f"[DEBUG] Row {idx}: {category_key}={label_val}, {value_key}={val} (type={type(val).__name__})")
                    
                  
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
                        except Exception as e:
                            print(f"[DEBUG] Failed to parse string value '{val}': {e}")
                            numeric_val = 0
                    else:
                        print(f"[DEBUG] Unknown value type: {type(val)} for value: {val}")
                        numeric_val = 0
                    
                    values.append(numeric_val)
                    print(f"[DEBUG] Row {idx} final numeric value: {numeric_val}")
                
              
                if len(labels) != len(values):
                    print(f"[WARNING] Mismatch: {len(labels)} labels vs {len(values)} values")
                    min_len = min(len(labels), len(values))
                    labels = labels[:min_len]
                    values = values[:min_len]
                
                print(f"[DEBUG] Final values array: {values}")
                print(f"[DEBUG] Max value: {max(values) if values else 'N/A'}, Min value: {min(values) if values else 'N/A'}")
                
              
                if all(v == 0 for v in values) and len(results) > 0:
                    print(f"[DEBUG] All values are zero, trying to find numeric column automatically...")
                    # Try to find a column with numeric values
                    for test_key in keys:
                        if test_key == category_key:
                            continue
                        test_values = []
                        for row in results:
                            test_val = row.get(test_key, 0)
                            if isinstance(test_val, (int, float)) or (hasattr(test_val, '__float__')):
                                try:
                                    test_values.append(float(test_val))
                                except:
                                    pass
                        if test_values and any(v > 0 for v in test_values):
                            print(f"[DEBUG] Found numeric column: {test_key} with values: {test_values[:3]}")
                            value_key = test_key
                            # Re-extract values with new key
                            values = []
                            for row in results:
                                val = row.get(value_key, 0)
                                if isinstance(val, (int, float)):
                                    values.append(float(val))
                                elif hasattr(val, '__float__'):
                                    try:
                                        values.append(float(val))
                                    except:
                                        values.append(0)
                                elif isinstance(val, str):
                                    try:
                                        cleaned = val.replace(',', '').replace('₹', '').replace('$', '').strip()
                                        values.append(float(cleaned) if cleaned else 0)
                                    except:
                                        values.append(0)
                                else:
                                    values.append(0)
                            print(f"[DEBUG] Re-extracted values: {values}")
                            break
                
                # Determine chart type
                if "percentage" in sql_lower or "%" in results_lower:
                    chart_type = "pie_chart"
                elif "time" in category_key.lower() or "date" in category_key.lower():
                    chart_type = "line_chart"
                else:
                    chart_type = "bar_chart"
                
                # Validate data before returning
                if len(labels) > 0 and len(values) > 0 and any(v > 0 for v in values):
                    print(f"[DEBUG] Generated chart data: type={chart_type}, labels={len(labels)}, values={len(values)}, sample={values[:3]}")
                    return {
                        "chart_type": chart_type,
                        "labels": labels,
                        "values": values,
                        "category_label": category_key.replace('_', ' ').title(),
                        "value_label": value_key.replace('_', ' ').title(),
                        "title": query[:100]  # Truncate long queries
                    }
                else:
                    print(f"[WARNING] Invalid chart data: labels={len(labels)}, values={len(values)}, all_zero={all(v == 0 for v in values) if values else True}")
                    print(f"[DEBUG] Values breakdown: {[(i, v) for i, v in enumerate(values)]}")
                    print(f"[DEBUG] Sample row data: {results[0] if results else 'No results'}")
                    return None
        
        # Check for time-series or single value queries
        elif any(keyword in sql_lower for keyword in ['sum(', 'avg(', 'count(', 'max(', 'min(']):
            # Single aggregated value
            first_row = results[0]
            keys = list(first_row.keys())
            
            if keys:
                value_key = keys[0]
                value = first_row.get(value_key, 0)
                
                # Convert to number
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
        
        # Default: use first two columns as labels and values
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
    """
    Generate structured table data for HTML table rendering.
    
    Args:
        results: Query results
    
    Returns:
        dict: Table data with headers and rows
    """
    if not results:
        return None
    
    try:
        # Extract headers from first row
        first_row = results[0]
        headers = list(first_row.keys())
        
        # Extract rows
        rows = []
        for row in results:
            row_data = []
            for header in headers:
                value = row.get(header, '')
                # Convert to string, handle None
                if value is None:
                    row_data.append('')
                else:
                    row_data.append(str(value))
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


def _generate_natural_answer(query: str, results: List[Dict[str, Any]], table_schema: str, mode: str = "text") -> str:
    """
    Use Gemini to generate natural language answer from query results.
    
    Args:
        query: Original natural language query
        results: Retrieved data rows
        table_schema: Table schema description
        mode: Response mode - "text", "graph", or "table"
    
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
        
        # Adjust prompt based on mode
        if mode == "table":
            # For table mode, generate a very brief summary (1-2 sentences max)
            prompt = f"""You are a data analyst. Generate a VERY BRIEF summary (1-2 sentences maximum) for the query results that will be displayed in a table format.

IMPORTANT: 
- Keep the response SHORT and CONCISE (maximum 2 sentences)
- Just state what data is being shown, don't list all details
- The detailed data will be shown in the table below
- Example: "Found {len(results)} records matching your query." or "Showing {len(results)} challans above ₹1,000 in Indore."

USER QUERY: {query}
NUMBER OF RESULTS: {len(results)}

RETRIEVED DATA ROWS ({len(results)} rows):
{results_str[:500]}... (data will be shown in table)

Generate ONLY a brief 1-2 sentence summary:"""
        else:
            # For text and graph modes, use the comprehensive prompt
            prompt = f"""You are an expert data analyst specialized in traffic challan and transportation data. You analyze structured data from Excel files and provide comprehensive, accurate answers to complex queries.

CONTEXT:
- You are analyzing traffic challan data retrieved from a database query
- Each row represents a traffic challan record with details like amount, location, vehicle information
- The data is stored exactly as it appeared in the uploaded Excel file
- You must answer based ONLY on the provided data rows - no external assumptions
- You can perform complex mathematical operations, aggregations, and cross-dimensional analysis

TABLE STRUCTURE:
{table_schema}
{column_info}

USER QUERY:
{query}

RETRIEVED DATA ROWS ({len(results)} rows):
{results_str}
{calculations_info}

DOMAIN KNOWLEDGE - TRAFFIC CHALLAN DATA:
- Challan Amount: The fine/penalty amount (numeric, typically in rupees)
- Location Fields: Street Name, Locality Name, City Name (hierarchical location data)
- Vehicle Information: Vehicle Name, Vehicle Number, Mode of Transport
- Common patterns: High-value challans, location-based analysis, vehicle type breakdowns

STRICT RULES:
1. Understand the table structure deeply - identify what each column represents in the traffic challan context
2. Match query intent precisely to data fields - understand what the user REALLY wants
3. Answer STRICTLY from retrieved rows only - never use external knowledge or assumptions
4. If answer is not in data, explicitly state "Not found in the dataset" or "No records match the criteria"
5. NEVER hallucinate, guess, or infer beyond what is in the table data
6. Extract values exactly as they appear in the data
7. For counts/summaries, use the provided aggregated values or calculate from rows
8. For multiple rows, provide clear, organized summaries
9. Use natural, conversational, professional language
10. Present data clearly with proper formatting (currency, percentages, numbers)

ADVANCED MATHEMATICAL & COMPLEX QUERY HANDLING:

1. AGGREGATIONS (Already calculated by SQL):
   - SUM: Present as "The total challan amount is ₹X" or "Total collected: ₹X"
   - AVG: Present as "The average challan amount is ₹X" or "Average fine: ₹X"
   - COUNT: Present as "There are X challans" or "X records found"
   - MAX/MIN: Present as "The highest challan is ₹X" or "The lowest challan is ₹X"
   - GROUP BY results: Present breakdown clearly by dimension (city, vehicle type, etc.)

2. PERCENTAGES & PROPORTIONS:
   - Calculate and present clearly: "X% of challans are above ₹5000" or "X out of Y (Z%)"
   - For comparisons: "City A has X% more challans than City B"
   - Show both absolute and percentage values when relevant

3. COMPARISONS & CROSS-ANALYSIS:
   - Compare values across different dimensions (cities, vehicle types, localities)
   - Highlight differences: "Indore has ₹X more in total challans than Mumbai"
   - Rank and order: "Top 3 cities by challan amount: 1) City A (₹X), 2) City B (₹Y), 3) City C (₹Z)"
   - Relative comparisons: "X is Y% higher/lower than Z"

4. COMPLEX MULTI-DIMENSIONAL QUERIES:
   - Handle queries spanning multiple dimensions (location + vehicle + amount)
   - Break down results by each relevant dimension
   - Provide insights across dimensions: "In Indore, cars account for X% of total challans"

5. STATISTICAL ANALYSIS:
   - Mean, median, range when applicable
   - Distribution insights: "Most challans (X%) fall in the ₹Y-₹Z range"
   - Outliers: "The highest challan of ₹X is significantly above the average of ₹Y"

6. TREND & PATTERN IDENTIFICATION:
   - Identify patterns in the data: "Most challans are concentrated in [location]"
   - Vehicle type distribution: "Cars account for X% of all challans"
   - Amount distribution: "X% of challans are below ₹Y, Y% are above ₹Z"

7. CONDITIONAL & FILTERED ANALYSIS:
   - Handle queries with multiple conditions: "Challans above ₹X in City Y for Vehicle Type Z"
   - Present filtered results clearly with context
   - Explain what filters were applied

RESPONSE FORMAT GUIDELINES:

1. START WITH DIRECT ANSWER:
   - Answer the query directly in the first sentence
   - Example: "The total challan amount collected is ₹1,250,000"

2. PROVIDE CONTEXT & DETAILS:
   - Mention how many records were analyzed
   - Provide specific values, numbers, locations, vehicle types
   - Include relevant breakdowns if query implies multi-dimensional analysis

3. FORMAT NUMBERS PROPERLY:
   - Currency: Use ₹ symbol, format with commas (₹1,25,000)
   - Percentages: Show as "X%" or "X out of Y (Z%)"
   - Counts: Use clear numbers (1,234 challans)
   - Decimals: Round appropriately (₹1,234.56 or ₹1,235)

4. STRUCTURE COMPLEX ANSWERS:
   - Use bullet points or numbered lists for multiple items
   - Group related information together
   - Use clear headings or separators for different dimensions

5. BE COMPREHENSIVE BUT CONCISE:
   - Answer the query completely
   - Include relevant insights that add value
   - Don't be verbose - be precise and informative

EXAMPLES OF EXCELLENT RESPONSES FOR TRAFFIC CHALLAN QUERIES:

1. Query: "What is the total challan amount?"
   Response: "The total challan amount collected is ₹12,50,000 across all records."

2. Query: "Show me challans above 1000 rupees in Indore"
   Response: "There are 45 challans above ₹1,000 in Indore. The total amount for these challans is ₹1,25,000. The highest challan in this category is ₹5,000 for vehicle number ABC-1234."

3. Query: "Average challan amount by city"
   Response: "Average challan amounts by city:
   - Indore: ₹2,500 (based on 120 challans)
   - Mumbai: ₹3,200 (based on 95 challans)
   - Delhi: ₹2,800 (based on 110 challans)
   
   Mumbai has the highest average challan amount, which is 28% higher than Indore."

4. Query: "Top 5 highest challans"
   Response: "The top 5 highest challans are:
   1. ₹10,000 - Vehicle: Car (ABC-1234), Location: Indore, MG Road
   2. ₹8,500 - Vehicle: Bike (XYZ-5678), Location: Mumbai, Marine Drive
   3. ₹7,200 - Vehicle: Car (DEF-9012), Location: Delhi, Connaught Place
   4. ₹6,800 - Vehicle: Truck (GHI-3456), Location: Indore, Ring Road
   5. ₹6,500 - Vehicle: Car (JKL-7890), Location: Mumbai, Bandra"

5. Query: "What percentage of challans are above 5000?"
   Response: "Out of 500 total challans, 75 challans are above ₹5,000, which represents 15% of all challans. The remaining 85% (425 challans) are ₹5,000 or below."

6. Query: "Compare total challans between Indore and Mumbai"
   Response: "Comparison of challans between Indore and Mumbai:
   - Indore: 120 challans, Total amount: ₹3,00,000, Average: ₹2,500
   - Mumbai: 95 challans, Total amount: ₹3,04,000, Average: ₹3,200
   
   While Mumbai has 25 fewer challans, it has ₹4,000 more in total amount. Mumbai's average challan is 28% higher than Indore's."

7. Query: "Challans for cars in Indore above 2000 rupees"
   Response: "There are 18 challans for cars in Indore above ₹2,000. The total amount is ₹65,000, with an average of ₹3,611 per challan. The highest challan in this category is ₹8,000 for vehicle number ABC-1234 on MG Road."

8. Query: "Total amount collected by each locality"
   Response: "Total challan amounts collected by locality:
   - MG Road: ₹1,25,000 (50 challans)
   - Ring Road: ₹95,000 (38 challans)
   - Vijay Nagar: ₹80,000 (32 challans)
   - Palasia: ₹65,000 (26 challans)
   
   MG Road has the highest collection, accounting for 34% of the total."

9. Query: "Count of challans by vehicle type"
   Response: "Breakdown of challans by vehicle type:
   - Cars: 180 challans (45% of total)
   - Bikes: 150 challans (37.5% of total)
   - Trucks: 50 challans (12.5% of total)
   - Buses: 20 challans (5% of total)
   
   Cars account for the highest number of challans, followed by bikes."

10. Query: "Show me all challans above 1000 rupees in Indore city for cars"
    Response: "Found 25 challans above ₹1,000 for cars in Indore. The total amount is ₹85,000. Here are the details:
    - Highest: ₹5,000 (Vehicle: ABC-1234, Location: MG Road)
    - Lowest: ₹1,200 (Vehicle: XYZ-5678, Location: Ring Road)
    - Average: ₹3,400 per challan
    - Most common locality: MG Road (8 challans)"

CRITICAL: 
- Always base your answer on the actual data provided
- If the query asks for something not in the data, say so clearly
- Be precise with numbers and calculations
- Provide context and insights that help the user understand the data
- Use professional, clear language suitable for traffic challan analysis

Now provide a comprehensive, accurate answer to the user's query:"""
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        return answer
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def list_files_service(user_id: str) -> dict:
   
    db: Session = SessionLocal()
    try:
        if not user_id:
            return {
                "status": False,
                "message": "User authentication required",
                "data": None
            }
        
        # Get all uploads for this user, ordered by most recent first
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
            "data": {
                "files": files,
                "total_count": len(files)
            }
        }
    except Exception as e:
        return {
            "status": False,
            "message": f"Error listing files: {str(e)}",
            "data": None
        }
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
            return {
                "status": False,
                "message": "User authentication required",
                "data": None
            }
        
        # Find the upload record
        upload = db.query(ExcelUploads).filter(
            ExcelUploads.id == file_id,
            ExcelUploads.user_id == user_id  # Ensure user owns this file
        ).first()
        
        if not upload:
            return {
                "status": False,
                "message": "File not found or you don't have permission to delete it",
                "data": None
            }
        
        table_name = upload.table_name
        filename = upload.filename
        
        # Drop the database table
        table_dropped = _drop_table(db, table_name)
        
        if not table_dropped:
            print(f"[WARNING] Failed to drop table {table_name}, but continuing with record deletion")
        
        # Delete the upload record
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
        return {
            "status": False,
            "message": f"Error deleting file: {str(e)}",
            "data": None
        }
    finally:
        db.close()


def _get_table_name_by_id_or_latest(db: Session, user_id: str, table_name: Optional[str] = None) -> Optional[str]:
   
    if table_name:
        # Verify the table belongs to this user
        upload = db.query(ExcelUploads).filter(
            ExcelUploads.table_name == table_name,
            ExcelUploads.user_id == user_id
        ).first()
        if upload:
            return table_name
        return None
    else:
        # Use latest upload
        return _get_latest_table_name(db, user_id)


def query_service(query: str, top_k: int = 5, user_id: str = None, mode: str = "text", table_name: Optional[str] = None) -> dict:
   
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
        
        # Get table name (either specified or latest)
        selected_table_name = _get_table_name_by_id_or_latest(db, user_id, table_name)
        
        if not selected_table_name:
            if table_name:
                return {
                    "status": False,
                    "message": f"Table '{table_name}' not found or you don't have permission to access it. Please upload a file first or select a valid file.",
                    "data": None
                }
            else:
                return {
                    "status": False,
                    "message": "No Excel file has been uploaded yet. Please upload an Excel file first.",
                    "data": None
                }
        
        # Get table schema
        table_schema = _get_table_schema(db, selected_table_name)
        
        # Generate SQL query using Gemini
        sql_query = _generate_sql_query(query, table_schema, selected_table_name)
        
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
        
        # Generate natural language answer (mode-specific: brief for table, comprehensive for text/graph)
        answer = _generate_natural_answer(query, results, table_schema, mode)
        
        # Prepare response data
        response_data = {
            "answer": answer,
            "results": results if results else None,
            "sql_query": sql_query,
            "table_name": selected_table_name,
            "mode": mode
        }
        
        # Add mode-specific data
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
        return {
            "status": False,
            "message": f"Error processing query: {str(e)}",
            "data": None
        }
    finally:
        db.close()
