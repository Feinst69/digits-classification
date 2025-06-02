// Utility script for managing prediction display
document.addEventListener('DOMContentLoaded', function() {
    
    // Animation utilities
    function fadeIn(element, duration = 300) {
        element.style.opacity = 0;
        element.style.display = 'block';
        
        let start = performance.now();
        
        function animate(timestamp) {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    function fadeOut(element, duration = 300) {
        let start = performance.now();
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        function animate(timestamp) {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = initialOpacity * (1 - progress);
            
            if (progress >= 1) {
                element.style.display = 'none';
                element.style.opacity = initialOpacity; // Reset for future use
            } else {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    // Enhanced prediction display with animations
    function displayPredictionResultsWithAnimation(data) {
        const resultsContainer = document.getElementById('prediction-results');
        const placeholder = document.getElementById('prediction-placeholder');
        
        // Mettre à jour les valeurs
        document.getElementById('predicted-digit').textContent = data.predicted_digit;
        document.getElementById('confidence').textContent = `Confiance : ${data.confidence.toFixed(2)}%`;
        
        // Créer le graphique des probabilités avec animation
        const chartContainer = document.getElementById('probabilities-chart');
        chartContainer.innerHTML = '<h4>Détail des probabilités :</h4>';
        
        data.probabilities.forEach((prob, digit) => {
            const isHighest = digit === data.predicted_digit;
            
            const barContainer = document.createElement('div');
            barContainer.className = `prob-bar-container ${isHighest ? 'highlighted-prediction' : ''}`;
            barContainer.style.opacity = '0';
            barContainer.style.transform = 'translateX(-20px)';
            
            barContainer.innerHTML = `
                <div class="prob-label">${digit}</div>
                <div class="prob-bar-wrapper">
                    <div class="prob-bar" style="width: 0%; transition: width 0.8s ease-out;"></div>
                </div>
                <div class="prob-value">${prob.toFixed(1)}%</div>
            `;
            
            chartContainer.appendChild(barContainer);
            
            // Animer l'apparition de chaque barre avec un délai
            setTimeout(() => {
                barContainer.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                barContainer.style.opacity = '1';
                barContainer.style.transform = 'translateX(0)';
                
                // Animer la largeur de la barre
                setTimeout(() => {
                    const bar = barContainer.querySelector('.prob-bar');
                    bar.style.width = `${prob}%`;
                    
                    // Couleur spéciale pour la prédiction principale
                    if (isHighest) {
                        setTimeout(() => {
                            bar.style.backgroundColor = '#28a745';
                        }, 400);
                    }
                }, 100);
            }, digit * 100); // Délai progressif pour chaque barre
        });
        
        // Transition entre placeholder et résultats
        if (placeholder.style.display !== 'none') {
            fadeOut(placeholder, 200);
            setTimeout(() => {
                fadeIn(resultsContainer, 300);
            }, 150);
        } else {
            resultsContainer.style.display = 'block';
        }
    }
    
    // Fonction pour masquer les résultats avec animation
    function hidePredictionResultsWithAnimation() {
        const resultsContainer = document.getElementById('prediction-results');
        const placeholder = document.getElementById('prediction-placeholder');
        
        if (resultsContainer.style.display !== 'none') {
            fadeOut(resultsContainer, 200);
            setTimeout(() => {
                fadeIn(placeholder, 300);
            }, 150);
        }
    }
    
    // Fonction pour nettoyer toute l'interface
    function resetInterface() {
        // Masquer les résultats
        hidePredictionResultsWithAnimation();
        
        // Effacer l'image uploadée si elle existe
        if (window.uploadApp) {
            window.uploadApp.clearUploadedImage();
        }
        
        // Reset canvas si nécessaire
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Masquer le canvas redimensionné
        document.getElementById('resized-canvas').style.display = 'none';
        document.getElementById('resized-image-placeholder').style.display = 'flex';
    }
    
    // Améliorer l'expérience utilisateur avec des feedbacks visuels
    function showLoadingState() {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.style.display = 'block';
        }
        
        // Désactiver le bouton d'effacement pendant le chargement
        const clearBtn = document.getElementById('clear-canvas');
        
        if (clearBtn) {
            clearBtn.disabled = true;
            clearBtn.style.opacity = '0.6';
        }
    }
    
    function hideLoadingState() {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.style.display = 'none';
        }
        
        // Réactiver le bouton d'effacement
        const clearBtn = document.getElementById('clear-canvas');
        
        if (clearBtn) {
            clearBtn.disabled = false;
            clearBtn.style.opacity = '1';
        }
    }
    
    // Fonction pour afficher des messages d'erreur stylés
    function showError(message) {
        // Créer un toast d'erreur
        const errorToast = document.createElement('div');
        errorToast.className = 'error-toast';
        errorToast.innerHTML = `
            <div class="error-content">
                <span class="error-icon">⚠️</span>
                <span class="error-message">${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Ajouter les styles si ils n'existent pas
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .error-toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 0;
                    z-index: 1000;
                    min-width: 300px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    animation: slideIn 0.3s ease-out;
                }
                
                .error-content {
                    display: flex;
                    align-items: center;
                    padding: 12px 16px;
                }
                
                .error-icon {
                    margin-right: 10px;
                    font-size: 18px;
                }
                
                .error-message {
                    flex: 1;
                    font-weight: 500;
                }
                
                .error-close {
                    background: none;
                    border: none;
                    font-size: 20px;
                    cursor: pointer;
                    margin-left: 10px;
                    color: #721c24;
                }
                
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(errorToast);
        
        // Auto-remove après 5 secondes
        setTimeout(() => {
            if (errorToast.parentElement) {
                errorToast.remove();
            }
        }, 5000);
    }
    
    // Exposer les fonctions utilitaires
    window.predictionUtils = {
        displayPredictionResultsWithAnimation,
        hidePredictionResultsWithAnimation,
        resetInterface,
        showLoadingState,
        hideLoadingState,
        showError,
        fadeIn,
        fadeOut
    };
    
    // Améliorer les fonctions existantes si elles existent
    if (window.drawingApp) {
        const originalDisplayResults = window.drawingApp.displayPredictionResults;
        window.drawingApp.displayPredictionResults = function(data) {
            displayPredictionResultsWithAnimation(data);
        };
        
        const originalHideResults = window.drawingApp.hidePredictionResults;
        window.drawingApp.hidePredictionResults = function() {
            hidePredictionResultsWithAnimation();
        };
    }
});
