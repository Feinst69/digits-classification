# Techniques d'amélioration des réseaux CNN

## Couches et structure

### Conv2D avec padding='same'
Maintient les dimensions spatiales durant la convolution en ajoutant des zéros autour de l'entrée. Permet de préserver les informations aux bords des images et de construire des réseaux plus profonds.

### BatchNormalization
Normalise les activations d'une couche précédente pour chaque mini-batch. Accélère l'entraînement, permet d'utiliser des taux d'apprentissage plus élevés et réduit la dépendance à l'initialisation des poids.

### Activation séparée
Extraction de la fonction d'activation en couche distincte pour plus de clarté. Facilite la visualisation du flux de données et permet une meilleure modularité dans la conception du réseau.

### MaxPool2D
Réduit la dimension spatiale (largeur et hauteur) des cartes de caractéristiques. Diminue le nombre de paramètres et le temps de calcul tout en rendant le modèle plus robuste aux variations de position.

### Dropout
Désactive aléatoirement un pourcentage de neurones pendant l'entraînement. Fonctionne comme une régularisation, empêche la co-adaptation des neurones et réduit significativement le surapprentissage.

### Dense avec plus de neurones
Augmente la capacité du réseau à apprendre des représentations complexes. Capture davantage de caractéristiques abstraites avant la classification finale, améliorant généralement la précision.

## Configuration d'entraînement

### Adam optimizer
Algorithme d'optimisation adaptatif combinant les avantages d'AdaGrad et RMSProp. Ajuste automatiquement les taux d'apprentissage par paramètre et incorpore la notion de momentum pour une convergence plus rapide.

### EarlyStopping
Arrête l'entraînement lorsque la métrique surveillée cesse de s'améliorer pendant un nombre défini d'époques. Évite le surapprentissage et économise du temps de calcul en détectant quand le modèle cesse de progresser.

### ReduceLROnPlateau
Réduit le taux d'apprentissage lorsque la métrique surveillée stagne. Permet d'affiner l'apprentissage dans les dernières phases d'entraînement pour franchir les plateaux de la fonction de coût.

### ModelCheckpoint
Sauvegarde le modèle à différents moments de l'entraînement selon un critère défini. Garantit que la meilleure version du modèle est conservée, même si l'entraînement se détériore par la suite.

### Validation split
Réserve une portion des données d'entraînement pour évaluer le modèle pendant l'apprentissage. Fournit un signal crucial sur la capacité de généralisation et aide à détecter le surapprentissage.

### Batch size plus grand
Augmente le nombre d'échantillons traités avant la mise à jour des poids. Stabilise l'entraînement avec des gradients moins bruités et permet une meilleure utilisation du parallélisme matériel.
