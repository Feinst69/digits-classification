# Application de Reconnaissance de Chiffres Manuscrits

Cette application Flask utilise un réseau de neurones convolutif (CNN) pour reconnaître des chiffres manuscrits. Elle offre deux méthodes d'entrée : le dessin direct sur un canvas et le téléchargement d'images.

## Fonctionnalités

- Interface de dessin interactive pour dessiner un chiffre
- Glisser-déposer ou téléchargement d'images de chiffres
- Visualisation des résultats avec graphiques de probabilités
- API JSON pour l'intégration avec d'autres applications

## Structure du Projet

```
CNN/
├── app/                      # Application Flask
│   ├── static/               # Fichiers statiques (CSS, JS)
│   │   ├── css/              # Styles CSS
│   │   ├── js/               # Scripts JavaScript
│   │   ├── temp/             # Dossier pour les graphiques temporaires
│   │   └── uploads/          # Dossier pour les images téléchargées
│   ├── templates/            # Templates HTML
│   └── script.py             # Script principal Flask
├── models/                   # Modèles entraînés
│   └── best_cnn_model.keras  # Modèle CNN utilisé pour les prédictions
├── src/                      # Code source
│   └── CNN_MODEL.py          # Classe pour la gestion du modèle
└── images/                   # Images d'exemple pour les tests
```

## Prérequis

- Python 3.6+
- TensorFlow 2.x
- Flask
- Pillow
- NumPy
- Matplotlib

## Installation

1. Clonez ce dépôt :
```bash
git clone <repository-url>
cd CNN
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Exécution de l'Application

1. Lancez l'application Flask :
```bash
cd app
python script.py
```

2. Ouvrez votre navigateur et accédez à :
```
http://localhost:5000
```

## Utilisation

### Dessiner un Chiffre
1. Utilisez la zone de dessin pour dessiner un chiffre en noir sur fond blanc
2. Cliquez sur "Analyser" pour obtenir la prédiction

### Télécharger une Image
1. Glissez-déposez une image dans la zone prévue ou cliquez pour sélectionner une image
2. L'analyse se lancera automatiquement après le téléchargement

## API JSON

L'application fournit également une API JSON pour l'intégration :

- Endpoint : `/api/predict`
- Méthode : POST
- Entrées : 
  - Soit `file` : fichier image
  - Soit `image_data` : données d'image en base64
- Sortie : JSON avec les résultats de prédiction

## Développement

- Le modèle CNN a été entraîné sur le dataset MNIST
- Les différentes versions du modèle (basic, intermediate, best) sont disponibles dans le dossier `models`
- La classe `CNN_MODEL` centralise toutes les fonctionnalités de prédiction et visualisation
