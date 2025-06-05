// AJAX-based drawing functionality with auto-prediction and race condition prevention
document.addEventListener('DOMContentLoaded', function () {
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

  // ===== RACE CONDITION PREVENTION SYSTEM =====
  let isPredictionInProgress = false;
  let hasPendingPrediction = false;
  let currentAbortController = null;
  let predictionQueue = [];
  let lastPredictionTimestamp = 0;
  const MIN_PREDICTION_INTERVAL = 1000; // Minimum 1 second between predictions

  // Système de file d'attente pour les prédictions
  const predictionManager = {
    // Ajouter une nouvelle demande de prédiction à la file
    enqueuePrediction: function (imageData, priority = 'normal') {
      const timestamp = Date.now();
      const request = {
        id: `pred_${timestamp}_${Math.random().toString(36).substr(2, 9)}`,
        imageData: imageData,
        timestamp: timestamp,
        priority: priority
      };

      // Si c'est une prédiction haute priorité, l'ajouter au début
      if (priority === 'high') {
        predictionQueue.unshift(request);
      } else {
        predictionQueue.push(request);
      }

      console.log(`[PredictionManager] Enqueued prediction ${request.id}, queue size: ${predictionQueue.length}`);
      this.processQueue();
      return request.id;
    },

    // Traiter la file d'attente
    processQueue: function () {
      // Si une prédiction est en cours ou si la file est vide, ne rien faire
      if (isPredictionInProgress || predictionQueue.length === 0) {
        return;
      }

      // Vérifier l'intervalle minimum entre les prédictions
      const now = Date.now();
      const timeSinceLastPrediction = now - lastPredictionTimestamp;

      if (timeSinceLastPrediction < MIN_PREDICTION_INTERVAL) {
        const remainingDelay = MIN_PREDICTION_INTERVAL - timeSinceLastPrediction;
        console.log(`[PredictionManager] Throttling prediction, waiting ${remainingDelay}ms`);
        setTimeout(() => this.processQueue(), remainingDelay);
        return;
      }

      // Prendre le premier élément de la file
      const request = predictionQueue.shift();
      console.log(`[PredictionManager] Processing prediction ${request.id}`);

      this.executePrediction(request);
    },

    // Exécuter une prédiction
    executePrediction: function (request) {
      isPredictionInProgress = true;
      lastPredictionTimestamp = Date.now();

      // Créer un nouveau AbortController pour cette requête
      if (currentAbortController) {
        currentAbortController.abort();
      }
      currentAbortController = new AbortController();

      // Afficher le loader et l'état de chargement
      this.showLoadingState();

      // Préparer les données pour la requête
      const formData = new FormData();
      formData.append('image_data', request.imageData);

      // Ajouter le paramètre pour les filtres si disponible
      if (window.filterVisualization) {
        formData.append('show_filters', window.filterVisualization.getFilterParameter());
      }

      // Faire la requête avec timeout et abort controller
      const timeoutId = setTimeout(() => {
        currentAbortController.abort();
        console.log(`[PredictionManager] Prediction ${request.id} timed out`);
      }, 10000); // Timeout de 10 secondes

      fetch('/api/predict-and-save', {
        method: 'POST',
        body: formData,
        signal: currentAbortController.signal
      })
        .then(response => {
          clearTimeout(timeoutId);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          console.log(`[PredictionManager] Prediction ${request.id} completed successfully`);

          if (data.error) {
            throw new Error(data.error);
          }

          // Afficher les résultats de prédiction
          if (window.predictionUtils) {
            window.predictionUtils.displayPredictionResultsWithAnimation(data);
          } else {
            displayPredictionResults(data);
          }

          // Afficher les filtres CNN si disponibles
          if (data.feature_filters && data.feature_filters.length > 0 && window.filterVisualization) {
            console.log(`[PredictionManager] Displaying ${data.feature_filters.length} CNN filters`);
            // Attendre que l'affichage des résultats soit terminé avant d'afficher les filtres
            setTimeout(() => {
              window.filterVisualization.displayFilters(data.feature_filters);
            }, 300);
          } else if (window.filterVisualization) {
            // Masquer les filtres s'il n'y en a pas
            window.filterVisualization.hideFilters();
          }
        })
        .catch(error => {
          if (error.name === 'AbortError') {
            console.log(`[PredictionManager] Prediction ${request.id} was cancelled`);
          } else {
            console.error(`[PredictionManager] Prediction ${request.id} failed:`, error);

            // Afficher l'erreur avec plus de contexte
            const errorMessage = error.message.includes('HTTP')
              ? 'Erreur de connexion au serveur. Veuillez réessayer.'
              : `Erreur lors de la prédiction: ${error.message}`;

            if (window.predictionUtils) {
              window.predictionUtils.showError(errorMessage);
            } else {
              console.error('Error displaying prediction:', errorMessage);
            }

            // Masquer les filtres en cas d'erreur
            if (window.filterVisualization) {
              window.filterVisualization.hideFilters();
            }
          }
        })
        .finally(() => {
          clearTimeout(timeoutId);
          isPredictionInProgress = false;
          currentAbortController = null;

          // Masquer le loader
          this.hideLoadingState();

          // Traiter le prochain élément de la file après un court délai
          setTimeout(() => this.processQueue(), 100);
        });
    },

    // Vider la file d'attente (utilisé lors du clear)
    clearQueue: function () {
      console.log(`[PredictionManager] Clearing queue (${predictionQueue.length} items)`);
      predictionQueue = [];

      if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
      }

      isPredictionInProgress = false;
      this.hideLoadingState();

      // Masquer aussi les filtres
      if (window.filterVisualization) {
        window.filterVisualization.hideFilters();
      }
    },

    // Afficher l'état de chargement
    showLoadingState: function () {
      loader.style.display = 'block';
      if (window.predictionUtils) {
        window.predictionUtils.showLoadingState();
      }

      // Désactiver le bouton clear pendant le chargement
      clearBtn.disabled = true;
      clearBtn.style.opacity = '0.6';
    },

    // Masquer l'état de chargement
    hideLoadingState: function () {
      loader.style.display = 'none';
      if (window.predictionUtils) {
        window.predictionUtils.hideLoadingState();
      }

      // Réactiver le bouton clear
      clearBtn.disabled = false;
      clearBtn.style.opacity = '1';
    },

    // Obtenir le statut du gestionnaire
    getStatus: function () {
      return {
        inProgress: isPredictionInProgress,
        queueSize: predictionQueue.length,
        lastPrediction: lastPredictionTimestamp
      };
    }
  };

  // ===== FONCTIONS DE DESSIN (inchangées) =====
  function initCanvas() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.lineWidth = 16;
    ctx.strokeStyle = 'black';
  }

  initCanvas();

  function draw(e) {
    if (!isDrawing) return;

    e.preventDefault();

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches[0].clientX) - rect.left;
    const y = (e.clientY || e.touches[0].clientY) - rect.top;

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();

    [lastX, lastY] = [x, y];
    updateResizedImage();
  }

  function updateResizedImage() {
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = 28;
    tempCanvas.height = 28;

    tempCtx.drawImage(canvas, 0, 0, 28, 28);

    resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
    resizedCtx.imageSmoothingEnabled = false;
    resizedCtx.drawImage(tempCanvas, 0, 0, 280, 280);

    document.getElementById('resized-image-placeholder').style.display = 'none';
    resizedCanvas.style.display = 'block';
  }

  // ===== GESTION AMÉLIORÉE DE LA PRÉDICTION AUTOMATIQUE =====
  function cancelAutoPrediction() {
    if (drawingTimeout) {
      clearTimeout(drawingTimeout);
      drawingTimeout = null;
    }

    const indicator = document.getElementById('auto-predict-indicator');
    if (indicator) {
      indicator.style.display = 'none';
    }
  }

  function scheduleAutoPrediction() {
    cancelAutoPrediction();

    const indicator = document.getElementById('auto-predict-indicator');
    if (indicator) {
      indicator.style.display = 'flex';
      const countdownBar = indicator.querySelector('.countdown-bar');
      if (countdownBar) {
        countdownBar.style.animation = 'none';
        countdownBar.offsetHeight;
        countdownBar.style.animation = 'countdown 0.8s linear forwards';
      }
    }

    drawingTimeout = setTimeout(() => {
      if (indicator) {
        indicator.style.display = 'none';
      }

      if (hasDrawn && !isCanvasBlank()) {
        performAutoPrediction();
      }
    }, PREDICTION_DELAY);
  }

  // ===== NOUVELLE FONCTION DE PRÉDICTION AVEC PROTECTION =====
  function performAutoPrediction() {
    if (isCanvasBlank()) {
      console.log('[AutoPrediction] Canvas is blank, skipping prediction');
      return;
    }

    const status = predictionManager.getStatus();
    console.log('[AutoPrediction] Manager status:', status);

    // Si une prédiction est déjà en cours, ne pas en déclencher une nouvelle
    if (status.inProgress) {
      console.log('[AutoPrediction] Prediction already in progress, skipping');
      hasPendingPrediction = true;
      return;
    }

    // Convertir le canvas en base64
    const imageData = canvas.toDataURL('image/png');

    // Ajouter à la file d'attente avec priorité normale
    const predictionId = predictionManager.enqueuePrediction(imageData, 'normal');
    console.log(`[AutoPrediction] Scheduled prediction with ID: ${predictionId}`);

    hasPendingPrediction = false;
  }

  // ===== GESTIONNAIRES D'ÉVÉNEMENTS (améliorés) =====
  canvas.addEventListener('mousedown', (e) => {
    isDrawing = true;
    hasDrawn = true;
    const rect = canvas.getBoundingClientRect();
    [lastX, lastY] = [e.clientX - rect.left, e.clientY - rect.top];
    cancelAutoPrediction();
  });

  canvas.addEventListener('touchstart', (e) => {
    isDrawing = true;
    hasDrawn = true;
    const rect = canvas.getBoundingClientRect();
    [lastX, lastY] = [e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top];
    cancelAutoPrediction();
  });

  canvas.addEventListener('mousemove', draw);
  canvas.addEventListener('touchmove', draw);

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

  // ===== EFFACEMENT AMÉLIORÉ =====
  clearBtn.addEventListener('click', function () {
    console.log('[Clear] Clearing canvas and prediction queue');

    // Arrêter toutes les prédictions en cours et vider la file
    predictionManager.clearQueue();

    initCanvas();
    hasDrawn = false;
    cancelAutoPrediction();

    resizedCanvas.style.display = 'none';
    document.getElementById('resized-image-placeholder').style.display = 'flex';

    hidePredictionResults();
  });

  // ===== FONCTIONS UTILITAIRES (inchangées) =====
  function isCanvasBlank() {
    const pixelBuffer = new Uint32Array(
      ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
    );

    const whitePixel = 0xFFFFFFFF;
    const sampleSize = 1000;
    const stride = Math.max(1, Math.floor(pixelBuffer.length / sampleSize));

    for (let i = 0; i < pixelBuffer.length; i += stride) {
      if (pixelBuffer[i] !== whitePixel) {
        return false;
      }
    }

    return true;
  }

  function hidePredictionResults() {
    document.getElementById('prediction-results').style.display = 'none';
    document.getElementById('prediction-placeholder').style.display = 'flex';
  }

  function displayPredictionResults(data) {
    document.getElementById('predicted-digit').textContent = data.predicted_digit;
    document.getElementById('confidence').textContent = `Confiance : ${data.confidence.toFixed(2)}%`;

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

    document.getElementById('prediction-placeholder').style.display = 'none';
    document.getElementById('prediction-results').style.display = 'block';
  }

  // ===== API EXPOSÉE (améliorée) =====
  window.drawingApp = {
    displayPredictionResults,
    hidePredictionResults,
    updateResizedImage,
    loader,
    performAutoPrediction,
    scheduleAutoPrediction,
    cancelAutoPrediction,
    predictionManager: predictionManager, // Exposer le gestionnaire pour debug
    getStatus: () => predictionManager.getStatus()
  };

  // ===== DEBUG ET MONITORING =====
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Mode debug uniquement en local
    setInterval(() => {
      const status = predictionManager.getStatus();
      if (status.queueSize > 0 || status.inProgress) {
        console.log('[Debug] Prediction status:', status);
      }
    }, 2000);
  }
});
