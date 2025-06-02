"""
Lanceur simple pour l'application de reconnaissance de chiffres
Lance l'application depuis le répertoire racine du projet
"""
import os
import sys
import subprocess

def main():
    """Lance l'application Flask"""
    # S'assurer qu'on est dans le bon répertoire
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Chemin vers l'application
    app_script = os.path.join('app', 'app.py')
    
    if not os.path.exists(app_script):
        print(f"Erreur: {app_script} n'existe pas")
        sys.exit(1)
    
    print(f"Démarrage de l'application depuis: {project_root}")
    print(f"Script: {app_script}")
    
    # Lancer l'application
    try:
        subprocess.run([sys.executable, app_script], cwd=project_root)
    except KeyboardInterrupt:
        print("\nArrêt de l'application")
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
