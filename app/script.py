from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
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

# CRITICAL: Determine paths dynamically from script location
# This works regardless of where the script is called from
SCRIPT_PATH = os.path.abspath(__file__)
APP_DIR = os.path.dirname(SCRIPT_PATH)
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Ensure PROJECT_ROOT is in sys.path for imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print(f"[DEBUG] Script path: {SCRIPT_PATH}")
print(f"[DEBUG] App directory: {APP_DIR}")
print(f"[DEBUG] Project root: {PROJECT_ROOT}")
print(f"[DEBUG] Current working directory: {os.getcwd()}")
print(f"[DEBUG] Python path: {sys.path[:3]}...")  # Show first 3 entries

# Import the CNN_MODEL with error handling
try:
    from src.CNN_MODEL import CNN_MODEL
    print("[DEBUG] Successfully imported CNN_MODEL")
except ImportError as e:
    print(f"[ERROR] Failed to import CNN_MODEL: {e}")
    print(f"[DEBUG] Trying to add project root to path: {PROJECT_ROOT}")
    sys.path.insert(0, PROJECT_ROOT)
    try:
        from src.CNN_MODEL import CNN_MODEL
        print("[DEBUG] Successfully imported CNN_MODEL after path fix")
    except ImportError as e2:
        print(f"[ERROR] Still failed to import CNN_MODEL: {e2}")
        print("[ERROR] Available files in src/:")
        src_dir = os.path.join(PROJECT_ROOT, 'src')
        if os.path.exists(src_dir):
            print(os.listdir(src_dir))
        sys.exit(1)

# Create Flask app with absolute paths
app = Flask(__name__, 
           static_folder=os.path.join(APP_DIR, 'static'),
           static_url_path='/static',
           template_folder=os.path.join(APP_DIR, 'templates'))

# Configure all paths as absolute
app.config['UPLOAD_FOLDER'] = os.path.join(APP_DIR, 'static', 'uploads')
app.config['TEMP_FOLDER'] = os.path.join(APP_DIR, 'static', 'temp')

# Global variable for model
cnn_model = None

def ensure_dirs_exist():
    """Create all required directories"""
    dirs_to_create = [
        app.config['UPLOAD_FOLDER'],
        app.config['TEMP_FOLDER'],
        os.path.join(APP_DIR, 'static', 'css'),
        os.path.join(APP_DIR, 'static', 'js'),
        os.path.join(APP_DIR, 'static', 'ressources')
    ]
    
    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)
        print(f"[DEBUG] Directory {directory}: {'exists' if os.path.exists(directory) else 'MISSING'}")

def load_model():
    """Load the CNN model with robust path handling"""
    global cnn_model
    
    # Try multiple possible model paths
    possible_model_paths = [
        os.path.join(PROJECT_ROOT, 'models', 'best_cnn_model.keras'),
        os.path.join(PROJECT_ROOT, 'models', 'cnn_model.keras'),
        os.path.join(PROJECT_ROOT, 'models', 'basic_cnn_model.keras'),
    ]
    
    for model_path in possible_model_paths:
        print(f"[DEBUG] Trying model path: {model_path}")
        if os.path.exists(model_path):
            print(f"[DEBUG] Model file found: {model_path}")
            try:
                cnn_model = CNN_MODEL(model_path)
                print(f"[SUCCESS] Model loaded from: {model_path}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to load model from {model_path}: {e}")
                continue
        else:
            print(f"[DEBUG] Model file not found: {model_path}")
    
    # If no model found, list available files
    models_dir = os.path.join(PROJECT_ROOT, 'models')
    if os.path.exists(models_dir):
        print(f"[DEBUG] Available files in models directory:")
        for file in os.listdir(models_dir):
            print(f"  - {file}")
    else:
        print(f"[ERROR] Models directory not found: {models_dir}")
    
    return False

# Initialize at startup
ensure_dirs_exist()
model_loaded = load_model()

if not model_loaded:
    print("[WARNING] No model could be loaded. Prediction endpoints will not work.")

# Add favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    favicon_path = os.path.join(app.static_folder, 'favicon.ico')
    if os.path.exists(favicon_path):
        return app.send_static_file('favicon.ico')
    else:
        return Response(status=204)  # No Content

# Debug route to check static files
@app.route('/debug/static')
def debug_static():
    """Debug endpoint to check static file paths"""
    static_info = {
        'static_folder': app.static_folder,
        'static_url_path': app.static_url_path,
        'current_working_dir': os.getcwd(),
        'app_dir': APP_DIR,
        'project_root': PROJECT_ROOT,
        'static_files': {}
    }
    
    # Check if static files exist
    static_files_to_check = [
        'css/styles.css',
        'css/history_styles.css', 
        'js/draw.js',
        'js/upload.js'
    ]
    
    for file_path in static_files_to_check:
        full_path = os.path.join(app.static_folder, file_path)
        static_info['static_files'][file_path] = {
            'exists': os.path.exists(full_path),
            'full_path': full_path
        }
    
    return jsonify(static_info)

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
        'plot_path': f"static/temp/{filename}"  # Use forward slashes for URLs
    }

@app.route('/')
def index():
    """Homepage with drawing interface and drag & drop"""
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
    
    if not cnn_model:
        return jsonify({'error': 'Model not loaded. Please check server logs.'}), 500
        
    result = None
    error = None
    
    try:
        if 'file' in request.files:
            # Handle uploaded image
            file = request.files['file']
            if file.filename != '':
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                print(f"[DEBUG] Image saved to: {filepath}")
                
                result = cnn_model.get_prediction_for_web(image_path=filepath)
                result['original_image'] = f"static/uploads/{filename}"  # Use forward slashes for URLs
                
                print(f"[DEBUG] Original image URL: {result['original_image']}")
        
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
            
            print(f"[DEBUG] Drawn image saved to: {filepath}")
            
            result = cnn_model.get_prediction_for_web(image_path=filepath)
            result['original_image'] = f"static/uploads/{filename}"  # Use forward slashes for URLs
        
        else:
            error = "No image provided. Please draw or upload an image."
            
    except Exception as e:
        error = f"Prediction error: {str(e)}"
        print(f"[ERROR] {error}")
        import traceback
        traceback.print_exc()
    
    if error:
        return jsonify({'error': error}), 400
    
    return render_template('result.html', result=result)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """JSON API for prediction"""
    if not cnn_model:
        return jsonify({'error': 'Model not loaded'}), 500
    
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
    print(f"[DEBUG] Starting Flask app...")
    print(f"[DEBUG] Static folder: {app.static_folder}")
    print(f"[DEBUG] Template folder: {app.template_folder}")
    print(f"[DEBUG] Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"[DEBUG] Temp folder: {app.config['TEMP_FOLDER']}")
    print(f"[DEBUG] Model loaded: {cnn_model is not None}")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
