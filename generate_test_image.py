"""
Script pour générer une image de test en forme de chiffre
pour tester l'application de reconnaissance de chiffres
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

def generate_digit_image(digit, size=(280, 280), stroke_width=30, output_dir='images'):
    """
    Génère une image d'un chiffre manuscrit simulé
    
    Args:
        digit (int): Le chiffre à dessiner (0-9)
        size (tuple): Taille de l'image (largeur, hauteur)
        stroke_width (int): Épaisseur du trait
        output_dir (str): Répertoire de sortie
    
    Returns:
        str: Chemin vers l'image générée
    """
    # Créer une image blanche
    image = Image.new('L', size, color=255)
    draw = ImageDraw.Draw(image)
    
    # Dessiner le chiffre avec un peu de "tremblement" pour simuler l'écriture manuscrite
    digit_str = str(digit)
    
    # Charger une police pour dessiner le chiffre
    try:
        # Essayer de charger une police
        font = ImageFont.truetype("arial.ttf", size=size[0]//2)
    except IOError:
        # Si la police n'est pas disponible, utiliser la police par défaut
        font = ImageFont.load_default()
    
    # Calculer la position pour centrer le chiffre
    text_width, text_height = draw.textsize(digit_str, font=font)
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    # Ajouter un léger décalage aléatoire pour simuler l'écriture manuscrite
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    position = (position[0] + offset_x, position[1] + offset_y)
    
    # Dessiner le chiffre
    draw.text(position, digit_str, fill=0, font=font)
    
    # Ajouter un peu de bruit pour simuler une capture réelle
    img_array = np.array(image)
    noise = np.random.normal(0, 5, img_array.shape)
    img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    
    # Reconvertir en image
    image = Image.fromarray(img_array)
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Sauvegarder l'image
    output_path = os.path.join(output_dir, f"test_digit_{digit}.png")
    image.save(output_path)
    
    print(f"Image générée: {output_path}")
    return output_path

def main():
    """Génère des images pour tous les chiffres (0-9)"""
    for digit in range(10):
        generate_digit_image(digit)

if __name__ == "__main__":
    main()
