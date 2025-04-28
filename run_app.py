"""
Script de lancement pour l'application de reconnaissance de chiffres
"""
import os
import sys
import subprocess

def main():
    """
    Lance l'application Flask après avoir vérifié que les répertoires nécessaires existent
    """
    # Définir le chemin de l'application
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
    app_script = os.path.join(app_dir, 'script.py')
    
    # Vérifier que le script existe
    if not os.path.exists(app_script):
        print(f"Erreur: Le script d'application n'existe pas à {app_script}")
        sys.exit(1)
    
    # Créer les répertoires nécessaires s'ils n'existent pas
    static_dir = os.path.join(app_dir, 'static')
    temp_dir = os.path.join(static_dir, 'temp')
    uploads_dir = os.path.join(static_dir, 'uploads')
    
    # S'assurer que les répertoires existent
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Vérifier si les répertoires ont été créés avec succès
    print(f"Le répertoire static existe: {os.path.exists(static_dir)}")
    print(f"Le répertoire temp existe: {os.path.exists(temp_dir)}")
    print(f"Le répertoire uploads existe: {os.path.exists(uploads_dir)}")
    
    # Lancer l'application Flask
    print("Lancement de l'application Flask...")
    try:
        # Changer le répertoire de travail
        os.chdir(app_dir)
        # Exécuter le script Flask
        subprocess.run([sys.executable, 'script.py'])
    except Exception as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
