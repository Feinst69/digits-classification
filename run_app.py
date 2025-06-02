"""
Enhanced launch script for the digit recognition application
Fixed to handle cross-platform deployment and cloud services
"""
import os
import sys
import subprocess

def main():
    """
    Launch Flask application with proper environment setup
    """
    # Get absolute paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(project_root, 'app')
    app_script = os.path.join(app_dir, 'script.py')
    
    print(f"Project root: {project_root}")
    print(f"App directory: {app_dir}")
    print(f"App script: {app_script}")
    
    # Verify that the script exists
    if not os.path.exists(app_script):
        print(f"Error: Application script does not exist at {app_script}")
        sys.exit(1)
    
    # Create necessary directories with absolute paths
    static_dir = os.path.join(app_dir, 'static')
    temp_dir = os.path.join(static_dir, 'temp')
    uploads_dir = os.path.join(static_dir, 'uploads')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    
    # Ensure all directories exist
    directories_to_create = [static_dir, temp_dir, uploads_dir, css_dir, js_dir]
    
    for directory in directories_to_create:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory {directory} exists: {os.path.exists(directory)}")
    
    # Verify static files exist
    static_files_to_check = [
        os.path.join(css_dir, 'styles.css'),
        os.path.join(css_dir, 'history_styles.css'),
        os.path.join(js_dir, 'draw.js'),
        os.path.join(js_dir, 'upload.js')
    ]
    
    print("\nStatic files check:")
    for file_path in static_files_to_check:
        exists = os.path.exists(file_path)
        print(f"  {os.path.basename(file_path)}: {'✓' if exists else '✗'}")
        if not exists:
            print(f"    Missing: {file_path}")
    
    # Check if models directory exists
    models_dir = os.path.join(project_root, 'models')
    print(f"\nModels directory exists: {os.path.exists(models_dir)}")
    if os.path.exists(models_dir):
        model_files = os.listdir(models_dir)
        print(f"Model files: {model_files}")
    
    # Set environment variables for the Flask app
    env = os.environ.copy()
    env['FLASK_APP'] = app_script
    env['FLASK_ENV'] = 'production'  # Change to 'development' for debugging
    env['PYTHONPATH'] = project_root
    
    print(f"\nLaunching Flask application...")
    print(f"Working directory: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    try:
        # Stay in project root directory (don't change to app dir)
        # This ensures relative imports work correctly
        os.chdir(project_root)
        
        # Run the Flask application
        result = subprocess.run([
            sys.executable, 
            os.path.join('app', 'script.py')
        ], env=env, cwd=project_root)
        
        return result.returncode
        
    except Exception as e:
        print(f"Error launching application: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
