"""
Configuration centralisée pour l'application de reconnaissance de chiffres
"""
import os

# Répertoire racine du projet
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Répertoires principaux
APP_DIR = os.path.join(PROJECT_ROOT, 'app')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Répertoires statiques
STATIC_DIR = os.path.join(APP_DIR, 'static')
TEMPLATES_DIR = os.path.join(APP_DIR, 'templates')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'uploads')
TEMP_DIR = os.path.join(STATIC_DIR, 'temp')
CSS_DIR = os.path.join(STATIC_DIR, 'css')
JS_DIR = os.path.join(STATIC_DIR, 'js')

# Modèles
BEST_MODEL_PATH = os.path.join(MODELS_DIR, 'best_cnn_model.keras')

def ensure_directories():
    """Créer tous les répertoires nécessaires"""
    directories = [
        UPLOAD_DIR,
        TEMP_DIR,
        CSS_DIR,
        JS_DIR,
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Répertoire: {directory} - Existe: {os.path.exists(directory)}")

def get_relative_path_for_flask(absolute_path, static_folder):
    """
    Convertit un chemin absolu en chemin relatif pour Flask
    
    Args:
        absolute_path (str): Chemin absolu du fichier
        static_folder (str): Dossier static de Flask
        
    Returns:
        str: Chemin relatif pour Flask
    """
    try:
        return os.path.relpath(absolute_path, static_folder)
    except ValueError:
        # Si les chemins sont sur des disques différents, utiliser le nom de fichier
        return os.path.basename(absolute_path)

if __name__ == "__main__":
    print("Configuration des chemins:")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"APP_DIR: {APP_DIR}")
    print(f"STATIC_DIR: {STATIC_DIR}")
    print(f"UPLOAD_DIR: {UPLOAD_DIR}")
    print(f"TEMP_DIR: {TEMP_DIR}")
    print(f"BEST_MODEL_PATH: {BEST_MODEL_PATH}")
    
    ensure_directories()
