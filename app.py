from flask import Flask, render_template, request, redirect, url_for,json,jsonify,send_from_directory
from PIL import Image
import numpy as np
import cv2
import os
from rembg import remove

app = Flask(__name__,template_folder='templates')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

# Route to serve static files (e.g., images)
@app.route('/uploads/<path:filename>')
def serve_static(filename):
    return send_from_directory('uploads', filename)

@app.route('/backgroundRemove', methods=['POST'])
def process():
    try:
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # print(file)
        if file.filename == '':
            return redirect(request.url)
        if file:
            # Save the file temporarily
            filename = 'input.jpg'  
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # print(file_path)
            input_image = Image.open(file_path)
            # Convert RGBA image to RGB
            input_image = input_image.convert("RGB")
            # Convert the input image to a numpy array
            input_array = np.array(input_image)
            # Apply background removal using rembg
            output_array = remove(input_array)
            # Create a PIL Image from the output array
            output_image = Image.fromarray(output_array)
            # print(output_image)
            output_image = output_image.convert("RGB")
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_image.jpg')
            output_image.save(output_file_path)
            # output_image.save('uploads/output_image.jpg')
            if os.path.exists(file_path):
                os.remove(file_path)
            # output_image_path = os.path.join(app.config['UPLOAD_FOLDER'],output_image)  # Output file path
            # output_image.save(output_image_path)  # Save processed image
            return send_from_directory('uploads', 'output_image.jpg')

             # return render_template('result.html', image_path=processed_image_path)
    except Exception as e: 
        print(e)
        return jsonify({"code" :500,"message" : "error processing","data" : str(e)});


@app.route('/backgroundWithWhite', methods=['POST'])
def backgroundWithWhite():
    try:
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # print(file)
        if file.filename == '':
            return redirect(request.url)
        if file:
            # Save the file temporarily
            filename = 'input.jpg'  
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # print(file_path)
            input_image = Image.open(file_path)
            # Convert RGBA image to RGB
            input_image = input_image.convert("RGB")
            # Convert the input image to a numpy array
            input_array = np.array(input_image)
            # Apply background removal using rembg
            output_array = remove(input_array)
                    
            # Create a PIL Image from the output array
            output_image = Image.fromarray(output_array)
            
            # Ensure output image contains transparency
            if output_image.mode != "RGBA":
                output_image = output_image.convert("RGBA")
            
            # Create a new image with white background
            new_image = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
            
            # Paste the output image onto the new image with white background
            new_image.paste(output_image, (0, 0), output_image)
            
            # Save the result with white background
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'white_image.png')
            new_image.save(output_file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            return send_from_directory('uploads', 'white_image.png')

             # return render_template('result.html', image_path=processed_image_path)
    except Exception as e: 
        print(e)
        return jsonify({"code" :500,"message" : "error processing","data" : str(e)});


