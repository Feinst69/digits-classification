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

    def _ensure_extractors_initialized(self):
        """S'assurer que les extracteurs sont initialisés (thread-safe)"""
        if self._extractors_initialized:
            return

        with self._extractor_lock:
            # Double-check locking pattern
            if self._extractors_initialized:
                return

            print("🔧 Initialisation des extracteurs de features...")
            self._create_feature_extractors()

    def _create_feature_extractors(self):
        """Créer des extracteurs de features pour visualiser les couches intermédiaires"""
        self.feature_extractors = {}

        if self.model is None:
            print("❌ Impossible de créer les extracteurs: modèle non chargé")
            return

        print("\n=== CRÉATION DES EXTRACTEURS DE FEATURES ===")

        try:
            # SOLUTION ALTERNATIVE: Reconstruire le modèle avec input explicite
            print("🔧 Reconstruction du modèle avec input explicite...")

            # Créer un input explicite
            from tensorflow.keras.layers import Input
            from tensorflow.keras.models import Model

            # Définir l'input explicitement
            input_layer = Input(shape=(28, 28, 1), name='explicit_input')

            # Appliquer le modèle à cet input pour forcer la construction
            try:
                # Première tentative: utiliser le modèle directement
                output = self.model(input_layer)

                # Créer un nouveau modèle avec input/output explicites
                self.functional_model = Model(inputs=input_layer, outputs=output)
                print("✓ Modèle fonctionnel créé avec succès")

                # Utiliser le modèle fonctionnel pour les extracteurs
                model_to_use = self.functional_model

            except Exception as func_error:
                print(f"⚠️ Échec création modèle fonctionnel: {func_error}")

                # Deuxième tentative: forcer la construction avec predict
                print("🔧 Tentative de construction par prédiction...")
                test_input = np.random.rand(1, 28, 28, 1).astype(np.float32)
                _ = self.model.predict(test_input, verbose=0)

                # Troisième tentative: créer un modèle à partir de zéro
                print("🔧 Reconstruction complète du modèle...")
                try:
                    # Créer un nouveau modèle en clonant l'architecture
                    input_layer = Input(shape=(28, 28, 1), name='reconstructed_input')
                    x = input_layer

                    # Appliquer chaque couche séquentiellement
                    for layer in self.model.layers:
                        x = layer(x)

                    # Créer le modèle reconstruit
                    self.functional_model = Model(inputs=input_layer, outputs=x)
                    model_to_use = self.functional_model
                    print("✓ Modèle reconstruit avec succès")

                except Exception as recons_error:
                    print(f"❌ Échec reconstruction: {recons_error}")

                    # DERNIER RECOURS: Utiliser une approche manuelle
                    print("🔧 Dernier recours: approche manuelle...")
                    if self._create_extractors_manual():
                        return  # Succès avec l'approche manuelle
                    else:
                        print("❌ Toutes les approches ont échoué")
                        self._extractors_initialized = True  # Éviter de réessayer
                        return

        except Exception as e:
            print(f"❌ Erreur construction du modèle: {e}")
            import traceback
            traceback.print_exc()
            return

        # DEBUG: Lister toutes les couches
        print(f"Nombre total de couches: {len(self.model.layers)}")
        for i, layer in enumerate(self.model.layers):
            print(f"Couche {i}: {layer.name} (Type: {type(layer).__name__})")

        # APPROCHE ALTERNATIVE: Identifier les couches conv depuis le modèle fonctionnel
        conv_layers = []

        # Utiliser le modèle fonctionnel si disponible
        source_model = getattr(self, 'functional_model', model_to_use)

        for i, layer in enumerate(source_model.layers):
            is_conv = ('conv' in layer.name.lower() or
                      isinstance(layer, tf.keras.layers.Conv2D) or
                      type(layer).__name__ in ['Conv2D', 'DepthwiseConv2D', 'SeparableConv2D'])

            if is_conv:
                try:
                    # Utiliser get_layer pour obtenir la couche depuis le modèle fonctionnel
                    layer_from_model = source_model.get_layer(layer.name)

                    conv_layers.append((i, layer.name, layer_from_model))
                    print(f"✓ Couche convolutionnelle trouvée: {i} - {layer.name}")

                except Exception as layer_error:
                    print(f"⚠️ Erreur vérification couche {i} - {layer.name}: {layer_error}")

        print(f"\nCouches convolutionnelles valides trouvées: {len(conv_layers)}")
        print(f"Détails: {[(i, name) for i, name, _ in conv_layers]}")

        if len(conv_layers) == 0:
            print("❌ AUCUNE COUCHE CONVOLUTIONNELLE VALIDE TROUVÉE!")
            self._extractors_initialized = True  # Éviter de réessayer
            return

        # Créer des extracteurs pour les premières couches (les plus interprétables)
        extractors_created = 0
        for i, (layer_idx, layer_name, layer) in enumerate(conv_layers[:4]):  # Prendre les 4 premières couches conv
            try:
                print(f"\nCréation extracteur pour couche {layer_idx}: {layer_name}")
                print(f"  Shape de sortie: {layer.output.shape}")

                # Utiliser le modèle approprié (fonctionnel si disponible, sinon original)
                source_model = getattr(self, 'functional_model', model_to_use)
                model_input = source_model.input if hasattr(source_model, 'input') else source_model.inputs[0]

                # Obtenir la sortie de la couche depuis le bon modèle
                layer_output = source_model.get_layer(layer_name).output

                # Créer l'extracteur avec gestion d'erreur robuste
                extractor = Model(inputs=model_input, outputs=layer_output)
                extractor_name = f"conv_{i+1}_{layer_name}"

                # Test de l'extracteur avant de le sauvegarder
                test_input = np.random.rand(1, 28, 28, 1).astype(np.float32)
                test_output = extractor.predict(test_input, verbose=0)
                print(f"  Test réussi - Output shape: {test_output.shape}")

                # Si le test réussit, sauvegarder l'extracteur
                self.feature_extractors[extractor_name] = extractor
                extractors_created += 1
                print(f"✓ Extracteur créé: {extractor_name}")

            except Exception as e:
                print(f"✗ Erreur création extracteur pour {layer_name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n=== RÉSUMÉ EXTRACTEURS ===")
        print(f"Extracteurs créés: {extractors_created}")
        print(f"Noms des extracteurs: {list(self.feature_extractors.keys())}")
        print("===========================\n")

        self._extractors_initialized = True

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
        print(f"\n=== EXTRACTION DES FEATURE MAPS ===")

        # S'assurer que les extracteurs sont initialisés
        self._ensure_extractors_initialized()

        print(f"Nombre d'extracteurs disponibles: {len(self.feature_extractors)}")
        print(f"Image input shape: {processed_image.shape}")

        feature_maps = {}

        for layer_name, extractor in self.feature_extractors.items():
            try:
                print(f"Extraction pour {layer_name}...")
                features = extractor.predict(processed_image, verbose=0)
                feature_maps[layer_name] = features
                print(f"✓ Feature maps extraites pour {layer_name}: shape {features.shape}")
                print(f"  Min: {features.min():.4f}, Max: {features.max():.4f}, Mean: {features.mean():.4f}")
            except Exception as e:
                print(f"❌ Erreur extraction features {layer_name}: {e}")
                import traceback
                traceback.print_exc()

        print(f"Feature maps extraites avec succès: {len(feature_maps)}")
        print("=====================================\n")
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
        print(f"\n=== SÉLECTION DES FILTRES REPRÉSENTATIFS ===")
        print(f"Feature maps disponibles: {len(feature_maps)}")
        print(f"Cible: {n_filters} filtres")

        selected_filters = []

        for layer_name, features in feature_maps.items():
            print(f"\nAnalyse de la couche: {layer_name}")
            print(f"  Shape: {features.shape}")

            if len(features.shape) == 4:  # (batch, height, width, channels)
                n_channels = features.shape[-1]
                print(f"  Nombre de canaux: {n_channels}")

                # Calculer la variance de chaque filtre pour trouver les plus actifs
                filter_variances = []
                for i in range(n_channels):
                    filter_map = features[0, :, :, i]
                    variance = np.var(filter_map)
                    # Aussi calculer l'activation moyenne pour éviter les filtres "morts"
                    mean_activation = np.mean(np.abs(filter_map))
                    combined_score = variance * (1 + mean_activation)  # Score combiné
                    filter_variances.append((combined_score, i, filter_map, variance))

                # Trier par score combiné décroissant
                filter_variances.sort(reverse=True, key=lambda x: x[0])

                print(f"  Top 3 scores: {[f'{score:.6f}' for score, _, _, _ in filter_variances[:3]]}")

                # Prendre les filtres les plus actifs
                filters_per_layer = min(3, len(filter_variances))  # Max 3 par couche
                print(f"  Filtres sélectionnés pour cette couche: {filters_per_layer}")

                for j in range(filters_per_layer):
                    if len(selected_filters) < n_filters:
                        combined_score, filter_idx, filter_map, variance = filter_variances[j]

                        # Extraire le numéro de couche pour le titre
                        try:
                            layer_num = layer_name.split('_')[1]
                        except:
                            layer_num = "?"

                        filter_info = {
                            'layer_name': layer_name,
                            'filter_index': filter_idx,
                            'feature_map': filter_map,
                            'variance': variance,
                            'combined_score': combined_score,
                            'title': f"L{layer_num} F{filter_idx}"
                        }
                        selected_filters.append(filter_info)
                        print(f"    ✓ Filtre ajouté: {filter_info['title']} (score: {combined_score:.6f})")
            else:
                print(f"  ❌ Shape incompatible pour l'extraction de filtres: {features.shape}")

        print(f"\nFiltres sélectionnés au total: {len(selected_filters)}")
        print("==========================================\n")
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
        print(f"\n🧠 PRÉDICTION AVEC FEATURE MAPS")

        # Faire la prédiction normale
        results, processed_image = self.predict_from_image(image_path, image_data)
        print(f"Prédiction: {results['predicted_digit']} (confiance: {results['confidence']:.2f}%)")

        # Extraire les feature maps (ceci initialise les extracteurs si nécessaire)
        feature_maps = self.extract_feature_maps(processed_image)

        # Sélectionner les filtres les plus représentatifs
        selected_filters = self.select_representative_filters(feature_maps, n_filters=9)

        print(f"🎯 Résultat final: {len(selected_filters)} filtres sélectionnés\n")

        return results, processed_image, selected_filters

    def create_filter_visualization(self, selected_filters):
        """
        Créer une visualisation des filtres sous forme d'images base64.

        Args:
            selected_filters: Liste des filtres sélectionnés

        Returns:
            list: Liste des images en base64
        """
        print(f"\n🎨 CRÉATION DES VISUALISATIONS")
        print(f"Filtres à visualiser: {len(selected_filters)}")

        filter_images = []

        for idx, filter_info in enumerate(selected_filters):
            try:
                print(f"  Création image {idx+1}/{len(selected_filters)}: {filter_info['title']}")

                # Créer une petite figure pour chaque filtre
                fig, ax = plt.subplots(1, 1, figsize=(2, 2))

                # Normaliser le feature map pour l'affichage
                feature_map = filter_info['feature_map']

                # Debug info sur le feature map
                print(f"    Feature map shape: {feature_map.shape}")
                print(f"    Range: [{feature_map.min():.4f}, {feature_map.max():.4f}]")

                if feature_map.max() - feature_map.min() > 1e-8:
                    normalized_map = (feature_map - feature_map.min()) / (feature_map.max() - feature_map.min())
                else:
                    normalized_map = feature_map
                    print(f"    ⚠️ Feature map constant, pas de normalisation")

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

                filter_data = {
                    'image': f"data:image/png;base64,{img_base64}",
                    'title': filter_info['title'],
                    'layer': filter_info['layer_name'],
                    'variance': float(filter_info['variance'])
                }
                filter_images.append(filter_data)

                print(f"    ✓ Image créée avec succès")

                plt.close(fig)
                buffer.close()

            except Exception as e:
                print(f"    ❌ Erreur création visualisation filtre {filter_info['title']}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"🎨 Visualisations créées: {len(filter_images)}/{len(selected_filters)}\n")
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
            print(f"\n🌐 GET_PREDICTION_FOR_WEB_WITH_FILTERS")
            print(f"Image path: {image_path}")
            print(f"Temp folder: {temp_folder}")

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

            print(f"🎯 Résultat final web: {len(filter_visualizations)} filtres dans la réponse\n")

            return web_results

        except Exception as e:
            print(f"❌ Erreur dans get_prediction_for_web_with_filters: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_extractors_manual(self):
        """Méthode de fallback pour créer des extracteurs manuellement"""
        try:
            print("🛠️ Création manuelle d'extracteurs...")

            # Faire une prédiction pour s'assurer que le modèle est exécuté
            test_input = np.random.rand(1, 28, 28, 1).astype(np.float32)
            _ = self.model.predict(test_input, verbose=0)

            from tensorflow.keras.models import Model
            from tensorflow.keras.layers import Input

            # Identifier manuellement les couches par nom (basé sur votre log)
            target_layers = ['conv2d_8', 'conv2d_9', 'conv2d_10', 'conv2d_11']

            # Créer un input explicite
            manual_input = Input(shape=(28, 28, 1), name='manual_input')

            extractors_created = 0
            for i, layer_name in enumerate(target_layers):
                try:
                    print(f"Tentative manuelle pour {layer_name}...")

                    # Reconstruire le modèle jusqu'à cette couche
                    x = manual_input
                    target_found = False

                    for layer in self.model.layers:
                        x = layer(x)
                        if layer.name == layer_name:
                            # Créer l'extracteur pour cette couche
                            extractor = Model(inputs=manual_input, outputs=x)
                            extractor_name = f"conv_{i+1}_{layer_name}"

                            # Test rapide
                            test_output = extractor.predict(test_input, verbose=0)

                            self.feature_extractors[extractor_name] = extractor
                            extractors_created += 1
                            target_found = True
                            print(f"✓ Extracteur manuel créé: {extractor_name}")
                            break

                    if not target_found:
                        print(f"⚠️ Couche {layer_name} non trouvée")

                except Exception as manual_error:
                    print(f"❌ Erreur extracteur manuel {layer_name}: {manual_error}")
                    continue

            print(f"🛠️ Extracteurs manuels créés: {extractors_created}")

            if extractors_created > 0:
                self._extractors_initialized = True
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Échec méthode manuelle: {e}")
            return False

    # Garder la méthode originale pour compatibilité - maintenant avec filtres par défaut
    def get_prediction_for_web(self, image_data=None, image_path=None, temp_folder=None):
        """Version avec filtres par défaut pour compatibilité"""
        return self.get_prediction_for_web_with_filters(image_data, image_path, temp_folder)
