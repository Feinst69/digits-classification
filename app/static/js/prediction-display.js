// Enhanced utility script for managing prediction display with race condition prevention
document.addEventListener('DOMContentLoaded', function () {

  // ===== SYSTÈME DE GESTION D'ÉTAT GLOBAL =====
  const globalState = {
    isDisplayingResults: false,
    lastDisplayedTimestamp: 0,
    displayQueue: [],
    isAnimating: false
  };

  // Gestionnaire pour éviter les conflits d'affichage
  const displayManager = {
    // Vérifier si on peut afficher de nouveaux résultats
    canDisplay: function () {
      return !globalState.isAnimating;
    },

    // Mettre en file d'attente un affichage de résultats
    queueDisplay: function (data, callback) {
      const displayRequest = {
        id: `display_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        data: data,
        callback: callback,
        timestamp: Date.now()
      };

      globalState.displayQueue.push(displayRequest);
      console.log(`[DisplayManager] Queued display ${displayRequest.id}`);

      this.processQueue();
      return displayRequest.id;
    },

    // Traiter la file d'attente d'affichage
    processQueue: function () {
      if (globalState.isAnimating || globalState.displayQueue.length === 0) {
        return;
      }

      const request = globalState.displayQueue.shift();
      console.log(`[DisplayManager] Processing display ${request.id}`);

      globalState.isAnimating = true;
      globalState.lastDisplayedTimestamp = request.timestamp;

      // Exécuter le callback d'affichage
      Promise.resolve(request.callback(request.data))
        .then(() => {
          console.log(`[DisplayManager] Display ${request.id} completed`);
        })
        .catch(error => {
          console.error(`[DisplayManager] Display ${request.id} failed:`, error);
        })
        .finally(() => {
          globalState.isAnimating = false;
          // Traiter le prochain élément après un court délai
          setTimeout(() => this.processQueue(), 50);
        });
    },

    // Vider la file d'attente (utilisé lors du clear)
    clearQueue: function () {
      console.log(`[DisplayManager] Clearing display queue (${globalState.displayQueue.length} items)`);
      globalState.displayQueue = [];
      globalState.isAnimating = false;
    }
  };

  // ===== UTILITAIRES D'ANIMATION AMÉLIORÉS =====
  function fadeIn(element, duration = 300) {
    return new Promise((resolve) => {
      if (getComputedStyle(element).display === 'none') {
        element.style.opacity = 0;
        element.style.display = 'block';
      }

      let start = performance.now();

      function animate(timestamp) {
        const elapsed = timestamp - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = progress;

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      }

      requestAnimationFrame(animate);
    });
  }

  function fadeOut(element, duration = 300) {
    return new Promise((resolve) => {
      let start = performance.now();
      const initialOpacity = parseFloat(getComputedStyle(element).opacity) || 1;

      function animate(timestamp) {
        const elapsed = timestamp - start;
        const progress = Math.min(elapsed / duration, 1);

        element.style.opacity = initialOpacity * (1 - progress);

        if (progress >= 1) {
          element.style.display = 'none';
          element.style.opacity = initialOpacity;
          resolve();
        } else {
          requestAnimationFrame(animate);
        }
      }

      requestAnimationFrame(animate);
    });
  }

  // ===== AFFICHAGE DES RÉSULTATS AVEC PROTECTION =====
  function displayPredictionResultsWithAnimation(data) {
    return new Promise((resolve, reject) => {
      try {
        console.log('[PredictionDisplay] Starting result display with animation');

        const resultsContainer = document.getElementById('prediction-results');
        const placeholder = document.getElementById('prediction-placeholder');

        if (!resultsContainer || !placeholder) {
          throw new Error('Required DOM elements not found');
        }

        // Mettre à jour les valeurs de base
        const predictedDigitEl = document.getElementById('predicted-digit');
        const confidenceEl = document.getElementById('confidence');

        if (predictedDigitEl) predictedDigitEl.textContent = data.predicted_digit;
        if (confidenceEl) confidenceEl.textContent = `Confiance : ${data.confidence.toFixed(2)}%`;

        // Créer le graphique des probabilités avec animation
        createAnimatedProbabilitiesChart(data.probabilities, data.predicted_digit)
          .then(() => {
            // Transition entre placeholder et résultats
            if (placeholder.style.display !== 'none') {
              return fadeOut(placeholder, 200)
                .then(() => fadeIn(resultsContainer, 300));
            } else {
              resultsContainer.style.display = 'block';
              return Promise.resolve();
            }
          })
          .then(() => {
            globalState.isDisplayingResults = true;
            console.log('[PredictionDisplay] Result display completed successfully');
            resolve();
          })
          .catch(reject);

      } catch (error) {
        console.error('[PredictionDisplay] Error in displayPredictionResultsWithAnimation:', error);
        reject(error);
      }
    });
  }

  // ===== CRÉATION DU GRAPHIQUE ANIMÉ =====
  function createAnimatedProbabilitiesChart(probabilities, predictedDigit) {
    return new Promise((resolve) => {
      const chartContainer = document.getElementById('probabilities-chart');
      if (!chartContainer) {
        resolve();
        return;
      }

      chartContainer.innerHTML = '<h4>Détail des probabilités :</h4>';

      let animationsCompleted = 0;
      const totalBars = probabilities.length;

      probabilities.forEach((prob, digit) => {
        const isHighest = digit === predictedDigit;

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
            if (bar) {
              bar.style.width = `${prob}%`;

              // Couleur spéciale pour la prédiction principale
              if (isHighest) {
                setTimeout(() => {
                  bar.style.backgroundColor = '#28a745';
                  animationsCompleted++;
                  if (animationsCompleted >= totalBars) {
                    resolve();
                  }
                }, 400);
              } else {
                animationsCompleted++;
                if (animationsCompleted >= totalBars) {
                  resolve();
                }
              }
            }
          }, 100);
        }, digit * 100); // Délai progressif pour chaque barre
      });

      // Fallback au cas où les animations ne se termineraient pas
      setTimeout(() => {
        if (animationsCompleted < totalBars) {
          console.warn('[PredictionDisplay] Animation timeout, resolving anyway');
          resolve();
        }
      }, 3000);
    });
  }

  // ===== MASQUAGE DES RÉSULTATS AVEC PROTECTION =====
  function hidePredictionResultsWithAnimation() {
    return new Promise((resolve) => {
      if (globalState.isAnimating) {
        console.log('[PredictionDisplay] Display animation in progress, deferring hide');
        setTimeout(() => hidePredictionResultsWithAnimation().then(resolve), 100);
        return;
      }

      const resultsContainer = document.getElementById('prediction-results');
      const placeholder = document.getElementById('prediction-placeholder');

      if (!resultsContainer || !placeholder) {
        resolve();
        return;
      }

      if (resultsContainer.style.display !== 'none') {
        fadeOut(resultsContainer, 200)
          .then(() => fadeIn(placeholder, 300))
          .then(() => {
            globalState.isDisplayingResults = false;
            console.log('[PredictionDisplay] Results hidden successfully');
            resolve();
          });
      } else {
        resolve();
      }
    });
  }

  // ===== RÉINITIALISATION COMPLÈTE =====
  function resetInterface() {
    console.log('[PredictionDisplay] Resetting interface');

    // Arrêter toutes les animations en cours
    displayManager.clearQueue();

    // Masquer les résultats
    return hidePredictionResultsWithAnimation()
      .then(() => {
        // Effacer l'image uploadée si elle existe
        if (window.uploadApp && window.uploadApp.clearUploadedImage) {
          window.uploadApp.clearUploadedImage();
        }

        // Reset canvas si nécessaire
        const canvas = document.getElementById('canvas');
        if (canvas) {
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = 'white';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        // Masquer le canvas redimensionné
        const resizedCanvas = document.getElementById('resized-canvas');
        const placeholder = document.getElementById('resized-image-placeholder');
        if (resizedCanvas) resizedCanvas.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';

        console.log('[PredictionDisplay] Interface reset completed');
      });
  }

  // ===== GESTION DE L'ÉTAT DE CHARGEMENT =====
  function showLoadingState() {
    const loader = document.getElementById('loader');
    if (loader) {
      loader.style.display = 'block';
    }

    const clearBtn = document.getElementById('clear-canvas');
    if (clearBtn) {
      clearBtn.disabled = true;
      clearBtn.style.opacity = '0.6';
    }

    // Désactiver temporairement le dropzone pendant le chargement
    const dropzone = document.getElementById('dropzone');
    if (dropzone) {
      dropzone.style.pointerEvents = 'none';
      dropzone.style.opacity = '0.7';
    }
  }

  function hideLoadingState() {
    const loader = document.getElementById('loader');
    if (loader) {
      loader.style.display = 'none';
    }

    const clearBtn = document.getElementById('clear-canvas');
    if (clearBtn) {
      clearBtn.disabled = false;
      clearBtn.style.opacity = '1';
    }

    // Réactiver le dropzone
    const dropzone = document.getElementById('dropzone');
    if (dropzone) {
      dropzone.style.pointerEvents = 'auto';
      dropzone.style.opacity = '1';
    }
  }

  // ===== AFFICHAGE D'ERREUR AMÉLIORÉ =====
  function showError(message) {
    console.error('[PredictionDisplay] Showing error:', message);

    // Masquer le loader en cas d'erreur
    hideLoadingState();

    // Créer un toast d'erreur amélioré
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
                  max-width: 500px;
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
                  word-wrap: break-word;
              }

              .error-close {
                  background: none;
                  border: none;
                  font-size: 20px;
                  cursor: pointer;
                  margin-left: 10px;
                  color: #721c24;
                  padding: 0;
                  width: 24px;
                  height: 24px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
              }

              .error-close:hover {
                  background-color: rgba(114, 28, 36, 0.1);
                  border-radius: 4px;
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

              @keyframes slideOut {
                  from {
                      transform: translateX(0);
                      opacity: 1;
                  }
                  to {
                      transform: translateX(100%);
                      opacity: 0;
                  }
              }
          `;
      document.head.appendChild(style);
    }

    document.body.appendChild(errorToast);

    // Auto-remove avec animation après 7 secondes
    setTimeout(() => {
      if (errorToast.parentElement) {
        errorToast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
          if (errorToast.parentElement) {
            errorToast.remove();
          }
        }, 300);
      }
    }, 7000);
  }

  // ===== WRAPPER SÉCURISÉ POUR L'AFFICHAGE DES RÉSULTATS =====
  function safeDisplayPredictionResults(data) {
    return displayManager.queueDisplay(data, displayPredictionResultsWithAnimation);
  }

  // ===== API EXPOSÉE =====
  window.predictionUtils = {
    displayPredictionResultsWithAnimation: safeDisplayPredictionResults,
    hidePredictionResultsWithAnimation,
    resetInterface,
    showLoadingState,
    hideLoadingState,
    showError,
    fadeIn,
    fadeOut,
    displayManager: displayManager, // Pour debug
    globalState: globalState // Pour debug
  };

  // ===== AMÉLIORATION DES FONCTIONS EXISTANTES =====
  // Remplacer les fonctions du système de dessin par les versions sécurisées
  if (window.drawingApp) {
    const originalDisplayResults = window.drawingApp.displayPredictionResults;
    window.drawingApp.displayPredictionResults = function (data) {
      return safeDisplayPredictionResults(data);
    };

    const originalHideResults = window.drawingApp.hidePredictionResults;
    window.drawingApp.hidePredictionResults = function () {
      return hidePredictionResultsWithAnimation();
    };
  }

  // ===== NETTOYAGE GLOBAL LORS DU CLEAR =====
  document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'clear-canvas') {
      console.log('[PredictionDisplay] Clear button clicked, performing global cleanup');
      displayManager.clearQueue();

      // Arrêter les uploads en cours
      if (window.uploadApp && window.uploadApp.uploadManager) {
        window.uploadApp.uploadManager.cancelUpload();
      }
    }
  });

  // ===== DEBUG ET MONITORING =====
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    setInterval(() => {
      if (globalState.displayQueue.length > 0 || globalState.isAnimating) {
        console.log('[Debug] Display state:', {
          queueSize: globalState.displayQueue.length,
          isAnimating: globalState.isAnimating,
          isDisplayingResults: globalState.isDisplayingResults
        });
      }
    }, 2000);
  }
});
