"""
Script de test pour vérifier la création des graphiques
"""
import os
import sys
from src.CNN_MODEL import CNN_MODEL

def main():
    # Créer les dossiers nécessaires
    os.makedirs('app/static/temp', exist_ok=True)
    
    # Vérifier que les dossiers existent
    print(f"Dossier app/static/temp existe: {os.path.exists('app/static/temp')}")
    
    # Charger le modèle
    model_path = os.path.join('models', 'best_cnn_model.keras')
    cnn_model = CNN_MODEL(model_path)
    
    # Chercher une image de test
    if os.path.exists('images'):
        test_images = [f for f in os.listdir('images') if f.endswith(('.png', '.jpg', '.jpeg'))]
        if test_images:
            test_image_path = os.path.join('images', test_images[0])
            print(f"Utilisation de l'image de test: {test_image_path}")
            
            # Tester la fonction get_prediction_for_web
            result = cnn_model.get_prediction_for_web(image_path=test_image_path)
            
            print(f"Prédiction: {result['predicted_digit']}")
            print(f"Confiance: {result['confidence']:.2f}%")
            print(f"Chemin du graphique: {result['plot_path']}")
            
            # Vérifier si le fichier a été créé
            full_path = os.path.join('app/static', result['plot_path'])
            print(f"Le fichier existe: {os.path.exists(full_path)}")
            
            # Si le fichier n'existe pas dans le chemin attendu, essayer d'autres chemins
            if not os.path.exists(full_path):
                # Liste de chemins alternatifs possibles
                alt_paths = [
                    result['plot_path'],  # Chemin relatif direct
                    os.path.basename(result['plot_path']),  # Juste le nom du fichier
                    os.path.join('static', result['plot_path']),  # static/temp/...
                ]
                
                for path in alt_paths:
                    if os.path.exists(path):
                        print(f"Fichier trouvé dans le chemin alternatif: {path}")
        else:
            print("Aucune image de test trouvée dans le dossier 'images'.")
    else:
        print("Le dossier 'images' n'existe pas.")

if __name__ == "__main__":
    main()
