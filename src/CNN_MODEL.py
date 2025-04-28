import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import os
import io
import time

class CNN_MODEL:
    def __init__(self, model_path='models/best_cnn_model.keras'):
        """
        Initialise le modèle CNN pour la reconnaissance de chiffres manuscrits.
        
        Args:
            model_path (str): Chemin vers le modèle Keras sauvegardé
        """
        try:
            self.model = load_model(model_path)
            print(f"Modèle chargé depuis: {model_path}")
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.model = None

    def prepare_image(self, image_path=None, image_data=None):
        """
        Prépare l'image pour la prédiction (redimensionne à 28x28, normalise).
        
        Args:
            image_path (str, optional): Chemin vers l'image
            image_data (bytes, optional): Données d'image en bytes (pour les uploads)
            
        Returns:
            tuple: (image préparée pour le modèle, taille originale)
        """
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
        elif image_data:
            img = Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Veuillez fournir soit un chemin d'image valide, soit des données d'image.")
            
        # Sauvegarder la taille originale
        original_size = img.size
        
        # Convertir en niveaux de gris
        if img.mode != 'L':
            img = img.convert('L')
            
        # Redimensionner en 28x28 pixels
        img = img.resize((28, 28), Image.LANCZOS)
        
        # Convertir en array numpy et normaliser
        img_array = np.array(img)
        img_array = img_array / 255.0
        
        # Inverser les couleurs si nécessaire (fond blanc, chiffre noir comme dans MNIST)
        # Si la moyenne des pixels est > 0.5, on suppose que l'arrière-plan est plus clair que le chiffre
        if np.mean(img_array) > 0.5:
            img_array = 1 - img_array
            
        # Reshape pour le modèle CNN (ajouter la dimension de batch et de canal)
        img_array = img_array.reshape(1, 28, 28, 1)
        
        return img_array, original_size

    def predict(self, processed_image):
        """
        Réalise la prédiction à partir d'une image préparée.
        
        Args:
            processed_image: Image préparée pour le modèle
            
        Returns:
            array: Tableau de probabilités pour chaque chiffre
        """
        if self.model is None:
            raise ValueError("Le modèle n'a pas été chargé correctement.")
            
        return self.model.predict(processed_image)

    def predict_from_image(self, image_path=None, image_data=None):
        """
        Prépare l'image et réalise la prédiction.
        
        Args:
            image_path (str, optional): Chemin vers l'image
            image_data (bytes, optional): Données d'image en bytes
            
        Returns:
            dict: Résultats de la prédiction avec les probabilités
        """
        processed_image, original_size = self.prepare_image(image_path, image_data)
        predictions = self.predict(processed_image)
        
        predicted_class = np.argmax(predictions[0])
        confidence = predictions[0][predicted_class] * 100
        
        # Créer un dictionnaire de résultats
        results = {
            'predicted_digit': int(predicted_class),
            'confidence': float(confidence),
            'probabilities': [float(prob * 100) for prob in predictions[0]],
            'original_size': original_size
        }
        
        return results, processed_image

    def predict_and_visualize(self, image_path=None, image_data=None, save_plot=False, output_path=None):
        """
        Fait la prédiction et visualise les résultats.
        
        Args:
            image_path (str, optional): Chemin vers l'image
            image_data (bytes, optional): Données d'image en bytes
            save_plot (bool): Si True, sauvegarde le graphique au lieu de l'afficher
            output_path (str, optional): Chemin pour sauvegarder le graphique
            
        Returns:
            dict: Résultats de la prédiction
            str: Chemin vers le graphique sauvegardé (si save_plot=True)
        """
        results, processed_image = self.predict_from_image(image_path, image_data)
        
        # Configurer la figure pour l'affichage
        plt.figure(figsize=(12, 6))
        
        # Afficher l'image originale
        if image_path and os.path.exists(image_path):
            img_original = Image.open(image_path)
        elif image_data:
            img_original = Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Veuillez fournir soit un chemin d'image valide, soit des données d'image.")
            
        plt.subplot(1, 3, 1)
        plt.title(f"Image originale\nTaille: {results['original_size'][0]}x{results['original_size'][1]}")
        plt.imshow(img_original, cmap='gray' if img_original.mode == 'L' else None)
        plt.axis('off')
        
        # Afficher l'image préparée (28x28)
        plt.subplot(1, 3, 2)
        plt.title("Image redimensionnée (28x28)")
        plt.imshow(processed_image[0, :, :, 0], cmap='gray')
        plt.axis('off')
        
        # Afficher les résultats
        plt.subplot(1, 3, 3)
        plt.title("Prédictions")
        plt.bar(range(10), results['probabilities'])
        plt.xticks(range(10))
        plt.xlabel("Chiffre")
        plt.ylabel("Probabilité (%)")
        
        # Afficher le résultat principal
        plt.suptitle(f"Prédiction: {results['predicted_digit']} (Confiance: {results['confidence']:.2f}%)", fontsize=16)
        plt.tight_layout()
        
        if save_plot:
            if output_path is None:
                output_path = "predictions/prediction_result.png"
                # Créer le dossier s'il n'existe pas
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # S'assurer que le dossier parent existe
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            try:
                plt.savefig(output_path)
                print(f"Graphique sauvegardé dans: {output_path}")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du graphique: {e}")
            
            plt.close()
            return results, output_path
        else:
            plt.show()
            return results, None

    def get_prediction_for_web(self, image_data=None, image_path=None):
        """
        Version adaptée pour l'application web qui renvoie des données formatées pour Flask.
        
        Args:
            image_data (bytes, optional): Données d'image en bytes
            image_path (str, optional): Chemin vers l'image
            
        Returns:
            dict: Résultats formatés pour l'affichage web
        """
        # Faire la prédiction
        results, _ = self.predict_from_image(image_path=image_path, image_data=image_data)
        
        # Générer un nom unique pour l'image de résultat
        timestamp = int(time.time())
        output_filename = f"prediction_{timestamp}.png"
        
        # Déterminer le chemin absolu du répertoire de travail courant
        current_dir = os.getcwd()
        print(f"Répertoire de travail actuel: {current_dir}")
        
        # Déterminer le chemin du dossier static/temp
        if os.path.basename(current_dir) == 'app':
            # Déjà dans le dossier app
            temp_dir = os.path.join(current_dir, 'static', 'temp')
        else:
            # Vérifier si nous sommes dans le répertoire parent
            app_dir = os.path.join(current_dir, 'app')
            if os.path.exists(app_dir):
                temp_dir = os.path.join(app_dir, 'static', 'temp')
            else:
                # Fallback sur le répertoire courant
                temp_dir = 'static/temp'
        
        # Créer le dossier temp s'il n'existe pas
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, output_filename)
        
        # DEBUG: Afficher les chemins
        print(f"Chemin du dossier temp: {temp_dir}")
        print(f"Chemin complet du fichier de sortie: {output_path}")
        print(f"Dossier temp existe: {os.path.exists(temp_dir)}")
        
        # Configurer la figure pour l'affichage
        plt.figure(figsize=(12, 6))
        
        # Afficher l'image originale
        if image_path and os.path.exists(image_path):
            img_original = Image.open(image_path)
        elif image_data:
            img_original = Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Veuillez fournir soit un chemin d'image valide, soit des données d'image.")
            
        plt.subplot(1, 3, 1)
        plt.title(f"Image originale\nTaille: {results['original_size'][0]}x{results['original_size'][1]}")
        plt.imshow(img_original, cmap='gray' if img_original.mode == 'L' else None)
        plt.axis('off')
        
        # Afficher l'image préparée (28x28)
        plt.subplot(1, 3, 2)
        plt.title("Image redimensionnée (28x28)")
        processed_image, _ = self.prepare_image(image_path, image_data)
        plt.imshow(processed_image[0, :, :, 0], cmap='gray')
        plt.axis('off')
        
        # Afficher les résultats
        plt.subplot(1, 3, 3)
        plt.title("Prédictions")
        plt.bar(range(10), [prob/100 for prob in results['probabilities']])
        plt.xticks(range(10))
        plt.xlabel("Chiffre")
        plt.ylabel("Probabilité")
        
        # Afficher le résultat principal
        plt.suptitle(f"Prédiction: {results['predicted_digit']} (Confiance: {results['confidence']:.2f}%)", fontsize=16)
        plt.tight_layout()
        
        # Sauvegarder l'image
        try:
            plt.savefig(output_path)
            print(f"Graphique sauvegardé dans: {output_path}")
            print(f"Le fichier existe: {os.path.exists(output_path)}")
            
            # Utiliser un chemin relatif pour Flask
            plot_path = 'temp/' + output_filename
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du graphique: {e}")
            # Utiliser un chemin relatif simple en cas d'échec
            plot_path = 'temp/default.png'
            
        plt.close()
        
        # Formater les données pour le template
        web_results = {
            'predicted_digit': results['predicted_digit'],
            'confidence': results['confidence'],
            'probabilities': [
                {'digit': i, 'probability': prob} 
                for i, prob in enumerate(results['probabilities'])
            ],
            'plot_path': plot_path
        }
        
        return web_results
