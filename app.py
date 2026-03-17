import io
import os
import cv2
import numpy as np
import pytesseract
import aspose.words as aw
from PIL import Image
from rembg import remove
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Image Processing API")

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Static files and templates
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process")
@app.post("/backgroundRemove")
async def process_image(file: UploadFile = File(...)):
    """
    Remove background from an image and return the result as a JPEG.
    Consolidates /process and /backgroundRemove.
    Optimized: In-memory processing, async file handling.
    """
    try:
        # Read file into memory
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        
        # Optimization: Process directly in memory
        input_image = input_image.convert("RGB")
        input_array = np.array(input_image)
        
        # Apply background removal
        output_array = remove(input_array)
        
        # Create output image
        output_image = Image.fromarray(output_array).convert("RGB")
        
        # Save to BytesIO for streaming
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Error processing image", "data": str(e)}
        )

@app.post("/backgroundWithWhite")
async def background_with_white(file: UploadFile = File(...)):
    """
    Remove background and replace with white.
    Optimized: In-memory processing, async file handling.
    """
    try:
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if needed for rembg
        if input_image.mode != "RGB":
            input_image = input_image.convert("RGB")
        
        input_array = np.array(input_image)
        output_array = remove(input_array)
        output_image = Image.fromarray(output_array)
        
        # Ensure output is RGBA for transparency handling
        if output_image.mode != "RGBA":
            output_image = output_image.convert("RGBA")
            
        # Create white background
        new_image = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
        new_image.paste(output_image, (0, 0), output_image)
        
        # Convert to RGB to save as PNG or JPEG without alpha if preferred
        final_image = new_image.convert("RGB")
        
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Error processing image with white background", "data": str(e)}
        )

@app.post("/readText")
async def read_text(file: UploadFile = File(...)):
    """
    OCR: Extract text from an image.
    Optimized: Use in-memory data for CV2 processing.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Standard OCR preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        median = cv2.medianBlur(thresh, 3)
        
        text = pytesseract.image_to_string(median)
        return {"code": 200, "text": text.strip()}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Error reading text", "data": str(e)}
        )

@app.post("/textImage")
async def document_to_image(file: UploadFile = File(...)):
    """
    Convert document pages to images using Aspose.Words.
    Note: Aspose.Words usually needs a physical file or stream.
    """
    try:
        # Save temp file for Aspose as it works best with paths or streams
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        doc = aw.Document(temp_path)
        output_files = []
        
        for page in range(0, doc.page_count):
            extracted_page = doc.extract_pages(page, 1)
            output_filename = f"Output_{page + 1}.jpg"
            output_path = os.path.join(UPLOAD_FOLDER, output_filename)
            extracted_page.save(output_path)
            output_files.append(output_filename)
            
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {
            "code": 200, 
            "message": "Successfully converted document to images", 
            "pages": doc.page_count,
            "files": output_files
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Error processing document", "data": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
