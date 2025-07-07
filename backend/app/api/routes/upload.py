from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path
import logging
from typing import List
import aiofiles
import mimetypes

logger = logging.getLogger(__name__)

router = APIRouter()

# Configure upload settings
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
    '.csv', '.txt', '.json', '.xml', '.zip'
}

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and process files"""
    try:
        uploaded_files = []
        
        for file in files:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                )
            
            # Check file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{file.filename}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Get file metadata
            file_info = {
                "id": file_id,
                "original_name": file.filename,
                "saved_name": safe_filename,
                "size": len(content),
                "mime_type": mimetypes.guess_type(file.filename)[0],
                "extension": file_ext,
                "upload_path": str(file_path),
                "url": f"/uploads/{safe_filename}"
            }
            
            uploaded_files.append(file_info)
            
            # Process file content (extract text, metadata, etc.)
            try:
                processed_content = await process_uploaded_file(file_path, file_info)
                file_info["processed_content"] = processed_content
            except Exception as e:
                logger.warning(f"Could not process file {file.filename}: {e}")
                file_info["processing_error"] = str(e)
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_uploaded_file(file_path: Path, file_info: dict) -> dict:
    """Process uploaded file to extract content and metadata"""
    try:
        content = {}
        
        if file_info["extension"] == '.txt':
            # Process text file
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                text_content = await f.read()
                content = {
                    "type": "text",
                    "text": text_content,
                    "word_count": len(text_content.split()),
                    "char_count": len(text_content)
                }
        
        elif file_info["extension"] == '.json':
            # Process JSON file
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                json_content = await f.read()
                import json
                parsed_json = json.loads(json_content)
                content = {
                    "type": "json",
                    "data": parsed_json,
                    "keys": list(parsed_json.keys()) if isinstance(parsed_json, dict) else None,
                    "size": len(json_content)
                }
        
        elif file_info["extension"] == '.csv':
            # Process CSV file
            import pandas as pd
            df = pd.read_csv(file_path)
            content = {
                "type": "csv",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "sample_data": df.head(5).to_dict('records')
            }
        
        elif file_info["extension"] in ['.pdf']:
            # Process PDF file (placeholder - would need proper PDF processing)
            content = {
                "type": "pdf",
                "status": "uploaded",
                "note": "PDF processing requires additional setup"
            }
        
        elif file_info["extension"] in ['.doc', '.docx']:
            # Process Word document (placeholder)
            content = {
                "type": "document",
                "status": "uploaded",
                "note": "Document processing requires additional setup"
            }
        
        elif file_info["extension"] in ['.xls', '.xlsx']:
            # Process Excel file
            import pandas as pd
            df = pd.read_excel(file_path)
            content = {
                "type": "excel",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "sample_data": df.head(5).to_dict('records')
            }
        
        else:
            content = {
                "type": "unknown",
                "status": "uploaded",
                "note": f"File type {file_info['extension']} uploaded but not processed"
            }
        
        return content
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return {
            "type": "error",
            "error": str(e)
        }

@router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve uploaded files"""
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file info (in a real app, you might serve the actual file)
        return {
            "filename": filename,
            "exists": True,
            "size": file_path.stat().st_size,
            "path": str(file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

@router.delete("/uploads/{filename}")
async def delete_uploaded_file(filename: str):
    """Delete uploaded file"""
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        
        return {
            "status": "success",
            "message": f"File {filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@router.get("/uploads")
async def list_uploaded_files():
    """List all uploaded files"""
    try:
        files = []
        
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "url": f"/uploads/{file_path.name}"
                })
        
        return {
            "status": "success",
            "files": files,
            "total": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")