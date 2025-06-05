
# Veille documentaire du projet DIGITS-CLASSIFICATION

## 1. Réalisez une veille sur les réseaux de neurones artificiels de type convolutifs. Quel est l’architecture typique d’un CNN ?

Un réseau neuronal convolutif (CNN) est une architecture de réseau pour l'apprentissage profond. Les CNN sont particulièrement utiles pour trouver des motifs dans les images afin de reconnaître des objets. Ils peuvent également être très efficaces pour classer des données non-image comme l'audio, les séries temporelles et les données de signal.

Un réseau de neurones convolutifs (CNN) est composé de couches convolutives pour extraire des caractéristiques, de fonctions d'activation pour introduire de la non-linéarité, de couches de pooling pour réduire la dimensionnalité, puis de couches entièrement connectées pour effectuer la classification, avec parfois des couches de dropout pour éviter le surapprentissage.

Détails des composantes principales d'un CNN

Couches Convolutives : Ces couches appliquent des filtres (noyaux) à l'image d'entrée pour en extraire des caractéristiques telles que les contours, les textures et les formes. Chaque filtre produit une carte de caractéristiques qui met en évidence certains aspects spécifiques de l'entrée.

Fonctions d'Activation : Après la convolution, des fonctions d'activation comme ReLU (Rectified Linear Unit) introduisent de la non-linéarité, permettant au réseau de modéliser des relations complexes.

Couches de Pooling : Le pooling réduit les dimensions spatiales des cartes de caractéristiques, conservant l'information la plus importante tout en diminuant la charge de calcul. Les méthodes de pooling les plus courantes incluent le max pooling et le average pooling.

Couches Entièrement Connectées : Ces couches prennent les caractéristiques de haut niveau extraites par les couches de convolution et de pooling, et les associent à la sortie finale, comme les probabilités de classes dans les tâches de classification.

Couches de Dropout : Pour éviter le surapprentissage (overfitting), les couches de dropout désactivent aléatoirement une fraction des neurones pendant l'entraînement, favorisant ainsi la capacité du réseau à généraliser.

![alt text](images/image.png)
![alt text](images/image-1.png)
![alt text](images/image-2.png)

Sources:
- https://medium.com/@draj0718/convolutional-neural-networks-cnn-architectures-explained-716fb197b243
- https://learnopencv.com/understanding-convolutional-neural-networks-cnn/?utm_source=chatgpt.com

## 2. Donnez le principe de fonctionnement d’une couche convolutive. Qu’est ce qu’un filtre de convolution ?

![alt text](images/image-3.png)
![alt text](images/image-5.png)

Sources:
- https://www.innovatiana.com/post/convolutional-neural-network?utm_source=chatgpt.com

## 3. Comment un filtre de convolution est-il appliqué à une image en entrée ? Qu’est ce qui en résulte ? En quoi est-il utile pour la détection d'objets ?

La couche convolutive fonctionne donc en faisant glisser un filtre de convolution sur l'image d'entrée.
Les filtres sont généralement de petites matrices (3x3 - 5x5).
Elle effectue sur chaque position une opération de produit scalaire entre le filtre et la portion correspondante de l'image. Le résultat de cette opération est une carte de caractéristiques qui met en avant certaines caractéristiques de l'image et facilite le processus de détection d'objets.


Sources:
- https://blent.ai/blog/a/cnn-comment-ca-marche



images/
