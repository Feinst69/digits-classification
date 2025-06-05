import matplotlib
# Force matplotlib to use Agg backend (non-interactive, thread-safe)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import os
import io
import time
import threading
from contextlib import contextmanager

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

        # Thread lock pour les opérations matplotlib
        self._plot_lock = threading.Lock()

        # Configuration matplotlib pour éviter les problèmes de threading
        plt.ioff()  # Turn off interactive mode

    @contextmanager
    def _safe_plotting(self):
        """Context manager pour les opérations matplotlib thread-safe"""
        with self._plot_lock:
            # Créer une nouvelle figure avec des paramètres explicites
            fig = plt.figure(figsize=(12, 6))
            try:
                yield fig
            finally:
                # Nettoyer proprement la figure
                plt.close(fig)
                # Force garbage collection pour libérer la mémoire
                import gc
                gc.collect()

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
        Fait la prédiction et visualise les résultats de manière thread-safe.

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

        # Charger l'image originale
        if image_path and os.path.exists(image_path):
            img_original = Image.open(image_path)
        elif image_data:
            img_original = Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Veuillez fournir soit un chemin d'image valide, soit des données d'image.")

        # Utiliser le context manager pour la création du plot
        with self._safe_plotting() as fig:
            # Afficher l'image originale
            ax1 = fig.add_subplot(1, 3, 1)
            ax1.set_title(f"Image originale\nTaille: {results['original_size'][0]}x{results['original_size'][1]}")
            ax1.imshow(img_original, cmap='gray' if img_original.mode == 'L' else None)
            ax1.axis('off')

            # Afficher l'image préparée (28x28)
            ax2 = fig.add_subplot(1, 3, 2)
            ax2.set_title("Image redimensionnée (28x28)")
            ax2.imshow(processed_image[0, :, :, 0], cmap='gray')
            ax2.axis('off')

            # Afficher les résultats
            ax3 = fig.add_subplot(1, 3, 3)
            ax3.set_title("Prédictions")
            ax3.bar(range(10), results['probabilities'])
            ax3.set_xticks(range(10))
            ax3.set_xlabel("Chiffre")
            ax3.set_ylabel("Probabilité (%)")

            # Afficher le résultat principal
            fig.suptitle(f"Prédiction: {results['predicted_digit']} (Confiance: {results['confidence']:.2f}%)", fontsize=16)
            fig.tight_layout()

            if save_plot:
                if output_path is None:
                    output_path = "predictions/prediction_result.png"
                    # Créer le dossier s'il n'existe pas
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # S'assurer que le dossier parent existe
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

                try:
                    fig.savefig(output_path, dpi=100, bbox_inches='tight')
                    print(f"Graphique sauvegardé dans: {output_path}")
                except Exception as e:
                    print(f"Erreur lors de la sauvegarde du graphique: {e}")
                    raise

                return results, output_path
            else:
                # En mode non-interactif, on ne peut pas utiliser plt.show()
                print("Mode non-interactif: utilisez save_plot=True pour sauvegarder le graphique")
                return results, None

    def get_prediction_for_web(self, image_data=None, image_path=None, temp_folder=None):
        """
        Version thread-safe adaptée pour l'application web qui renvoie des données formatées pour Flask.

        Args:
            image_data (bytes, optional): Données d'image en bytes
            image_path (str, optional): Chemin vers l'image
            temp_folder (str, optional): Chemin vers le dossier temp

        Returns:
            dict: Résultats formatés pour l'affichage web
        """
        try:
            # Faire la prédiction
            results, processed_image = self.predict_from_image(image_path=image_path, image_data=image_data)

            # Générer un nom unique pour l'image de résultat
            timestamp = int(time.time())
            output_filename = f"prediction_{timestamp}.png"

            # Utiliser le dossier temp fourni ou déterminer automatiquement
            if temp_folder and os.path.exists(temp_folder):
                temp_dir = temp_folder
            else:
                # Fallback: créer un dossier temp dans le répertoire courant
                temp_dir = os.path.join(os.getcwd(), 'temp')
                os.makedirs(temp_dir, exist_ok=True)

            output_path = os.path.join(temp_dir, output_filename)

            print(f"Dossier temp utilisé: {temp_dir}")
            print(f"Fichier de sortie: {output_path}")

            # Charger l'image originale
            if image_path and os.path.exists(image_path):
                img_original = Image.open(image_path)
            elif image_data:
                img_original = Image.open(io.BytesIO(image_data))
            else:
                raise ValueError("Veuillez fournir soit un chemin d'image valide, soit des données d'image.")

            # Utiliser le context manager pour la création thread-safe du plot
            with self._safe_plotting() as fig:
                # Afficher l'image originale
                ax1 = fig.add_subplot(1, 3, 1)
                ax1.set_title(f"Image originale\nTaille: {results['original_size'][0]}x{results['original_size'][1]}")
                ax1.imshow(img_original, cmap='gray' if img_original.mode == 'L' else None)
                ax1.axis('off')

                # Afficher l'image préparée (28x28)
                ax2 = fig.add_subplot(1, 3, 2)
                ax2.set_title("Image redimensionnée (28x28)")
                ax2.imshow(processed_image[0, :, :, 0], cmap='gray')
                ax2.axis('off')

                # Afficher les résultats
                ax3 = fig.add_subplot(1, 3, 3)
                ax3.set_title("Prédictions")
                bars = ax3.bar(range(10), [prob/100 for prob in results['probabilities']])
                ax3.set_xticks(range(10))
                ax3.set_xlabel("Chiffre")
                ax3.set_ylabel("Probabilité")

                # Mettre en évidence la prédiction la plus probable
                bars[results['predicted_digit']].set_color('#28a745')

                # Afficher le résultat principal
                fig.suptitle(f"Prédiction: {results['predicted_digit']} (Confiance: {results['confidence']:.2f}%)", fontsize=16)
                fig.tight_layout()

                # Sauvegarder l'image de manière thread-safe
                try:
                    fig.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
                    print(f"Graphique sauvegardé dans: {output_path}")
                    print(f"Le fichier existe: {os.path.exists(output_path)}")

                    # Utiliser un chemin relatif pour Flask
                    plot_path = 'temp/' + output_filename

                except Exception as e:
                    print(f"Erreur lors de la sauvegarde du graphique: {e}")
                    # Utiliser un chemin relatif simple en cas d'échec
                    plot_path = 'temp/default.png'
                    raise

            # Sauvegarder les métadonnées pour l'historique (en dehors du context manager)
            try:
                metadata_path = output_path.replace('.png', '_metadata.json')
                import json
                metadata = {
                    'predicted_digit': results['predicted_digit'],
                    'confidence': results['confidence'],
                    'probabilities': results['probabilities'],
                    'timestamp': timestamp,
                    'original_size': results['original_size']
                }

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
                print(f"Métadonnées sauvegardées dans: {metadata_path}")
            except Exception as meta_error:
                print(f"Erreur lors de la sauvegarde des métadonnées: {meta_error}")

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

        except Exception as e:
            print(f"Erreur dans get_prediction_for_web: {e}")
            import traceback
            traceback.print_exc()
            raise
