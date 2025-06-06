// CNN Filter Visualization Handler
document.addEventListener('DOMContentLoaded', function () {

  const filtersSection = document.getElementById('filters-section');
  const filtersContainer = document.getElementById('filters-container');
  const filtersPlaceholder = document.getElementById('filters-placeholder');
  const filtersGrid = document.getElementById('filters-grid');
  const showFiltersCheckbox = document.getElementById('show-filters-checkbox');

  // État des filtres
  let filtersEnabled = true;
  let bestFiltersEnabled = true; // Activé par défaut
  let currentFilters = [];

  // Ajouter le toggle pour les meilleurs filtres
  function addBestFiltersToggle() {
    // Vérifier si le toggle existe déjà pour éviter les doublons
    if (document.getElementById('best-filters-checkbox')) {
      return; // Déjà ajouté
    }
    
    // Trouver le conteneur des outils de dessin où se trouve le toggle principal
    const drawingTools = document.querySelector('.drawing-tools');
    if (drawingTools) {
      const toggleHTML = `
        <label class="filter-toggle best-filters-toggle">
          <input type="checkbox" id="best-filters-checkbox" checked>
          <span class="toggle-text">🎯 Utiliser les meilleurs filtres (activité élevée)</span>
        </label>
        <p class="best-filters-description">Active la sélection des 3 filtres les plus actifs au lieu des 3 premiers</p>
      `;
      
      // Insérer après le toggle principal des filtres
      const mainToggle = drawingTools.querySelector('.filter-toggle');
      if (mainToggle) {
        mainToggle.insertAdjacentHTML('afterend', toggleHTML);
        
        // Ajouter l'event listener pour le nouveau toggle
        const bestFiltersCheckbox = document.getElementById('best-filters-checkbox');
        if (bestFiltersCheckbox) {
          // Synchroniser l'état avec le checkbox (activé par défaut)
          bestFiltersEnabled = bestFiltersCheckbox.checked;
          
          bestFiltersCheckbox.addEventListener('change', function () {
            bestFiltersEnabled = this.checked;
            console.log(`[FilterViz] Best filters ${bestFiltersEnabled ? 'enabled' : 'disabled'}`);
            
            // Afficher un message informatif et l'indicateur visuel
            if (bestFiltersEnabled) {
              showInfoMessage('🎯 Mode meilleurs filtres activé - Les prochaines prédictions utiliseront les filtres les plus actifs');
              updateBestFiltersIndicator();
            }
          });
          
          // Afficher l'indicateur au chargement si activé par défaut
          if (bestFiltersEnabled) {
            setTimeout(() => updateBestFiltersIndicator(), 1000);
          }
        }
      }
    }
  }

  // Fonction pour afficher un message informatif
  function showInfoMessage(message) {
    const infoDiv = document.createElement('div');
    infoDiv.className = 'filter-info-message';
    infoDiv.innerHTML = `
      <div style="
        background: #d1ecf1;
        color: #0c5460;
        padding: 10px 15px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 4px solid #bee5eb;
        font-size: 14px;
        animation: fadeInOut 4s ease-in-out;
      ">
        ${message}
      </div>
    `;
    
    // Ajouter les styles d'animation si pas déjà présents
    if (!document.getElementById('filter-info-styles')) {
      const style = document.createElement('style');
      style.id = 'filter-info-styles';
      style.textContent = `
        @keyframes fadeInOut {
          0% { opacity: 0; transform: translateY(-10px); }
          15% { opacity: 1; transform: translateY(0); }
          85% { opacity: 1; transform: translateY(0); }
          100% { opacity: 0; transform: translateY(-10px); }
        }
      `;
      document.head.appendChild(style);
    }
    
    // Insérer le message
    const controlsDiv = filtersSection.querySelector('.filter-controls');
    if (controlsDiv) {
      controlsDiv.insertAdjacentElement('afterend', infoDiv);
      
      // Supprimer automatiquement après l'animation
      setTimeout(() => {
        if (infoDiv.parentNode) {
          infoDiv.remove();
        }
      }, 4000);
    }
  }

  // Gestionnaire pour le toggle des filtres
  if (showFiltersCheckbox) {
    showFiltersCheckbox.addEventListener('change', function () {
      filtersEnabled = this.checked;
      updateFiltersVisibility();

      console.log(`[FilterViz] Filters ${filtersEnabled ? 'enabled' : 'disabled'}`);
      
      // Ajouter le toggle des meilleurs filtres quand les filtres sont activés
      if (filtersEnabled) {
        addBestFiltersToggle();
      }
    });

    // Initialiser l'état
    filtersEnabled = showFiltersCheckbox.checked;
    updateFiltersVisibility();
    
    // Si les filtres sont déjà activés au chargement, ajouter le toggle
    if (filtersEnabled) {
      addBestFiltersToggle();
    }
  }

  // Fonction pour mettre à jour la visibilité de la section des filtres
  function updateFiltersVisibility() {
    if (filtersEnabled && currentFilters.length > 0) {
      showFiltersSection();
    } else if (!filtersEnabled) {
      hideFiltersSection();
    }
  }

  // Afficher la section des filtres
  function showFiltersSection() {
    if (filtersSection) {
      filtersSection.style.display = 'block';
      // Animation d'entrée
      filtersSection.style.opacity = '0';
      filtersSection.style.transform = 'translateY(20px)';
      filtersSection.style.transition = 'all 0.5s ease-out';

      setTimeout(() => {
        filtersSection.style.opacity = '1';
        filtersSection.style.transform = 'translateY(0)';
      }, 50);
    }
  }

  // Masquer la section des filtres
  function hideFiltersSection() {
    if (filtersSection) {
      filtersSection.style.transition = 'all 0.3s ease-in';
      filtersSection.style.opacity = '0';
      filtersSection.style.transform = 'translateY(-20px)';

      setTimeout(() => {
        filtersSection.style.display = 'none';
      }, 300);
    }
  }

  // Fonction pour afficher les filtres CNN
  function displayFilters(filters) {
    console.log(`[FilterViz] Displaying ${filters.length} filters`);
    console.log('[FilterViz] Filters received:', filters);

    currentFilters = filters;

    if (!filtersEnabled) {
      console.log('[FilterViz] Filters disabled, not displaying');
      return;
    }

    if (!filtersGrid || !filtersPlaceholder) {
      console.error('[FilterViz] Required DOM elements not found');
      return;
    }

    // Masquer le placeholder
    filtersPlaceholder.style.display = 'none';

    // Vider la grille existante
    filtersGrid.innerHTML = '';

    // Si aucun filtre, afficher un message
    if (filters.length === 0) {
      showNoFiltersMessage();
      return;
    }

    // Grouper les filtres par bloc de convolution en utilisant le champ layer_display
    const filtersByBlock = {};
    filters.forEach(filter => {
      const blockName = filter.layer_display || '1er Bloc de Convolution';
      if (!filtersByBlock[blockName]) {
        filtersByBlock[blockName] = [];
      }
      filtersByBlock[blockName].push(filter);
    });
    
    console.log('[FilterViz] Filters grouped by block:', filtersByBlock);

    // Afficher la grille immédiatement
    filtersGrid.style.display = 'block';
    showFiltersSection();

    // Créer les sections pour chaque bloc avec grille 3x3
    let filterIndex = 0;
    Object.entries(filtersByBlock).forEach(([blockName, blockFilters]) => {
      console.log(`[FilterViz] Creating block: ${blockName} with ${blockFilters.length} filters`);
      
      // Créer un container pour ce bloc
      const blockContainer = document.createElement('div');
      blockContainer.className = 'filter-block-container';
      blockContainer.style.cssText = `
        margin: 30px 0;
        padding: 20px;
        background: rgba(248, 249, 250, 0.8);
        border-radius: 12px;
        border-left: 4px solid #007bff;
      `;
      
      // Créer le titre du bloc
      const blockTitle = document.createElement('h3');
      blockTitle.className = 'filter-block-title';
      blockTitle.style.cssText = `
        text-align: center;
        color: #495057;
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 20px 0;
        padding: 10px;
        background: rgba(0,123,255,0.1);
        border-radius: 8px;
      `;
      blockTitle.textContent = blockName;
      blockContainer.appendChild(blockTitle);
      
      // Créer une grille 3x1 pour les filtres de ce bloc
      const blockGrid = document.createElement('div');
      blockGrid.className = 'filter-block-grid';
      blockGrid.style.cssText = `
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        justify-items: center;
      `;
      
      // Ajouter les filtres de ce bloc
      blockFilters.forEach((filter, filterInBlockIndex) => {
        console.log(`[FilterViz] Adding filter ${filterInBlockIndex} to block ${blockName}:`, filter.title);
        setTimeout(() => {
          const filterElement = createFilterElement(filter, filterIndex);
          blockGrid.appendChild(filterElement);
        }, filterIndex * 50);
        filterIndex++;
      });
      
      blockContainer.appendChild(blockGrid);
      filtersGrid.appendChild(blockContainer);
      
      console.log(`[FilterViz] Created block container for ${blockName} with ${blockFilters.length} filters`);
    });
  }

  // Créer un élément de filtre
  function createFilterElement(filter, index) {
    const filterItem = document.createElement('div');
    filterItem.className = 'filter-item';
    filterItem.style.animationDelay = `${index * 0.05}s`; // Animation plus rapide

    // Image du filtre
    const filterImage = document.createElement('img');
    filterImage.className = 'filter-image';
    filterImage.src = filter.image;
    filterImage.alt = `${filter.title}`;
    filterImage.loading = 'eager'; // Charger immédiatement

    // Informations du filtre (activation en gras comme titre principal)
    const filterInfo = document.createElement('div');
    filterInfo.className = 'filter-info';
    filterInfo.innerHTML = `
      <div class="activation-title">Activation: ${filter.variance ? filter.variance.toFixed(3) : 'N/A'}</div>
    `;

    // Ajouter les éléments (pas de titre redondant)
    filterItem.appendChild(filterImage);
    filterItem.appendChild(filterInfo);

    // Ajouter un effet de hover avec info-bulle
    filterItem.addEventListener('mouseenter', function () {
      showFilterTooltip(filterItem, filter);
    });

    filterItem.addEventListener('mouseleave', function () {
      hideFilterTooltip();
    });

    // Gestion d'erreur pour l'image avec meilleur fallback
    filterImage.addEventListener('error', function () {
      console.warn(`[FilterViz] Failed to load filter image: ${filter.title}`);
      filterImage.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDEyMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiBmaWxsPSIjZjhmOWZhIi8+CjxwYXRoIGQ9Ik02MCA0MEw4MCA4MEg0MEw2MCA0MFoiIGZpbGw9IiNkZWUyZTYiLz4KPHRleHQgeD0iNjAiIHk9IjEwMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzZjNzU3ZCIgZm9udC1zaXplPSIxMiI+RXJyZXVyPC90ZXh0Pgo8L3N2Zz4=';
    });

    // Préparer pour l'animation d'entrée
    filterItem.style.opacity = '0';
    filterItem.style.transform = 'translateY(20px)';
    
    // Déclencher l'animation après ajout au DOM (sera fait par l'appelant)
    setTimeout(() => {
      filterItem.style.transition = 'all 0.3s ease-out';
      filterItem.style.opacity = '1';
      filterItem.style.transform = 'translateY(0)';
    }, 50);

    return filterItem;
  }

  // Afficher un message quand il n'y a pas de filtres
  function showNoFiltersMessage() {
    filtersGrid.innerHTML = `
          <div class="no-filters-message" style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #6c757d;">
              <div style="font-size: 36px; margin-bottom: 15px;">🔧</div>
              <h4>Aucun filtre disponible</h4>
              <p>Les filtres CNN ne sont pas disponibles pour cette prédiction.</p>
          </div>
      `;
    filtersGrid.style.display = 'block';
    showFiltersSection();
  }

  // Info-bulle pour les filtres
  let currentTooltip = null;

  function showFilterTooltip(element, filter) {
    // Supprimer l'ancienne info-bulle
    hideFilterTooltip();

    const tooltip = document.createElement('div');
    tooltip.className = 'filter-tooltip';
    
    const layerDisplay = filter.layer_display || filter.layer;
    
    tooltip.innerHTML = `
          <strong>${filter.title}</strong><br>
          ${layerDisplay}<br>
          Activation: ${filter.variance ? filter.variance.toFixed(4) : 'N/A'}<br>
          <em>Ce filtre détecte des motifs spécifiques dans l'image</em>
      `;

    // Styles de l'info-bulle
    tooltip.style.cssText = `
          position: absolute;
          background: rgba(0,0,0,0.9);
          color: white;
          padding: 10px;
          border-radius: 6px;
          font-size: 12px;
          line-height: 1.4;
          z-index: 1000;
          pointer-events: none;
          box-shadow: 0 4px 15px rgba(0,0,0,0.3);
          max-width: 200px;
      `;

    document.body.appendChild(tooltip);
    currentTooltip = tooltip;

    // Positionner l'info-bulle
    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;

    // Ajuster si hors écran
    if (parseInt(tooltip.style.top) < 0) {
      tooltip.style.top = `${rect.bottom + 10}px`;
    }
  }

  function hideFilterTooltip() {
    if (currentTooltip) {
      currentTooltip.remove();
      currentTooltip = null;
    }
  }

  // Masquer les filtres
  function hideFilters() {
    console.log('[FilterViz] Hiding filters');

    currentFilters = [];

    if (filtersGrid) {
      filtersGrid.style.display = 'none';
      filtersGrid.innerHTML = '';
    }

    if (filtersPlaceholder) {
      filtersPlaceholder.style.display = 'flex';
    }

    hideFiltersSection();
    hideFilterTooltip();
  }

  // Vérifier si les filtres sont activés
  function areFiltersEnabled() {
    return filtersEnabled;
  }

  // Obtenir les paramètres à ajouter aux requêtes
  function getFilterParameter() {
    return filtersEnabled ? 'true' : 'false';
  }

  // Obtenir les paramètres complets pour les requêtes
  function getFilterParameters() {
    return {
      show_filters: filtersEnabled ? 'true' : 'false',
      best_filters: bestFiltersEnabled ? 'true' : 'false'
    };
  }

  // Exposer l'API pour les autres scripts
  window.filterVisualization = {
    displayFilters,
    hideFilters,
    areFiltersEnabled,
    getFilterParameter,
    getFilterParameters,
    showFiltersSection,
    hideFiltersSection,
    updateBestFiltersIndicator,
    // Getters pour l'état
    isBestFiltersEnabled: () => bestFiltersEnabled,
    isFiltersEnabled: () => filtersEnabled
  };

  // Intégration avec le système de nettoyage
  document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'clear-canvas') {
      console.log('[FilterViz] Clear button clicked, hiding filters');
      hideFilters();
    }
  });

  // Ajouter un indicateur visuel pour le mode meilleurs filtres
  function updateBestFiltersIndicator() {
    const existingIndicator = document.querySelector('.best-filters-indicator');
    if (existingIndicator) {
      existingIndicator.remove();
    }

    if (bestFiltersEnabled) {
      const indicator = document.createElement('div');
      indicator.className = 'best-filters-indicator';
      indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        animation: pulseGreen 2s infinite;
      `;
      indicator.innerHTML = '🎯 Mode meilleurs filtres actif';

      // Ajouter l'animation si pas déjà présente
      if (!document.getElementById('best-filters-animation')) {
        const style = document.createElement('style');
        style.id = 'best-filters-animation';
        style.textContent = `
          @keyframes pulseGreen {
            0% { transform: scale(1); opacity: 0.9; }
            50% { transform: scale(1.05); opacity: 1; }
            100% { transform: scale(1); opacity: 0.9; }
          }
        `;
        document.head.appendChild(style);
      }

      document.body.appendChild(indicator);

      // Supprimer l'indicateur après 5 secondes
      setTimeout(() => {
        if (indicator.parentNode) {
          indicator.style.transition = 'all 0.3s ease-out';
          indicator.style.opacity = '0';
          indicator.style.transform = 'translateX(100px)';
          setTimeout(() => indicator.remove(), 300);
        }
      }, 5000);
    }
  }

  console.log('[FilterViz] Filter visualization system initialized with best filters support');
});
