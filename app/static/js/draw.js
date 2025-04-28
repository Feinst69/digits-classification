// Gestionnaire du canvas de dessin
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const clearBtn = document.getElementById('clear-canvas');
    const predictBtn = document.getElementById('predict-drawing');
    const form = document.getElementById('drawing-form');
    const imageDataInput = document.getElementById('image-data');
    const loader = document.getElementById('loader');
    
    // Variables pour le dessin
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    
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
    }
    
    // Gestionnaires d'événements pour le dessin
    canvas.addEventListener('mousedown', (e) => {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        [lastX, lastY] = [e.clientX - rect.left, e.clientY - rect.top];
    });
    
    canvas.addEventListener('touchstart', (e) => {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        [lastX, lastY] = [e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top];
    });
    
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('touchmove', draw);
    
    canvas.addEventListener('mouseup', () => isDrawing = false);
    canvas.addEventListener('touchend', () => isDrawing = false);
    canvas.addEventListener('mouseout', () => isDrawing = false);
    
    // Effacer le canvas
    clearBtn.addEventListener('click', function() {
        initCanvas();
    });
    
    // Soumettre le dessin pour prédiction
    predictBtn.addEventListener('click', function() {
        // Convertir le canvas en base64
        const imageData = canvas.toDataURL('image/png');
        
        // Vérifier si le canvas est vide (tout blanc)
        if (isCanvasBlank()) {
            alert("Veuillez dessiner un chiffre avant de faire une prédiction.");
            return;
        }
        
        // Mettre les données d'image dans le formulaire
        imageDataInput.value = imageData;
        
        // Afficher le loader
        loader.style.display = 'block';
        
        // Soumettre le formulaire
        form.submit();
    });
    
    // Fonction pour vérifier si le canvas est vide
    function isCanvasBlank() {
        const pixelBuffer = new Uint32Array(
            ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
        );
        
        // Vérifier si tous les pixels sont blancs
        // Note: nous vérifions seulement une partie des pixels pour la performance
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
});
