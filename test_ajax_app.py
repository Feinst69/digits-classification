#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement de l'application AJAX
"""
import os
import sys
import time
import requests
import base64
from PIL import Image, ImageDraw
import io

# Configuration
BASE_URL = "http://localhost:5000"
TEST_IMAGE_SIZE = (280, 280)

def create_test_digit_image(digit=5, size=(280, 280)):
    """Créer une image de test avec un chiffre"""
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Dessiner un chiffre simple
    font_size = min(size) // 2
    
    if digit == 5:
        # Dessiner le chiffre 5
        draw.rectangle([size[0]//4, size[1]//4, size[0]*3//4, size[1]//2], outline='black', width=10)
        draw.rectangle([size[0]//4, size[1]//2, size[0]*3//4, size[1]*3//4], outline='black', width=10)
        draw.line([size[0]//4, size[1]//4, size[0]//4, size[1]//2], fill='black', width=10)
        draw.line([size[0]*3//4, size[1]//2, size[0]*3//4, size[1]*3//4], fill='black', width=10)
    
    return img

def test_api_predict():
    """Tester l'endpoint API /api/predict"""
    print("🧪 Test de l'API /api/predict...")
    
    # Créer une image de test
    test_img = create_test_digit_image(5)
    
    # Convertir en bytes
    img_buffer = io.BytesIO()
    test_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Test avec un fichier
    files = {'file': ('test_digit.png', img_buffer, 'image/png')}
    
    try:
        response = requests.post(f"{BASE_URL}/api/predict", files=files, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API /api/predict fonctionne")
            print(f"   Prédiction: {data.get('predicted_digit', 'N/A')}")
            print(f"   Confiance: {data.get('confidence', 'N/A'):.2f}%")
            return True
        else:
            print(f"❌ Erreur API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test API: {e}")
        return False

def test_api_predict_and_save():
    """Tester l'endpoint API /api/predict-and-save"""
    print("\n🧪 Test de l'API /api/predict-and-save...")
    
    # Créer une image de test
    test_img = create_test_digit_image(5)
    
    # Convertir en bytes
    img_buffer = io.BytesIO()
    test_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Test avec un fichier
    files = {'file': ('test_digit.png', img_buffer, 'image/png')}
    
    try:
        response = requests.post(f"{BASE_URL}/api/predict-and-save", files=files, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API /api/predict-and-save fonctionne")
            print(f"   Prédiction: {data.get('predicted_digit', 'N/A')}")
            print(f"   Confiance: {data.get('confidence', 'N/A'):.2f}%")
            
            if 'resized_image_base64' in data:
                print(f"   ✅ Image redimensionnée incluse")
            else:
                print(f"   ⚠️ Image redimensionnée manquante")
                
            if data.get('saved_to_history', False):
                print(f"   ✅ Sauvegardé dans l'historique")
            else:
                print(f"   ⚠️ Pas sauvegardé dans l'historique")
            
            return True
        else:
            print(f"❌ Erreur API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test API: {e}")
        return False

def test_canvas_data():
    """Tester avec des données canvas (base64)"""
    print("\n🧪 Test avec données canvas (base64)...")
    
    # Créer une image de test
    test_img = create_test_digit_image(5)
    
    # Convertir en base64
    img_buffer = io.BytesIO()
    test_img.save(img_buffer, format='PNG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    canvas_data = f"data:image/png;base64,{img_base64}"
    
    # Test avec données canvas
    data = {'image_data': canvas_data}
    
    try:
        response = requests.post(f"{BASE_URL}/api/predict-and-save", data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test canvas data fonctionne")
            print(f"   Prédiction: {result.get('predicted_digit', 'N/A')}")
            print(f"   Confiance: {result.get('confidence', 'N/A'):.2f}%")
            return True
        else:
            print(f"❌ Erreur canvas data: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test canvas: {e}")
        return False

def test_main_page():
    """Tester que la page principale se charge"""
    print("\n🧪 Test de la page principale...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            # Vérifier que les éléments clés sont présents
            checks = [
                ('canvas', 'id="canvas"' in content),
                ('resized-canvas', 'id="resized-canvas"' in content),
                ('prediction-results', 'prediction-results' in content),
                ('auto-predict-indicator', 'auto-predict-indicator' in content),
                ('draw-ajax.js', 'draw-ajax.js' in content),
                ('upload-ajax.js', 'upload-ajax.js' in content),
                ('prediction-display.js', 'prediction-display.js' in content)
            ]
            
            all_good = True
            for check_name, check_result in checks:
                if check_result:
                    print(f"   ✅ {check_name} présent")
                else:
                    print(f"   ❌ {check_name} manquant")
                    all_good = False
            
            return all_good
        else:
            print(f"❌ Erreur page principale: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test page principale: {e}")
        return False

def test_history_page():
    """Tester que la page d'historique se charge et affiche les prédictions"""
    print("\n🧪 Test de la page d'historique...")
    
    try:
        response = requests.get(f"{BASE_URL}/history", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            # Vérifier que les éléments clés sont présents
            checks = [
                ('history-section', 'history-section' in content or 'history' in content.lower()),
                ('predictions', 'prediction' in content.lower()),
                ('base-template', 'html' in content.lower())
            ]
            
            all_good = True
            for check_name, check_result in checks:
                if check_result:
                    print(f"   ✅ {check_name} présent")
                else:
                    print(f"   ❌ {check_name} manquant")
                    all_good = False
            
            return all_good
        else:
            print(f"❌ Erreur page historique: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test page historique: {e}")
        return False

def check_server_running():
    """Vérifier si le serveur Flask est en marche"""
    print("🔍 Vérification du serveur Flask...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=3)
        if response.status_code == 200:
            print("✅ Serveur Flask en marche")
            return True
        else:
            print(f"❌ Serveur répond avec le code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Serveur Flask non accessible")
        print("   💡 Assurez-vous de lancer: python app/app.py")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'application AJAX Digits Classification")
    print("=" * 60)
    
    # Vérifier si le serveur est en marche
    if not check_server_running():
        return False
    
    # Exécuter les tests
    tests = [
        test_main_page,
        test_api_predict,
        test_api_predict_and_save,
        test_canvas_data,
        test_history_page
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Tous les tests passent! ({passed}/{total})")
        print("\n✨ L'application AJAX est prête à être utilisée!")
        print(f"🌐 Accédez à: {BASE_URL}")
        print("\n📚 FONCTIONNALITÉS TESTÉES:")
        print("   ✅ Interface principale avec prédiction automatique")
        print("   ✅ API de prédiction simple")
        print("   ✅ API de prédiction avec sauvegarde historique")
        print("   ✅ Support des données canvas (dessins)")
        print("   ✅ Page d'historique des prédictions")
    else:
        print(f"⚠️ {passed}/{total} tests passent")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
