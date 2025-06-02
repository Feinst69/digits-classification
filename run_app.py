"""
Script de lancement pour l'application de reconnaissance de chiffres
Version simplifiée avec gestion des chemins améliorée
"""
import os
import sys

def main():
    """
    Lance l'application Flask avec une gestion des chemins simplifiée
    """
    # Obtenir le chemin absolu du répertoire du projet
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Ajouter le répertoire racine au chemin Python
    sys.path.insert(0, project_root)
    
    # Importer et lancer l'application
    from app.script import app
    
    print(f"Répertoire du projet: {project_root}")
    print("Lancement de l'application Flask...")
    
    # Lancer l'application depuis le répertoire racine du projet
    app.run(debug=True, port=5000, host='0.0.0.0')

if __name__ == "__main__":
    main()
