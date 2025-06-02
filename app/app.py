"""
Application Flask de reconnaissance de chiffres manuscrits - Version simplifiée
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import datetime
import os
import sys
import uuid
import base64
import random
import glob
import re
from PIL import Image

# Configuration des chemins
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Ajouter le répertoire racine au chemin Python
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.CNN_MODEL import CNN_MODEL

# Créer l'application Flask - CONFIGURATION SIMPLIFIÉE
app = Flask(__name__)  # Configuration par défaut

# Répertoires
UPLOAD_FOLDER = os.path.join(APP_DIR, 'static', 'uploads')
TEMP_FOLDER = os.path.join(APP_DIR, 'static', 'temp')
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'best_cnn_model.keras')

def ensure_directories():
    """Créer tous les répertoires nécessaires"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    print(f"✓ Upload: {UPLOAD_FOLDER}")
    print(f"✓ Temp: {TEMP_FOLDER}")

ensure_directories()

# Charger le modèle
print(f"Chargement du modèle: {MODEL_PATH}")
cnn_model = CNN_MODEL(MODEL_PATH)

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

def get_prediction_files():
    """Récupère les 10 dernières prédictions générées."""
    prediction_pattern = os.path.join(TEMP_FOLDER, 'prediction_*.png')
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
    """Extrait les informations de prédiction à partir du nom de fichier et des métadonnées."""
    filename = os.path.basename(file_path)
    timestamp_pattern = re.compile(r'prediction_(\d+)\.png')
    match = timestamp_pattern.match(filename)
    timestamp = int(match.group(1)) if match else 0
    
    # Essayer de récupérer les vraies données de prédiction depuis le fichier de métadonnées
    metadata_file = file_path.replace('.png', '_metadata.json')
    
    # Valeurs par défaut si pas de métadonnées
    digit = random.randint(0, 9)
    confidence = random.uniform(80, 100)
    
    # Si on a un fichier de métadonnées, l'utiliser
    if os.path.exists(metadata_file):
        try:
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                digit = metadata.get('predicted_digit', digit)
                confidence = metadata.get('confidence', confidence)
        except:
            pass  # Utiliser les valeurs par défaut en cas d'erreur
    
    date = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
    
    return {
        'timestamp': timestamp,
        'digit': digit,
        'confidence': confidence,
        'date': date,
        'plot_path': 'temp/' + filename
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    prediction_files = get_prediction_files()
    predictions = [get_prediction_info(file_path) for _, _, file_path in prediction_files]
    
    start_separator = random.randint(1, 5)
    separators = []
    
    for i in range(len(predictions) - 1):
        separator_index = ((start_separator + i - 1) % 5) + 1
        separators.append(f"{separator_index}.svg")
    
    return render_template('history.html', predictions=predictions, separators=separators)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    result = None
    error = None
    
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                result = cnn_model.get_prediction_for_web(image_path=filepath, temp_folder=TEMP_FOLDER)
                result['original_image'] = 'uploads/' + filename
                
        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_binary = base64.b64decode(image_data)
            filename = str(uuid.uuid4()) + '.png'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(image_binary)
            
            result = cnn_model.get_prediction_for_web(image_path=filepath, temp_folder=TEMP_FOLDER)
            result['original_image'] = 'uploads/' + filename
        
        else:
            error = "Aucune image n'a été fournie."
            
    except Exception as e:
        error = f"Erreur: {str(e)}"
        print(f"ERREUR: {error}")
        import traceback
        traceback.print_exc()
    
    if error:
        return jsonify({'error': error}), 400
    
    return render_template('result.html', result=result)

@app.route('/api/predict', methods=['POST'])
def api_predict():
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
            
        return jsonify({'error': 'Aucune image fournie'}), 400
        
    except Exception as e:
        print(f"Erreur dans api_predict: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-and-save', methods=['POST'])
def api_predict_and_save():
    """API endpoint qui fait la prédiction, sauvegarde pour l'historique ET retourne JSON"""
    try:
        filepath = None
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Sauvegarder le fichier uploadé pour l'historique
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Générer le graphique et les résultats pour l'historique
                web_result = cnn_model.get_prediction_for_web(image_path=filepath, temp_folder=TEMP_FOLDER)
                
                # Aussi obtenir les données pour l'AJAX
                ajax_results, processed_image = cnn_model.predict_from_image(image_path=filepath)
        
        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Sauvegarder l'image canvas pour l'historique
            image_binary = base64.b64decode(image_data)
            filename = str(uuid.uuid4()) + '.png'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(image_binary)
            
            # Générer le graphique et les résultats pour l'historique
            web_result = cnn_model.get_prediction_for_web(image_path=filepath, temp_folder=TEMP_FOLDER)
            
            # Aussi obtenir les données pour l'AJAX
            ajax_results, processed_image = cnn_model.predict_from_image(image_path=filepath)
        else:
            return jsonify({'error': 'Aucune image fournie'}), 400
        
        # Ajouter l'image redimensionnée en base64 pour l'affichage AJAX
        if processed_image is not None:
            from PIL import Image as PILImage
            import io
            
            img_array = processed_image[0, :, :, 0]
            img_array = (img_array * 255).astype('uint8')
            
            pil_img = PILImage.fromarray(img_array, mode='L')
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            ajax_results['resized_image_base64'] = f"data:image/png;base64,{img_base64}"
        
        # Ajouter des métadonnées pour l'historique
        ajax_results['saved_to_history'] = True
        ajax_results['plot_path'] = web_result.get('plot_path', '') if web_result else ''
        ajax_results['original_image'] = f"uploads/{filename}" if filepath else ''
        
        return jsonify(ajax_results)
        
    except Exception as e:
        print(f"Erreur dans api_predict_and_save: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/debug')
def debug_paths():
    """Route de debug pour vérifier les chemins"""
    import glob
    css_files = glob.glob(os.path.join(APP_DIR, 'static', 'css', '*.css'))
    
    return jsonify({
        'app_dir': APP_DIR,
        'project_root': PROJECT_ROOT,
        'static_folder': app.static_folder,
        'template_folder': app.template_folder,
        'css_files_found': css_files,
        'css_files_exist': [os.path.exists(f) for f in css_files]
    })

if __name__ == '__main__':
    print("=== DÉMARRAGE APPLICATION ===")
    print(f"APP_DIR: {APP_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    print("============================")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
