#!/usr/bin/env python3
"""
Flask API for image conversion to LVGL format with resizing
This application takes an image, resizes it, and converts it to LVGL format.
"""

import os
import tempfile
from urllib.parse import urlparse

import requests
from flask import Flask, request, jsonify, send_file

# Import the resize_image function
from resize_image import resize_image

# Import LVGLImage
from LVGLImage.LVGLImage import LVGLImage, ColorFormat, OutputFormat, CompressMethod

app = Flask(__name__)

# Set maximum file size for uploads (16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Create temp directory for processing
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'lvgl_converter')
os.makedirs(TEMP_DIR, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_enum_value(enum_class, value_str):
    """Convert string to enum value safely"""
    try:
        return getattr(enum_class, value_str)
    except AttributeError:
        return None

@app.route('/convert', methods=['POST'])
def convert_image():
    """Convert an image to LVGL format with optional resizing"""
    # Create temporary files
    temp_input = os.path.join(TEMP_DIR, 'input.png')
    temp_resized = os.path.join(TEMP_DIR, 'resized.png')
    temp_output = os.path.join(TEMP_DIR, 'output.bin')

    # Handle file uploads (multipart/form-data) or JSON parameters with URL
    if request.files and 'image' in request.files:
        print("Received file upload")
        # Process file upload (requires multipart/form-data)
        file = request.files['image']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only JPG and PNG are supported.'}), 400
        file.save(temp_input)

        # Extract JSON parameters from the form data if available
        data = {}
        try:
            if request.form.get('params'):
                import json
                data = json.loads(request.form.get('params'))
                print(f"Extracted JSON parameters from form: {data}")
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in params field'}), 400
    elif request.is_json:
        # Process JSON request with URL
        data = request.json
        print(f"Received JSON data: {data}")

        # Download image from URL
        if 'url' not in data:
            return jsonify({'error': 'No URL provided in JSON'}), 400

        url = data['url']
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({'error': 'Invalid URL provided'}), 400

            # Download image
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith(('image/jpeg', 'image/png')):
                return jsonify({'error': 'URL does not point to a JPG or PNG image'}), 400

            # Save to temp file
            with open(temp_input, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Error downloading image: {str(e)}'}), 400
    else:
        return jsonify({'error': 'No image file or URL provided'}), 400

    # Get resize parameters from JSON data
    width = None
    height = None

    # Parse maxSize if provided (format: "800x480")
    if 'maxSize' in data:
        max_size = data['maxSize']
        if isinstance(max_size, str) and 'x' in max_size:
            try:
                width, height = map(int, max_size.split('x'))
            except ValueError:
                return jsonify({'error': 'Invalid maxSize format. Use "widthxheight", e.g. "800x480"'}), 400
        elif isinstance(max_size, dict) and 'width' in max_size and 'height' in max_size:
            # Alternative format: {"maxSize": {"width": 800, "height": 480}}
            width = max_size.get('width')
            height = max_size.get('height')

    # Validate resize parameters
    if not width and not height:
        # No resizing requested, just copy the file
        temp_resized = temp_input
    elif not width or not height:
        # Only one dimension specified
        target_size = width if width else height
        try:
            temp_resized = resize_image(temp_input, temp_resized, target_size)
        except Exception as e:
            return jsonify({'error': f'Error resizing image: {str(e)}'}), 500
    else:
        # Both dimensions specified
        try:
            temp_resized = resize_image(temp_input, temp_resized, (width, height))
        except Exception as e:
            return jsonify({'error': f'Error resizing image: {str(e)}'}), 500

    # Get color format from JSON data
    color_format_str = data.get('cf', 'RGB565')
    color_format = get_enum_value(ColorFormat, color_format_str)
    if not color_format:
        return jsonify({'error': f'Invalid color format: {color_format_str}'}), 400

    # Get output format (BIN or C_ARRAY)
    output_type = data.get('output', 'bin')
    # Map JSON output formats to OutputFormat enum values
    output_map = {
        'bin': 'BIN_FILE',
        'c_array': 'C_ARRAY'
    }
    output_format_str = output_map.get(output_type, 'BIN_FILE')
    output_format = get_enum_value(OutputFormat, output_format_str)
    if not output_format:
        return jsonify({'error': f'Invalid output format: {output_type}'}), 400

    # Get dithering option
    dithering = data.get('dithering', False)

    # Get compression option
    compression_str = data.get('compression', 'NONE')
    compression = get_enum_value(CompressMethod, compression_str)
    if not compression:
        return jsonify({'error': f'Invalid compression: {compression_str}'}), 400

    # Convert image to LVGL format
    try:
        # Apply dithering if requested and using RGB565
        if dithering and not color_format in [ColorFormat.RGB565, ColorFormat.RGB565A8]:
            dithering = False  # Dithering only applies to RGB565 formats

        # Create LVGLImage from resized image
        lvgl_img = LVGLImage().from_png(temp_resized, cf=color_format, rgb565_dither=dithering)

        # Generate output based on format
        if output_format == OutputFormat.BIN_FILE:
            lvgl_img.to_bin(temp_output, compress=compression)
            mime_type = 'application/octet-stream'
            filename = 'output.bin'
        else:  # C_ARRAY
            temp_output = os.path.join(TEMP_DIR, 'output.c')
            lvgl_img.to_c_array(temp_output, compress=compression, outputname='lvgl_image')
            mime_type = 'text/plain'
            filename = 'output.c'

        # Return the file
        return send_file(
            temp_output,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'Error converting image: {str(e)}'}), 500

@app.route('/formats', methods=['GET'])
def get_formats():
    """Return available color formats, output formats and compression options"""
    return jsonify({
        'color_formats': [format.name for format in ColorFormat],
        'output_formats': [format.name for format in OutputFormat],
        'compression_options': [comp.name for comp in CompressMethod],
        'api': {
            'url_endpoint': {
                'method': 'POST',
                'url': '/convert',
                'content_type': 'application/json',
                'parameters': {
                    'url': 'URL to the image (string)',
                    'cf': 'Color format (e.g. RGB565A8)',
                    'output': 'Output format (bin, c_array)',
                    'maxSize': 'Max dimensions as WIDTHxHEIGHT (e.g. "800x480") or {width: 800, height: 480}',
                    'dithering': 'Apply dithering (boolean)',
                    'compression': 'Compression method (NONE, RLE, LZ4)'
                },
                'example': {
                    'url': 'https://example.com/image.png',
                    'cf': 'RGB565A8',
                    'output': 'bin',
                    'maxSize': '800x480',
                    'dithering': True,
                    'compression': 'NONE'
                }
            },
            'file_upload_endpoint': {
                'method': 'POST',
                'url': '/convert',
                'content_type': 'multipart/form-data',
                'parameters': {
                    'image': 'Image file (JPG or PNG)',
                    'params': 'JSON string with the same parameters as the URL endpoint'
                }
            }
        }
    })

@app.route('/', methods=['GET'])
def index():
    """Return API information"""
    response = {
        'name': 'LVGL Image Converter API',
        'description': 'Resize and convert images to LVGL format',
        'endpoints': {
            '/convert': 'POST - Convert an image (JSON or file upload)',
            '/formats': 'GET - List available formats and API documentation'
        },
        'usage': 'See /formats for detailed API documentation'
    }
    print("Root endpoint accessed, returning:", response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
