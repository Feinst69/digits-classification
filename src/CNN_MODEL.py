import matplotlib
# Force matplotlib to use Agg backend (non-interactive, thread-safe)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from PIL import Image
import os
import io
import time
import threading
from contextlib import contextmanager
import base64

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

            # Créer des modèles pour extraire les feature maps des couches intermédiaires
            self._create_feature_extractors()

        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.model = None
            self.feature_extractors = {}

        # Thread lock pour les opérations matplotlib
        self._plot_lock = threading.Lock()

        # Configuration matplotlib pour éviter les problèmes de threading
        plt.ioff()  # Turn off interactive mode

    def _create_feature_extractors(self):
        """Créer des extracteurs de features pour visualiser les couches intermédiaires"""
        self.feature_extractors = {}

        if self.model is None:
            return

        # Identifier les couches convolutionnelles
        conv_layers = []
        for i, layer in enumerate(self.model.layers):
            if 'conv' in layer.name.lower() or isinstance(layer, tf.keras.layers.Conv2D):
                conv_layers.append((i, layer.name, layer))

        print(f"Couches convolutionnelles trouvées: {[name for _, name, _ in conv_layers]}")

        # Créer des extracteurs pour les premières couches (les plus interprétables)
        for i, (layer_idx, layer_name, layer) in enumerate(conv_layers[:3]):  # Prendre les 3 premières couches conv
            try:
                extractor = Model(inputs=self.model.input, outputs=layer.output)
                self.feature_extractors[f"conv_{i+1}_{layer_name}"] = extractor
                print(f"✓ Extracteur créé pour: {layer_name}")
            except Exception as e:
                print(f"✗ Erreur création extracteur pour {layer_name}: {e}")

    @contextmanager
    def _safe_plotting(self):
        """Context manager pour les opérations matplotlib thread-safe"""
        with self._plot_lock:
            # Créer une nouvelle figure avec des paramètres explicites
            fig = plt.figure(figsize=(15, 10))
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

    def extract_feature_maps(self, processed_image):
        """
        Extraire les feature maps des couches convolutionnelles.

        Args:
            processed_image: Image préparée pour le modèle

        Returns:
            dict: Feature maps pour chaque couche
        """
        feature_maps = {}

        for layer_name, extractor in self.feature_extractors.items():
            try:
                features = extractor.predict(processed_image, verbose=0)
                feature_maps[layer_name] = features
                print(f"Feature maps extraites pour {layer_name}: shape {features.shape}")
            except Exception as e:
                print(f"Erreur extraction features {layer_name}: {e}")

        return feature_maps

    def select_representative_filters(self, feature_maps, n_filters=9):
        """
        Sélectionner les filtres les plus représentatifs pour l'affichage.

        Args:
            feature_maps (dict): Feature maps de toutes les couches
            n_filters (int): Nombre de filtres à sélectionner

        Returns:
            list: Liste des (layer_name, filter_index, feature_map) sélectionnés
        """
        selected_filters = []

        for layer_name, features in feature_maps.items():
            if len(features.shape) == 4:  # (batch, height, width, channels)
                n_channels = features.shape[-1]

                # Calculer la variance de chaque filtre pour trouver les plus actifs
                filter_variances = []
                for i in range(n_channels):
                    variance = np.var(features[0, :, :, i])
                    filter_variances.append((variance, i, features[0, :, :, i]))

                # Trier par variance décroissante
                filter_variances.sort(reverse=True, key=lambda x: x[0])

                # Prendre les filtres les plus actifs
                filters_per_layer = min(3, len(filter_variances))  # Max 3 par couche
                for j in range(filters_per_layer):
                    if len(selected_filters) < n_filters:
                        variance, filter_idx, filter_map = filter_variances[j]
                        selected_filters.append({
                            'layer_name': layer_name,
                            'filter_index': filter_idx,
                            'feature_map': filter_map,
                            'variance': variance,
                            'title': f"{layer_name.split('_')[1]} F{filter_idx}"
                        })

        return selected_filters[:n_filters]

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

        return self.model.predict(processed_image, verbose=0)

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

    def predict_with_feature_maps(self, image_path=None, image_data=None):
        """
        Prédiction avec extraction des feature maps pour visualisation.

        Args:
            image_path (str, optional): Chemin vers l'image
            image_data (bytes, optional): Données d'image en bytes

        Returns:
            tuple: (résultats prédiction, image processed, feature maps sélectionnées)
        """
        # Faire la prédiction normale
        results, processed_image = self.predict_from_image(image_path, image_data)

        # Extraire les feature maps
        feature_maps = self.extract_feature_maps(processed_image)

        # Sélectionner les filtres les plus représentatifs
        selected_filters = self.select_representative_filters(feature_maps, n_filters=9)

        return results, processed_image, selected_filters

    def create_filter_visualization(self, selected_filters):
        """
        Créer une visualisation des filtres sous forme d'images base64.

        Args:
            selected_filters: Liste des filtres sélectionnés

        Returns:
            list: Liste des images en base64
        """
        filter_images = []

        for filter_info in selected_filters:
            try:
                # Créer une petite figure pour chaque filtre
                fig, ax = plt.subplots(1, 1, figsize=(2, 2))

                # Normaliser le feature map pour l'affichage
                feature_map = filter_info['feature_map']
                normalized_map = (feature_map - feature_map.min()) / (feature_map.max() - feature_map.min() + 1e-8)

                # Afficher avec une colormap
                im = ax.imshow(normalized_map, cmap='viridis', interpolation='nearest')
                ax.set_title(filter_info['title'], fontsize=8, pad=2)
                ax.axis('off')

                # Sauvegarder en base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                           facecolor='white', edgecolor='none', pad_inches=0.1)
                buffer.seek(0)

                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                filter_images.append({
                    'image': f"data:image/png;base64,{img_base64}",
                    'title': filter_info['title'],
                    'layer': filter_info['layer_name'],
                    'variance': float(filter_info['variance'])
                })

                plt.close(fig)
                buffer.close()

            except Exception as e:
                print(f"Erreur création visualisation filtre: {e}")
                continue

        return filter_images

    def get_prediction_for_web_with_filters(self, image_data=None, image_path=None, temp_folder=None):
        """
        Version complète pour l'application web avec visualisation des filtres.

        Args:
            image_data (bytes, optional): Données d'image en bytes
            image_path (str, optional): Chemin vers l'image
            temp_folder (str, optional): Chemin vers le dossier temp

        Returns:
            dict: Résultats formatés pour l'affichage web avec filtres
        """
        try:
            # Faire la prédiction avec feature maps
            results, processed_image, selected_filters = self.predict_with_feature_maps(
                image_path=image_path, image_data=image_data
            )

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

            # Créer les visualisations des filtres
            filter_visualizations = self.create_filter_visualization(selected_filters)

            # Sauvegarder les métadonnées pour l'historique (en dehors du context manager)
            try:
                metadata_path = output_path.replace('.png', '_metadata.json')
                import json
                metadata = {
                    'predicted_digit': results['predicted_digit'],
                    'confidence': results['confidence'],
                    'probabilities': results['probabilities'],
                    'timestamp': timestamp,
                    'original_size': results['original_size'],
                    'filters_count': len(filter_visualizations)
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
                'plot_path': plot_path,
                'feature_filters': filter_visualizations,  # Nouvelle donnée
                'has_filters': len(filter_visualizations) > 0
            }

            return web_results

        except Exception as e:
            print(f"Erreur dans get_prediction_for_web_with_filters: {e}")
            import traceback
            traceback.print_exc()
            raise

    # Garder la méthode originale pour compatibilité
    def get_prediction_for_web(self, image_data=None, image_path=None, temp_folder=None):
        """Version originale sans filtres pour compatibilité"""
        return self.get_prediction_for_web_with_filters(image_data, image_path, temp_folder)
