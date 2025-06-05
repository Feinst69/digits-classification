// CNN Filter Visualization Handler
document.addEventListener('DOMContentLoaded', function () {

  const filtersSection = document.getElementById('filters-section');
  const filtersContainer = document.getElementById('filters-container');
  const filtersPlaceholder = document.getElementById('filters-placeholder');
  const filtersGrid = document.getElementById('filters-grid');
  const showFiltersCheckbox = document.getElementById('show-filters-checkbox');

  // État des filtres
  let filtersEnabled = true;
  let currentFilters = [];

  // Gestionnaire pour le toggle des filtres
  if (showFiltersCheckbox) {
    showFiltersCheckbox.addEventListener('change', function () {
      filtersEnabled = this.checked;
      updateFiltersVisibility();

      console.log(`[FilterViz] Filters ${filtersEnabled ? 'enabled' : 'disabled'}`);
    });

    // Initialiser l'état
    filtersEnabled = showFiltersCheckbox.checked;
    updateFiltersVisibility();
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

    // Afficher la grille immédiatement
    filtersGrid.style.display = 'grid';
    showFiltersSection();

    // Créer les éléments de filtre avec animation décalée
    filters.forEach((filter, index) => {
      setTimeout(() => {
        createFilterElement(filter, index);
      }, index * 50); // Délai réduit à 50ms entre chaque filtre
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
    filterImage.alt = `Filtre ${filter.title}`;
    filterImage.loading = 'eager'; // Charger immédiatement

    // Titre du filtre
    const filterTitle = document.createElement('div');
    filterTitle.className = 'filter-title';
    filterTitle.textContent = filter.title;

    // Informations du filtre
    const filterInfo = document.createElement('div');
    filterInfo.className = 'filter-info';

    // Extraire le nom de la couche pour l'affichage
    const layerDisplay = filter.layer.includes('conv_1') ? 'Couche 1' :
      filter.layer.includes('conv_2') ? 'Couche 2' :
        filter.layer.includes('conv_3') ? 'Couche 3' :
        filter.layer.includes('conv_4') ? 'Couche 4' : 'Couche ?';

    filterInfo.innerHTML = `
          <div>${layerDisplay}</div>
          <div>Activation: ${filter.variance ? filter.variance.toFixed(3) : 'N/A'}</div>
      `;

    // Ajouter les éléments
    filterItem.appendChild(filterImage);
    filterItem.appendChild(filterTitle);
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

    // Ajouter avec une animation d'entrée
    filterItem.style.opacity = '0';
    filterItem.style.transform = 'translateY(20px)';
    filtersGrid.appendChild(filterItem);

    // Déclencher l'animation après ajout au DOM
    requestAnimationFrame(() => {
      filterItem.style.transition = 'all 0.3s ease-out';
      filterItem.style.opacity = '1';
      filterItem.style.transform = 'translateY(0)';
    });
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
    tooltip.innerHTML = `
          <strong>${filter.title}</strong><br>
          Couche: ${filter.layer}<br>
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

  // Obtenir le paramètre à ajouter aux requêtes
  function getFilterParameter() {
    return filtersEnabled ? 'true' : 'false';
  }

  // Exposer l'API pour les autres scripts
  window.filterVisualization = {
    displayFilters,
    hideFilters,
    areFiltersEnabled,
    getFilterParameter,
    showFiltersSection,
    hideFiltersSection
  };

  // Intégration avec le système de nettoyage
  document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'clear-canvas') {
      console.log('[FilterViz] Clear button clicked, hiding filters');
      hideFilters();
    }
  });

  console.log('[FilterViz] Filter visualization system initialized');
});
