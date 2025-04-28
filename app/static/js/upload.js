// Gestionnaire du drag & drop
document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    const loaderUpload = document.getElementById('loader-upload');
    
    // Gérer le clic sur la zone de dépôt
    dropzone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Gérer la sélection de fichier
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            // Afficher le loader
            loaderUpload.style.display = 'block';
            
            // Soumettre le formulaire
            uploadForm.submit();
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
            // Récupérer le fichier
            const file = e.dataTransfer.files[0];
            
            // Vérifier si c'est une image
            if (!file.type.match('image.*')) {
                alert('Veuillez déposer une image valide.');
                return;
            }
            
            // Assigner le fichier à l'input
            fileInput.files = e.dataTransfer.files;
            
            // Afficher le loader
            loaderUpload.style.display = 'block';
            
            // Soumettre le formulaire
            uploadForm.submit();
        }
    });
});
