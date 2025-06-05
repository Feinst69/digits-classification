// AJAX-based upload functionality with race condition prevention
document.addEventListener('DOMContentLoaded', function () {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const resizedCanvas = document.getElementById('resized-canvas');
  const resizedCtx = resizedCanvas.getContext('2d');

  // ===== RACE CONDITION PREVENTION FOR UPLOADS =====
  let isUploadInProgress = false;
  let currentUploadController = null;

  const uploadManager = {
    // Vérifier si un upload peut être déclenché
    canStartUpload: function () {
      if (isUploadInProgress) {
        console.log('[UploadManager] Upload already in progress, rejecting new upload');
        if (window.predictionUtils) {
          window.predictionUtils.showError('Un upload est déjà en cours. Veuillez patienter.');
        }
        return false;
      }

      // Vérifier si le système de prédiction est disponible
      if (window.drawingApp && window.drawingApp.getStatus) {
        const predictionStatus = window.drawingApp.getStatus();
        if (predictionStatus.inProgress) {
          console.log('[UploadManager] Prediction in progress, deferring upload');
          if (window.predictionUtils) {
            window.predictionUtils.showError('Une prédiction est en cours. Veuillez patienter.');
          }
          return false;
        }
      }

      return true;
    },

    // Démarrer un upload
    startUpload: function (file) {
      if (!this.canStartUpload()) {
        return false;
      }

      isUploadInProgress = true;

      // Nettoyer toute prédiction en cours si le système de dessin est disponible
      if (window.drawingApp && window.drawingApp.predictionManager) {
        console.log('[UploadManager] Clearing prediction queue for upload');
        window.drawingApp.predictionManager.clearQueue();
      }

      // Créer un nouveau AbortController pour cet upload
      if (currentUploadController) {
        currentUploadController.abort();
      }
      currentUploadController = new AbortController();

      return true;
    },

    // Terminer un upload
    finishUpload: function () {
      isUploadInProgress = false;
      currentUploadController = null;
      console.log('[UploadManager] Upload finished');
    },

    // Annuler un upload
    cancelUpload: function () {
      if (currentUploadController) {
        currentUploadController.abort();
      }
      this.finishUpload();
      console.log('[UploadManager] Upload cancelled');
    }
  };

  // ===== VALIDATION DE FICHIER AMÉLIORÉE =====
  function validateFile(file) {
    // Vérifier le type de fichier
    if (!file.type.match('image.*')) {
      throw new Error('Veuillez sélectionner une image valide (PNG, JPG, GIF, etc.)');
    }

    // Vérifier la taille du fichier (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new Error('L\'image est trop voluminuse. Taille maximum: 10MB');
    }

    // Vérifier les dimensions (sera fait après chargement)
    return true;
  }

  // ===== GESTIONNAIRES D'ÉVÉNEMENTS =====
  dropzone.addEventListener('click', function () {
    if (!uploadManager.canStartUpload()) {
      return;
    }
    fileInput.click();
  });

  fileInput.addEventListener('change', function () {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  dropzone.addEventListener('dragover', function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploadInProgress) {
      this.classList.add('dragover');
    }
  });

  dropzone.addEventListener('dragleave', function (e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');

    if (!uploadManager.canStartUpload()) {
      return;
    }

    if (e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];

      try {
        validateFile(file);
        handleFileUpload(file);
      } catch (error) {
        if (window.predictionUtils) {
          window.predictionUtils.showError(error.message);
        } else {
          alert(error.message);
        }
      }
    }
  });

  // ===== FONCTION PRINCIPALE D'UPLOAD AMÉLIORÉE =====
  function handleFileUpload(file) {
    console.log('[Upload] Starting file upload:', file.name);

    try {
      validateFile(file);
    } catch (error) {
      if (window.predictionUtils) {
        window.predictionUtils.showError(error.message);
      } else {
        alert(error.message);
      }
      return;
    }

    if (!uploadManager.startUpload(file)) {
      return;
    }

    // Afficher le loader
    if (window.drawingApp) {
      window.drawingApp.loader.style.display = 'block';
    }

    const reader = new FileReader();

    reader.onload = function (e) {
      const img = new Image();

      img.onload = function () {
        try {
          // Valider les dimensions de l'image
          if (img.width > 5000 || img.height > 5000) {
            throw new Error('Image trop grande. Dimensions maximum: 5000x5000 pixels');
          }

          if (img.width < 10 || img.height < 10) {
            throw new Error('Image trop petite. Dimensions minimum: 10x10 pixels');
          }

          // Afficher l'image redimensionnée
          displayResizedImage(img);

          // Faire la prédiction
          makePrediction(file);

        } catch (error) {
          uploadManager.finishUpload();
          if (window.drawingApp) {
            window.drawingApp.loader.style.display = 'none';
          }

          if (window.predictionUtils) {
            window.predictionUtils.showError(error.message);
          } else {
            alert(error.message);
          }
        }
      };

      img.onerror = function () {
        uploadManager.finishUpload();
        if (window.drawingApp) {
          window.drawingApp.loader.style.display = 'none';
        }

        const errorMsg = 'Impossible de charger l\'image. Vérifiez que le fichier n\'est pas corrompu.';
        if (window.predictionUtils) {
          window.predictionUtils.showError(errorMsg);
        } else {
          alert(errorMsg);
        }
      };

      img.src = e.target.result;
    };

    reader.onerror = function () {
      uploadManager.finishUpload();
      if (window.drawingApp) {
        window.drawingApp.loader.style.display = 'none';
      }

      const errorMsg = 'Erreur lors de la lecture du fichier.';
      if (window.predictionUtils) {
        window.predictionUtils.showError(errorMsg);
      } else {
        alert(errorMsg);
      }
    };

    reader.readAsDataURL(file);
  }

  // ===== AFFICHAGE D'IMAGE (amélioré) =====
  function displayResizedImage(img) {
    try {
      const tempCanvas = document.createElement('canvas');
      const tempCtx = tempCanvas.getContext('2d');
      tempCanvas.width = 28;
      tempCanvas.height = 28;

      tempCtx.drawImage(img, 0, 0, 28, 28);

      resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
      resizedCtx.imageSmoothingEnabled = false;
      resizedCtx.drawImage(tempCanvas, 0, 0, 280, 280);

      document.getElementById('resized-image-placeholder').style.display = 'none';
      resizedCanvas.style.display = 'block';

      console.log('[Upload] Image displayed successfully');
    } catch (error) {
      console.error('[Upload] Error displaying image:', error);
      throw new Error('Erreur lors de l\'affichage de l\'image redimensionnée');
    }
  }

  function displayResizedImageFromBase64(base64Image) {
    return new Promise((resolve, reject) => {
      const img = new Image();

      img.onload = function () {
        try {
          resizedCtx.clearRect(0, 0, resizedCanvas.width, resizedCanvas.height);
          resizedCtx.imageSmoothingEnabled = false;
          resizedCtx.drawImage(img, 0, 0, 280, 280);

          document.getElementById('resized-image-placeholder').style.display = 'none';
          resizedCanvas.style.display = 'block';

          resolve();
        } catch (error) {
          reject(error);
        }
      };

      img.onerror = function () {
        reject(new Error('Impossible de charger l\'image base64'));
      };

      img.src = base64Image;
    });
  }

  // ===== PRÉDICTION AVEC PROTECTION =====
  function makePrediction(file) {
    console.log('[Upload] Starting prediction for uploaded file');

    const formData = new FormData();
    formData.append('file', file);

    // Ajouter le paramètre pour les filtres si disponible
    if (window.filterVisualization) {
      formData.append('show_filters', window.filterVisualization.getFilterParameter());
    }

    // Utiliser le timeout et l'abort controller
    const timeoutId = setTimeout(() => {
      uploadManager.cancelUpload();
      console.log('[Upload] Prediction timed out');
    }, 15000); // Timeout de 15 secondes pour les uploads

    fetch('/api/predict-and-save', {
      method: 'POST',
      body: formData,
      signal: currentUploadController.signal
    })
      .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
          throw new Error(`Erreur serveur ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(async data => {
        if (data.error) {
          throw new Error(data.error);
        }

        console.log('[Upload] Prediction completed successfully');

        // Si nous avons l'image redimensionnée en base64, l'afficher
        if (data.resized_image_base64) {
          try {
            await displayResizedImageFromBase64(data.resized_image_base64);
          } catch (error) {
            console.warn('[Upload] Could not display base64 image:', error);
          }
        }

        // Afficher les résultats de prédiction
        if (window.drawingApp) {
          window.drawingApp.displayPredictionResults(data);
        } else if (window.predictionUtils) {
          window.predictionUtils.displayPredictionResultsWithAnimation(data);
        }

        // Afficher les filtres CNN si disponibles
        if (data.feature_filters && data.feature_filters.length > 0 && window.filterVisualization) {
          console.log(`[Upload] Displaying ${data.feature_filters.length} CNN filters`);
          window.filterVisualization.displayFilters(data.feature_filters);
        } else if (window.filterVisualization) {
          // Masquer les filtres s'il n'y en a pas
          window.filterVisualization.hideFilters();
        }
      })
      .catch(error => {
        if (error.name === 'AbortError') {
          console.log('[Upload] Upload was cancelled');
        } else {
          console.error('[Upload] Prediction failed:', error);

          const errorMessage = error.message.includes('Erreur serveur')
            ? 'Erreur de connexion au serveur. Veuillez réessayer.'
            : `Erreur lors de la prédiction: ${error.message}`;

          if (window.predictionUtils) {
            window.predictionUtils.showError(errorMessage);
          } else {
            alert(errorMessage);
          }

          // Masquer les filtres en cas d'erreur
          if (window.filterVisualization) {
            window.filterVisualization.hideFilters();
          }
        }
      })
      .finally(() => {
        clearTimeout(timeoutId);
        uploadManager.finishUpload();

        // Masquer le loader
        if (window.drawingApp) {
          window.drawingApp.loader.style.display = 'none';
        }
        if (window.predictionUtils) {
          window.predictionUtils.hideLoadingState();
        }
      });
  }

  // ===== NETTOYAGE =====
  function clearUploadedImage() {
    resizedCanvas.style.display = 'none';
    document.getElementById('resized-image-placeholder').style.display = 'flex';
    fileInput.value = '';

    // Masquer aussi les filtres
    if (window.filterVisualization) {
      window.filterVisualization.hideFilters();
    }

    console.log('[Upload] Cleared uploaded image');
  }

  // ===== API EXPOSÉE =====
  window.uploadApp = {
    clearUploadedImage,
    displayResizedImage,
    displayResizedImageFromBase64,
    makePrediction,
    uploadManager: uploadManager, // Exposer le gestionnaire pour debug
    isUploadInProgress: () => isUploadInProgress,
    validateFile
  };

  // ===== INTÉGRATION AVEC LE SYSTÈME DE DESSIN =====
  // S'assurer que les uploads et les prédictions de dessin ne se chevauchent pas
  const originalClearFunction = window.drawingApp?.predictionManager?.clearQueue;
  if (originalClearFunction) {
    window.drawingApp.predictionManager.clearQueue = function () {
      // Arrêter aussi les uploads en cours
      if (isUploadInProgress) {
        console.log('[Integration] Cancelling upload due to drawing clear');
        uploadManager.cancelUpload();
      }
      originalClearFunction.call(this);
    };
  }
});
