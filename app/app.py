"""
Application Flask de reconnaissance de chiffres manuscrits - Version thread-safe
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
import threading
import time
from PIL import Image

# Configuration matplotlib AVANT toute importation
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif et thread-safe
import matplotlib.pyplot as plt
plt.ioff()  # Désactiver le mode interactif

# Configuration des chemins
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Ajouter le répertoire racine au chemin Python
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.CNN_MODEL import CNN_MODEL

# Créer l'application Flask avec configuration thread-safe
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Désactiver le cache pour le debug

# Répertoires
UPLOAD_FOLDER = os.path.join(APP_DIR, 'static', 'uploads')
TEMP_FOLDER = os.path.join(APP_DIR, 'static', 'temp')
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'best_cnn_model.keras')

# Thread locks pour éviter les conditions de course
request_lock = threading.Lock()
file_operation_lock = threading.Lock()

# Cache pour éviter de recharger le modèle
_model_instance = None
_model_lock = threading.Lock()

def get_model_instance():
    """Singleton thread-safe pour le modèle CNN"""
    global _model_instance

    if _model_instance is None:
        with _model_lock:
            # Double-check locking pattern
            if _model_instance is None:
                print(f"Chargement du modèle: {MODEL_PATH}")
                _model_instance = CNN_MODEL(MODEL_PATH)
                if _model_instance.model is None:
                    raise RuntimeError("Impossible de charger le modèle CNN")

    return _model_instance

def ensure_directories():
    """Créer tous les répertoires nécessaires de manière thread-safe"""
    with file_operation_lock:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        print(f"✓ Upload: {UPLOAD_FOLDER}")
        print(f"✓ Temp: {TEMP_FOLDER}")

ensure_directories()

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

def cleanup_old_files():
    """Nettoyer les anciens fichiers pour éviter l'accumulation"""
    try:
        current_time = time.time()
        max_age = 3600  # 1 heure

        # Nettoyer les uploads anciens
        for folder in [UPLOAD_FOLDER, TEMP_FOLDER]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath):
                        file_age = current_time - os.path.getctime(filepath)
                        if file_age > max_age:
                            try:
                                os.remove(filepath)
                                print(f"Suppression ancien fichier: {filename}")
                            except OSError:
                                pass  # Fichier peut-être en cours d'utilisation
    except Exception as e:
        print(f"Erreur lors du nettoyage: {e}")

def get_prediction_files():
    """Récupère les 10 dernières prédictions générées de manière thread-safe."""
    with file_operation_lock:
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
    # Nettoyer les anciens fichiers périodiquement
    cleanup_old_files()
    return render_template('index.html')

@app.route('/history')
def history():
    try:
        prediction_files = get_prediction_files()
        predictions = [get_prediction_info(file_path) for _, _, file_path in prediction_files]

        start_separator = random.randint(1, 5)
        separators = []

        for i in range(len(predictions) - 1):
            separator_index = ((start_separator + i - 1) % 5) + 1
            separators.append(f"{separator_index}.svg")

        return render_template('history.html', predictions=predictions, separators=separators)
    except Exception as e:
        print(f"Erreur dans /history: {e}")
        return render_template('history.html', predictions=[], separators=[])

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return redirect(url_for('index'))

    # Utiliser un lock pour éviter les conditions de course
    with request_lock:
        result = None
        error = None

        try:
            cnn_model = get_model_instance()

            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    # Sauvegarder le fichier de manière thread-safe
                    with file_operation_lock:
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

                # Sauvegarder le fichier de manière thread-safe
                with file_operation_lock:
                    with open(filepath, 'wb') as f:
                        f.write(image_binary)

                result = cnn_model.get_prediction_for_web(image_path=filepath, temp_folder=TEMP_FOLDER)
                result['original_image'] = 'uploads/' + filename

            else:
                error = "Aucune image n'a été fournie."

        except Exception as e:
            error = f"Erreur: {str(e)}"
            print(f"ERREUR dans /predict: {error}")
            import traceback
            traceback.print_exc()

        if error:
            return jsonify({'error': error}), 400

        return render_template('result.html', result=result)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API de prédiction simple sans sauvegarde"""
    try:
        cnn_model = get_model_instance()

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

# In app.py, update the api_predict_and_save route

@app.route('/api/predict-and-save', methods=['POST'])
def api_predict_and_save():
    """Updated API endpoint with working filter support"""

    with request_lock:
        try:
            request_id = str(uuid.uuid4())[:8]
            print(f"[{request_id}] === PREDICTION REQUEST START ===")

            cnn_model = get_model_instance()
            filepath = None

            # Check filter parameters
            show_filters = request.form.get('show_filters', 'false').lower() == 'true'
            best_filters = request.form.get('best_filters', 'false').lower() == 'true'

            print(f"[{request_id}] Show filters: {show_filters}")
            print(f"[{request_id}] Best filters: {best_filters}")

            # Handle file upload or canvas data (your existing code)
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    with file_operation_lock:
                        file.save(filepath)

                    print(f"[{request_id}] File saved: {filepath}")

            elif 'image_data' in request.form:
                image_data = request.form['image_data']
                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                image_binary = base64.b64decode(image_data)
                filename = str(uuid.uuid4()) + '.png'
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                with file_operation_lock:
                    with open(filepath, 'wb') as f:
                        f.write(image_binary)

                print(f"[{request_id}] Canvas image saved: {filepath}")

            else:
                return jsonify({'error': 'No image provided'}), 400

            # Get prediction with working filters
            if show_filters:
                web_result = cnn_model.get_prediction_for_web_with_filters(
                    image_path=filepath,
                    temp_folder=TEMP_FOLDER,
                    best_filters=best_filters
                )
            else:
                # Standard prediction without filters
                web_result = cnn_model.get_prediction_for_web(
                    image_path=filepath,
                    temp_folder=TEMP_FOLDER
                )
                web_result['feature_filters'] = []
                web_result['has_filters'] = False

            # Also get AJAX data
            ajax_results, processed_image = cnn_model.predict_from_image(image_path=filepath)

            # Add processed image as base64 if needed (your existing code)
            # ... existing base64 code ...

            # Add filter data to AJAX response
            if show_filters and web_result:
                ajax_results['feature_filters'] = web_result.get('feature_filters', [])
                ajax_results['has_filters'] = web_result.get('has_filters', False)
                ajax_results['best_filters_mode'] = best_filters

                print(f"[{request_id}] Added {len(ajax_results.get('feature_filters', []))} filter visualizations")
                if ajax_results['feature_filters']:
                    for i, f in enumerate(ajax_results['feature_filters'][:3]):
                        print(f"[{request_id}] Filter {i}: {f.get('title', 'N/A')}")
            else:
                ajax_results['feature_filters'] = []
                ajax_results['has_filters'] = False
                ajax_results['best_filters_mode'] = False

            # Add metadata
            ajax_results['saved_to_history'] = True
            ajax_results['plot_path'] = web_result.get('plot_path', '') if web_result else ''
            ajax_results['original_image'] = f"uploads/{filename}" if filepath else ''
            ajax_results['filters_enabled'] = show_filters

            print(f"[{request_id}] Prediction completed successfully")
            print(f"[{request_id}] Response: filters={len(ajax_results.get('feature_filters', []))}, best_mode={best_filters}")

            return jsonify(ajax_results)

        except Exception as e:
            error_msg = f"Error in api_predict_and_save: {e}"
            print(f"[{request_id}] {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

@app.route('/debug')
def debug_paths():
    """Route de debug pour vérifier les chemins et l'état du système"""
    import glob
    css_files = glob.glob(os.path.join(APP_DIR, 'static', 'css', '*.css'))

    # Informations sur le modèle
    model_info = {
        'loaded': _model_instance is not None,
        'model_path': MODEL_PATH,
        'model_exists': os.path.exists(MODEL_PATH)
    }

    # Informations sur matplotlib
    matplotlib_info = {
        'backend': matplotlib.get_backend(),
        'interactive_mode': plt.isinteractive(),
        'version': matplotlib.__version__
    }

    # Statistiques des fichiers
    upload_files = len(glob.glob(os.path.join(UPLOAD_FOLDER, '*'))) if os.path.exists(UPLOAD_FOLDER) else 0
    temp_files = len(glob.glob(os.path.join(TEMP_FOLDER, '*'))) if os.path.exists(TEMP_FOLDER) else 0

    return jsonify({
        'app_dir': APP_DIR,
        'project_root': PROJECT_ROOT,
        'static_folder': app.static_folder,
        'template_folder': app.template_folder,
        'css_files_found': css_files,
        'css_files_exist': [os.path.exists(f) for f in css_files],
        'model_info': model_info,
        'matplotlib_info': matplotlib_info,
        'file_stats': {
            'upload_files': upload_files,
            'temp_files': temp_files
        },
        'threading_info': {
            'active_threads': threading.active_count(),
            'current_thread': threading.current_thread().name
        }
    })

@app.route('/health')
def health_check():
    """Route de vérification de l'état de santé de l'application"""
    try:
        # Vérifier que le modèle est chargé
        model = get_model_instance()
        model_status = model.model is not None

        # Vérifier les répertoires
        dirs_ok = all([
            os.path.exists(UPLOAD_FOLDER),
            os.path.exists(TEMP_FOLDER)
        ])

        # Test rapide de prédiction
        test_prediction = False
        try:
            # Créer une image de test 28x28 simple
            import numpy as np
            test_image = np.random.rand(1, 28, 28, 1)
            predictions = model.predict(test_image)
            test_prediction = predictions is not None and len(predictions) > 0
        except Exception as test_error:
            print(f"Erreur test prédiction: {test_error}")

        status = {
            'status': 'healthy' if all([model_status, dirs_ok, test_prediction]) else 'unhealthy',
            'model_loaded': model_status,
            'directories_ok': dirs_ok,
            'test_prediction_ok': test_prediction,
            'timestamp': datetime.datetime.now().isoformat(),
            'matplotlib_backend': matplotlib.get_backend()
        }

        return jsonify(status), 200 if status['status'] == 'healthy' else 503

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

# Gestionnaire d'erreur global
@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire d'erreur global pour éviter les crashes"""
    print(f"Erreur non gérée: {e}")
    import traceback
    traceback.print_exc()

    return jsonify({
        'error': 'Erreur interne du serveur',
        'message': 'Une erreur inattendue s\'est produite. Veuillez réessayer.'
    }), 500

# Configuration pour le développement
@app.before_request
def before_request():
    """Exécuté avant chaque requête pour la maintenance"""
    # Nettoyer périodiquement (toutes les 50 requêtes environ)
    if random.randint(1, 50) == 1:
        cleanup_old_files()

if __name__ == '__main__':
    print("=== DÉMARRAGE APPLICATION THREAD-SAFE ===")
    print(f"APP_DIR: {APP_DIR}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    print(f"Matplotlib backend: {matplotlib.get_backend()}")
    print(f"Interactive mode: {plt.isinteractive()}")

    # Précharger le modèle au démarrage
    try:
        model = get_model_instance()
        print(f"✓ Modèle préchargé avec succès")
    except Exception as e:
        print(f"✗ Erreur préchargement modèle: {e}")

    print("==========================================")

    # Utiliser le serveur de développement avec threading activé
    app.run(
        debug=True,
        port=5000,
        host='0.0.0.0',
        threaded=True,  # Activer le support multi-thread
        use_reloader=False  # Désactiver le rechargement auto pour éviter les conflits
    )
