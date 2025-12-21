
# Standard library imports
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local application imports
from utills.auth_utils import get_user_id_from_token
from .agent_dto import QueryRequest
from .agent_service import upload_excel_service, query_service, list_files_service, delete_file_service

# Create router
agentRouter = APIRouter(tags=["Agent"])


def _user_id_dep(authorization: Optional[str] = Header(default=None, alias="Authorization")):
   
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


@agentRouter.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(..., description="Excel file to upload"),
    user_id: str = Depends(_user_id_dep)
):
   
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return {
            "status": False,
            "message": "File must be an Excel file (.xlsx or .xls) or CSV file (.csv)",
            "data": None
        }
    
    # Read file content
    file_content = await file.read()
    
    return upload_excel_service(file_content, file.filename, user_id)


@agentRouter.post("/query")
def query_agent(req: QueryRequest, user_id: str = Depends(_user_id_dep)):
   
    # Validate mode
    valid_modes = ["text", "graph", "table"]
    mode = req.mode.lower() if req.mode else "text"
    if mode not in valid_modes:
        mode = "text"
    
    return query_service(req.query, req.top_k, user_id, mode, req.table_name)


@agentRouter.get("/files")
def list_files(user_id: str = Depends(_user_id_dep)):
   
    return list_files_service(user_id)


@agentRouter.delete("/files/{file_id}")
def delete_file(file_id: str, user_id: str = Depends(_user_id_dep)):
   
    return delete_file_service(file_id, user_id)

