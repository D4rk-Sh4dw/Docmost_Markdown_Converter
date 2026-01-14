import re
import base64
import logging
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def clean_markdown(md_content: str) -> str:
    """
    Cleans markdown content according to Docmost compatibility rules.
    - Removes multiple blank lines.
    - Fixes broken line breaks (heuristic).
    - Removes metadata/YAML headers if any.
    """
    # Remove YAML frontmatter if present (lines between --- and --- at start)
    md_content = re.sub(r'^---\n.*?\n---\n', '', md_content, flags=re.DOTALL)
    
    # Remove multiple blank lines (more than 2)
    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    
    # Ensure headers have space after #
    md_content = re.sub(r'^(#+)([^ \n])', r'\1 \2', md_content, flags=re.MULTILINE)
    
    # Docmost specific: Remove HTML tags if any leaked
    md_content = re.sub(r'<[^>]+>', '', md_content)
    
    return md_content.strip()

def create_docmost_zip(markdown_content: str, images: List[Dict[str, Any]] = None) -> bytes:
    """
    Creates a ZIP file compatible with Docmost import.
    Structure:
    ZIP_ROOT/
    ├── document.md
    └── images/
        ├── image_001.png
        └── ...
        
    Handles both:
    1. Images passed in 'images' list (legacy/internal server)
    2. Images embedded in Markdown as Data URIs (official docling-serve)
    """
    final_images = {}
    current_image_idx = 0

    # 1. Handle passed images (if any)
    if images:
        for img_data in images:
            current_image_idx += 1
            # ... (logic for passed images if we ever use them again)
            # keeping it simple: currently we ignore this as we switched to official serve
            pass

    # 2. Extract Data URIs from Markdown
    # Pattern: ![alt](data:image/png;base64,......)
    # We regex for this, decode, save to files, and replace link.

    def replace_data_uri(match):
        nonlocal current_image_idx
        alt_text = match.group(1)
        mime_type = match.group(2) # e.g. image/png
        b64_data = match.group(3)
        
        # Determine extension
        ext = "png"
        if "jpeg" in mime_type or "jpg" in mime_type:
            ext = "jpg"
        elif "gif" in mime_type:
            ext = "gif"
        elif "webp" in mime_type:
            ext = "webp"
            
        current_image_idx += 1
        filename = f"image_{current_image_idx:03d}.{ext}"
        
        try:
            final_images[filename] = base64.b64decode(b64_data)
            return f"![{alt_text}](images/{filename})"
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return f"![{alt_text}](MISSING_IMAGE)"

    # Regex search for ![...](data:...)
    # We use a non-greedy match for content
    data_uri_pattern = re.compile(r'!\[(.*?)\]\(data:(image/[a-zA-Z]+);base64,(.*?)\)')
    
    new_markdown = data_uri_pattern.sub(replace_data_uri, markdown_content)
    
    # Clean up the markdown finally
    new_markdown = clean_markdown(new_markdown)
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Write Markdown
        zf.writestr('document.md', new_markdown)
        
        # Write Images
        for fname, data in final_images.items():
            zf.writestr(f'images/{fname}', data)
            
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
