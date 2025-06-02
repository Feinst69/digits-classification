// AJAX-based upload functionality
document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const resizedCanvas = document.getElementById('resized-canvas');
    const resizedCtx = resizedCanvas.getContext('2d');
    
    // Gérer le clic sur la zone de dépôt
    dropzone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Gérer la sélection de fichier
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });
    
    // Gérer le drag over
    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
    });
    
    // Gérer le drag leave
    dropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
    });
    
    // Gérer le drop
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            
            // Vérifier si c'est une image
            if (!file.type.match('image.*')) {
                alert('Veuillez déposer une image valide.');
                return;
            }
            
            handleFileUpload(file);
        }
    });
    
    // Fonction principale pour gérer l'upload de fichier
    function handleFileUpload(file) {
        // Afficher le loader
        if (window.drawingApp) {
            window.drawingApp.loader.style.display = 'block';
        }
        
        // Créer un objet FileReader pour lire le fichier
        const reader = new FileReader();
        
        reader.onload = function(e) {
            // Créer une image pour afficher dans le canvas redimensionné
            const img = new Image();
            
            img.onload = function() {
                // Afficher l'image redimensionnée
                displayResizedImage(img);
                
                // Faire la prédiction via AJAX
                makePrediction(file);
            };
            
            img.src = e.target.result;
        };
        
        reader.readAsDataURL(file);
    }
    
    // Afficher l'image redimensionnée dans le canvas
    function displayResizedImage(img) {
        // Créer un canvas temporaire pour redimensionner à 28x28
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = 28;
        tempCanvas.height = 28;
        
        // Redimensionner l'image à 28x28
        tempCtx.drawImage(img, 0, 0, 28, 28);
        
        // Afficher l'image redimensionnée dans le canvas visible (280x280)
        resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
        resizedCtx.imageSmoothingEnabled = false; // Pixel art style
        resizedCtx.drawImage(tempCanvas, 0, 0, 280, 280);
        
        // Afficher le canvas redimensionné
        document.getElementById('resized-image-placeholder').style.display = 'none';
        resizedCanvas.style.display = 'block';
    }
    
    // Afficher l'image redimensionnée à partir d'une image base64
    function displayResizedImageFromBase64(base64Image) {
        const img = new Image();
        img.onload = function() {
            // Afficher directement l'image 28x28 agrandie à 280x280
            resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
            resizedCtx.imageSmoothingEnabled = false; // Pixel art style
            resizedCtx.drawImage(img, 0, 0, 280, 280);
            
            // Afficher le canvas redimensionné
            document.getElementById('resized-image-placeholder').style.display = 'none';
            resizedCanvas.style.display = 'block';
        };
        img.src = base64Image;
    }
    
    // Faire la prédiction via AJAX
    function makePrediction(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/api/predict-and-save', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (window.predictionUtils) {
                    window.predictionUtils.showError('Erreur lors de la prédiction: ' + data.error);
                } else {
                    alert('Erreur lors de la prédiction: ' + data.error);
                }
            } else {
                // Si nous avons l'image redimensionnée en base64, l'afficher
                if (data.resized_image_base64) {
                    displayResizedImageFromBase64(data.resized_image_base64);
                }
                
                // Afficher les résultats en utilisant la fonction du script de dessin
                if (window.drawingApp) {
                    window.drawingApp.displayPredictionResults(data);
                } else if (window.predictionUtils) {
                    window.predictionUtils.displayPredictionResultsWithAnimation(data);
                }
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            if (window.predictionUtils) {
                window.predictionUtils.showError('Erreur lors de la prédiction.');
            } else {
                alert('Erreur lors de la prédiction.');
            }
        })
        .finally(() => {
            // Masquer le loader
            if (window.drawingApp) {
                window.drawingApp.loader.style.display = 'none';
            }
            if (window.predictionUtils) {
                window.predictionUtils.hideLoadingState();
            }
        });
    }
    
    // Fonction pour effacer l'image uploadée (utilisée par les autres scripts)
    function clearUploadedImage() {
        resizedCanvas.style.display = 'none';
        document.getElementById('resized-image-placeholder').style.display = 'flex';
        fileInput.value = ''; // Reset file input
    }
    
    // Exposer les fonctions pour les autres scripts
    window.uploadApp = {
        clearUploadedImage,
        displayResizedImage,
        displayResizedImageFromBase64,
        makePrediction
    };
});
