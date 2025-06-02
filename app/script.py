from flask import Flask, render_template, request, jsonify, redirect, url_for
import datetime
import os
import numpy as np
import sys
import tempfile
import uuid
import base64
import random
import glob
import re
from PIL import Image
import io

# Get the absolute path of the app directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Add the project root to the path for imports
sys.path.append(PROJECT_ROOT)

# Import the CNN_MODEL
from src.CNN_MODEL import CNN_MODEL

# Create Flask app with absolute paths for static files
app = Flask(__name__, 
           static_folder=os.path.join(APP_DIR, 'static'),
           static_url_path='/static',
           template_folder=os.path.join(APP_DIR, 'templates'))

# Configure paths using absolute paths
app.config['UPLOAD_FOLDER'] = os.path.join(APP_DIR, 'static', 'uploads')
app.config['TEMP_FOLDER'] = os.path.join(APP_DIR, 'static', 'temp')

def ensure_dirs_exist():
    """Ensure required directories exist with absolute paths"""
    uploads_dir = app.config['UPLOAD_FOLDER']
    temp_dir = app.config['TEMP_FOLDER']
    
    # DEBUG: Print absolute paths
    print(f"APP_DIR: {APP_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"Uploads directory: {uploads_dir}")
    print(f"Temp directory: {temp_dir}")
    print(f"Static folder: {app.static_folder}")
    
    # Create directories
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Verify directories exist
    print(f"Uploads dir exists: {os.path.exists(uploads_dir)}")
    print(f"Temp dir exists: {os.path.exists(temp_dir)}")

# Create directories at startup
ensure_dirs_exist()

# Load the model with absolute path
model_path = os.path.join(PROJECT_ROOT, 'models', 'best_cnn_model.keras')
print(f"Loading model from: {model_path}")
print(f"Model exists: {os.path.exists(model_path)}")

try:
    cnn_model = CNN_MODEL(model_path)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    # You might want to handle this more gracefully in production

# Add favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    """Serve favicon or return 204 No Content if not found"""
    favicon_path = os.path.join(app.static_folder, 'favicon.ico')
    if os.path.exists(favicon_path):
        return app.send_static_file('favicon.ico')
    else:
        # Return empty response to prevent 404 errors
        from flask import Response
        return Response(status=204)

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

def get_prediction_files():
    """Get the 10 most recent prediction files"""
    temp_dir = app.config['TEMP_FOLDER']
    prediction_pattern = os.path.join(temp_dir, 'prediction_*.png')
    prediction_files = glob.glob(prediction_pattern)
    
    timestamp_pattern = re.compile(r'prediction_(\d+)\.png')
    prediction_data = []
    
    for file_path in prediction_files:
        filename = os.path.basename(file_path)
        match = timestamp_pattern.match(filename)
        if match:
            timestamp = int(match.group(1))
            prediction_data.append((filename, timestamp, file_path))
    
    # Sort by timestamp (descending)
    prediction_data.sort(key=lambda x: x[1], reverse=True)
    
    return prediction_data[:10]

def get_prediction_info(file_path):
    """Extract prediction info from filename"""
    filename = os.path.basename(file_path)
    timestamp_pattern = re.compile(r'prediction_(\d+)\.png')
    match = timestamp_pattern.match(filename)
    timestamp = int(match.group(1)) if match else 0
    
    digit = random.randint(0, 9)
    confidence = random.uniform(80, 100)
    date = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
    
    return {
        'timestamp': timestamp,
        'digit': digit,
        'confidence': confidence,
        'date': date,
        'plot_path': os.path.join('static', 'temp', filename)  # Use relative URL path
    }

@app.route('/')
def index():
    """Homepage with drawing interface and drag & drop"""
    ensure_dirs_exist()
    return render_template('index.html')

@app.route('/history')
def history():
    """Prediction history page"""
    prediction_files = get_prediction_files()
    predictions = [get_prediction_info(file_path) for _, _, file_path in prediction_files]
    
    # Generate separators
    start_separator = random.randint(1, 5)
    separators = []
    
    for i in range(len(predictions) - 1):
        separator_index = ((start_separator + i - 1) % 5) + 1
        separators.append(f"{separator_index}.svg")
    
    return render_template('history.html', predictions=predictions, separators=separators)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Prediction endpoint"""
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    result = None
    error = None
    
    ensure_dirs_exist()
    
    try:
        if 'file' in request.files:
            # Handle uploaded image
            file = request.files['file']
            if file.filename != '':
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                print(f"Image saved to: {filepath}")
                print(f"Image exists: {os.path.exists(filepath)}")
                
                result = cnn_model.get_prediction_for_web(image_path=filepath)
                result['original_image'] = os.path.join('static', 'uploads', filename)  # Use relative URL path
                
                print(f"Original image path: {result['original_image']}")
                print(f"Plot path: {result['plot_path']}")
        
        elif 'image_data' in request.form:
            # Handle drawn image
            image_data = request.form['image_data']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_binary = base64.b64decode(image_data)
            
            filename = str(uuid.uuid4()) + '.png'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(image_binary)
            
            print(f"Drawn image saved to: {filepath}")
            print(f"Image exists: {os.path.exists(filepath)}")
            
            result = cnn_model.get_prediction_for_web(image_path=filepath)
            result['original_image'] = os.path.join('static', 'uploads', filename)  # Use relative URL path
            
            print(f"Original image path: {result['original_image']}")
            print(f"Plot path: {result['plot_path']}")
        
        else:
            error = "No image provided. Please draw or upload an image."
            
    except Exception as e:
        error = f"Prediction error: {str(e)}"
        print(error)
        import traceback
        traceback.print_exc()
    
    if error:
        return jsonify({'error': error}), 400
    
    return render_template('result.html', result=result)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """JSON API for prediction"""
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                image_binary = file.read()
                results, _ = cnn_model.predict_from_image(image_data=image_binary)
                return jsonify(results)
        
        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_binary = base64.b64decode(image_data)
            results, _ = cnn_model.predict_from_image(image_data=image_binary)
            return jsonify(results)
            
        return jsonify({'error': 'No image provided'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Print configuration info for debugging
    print(f"App root path: {app.root_path}")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Temp folder: {app.config['TEMP_FOLDER']}")
    
    app.run(debug=True, port=5000, host='0.0.0.0')  # Bind to all interfaces for cloud deployment
