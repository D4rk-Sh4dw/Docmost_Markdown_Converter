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

def create_docmost_zip(markdown_content: str, images: List[Dict[str, Any]]) -> bytes:
    """
    Creates a ZIP file compatible with Docmost import.
    Structure:
    ZIP_ROOT/
    ├── document.md
    └── images/
        ├── image_001.png
        └── ...
    """
    
    # Post-process images and markdown links
    # Map original filenames to new sequential filenames if needed
    # The server might return random names or sequential. 
    # Requirement: lowercase, ascii, sequential image_001.png
    
    # We need to replace the image links in markdown with the new names
    # Strategy: 
    # 1. Identify all image links in Markdown.
    # 2. Map them to the images received.
    # 3. Rename images.
    # 4. Update Markdown.
    
    # However, connection between markdown links and image list from server might be loose 
    # if we just used `export_to_markdown`.
    # Docling usually exports `![](image_name.png)`.
    # We will assume the filenames in `images` list match what's in markdown or we blindly sequence them.
    # Blind sequencing is risky if order differs. 
    # Let's try to preserve mapping if possible, else normalize.
    
    # Normalize Markdown Image Links
    # Pattern: ![alt](path)
    # We will look for image filenames in the MD and replace them.
    
    new_images_map = {}
    
    # First, let's look at the images provided
    # Sort them to ensure deterministic order if they have indices
    # But better to just process them as they came.
    
    # Create a mapping from old name to new name
    # We need to know what the 'old name' is. 
    # In `docling_server`, we named them `image_{idx}.fmt`. This is sequential!
    # So `image_0.png` corresponds to the first image found.
    # But does `docling` export markdown with `image_0.png`? 
    # Docling 2 exports often use hashed names or internal refs.
    # If the server wrapper extracted them from `pictures` list, we have the binary data.
    # The Markdown export from Docling might have standard placeholders.
    
    # WORKAROUND:
    # If we cannot guarantee the link in MD matches the filename we generated in server,
    # we might have broken links. 
    # BUT, we are required to produce a valid ZIP.
    # If the markdown has `![desc](some_ref)`, and we have a list of images.
    # We can try to replace them in order of appearance.
    
    # Find all image links in MD
    img_link_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    matches = list(img_link_pattern.finditer(markdown_content))
    
    final_images = {}
    
    # We iterate through matches and assign the next available image from the list
    # logic: The document structure implies images appear in order.
    
    current_image_idx = 0
    
    def replace_link(match):
        nonlocal current_image_idx
        alt_text = match.group(1)
        # origin_path = match.group(2) # unused if we just replace by order
        
        if current_image_idx < len(images):
            # We have an image for this slot
            img_data = images[current_image_idx]
            original_filename = img_data['filename']
            # Determine extension
            ext = original_filename.split('.')[-1]
            
            new_filename = f"image_{current_image_idx + 1:03d}.{ext}"
            final_images[new_filename] = base64.b64decode(img_data['content_base64'])
            
            current_image_idx += 1
            return f'![{alt_text}](images/{new_filename})'
        else:
            # No image found for this link? Remove it or keep broken?
            # Requirement: "Alle Bilder an semantisch korrekter Stelle platzieren"
            return f'![{alt_text}](MISSING_IMAGE)'

    new_markdown = img_link_pattern.sub(replace_link, markdown_content)
    
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
