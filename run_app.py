"""
Universal launch script for the digit recognition application
Works from any directory, on any platform, with any path structure
"""
import os
import sys
import subprocess

def find_project_root():
    """
    Find the project root directory by looking for key files
    This works regardless of where the script is called from
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for distinctive project files to confirm we're in the right place
    required_files = ['app', 'models', 'src', 'requirements.txt']
    
    # Check current directory first
    if all(os.path.exists(os.path.join(current_dir, item)) for item in required_files):
        return current_dir
    
    # If not found, this script should be in the project root
    print(f"[ERROR] Project structure not found in {current_dir}")
    print(f"[DEBUG] Looking for: {required_files}")
    print(f"[DEBUG] Found in directory:")
    for item in os.listdir(current_dir):
        print(f"  - {item}")
    
    return current_dir  # Return anyway and let the app handle missing files

def main():
    """
    Launch Flask application with bulletproof path handling
    """
    print("=" * 60)
    print("DIGIT RECOGNITION APPLICATION LAUNCHER")
    print("=" * 60)
    
    # Find project root dynamically
    project_root = find_project_root()
    app_dir = os.path.join(project_root, 'app')
    app_script = os.path.join(app_dir, 'script.py')
    
    print(f"[INFO] Project root: {project_root}")
    print(f"[INFO] App directory: {app_dir}")
    print(f"[INFO] App script: {app_script}")
    print(f"[INFO] Current working directory: {os.getcwd()}")
    print(f"[INFO] Python executable: {sys.executable}")
    
    # Verify critical paths exist
    critical_paths = {
        'app_directory': app_dir,
        'app_script': app_script,
        'models_directory': os.path.join(project_root, 'models'),
        'src_directory': os.path.join(project_root, 'src'),
        'static_directory': os.path.join(app_dir, 'static')
    }
    
    print(f"\n[INFO] Checking critical paths:")
    missing_paths = []
    for name, path in critical_paths.items():
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
        if not exists:
            missing_paths.append(name)
    
    if missing_paths:
        print(f"\n[WARNING] Missing paths: {', '.join(missing_paths)}")
        print("[INFO] Continuing anyway - the app will handle missing files...")
    
    # Create necessary directories
    directories_to_create = [
        os.path.join(app_dir, 'static'),
        os.path.join(app_dir, 'static', 'css'),
        os.path.join(app_dir, 'static', 'js'),
        os.path.join(app_dir, 'static', 'temp'),
        os.path.join(app_dir, 'static', 'uploads'),
        os.path.join(app_dir, 'static', 'ressources')
    ]
    
    print(f"\n[INFO] Creating required directories:")
    for directory in directories_to_create:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  ✓ {directory}")
        except Exception as e:
            print(f"  ✗ {directory} - Error: {e}")
    
    # Check static files
    static_files_to_check = [
        os.path.join(app_dir, 'static', 'css', 'styles.css'),
        os.path.join(app_dir, 'static', 'css', 'history_styles.css'),
        os.path.join(app_dir, 'static', 'js', 'draw.js'),
        os.path.join(app_dir, 'static', 'js', 'upload.js')
    ]
    
    print(f"\n[INFO] Checking static files:")
    for file_path in static_files_to_check:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        filename = os.path.basename(file_path)
        print(f"  {status} {filename}")
        if not exists:
            print(f"      Missing: {file_path}")
    
    # Check model files
    models_dir = os.path.join(project_root, 'models')
    print(f"\n[INFO] Checking models directory: {models_dir}")
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith(('.keras', '.h5'))]
        print(f"  Found {len(model_files)} model files:")
        for model_file in model_files:
            print(f"    - {model_file}")
    else:
        print(f"  ✗ Models directory not found")
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    env['FLASK_APP'] = app_script
    
    # For debugging, you can set this to 'development'
    env['FLASK_ENV'] = 'production'
    
    print(f"\n[INFO] Environment setup:")
    print(f"  PYTHONPATH: {env.get('PYTHONPATH')}")
    print(f"  FLASK_APP: {env.get('FLASK_APP')}")
    print(f"  FLASK_ENV: {env.get('FLASK_ENV')}")
    
    print(f"\n" + "=" * 60)
    print("LAUNCHING FLASK APPLICATION")
    print("=" * 60)
    print(f"[INFO] If successful, the app will be available at:")
    print(f"[INFO] Local: http://localhost:5000")
    print(f"[INFO] Network: http://0.0.0.0:5000")
    print(f"[INFO] Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # CRITICAL: Stay in project root directory for imports to work
        os.chdir(project_root)
        print(f"[INFO] Changed working directory to: {os.getcwd()}")
        
        # Run the Flask application using absolute path
        result = subprocess.run([
            sys.executable, 
            app_script  # Use absolute path to script
        ], env=env, cwd=project_root)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print(f"\n[INFO] Application stopped by user")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Failed to launch application: {e}")
        print(f"[DEBUG] Attempted to run: {sys.executable} {app_script}")
        print(f"[DEBUG] From directory: {project_root}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n[INFO] Application exited with code: {exit_code}")
    sys.exit(exit_code)
