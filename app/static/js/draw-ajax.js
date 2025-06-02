// AJAX-based drawing functionality with auto-prediction
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const resizedCanvas = document.getElementById('resized-canvas');
    const resizedCtx = resizedCanvas.getContext('2d');
    const clearBtn = document.getElementById('clear-canvas');
    const loader = document.getElementById('loader');
    
    // Variables pour le dessin et la prédiction automatique
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let drawingTimeout = null;
    let hasDrawn = false;
    const PREDICTION_DELAY = 800; // Délai en ms après arrêt du dessin avant prédiction
    
    // Initialisation du canvas
    function initCanvas() {
        // Fond blanc
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Style de dessin
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.lineWidth = 16;
        ctx.strokeStyle = 'black';
    }
    
    initCanvas();
    
    // Fonction de dessin
    function draw(e) {
        if (!isDrawing) return;
        
        // Empêcher le défilement sur les appareils tactiles
        e.preventDefault();
        
        // Obtenir les coordonnées
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX || e.touches[0].clientX) - rect.left;
        const y = (e.clientY || e.touches[0].clientY) - rect.top;
        
        // Dessiner une ligne
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.stroke();
        
        // Mettre à jour les dernières coordonnées
        [lastX, lastY] = [x, y];
        
        // Mettre à jour l'image redimensionnée en temps réel
        updateResizedImage();
    }
    
    // Mettre à jour l'image redimensionnée (28x28)
    function updateResizedImage() {
        // Créer un canvas temporaire pour redimensionner
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = 28;
        tempCanvas.height = 28;
        
        // Redimensionner l'image du canvas principal
        tempCtx.drawImage(canvas, 0, 0, 28, 28);
        
        // Afficher l'image redimensionnée dans le canvas de droite (agrandi à 280x280)
        resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
        resizedCtx.imageSmoothingEnabled = false; // Pixel art style
        resizedCtx.drawImage(tempCanvas, 0, 0, 280, 280);
        
        // Afficher le canvas redimensionné
        document.getElementById('resized-image-placeholder').style.display = 'none';
        resizedCanvas.style.display = 'block';
    }
    
    // Fonction utilitaire pour annuler la prédiction en cours
    function cancelAutoPrediction() {
        if (drawingTimeout) {
            clearTimeout(drawingTimeout);
            drawingTimeout = null;
        }
        
        // Masquer l'indicateur de prédiction automatique
        const indicator = document.getElementById('auto-predict-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    // Gestionnaires d'événements pour le dessin avec prédiction automatique
    canvas.addEventListener('mousedown', (e) => {
        isDrawing = true;
        hasDrawn = true;
        const rect = canvas.getBoundingClientRect();
        [lastX, lastY] = [e.clientX - rect.left, e.clientY - rect.top];
        
        // Annuler toute prédiction en attente
        cancelAutoPrediction();
    });
    
    canvas.addEventListener('touchstart', (e) => {
        isDrawing = true;
        hasDrawn = true;
        const rect = canvas.getBoundingClientRect();
        [lastX, lastY] = [e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top];
        
        // Annuler toute prédiction en attente
        cancelAutoPrediction();
    });
    
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('touchmove', draw);
    
    // Événements de fin de dessin - déclenchent la prédiction automatique
    canvas.addEventListener('mouseup', () => {
        isDrawing = false;
        scheduleAutoPrediction();
    });
    
    canvas.addEventListener('touchend', () => {
        isDrawing = false;
        scheduleAutoPrediction();
    });
    
    canvas.addEventListener('mouseout', () => {
        if (isDrawing) {
            isDrawing = false;
            scheduleAutoPrediction();
        }
    });
    
    // Programmer une prédiction automatique après un délai
    function scheduleAutoPrediction() {
        // Annuler toute prédiction précédente en attente
        cancelAutoPrediction();
        
        // Afficher l'indicateur de prédiction automatique
        const indicator = document.getElementById('auto-predict-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
            // Redémarrer l'animation
            const countdownBar = indicator.querySelector('.countdown-bar');
            if (countdownBar) {
                countdownBar.style.animation = 'none';
                countdownBar.offsetHeight; // Force reflow
                countdownBar.style.animation = 'countdown 0.8s linear forwards';
            }
        }
        
        // Programmer une nouvelle prédiction
        drawingTimeout = setTimeout(() => {
            // Masquer l'indicateur
            if (indicator) {
                indicator.style.display = 'none';
            }
            
            if (hasDrawn && !isCanvasBlank()) {
                performAutoPrediction();
            }
        }, PREDICTION_DELAY);
    }
    
    // Effectuer la prédiction automatique
    function performAutoPrediction() {
        // Vérifier si le canvas contient quelque chose
        if (isCanvasBlank()) {
            return;
        }
        
        // Convertir le canvas en base64
        const imageData = canvas.toDataURL('image/png');
        
        // Afficher le loader
        loader.style.display = 'block';
        if (window.predictionUtils) {
            window.predictionUtils.showLoadingState();
        }
        
        // Faire la requête AJAX
        const formData = new FormData();
        formData.append('image_data', imageData);
        
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
                    console.error('Erreur prédiction:', data.error);
                }
            } else {
                // Afficher les résultats
                if (window.predictionUtils) {
                    window.predictionUtils.displayPredictionResultsWithAnimation(data);
                } else {
                    displayPredictionResults(data);
                }
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            if (window.predictionUtils) {
                window.predictionUtils.showError('Erreur lors de la prédiction.');
            }
        })
        .finally(() => {
            // Masquer le loader
            loader.style.display = 'none';
            if (window.predictionUtils) {
                window.predictionUtils.hideLoadingState();
            }
        });
    }
    
    // Effacer le canvas
    clearBtn.addEventListener('click', function() {
        initCanvas();
        
        // Reset des variables
        hasDrawn = false;
        cancelAutoPrediction();
        
        // Masquer l'image redimensionnée
        resizedCanvas.style.display = 'none';
        document.getElementById('resized-image-placeholder').style.display = 'flex';
        
        // Masquer les résultats de prédiction
        hidePredictionResults();
    });
    
    // Fonction pour vérifier si le canvas est vide
    function isCanvasBlank() {
        const pixelBuffer = new Uint32Array(
            ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
        );
        
        // Vérifier si tous les pixels sont blancs
        const whitePixel = 0xFFFFFFFF;  // RGBA pour blanc
        const sampleSize = 1000;
        const stride = Math.max(1, Math.floor(pixelBuffer.length / sampleSize));
        
        for (let i = 0; i < pixelBuffer.length; i += stride) {
            if (pixelBuffer[i] !== whitePixel) {
                return false;
            }
        }
        
        return true;
    }
    
    // Fonction pour masquer les résultats de prédiction
    function hidePredictionResults() {
        document.getElementById('prediction-results').style.display = 'none';
        document.getElementById('prediction-placeholder').style.display = 'flex';
    }
    
    // Fonction pour afficher les résultats de prédiction
    function displayPredictionResults(data) {
        // Mettre à jour les valeurs
        document.getElementById('predicted-digit').textContent = data.predicted_digit;
        document.getElementById('confidence').textContent = `Confiance : ${data.confidence.toFixed(2)}%`;
        
        // Créer le graphique des probabilités
        const chartContainer = document.getElementById('probabilities-chart');
        chartContainer.innerHTML = '<h4>Détail des probabilités :</h4>';
        
        data.probabilities.forEach((prob, digit) => {
            const isHighest = digit === data.predicted_digit;
            
            const barContainer = document.createElement('div');
            barContainer.className = `prob-bar-container ${isHighest ? 'highlighted-prediction' : ''}`;
            
            barContainer.innerHTML = `
                <div class="prob-label">${digit}</div>
                <div class="prob-bar-wrapper">
                    <div class="prob-bar" style="width: ${prob}%"></div>
                </div>
                <div class="prob-value">${prob.toFixed(1)}%</div>
            `;
            
            chartContainer.appendChild(barContainer);
        });
        
        // Afficher les résultats
        document.getElementById('prediction-placeholder').style.display = 'none';
        document.getElementById('prediction-results').style.display = 'block';
    }
    
    // Exposer les fonctions pour les autres scripts
    window.drawingApp = {
        displayPredictionResults,
        hidePredictionResults,
        updateResizedImage,
        loader,
        performAutoPrediction,
        scheduleAutoPrediction,
        cancelAutoPrediction
    };
});
