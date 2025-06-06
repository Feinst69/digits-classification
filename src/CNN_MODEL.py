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

            # DEBUG: Afficher l'architecture du modèle
            print("=== ARCHITECTURE DU MODÈLE ===")
            self.model.summary()
            print("==============================")

            # Initialiser les extracteurs à None - ils seront créés à la première prédiction
            self.feature_extractors = {}
            self._extractors_initialized = False

        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            import traceback
            traceback.print_exc()
            self.model = None
            self.feature_extractors = {}
            self._extractors_initialized = False

        # Thread lock pour les opérations matplotlib
        self._plot_lock = threading.Lock()
        self._extractor_lock = threading.Lock()

        # Configuration matplotlib pour éviter les problèmes de threading
        plt.ioff()  # Turn off interactive mode

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

    def create_working_extractors(self):
        """Create extractors using the working method from notebook"""
        extractors = {}

        print("🔧 Creating extractors with working method...")

        # Identify Conv2D layers with exact indices from your model
        conv_layers_info = [
            (0, 'conv2d_8'),
            (3, 'conv2d_9'),
            (8, 'conv2d_10'),
            (11, 'conv2d_11')
        ]

        print(f"Target Conv2D layers: {[name for _, name in conv_layers_info]}")

        try:
            # Create input layer matching your model
            from tensorflow.keras.layers import Input
            input_layer = Input(shape=(28, 28, 1), name='working_input')
            x = input_layer

            # Track outputs at specific Conv2D layers
            conv_outputs = {}

            for i, layer in enumerate(self.model.layers):
                x = layer(x)

                # Check if this is one of our target Conv2D layers
                if isinstance(layer, tf.keras.layers.Conv2D):
                    layer_name = layer.name
                    if layer_name in [name for _, name in conv_layers_info]:
                        conv_outputs[layer_name] = x
                        print(f"  ✅ Captured output from {layer_name}: {x.shape}")

            # Create extractors for captured outputs
            for layer_name, output_tensor in conv_outputs.items():
                try:
                    extractor = Model(inputs=input_layer, outputs=output_tensor)
                    extractor_name = f"extractor_{layer_name}"
                    extractors[extractor_name] = extractor
                    print(f"  ✅ Extractor created: {extractor_name}")
                except Exception as e:
                    print(f"  ❌ Failed extractor {layer_name}: {e}")

        except Exception as e:
            print(f"Working method failed: {e}")
            return {}

        print(f"🎯 Total working extractors created: {len(extractors)}")
        return extractors

    def extract_conv_features(self, processed_image, target_layers=['conv2d_8', 'conv2d_10'], best_filters=False):
        """Extract features from specific conv layers"""

        # Create extractors if not exists
        if not hasattr(self, '_working_extractors'):
            self._working_extractors = self.create_working_extractors()

        if not self._working_extractors:
            print("❌ No working extractors available")
            return {}

        print(f"🔍 Extracting features from: {target_layers}")

        extracted_features = {}

        for target_layer in target_layers:
            extractor_name = f"extractor_{target_layer}"

            if extractor_name in self._working_extractors:
                try:
                    extractor = self._working_extractors[extractor_name]
                    features = extractor.predict(processed_image, verbose=0)
                    extracted_features[target_layer] = features
                    print(f"  ✅ {target_layer}: {features.shape}")
                except Exception as e:
                    print(f"  ❌ Error extracting {target_layer}: {e}")
            else:
                print(f"  ❌ Extractor not found for {target_layer}")

        return extracted_features

    def select_best_filters(self, features, n_filters=3):
        """Select best filters based on variance (activity)"""

        if len(features.shape) != 4:
            print(f"❌ Unexpected features shape: {features.shape}")
            return list(range(min(n_filters, features.shape[-1])))

        n_available = features.shape[-1]

        # Calculate variance for each filter
        filter_variances = []
        for i in range(n_available):
            filter_map = features[0, :, :, i]
            variance = np.var(filter_map)
            mean_activation = np.mean(np.abs(filter_map))
            # Combined score: variance * (1 + mean_activation)
            combined_score = variance * (1 + mean_activation)
            filter_variances.append((combined_score, i))

        # Sort by score (highest first)
        filter_variances.sort(reverse=True, key=lambda x: x[0])

        # Return indices of best filters
        best_indices = [idx for _, idx in filter_variances[:n_filters]]

        print(f"  🎯 Best {n_filters} filters for this layer: {best_indices}")
        print(f"  📊 Scores: {[f'{score:.4f}' for score, _ in filter_variances[:n_filters]]}")

        return best_indices

    def create_filter_visualizations(self, processed_image, target_layers=['conv2d_8', 'conv2d_9', 'conv2d_10', 'conv2d_11'], best_filters=False):
        """Create filter visualizations for web display"""

        print(f"🎨 Creating filter visualizations...")
        print(f"Target layers: {target_layers}")
        print(f"Best filters mode: {best_filters}")

        # Extract features
        extracted_features = self.extract_conv_features(processed_image, target_layers, best_filters)

        if not extracted_features:
            print("❌ No features extracted")
            return []

        filter_visualizations = []
        
        # Mapping des couches vers des noms français
        layer_names_fr = {
            'conv2d_8': '1er Bloc de Convolution',
            'conv2d_9': '1er Bloc de Convolution', 
            'conv2d_10': '2e Bloc de Convolution',
            'conv2d_11': '2e Bloc de Convolution'
        }
        
        # Pour le mode best filters, prendre 3 meilleurs par couche ciblée
        # Pour le mode standard, prendre 3 premiers par couche ciblée
        target_layers_for_display = ['conv2d_8', 'conv2d_10']  # Les deux couches principales
        
        selected_filters = []
        
        for target_layer in target_layers_for_display:
            if target_layer in extracted_features:
                features = extracted_features[target_layer]
                print(f"\n🔍 Selecting filters from {target_layer} with shape {features.shape}")
                
                # Sélectionner 3 filtres de cette couche
                if best_filters:
                    filter_indices = self.select_best_filters(features, n_filters=3)
                    print(f"  🎯 Best 3 filters from {target_layer}: {filter_indices}")
                else:
                    filter_indices = list(range(min(3, features.shape[-1])))
                    print(f"  📊 First 3 filters from {target_layer}: {filter_indices}")
                
                # Ajouter les filtres de cette couche
                for filter_idx in filter_indices:
                    try:
                        filter_map = features[0, :, :, filter_idx]
                        variance = float(np.var(filter_map))
                        
                        filter_info = {
                            'layer_name': target_layer,
                            'filter_idx': filter_idx,
                            'filter_map': filter_map,
                            'variance': variance,
                            'is_best': best_filters
                        }
                        selected_filters.append(filter_info)
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {target_layer}_F{filter_idx}: {e}")
                        continue
        
        # Mapping des couches vers des blocs d'affichage
        layer_to_block = {
            'conv2d_8': '1er Bloc de Convolution',
            'conv2d_9': '1er Bloc de Convolution',
            'conv2d_10': '2e Bloc de Convolution', 
            'conv2d_11': '2e Bloc de Convolution'
        }
        
        # Assigner les blocs de convolution selon la couche réelle
        for filter_info in selected_filters:
            layer_name = filter_info['layer_name']
            filter_info['layer_display'] = layer_to_block.get(layer_name, '1er Bloc de Convolution')
            print(f"  ✅ Assigned {layer_name} filter {filter_info['filter_idx']} to {filter_info['layer_display']}")
            if layer_name in ['conv2d_8', 'conv2d_9']:
                filter_info['block_position'] = 'first'
            else:
                filter_info['block_position'] = 'second'
        
        # Créer les visualisations
        for filter_info in selected_filters:
            try:
                filter_map = filter_info['filter_map']
                
                # Normalize filter map
                if filter_map.max() > filter_map.min():
                    normalized_map = (filter_map - filter_map.min()) / (filter_map.max() - filter_map.min())
                else:
                    normalized_map = filter_map

                # Create matplotlib figure
                fig, ax = plt.subplots(1, 1, figsize=(3, 3))
                im = ax.imshow(normalized_map, cmap='viridis', interpolation='nearest')
                
                # Nom simplifié pour l'image: juste "Filtre X"
                ax.set_title(f'Filtre {filter_info["filter_idx"]}', fontsize=10, pad=5)
                ax.axis('off')

                # Convert to base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight',
                        facecolor='white', edgecolor='none', pad_inches=0.1)
                buffer.seek(0)

                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                # Create filter data avec nom français pour l'affichage
                filter_data = {
                    'image': f"data:image/png;base64,{img_base64}",
                    'title': f'Filtre {filter_info["filter_idx"]}',  # Titre simple
                    'layer': filter_info['layer_name'],
                    'layer_display': filter_info['layer_display'],  # Nom français
                    'filter_index': filter_info['filter_idx'],
                    'variance': filter_info['variance'],
                    'is_best': filter_info['is_best']
                }

                filter_visualizations.append(filter_data)
                print(f"  ✅ Created visualization: Filtre {filter_info['filter_idx']} ({filter_info['layer_display']})")

                plt.close(fig)
                buffer.close()

            except Exception as e:
                print(f"  ❌ Error creating visualization for filter: {e}")
                continue

        print(f"🎨 Created {len(filter_visualizations)} filter visualizations")
        return filter_visualizations

    def get_prediction_for_web_with_filters(self, image_data=None, image_path=None, temp_folder=None, best_filters=False):
        """
        Version complète pour l'application web avec visualisation des filtres.

        Args:
            image_data (bytes, optional): Données d'image en bytes
            image_path (str, optional): Chemin vers l'image
            temp_folder (str, optional): Chemin vers le dossier temp
            best_filters (bool): Si True, sélectionne les meilleurs filtres (plus actifs)

        Returns:
            dict: Résultats formatés pour l'affichage web avec filtres
        """
        try:
            print(f"\n🌐 GET_PREDICTION_FOR_WEB_WITH_FILTERS")
            print(f"Image path: {image_path}")
            print(f"Temp folder: {temp_folder}")
            print(f"Best filters mode: {best_filters}")

            # Faire la prédiction de base
            results, processed_image = self.predict_from_image(
                image_path=image_path, image_data=image_data
            )

            print(f"Prédiction: {results['predicted_digit']} (confiance: {results['confidence']:.2f}%)")

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

                # Afficher le résultat principal avec mode de filtre
                filter_mode_text = " (Meilleurs filtres)" if best_filters else ""
                fig.suptitle(f"Prédiction: {results['predicted_digit']} (Confiance: {results['confidence']:.2f}%){filter_mode_text}", fontsize=16)
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

            # Créer les visualisations des filtres avec la nouvelle méthode
            print(f"\n🎨 Création des visualisations de filtres...")
            filter_visualizations = self.create_filter_visualizations(
                processed_image, 
                target_layers=['conv2d_8', 'conv2d_9', 'conv2d_10', 'conv2d_11'], 
                best_filters=best_filters
            )

            print(f"✅ {len(filter_visualizations)} visualisations de filtres créées")

            # Sauvegarder les métadonnées pour l'historique
            try:
                metadata_path = output_path.replace('.png', '_metadata.json')
                import json
                metadata = {
                    'predicted_digit': results['predicted_digit'],
                    'confidence': results['confidence'],
                    'probabilities': results['probabilities'],
                    'timestamp': timestamp,
                    'original_size': results['original_size'],
                    'filters_count': len(filter_visualizations),
                    'best_filters_mode': best_filters
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
                'feature_filters': filter_visualizations,
                'has_filters': len(filter_visualizations) > 0,
                'best_filters_mode': best_filters
            }

            print(f"🎯 Résultat final web: {len(filter_visualizations)} filtres dans la réponse")
            print(f"Mode meilleurs filtres: {best_filters}\n")

            return web_results

        except Exception as e:
            print(f"❌ Erreur dans get_prediction_for_web_with_filters: {e}")
            import traceback
            traceback.print_exc()
            raise

    # Garder la méthode originale pour compatibilité - maintenant avec filtres par défaut
    def get_prediction_for_web(self, image_data=None, image_path=None, temp_folder=None):
        """Version avec filtres par défaut pour compatibilité"""
        return self.get_prediction_for_web_with_filters(image_data, image_path, temp_folder, best_filters=False)
