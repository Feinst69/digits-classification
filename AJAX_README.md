# Application AJAX - Reconnaissance de Chiffres Manuscrits

## 🆕 Nouvelles Fonctionnalités AJAX

L'application a été entièrement transformée pour offrir une expérience utilisateur moderne avec des prédictions en temps réel sur une seule page, sans rechargements.

### ✨ Fonctionnalités

#### Interface en Temps Réel
- **Canvas de dessin au centre** : Dessinez vos chiffres directement
- **Image redimensionnée à gauche** : Visualisez l'image 28x28 utilisée par le modèle
- **Prédictions à droite** : Résultats instantanés avec graphique des probabilités
- **Pas de rechargement de page** : Tout fonctionne en AJAX

#### Modes d'Entrée
1. **Dessin au canvas** : Dessinez directement avec la souris ou le tactile
2. **Upload de fichiers** : Glissez-déposez ou sélectionnez une image

#### Améliorations UX
- Animations fluides pour l'affichage des résultats
- Messages d'erreur stylés (toasts)
- Indicateurs de chargement améliorés
- Interface responsive (mobile/desktop)

## 📁 Structure des Fichiers

### Nouveaux Fichiers JavaScript
```
app/static/js/
├── draw-ajax.js           # Gestion du canvas avec AJAX
├── upload-ajax.js         # Upload de fichiers avec AJAX  
├── prediction-display.js  # Utilitaires d'affichage et animations
├── draw.js               # (ancien, gardé pour compatibilité)
└── upload.js             # (ancien, gardé pour compatibilité)
```

### Templates Mis à Jour
```
app/templates/
├── index.html            # Nouvelle interface AJAX
├── result.html           # Page de fallback 
└── result.html.backup    # Ancienne version sauvegardée
```

### Nouvelles Routes API
- `POST /api/predict` : Prédiction simple (existante)
- `POST /api/predict-with-image` : Prédiction avec image redimensionnée en base64

## 🚀 Utilisation

### Démarrer l'Application
```bash
cd app
python app.py
```

### Tester l'Application
```bash
# Exécuter les tests automatiques
python test_ajax_app.py
```

### Accéder à l'Interface
Ouvrez votre navigateur et allez à : `http://localhost:5000`

## 🎯 Mode d'Emploi

### 1. Dessiner un Chiffre
1. Utilisez la zone de dessin au centre
2. L'image redimensionnée apparaît automatiquement à gauche
3. **Arrêtez de dessiner** - un indicateur "Prédiction automatique..." apparaît
4. Après 800ms, la prédiction se lance automatiquement
5. Les résultats s'affichent à droite avec animations

### 2. Uploader une Image
1. Glissez-déposez une image sur la zone de drop
2. Ou cliquez pour sélectionner un fichier
3. La prédiction se lance automatiquement
4. L'image redimensionnée et les résultats s'affichent

### 3. Effacer et Recommencer
- Cliquez sur "Effacer" pour nettoyer le canvas
- Toutes les zones se remettent à zéro automatiquement

## 🔧 Architecture Technique

### Frontend (JavaScript)
- **draw-ajax.js** : Gère le canvas de dessin et les prédictions AJAX
- **upload-ajax.js** : Gère l'upload de fichiers et les prédictions
- **prediction-display.js** : Animations et utilitaires d'affichage

### Backend (Flask)
- Routes API RESTful pour les prédictions
- Support des images en base64 et fichiers
- Gestion d'erreurs améliorée

### Modèle IA
- Utilise le même modèle CNN existant
- Nouvelles fonctions pour retourner l'image redimensionnée
- Prédictions optimisées pour l'AJAX

## 🎨 Styles CSS

L'interface utilise un layout flexbox moderne :
- **Responsive design** : S'adapte aux écrans mobiles et desktop
- **Animations CSS** : Transitions fluides pour les résultats
- **Composants modulaires** : Styles réutilisables

## 📱 Compatibilité

- **Navigateurs modernes** : Chrome, Firefox, Safari, Edge
- **Appareils tactiles** : Support complet du dessin au doigt
- **Responsive** : Interface adaptée mobile/tablette/desktop

## 🔍 Débogage

### Vérifier les Erreurs JavaScript
```javascript
// Dans la console du navigateur
console.log(window.drawingApp);     // Fonctions de dessin
console.log(window.uploadApp);      // Fonctions d'upload
console.log(window.predictionUtils); // Utilitaires d'affichage
```

### Tester les API
```bash
# Test avec curl
curl -X POST -F "file=@image.png" http://localhost:5000/api/predict
curl -X POST -F "file=@image.png" http://localhost:5000/api/predict-with-image
```

### Logs Backend
Les erreurs backend s'affichent dans la console du serveur Flask.

## 🆙 Migration depuis l'Ancienne Version

### Changements Principaux
1. **Interface unifiée** : Plus besoin de pages séparées
2. **AJAX par défaut** : Pas de rechargements de page
3. **Nouveau layout** : Disposition en 3 colonnes
4. **🆕 Prédiction automatique** : Plus de bouton "Analyser" - tout est automatique !

### Rétrocompatibilité
- Les anciennes routes fonctionnent toujours
- L'ancien template `result.html` est gardé en fallback
- Les anciens scripts JS sont conservés

## 🎯 Prochaines Améliorations Possibles

- [ ] Historique des prédictions en temps réel
- [ ] Mode plein écran pour le canvas
- [ ] Enregistrement des dessins
- [ ] Partage des prédictions
- [ ] Mode sombre/clair
- [ ] Multi-langues
- [ ] ⚙️ Délai de prédiction configurable
- [ ] 🔄 Mode prédiction continue (mise à jour pendant le dessin)

## 📞 Support

En cas de problème :
1. Vérifiez la console JavaScript du navigateur
2. Vérifiez les logs du serveur Flask
3. Lancez `python test_ajax_app.py` pour diagnostiquer
