import os
import shutil
import tempfile
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Docling Conversion Server (Compatible Mode)")

# Initialize Converter
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Response Models to mimic docling-serve structure roughly
# We wrap our content in a structure that resembles expected output
class ExportDocumentResponse(BaseModel):
    markdown: str
    images: List[Dict[str, Any]] # simplified for our internal use-case, but compatible via returning dicts

class ConvertDocumentResponse(BaseModel):
    # The official one has 'document' field which contains the export
    document: Dict[str, Any] 
    status: str
    processing_time: float = 0.0

@app.post("/v1/convert/file", response_model=ConvertDocumentResponse)
async def result(files: List[UploadFile] = File(...)): # Official API accepts list of files
    """
    Convert uploaded documents. Mimics docling-serve /v1/convert/file.
    Currently only processes the first file to keep logic simple for this specific task.
    """
    file = files[0] # We process one file
    logger.info(f"Received file: {file.filename}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_file_path = temp_path / file.filename
        
        try:
            with open(input_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

        try:
            logger.info("Starting conversion...")
            conv_result = doc_converter.convert(input_file_path)
            
            # Export to markdown
            markdown_content = conv_result.document.export_to_markdown()
            
            # Extract images (using base64 logic from before)
            extracted_images = []
            if hasattr(conv_result.document, "pictures") and conv_result.document.pictures:
                for idx, pic in enumerate(conv_result.document.pictures):
                    if hasattr(pic, "image") and pic.image:
                        import io
                        buffered = io.BytesIO()
                        fmt = pic.image.format or "PNG"
                        pic.image.save(buffered, format=fmt)
                        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        img_filename = f"image_{idx}.{fmt.lower()}"
                        extracted_images.append({
                            "filename": img_filename,
                            "content_base64": img_str
                        })

            # Construct response mimicking structure
            # We put our data into 'document' dict. 
            # The client (converter_ui) will need to know to look for 'markdown' and 'images' inside 'document'.
            # Or if standard docling-serve returns differently, the client needs to adapt.
            # Ideally, we should standardize THIS output format.
            
            doc_data = {
                "markdown": markdown_content,
                "images": extracted_images
            }

            return ConvertDocumentResponse(
                document=doc_data,
                status="success",
                processing_time=0.0
            )
            
        except Exception as e:
            logger.exception("Conversion failed")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
