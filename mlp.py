from tensorflow.keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Flatten
from keras.optimizers import Adam
from keras.utils import to_categorical
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from itertools import product
import time

# Classe modifiée pour MNIST
class KerasModel:
    def __init__(self, input_dim, layers, activations, optimizer='adam', learning_rate=0.01):
        """
        Initialize the CustomModel class.

        Parameters:
        - input_dim: int, the number of input features.
        - layers: list of int, the number of neurons in each layer.
        - activations: list of str, the activation function for each layer.
        - optimizer: str, the optimizer to use (default is 'adam').
        - learning_rate: float, the learning rate for the optimizer (default is 0.001).
        """
        self.input_dim = input_dim
        self.layers = layers
        self.activations = activations
        self.optimizer = optimizer
        self.learning_rate = learning_rate
        self.model = self.build_model()

    def build_model(self):
        """
        Build the Sequential model based on the specified layers and activations.
        """
        model = Sequential()
        
        # Ajouter Flatten pour convertir les images 28x28 en vecteur 1D
        model.add(Flatten(input_shape=(28, 28)))
        
        # Add the first layer
        model.add(Dense(self.layers[0], activation=self.activations[0]))
        
        # Add the remaining layers
        for neurons, activation in zip(self.layers[1:-1], self.activations[1:-1]):
            model.add(Dense(neurons, activation=activation))
        
        # Dernière couche pour classification (10 classes pour MNIST)
        model.add(Dense(10, activation='softmax'))
        
        # Compile the model
        if self.optimizer == 'adam':
            optimizer = Adam(learning_rate=self.learning_rate)
        else:
            raise ValueError("Currently only 'adam' optimizer is supported.")
        
        # Utiliser categorical_crossentropy pour classification multi-classe
        model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])
        
        return model

    def train(self, X_train, y_train, epochs=10, batch_size=32, validation_data=None, verbose=0):
        """
        Train the model on the provided training data.
        """
        self.history = self.model.fit(
            X_train, y_train, 
            epochs=epochs, 
            batch_size=batch_size,
            validation_data=validation_data,
            verbose=verbose
        )

    def evaluate(self, X_test, y_test, verbose=0):
        """
        Evaluate the model on the provided test data.
        """
        return self.model.evaluate(X_test, y_test, verbose=verbose)

    def predict(self, X):
        """
        Make predictions on the provided data.
        """
        predictions = self.model.predict(X)
        return np.argmax(predictions, axis=1)

    def get_history(self):
        """
        Return the history of the model.
        """
        return self.history.history

# Fonction de grid search
def grid_search_mnist(X_train, y_train, X_test, y_test, param_grid, max_time_per_config=300):
    """
    Effectue un grid search pour trouver la meilleure architecture.
    
    Parameters:
    - X_train, y_train: données d'entraînement
    - X_test, y_test: données de test
    - param_grid: dictionnaire contenant les paramètres à tester
    - max_time_per_config: temps maximum par configuration en secondes
    """
    
    results = []
    
    # Générer toutes les combinaisons de paramètres
    param_combinations = list(product(
        param_grid['layers'],
        param_grid['learning_rates'],
        param_grid['batch_sizes'],
        param_grid['epochs']
    ))
    
    print(f"Nombre total de configurations à tester: {len(param_combinations)}")
    
    for i, (layers, lr, batch_size, epochs) in enumerate(param_combinations):
        print(f"\n--- Configuration {i+1}/{len(param_combinations)} ---")
        print(f"Couches: {layers}")
        print(f"Learning rate: {lr}")
        print(f"Batch size: {batch_size}")
        print(f"Epochs: {epochs}")
        
        start_time = time.time()
        
        try:
            # Créer les activations (relu pour couches cachées, softmax pour sortie)
            activations = ['relu'] * len(layers)
            
            # Créer le modèle
            model = KerasModel(
                input_dim=784,  # 28*28 pour MNIST
                layers=layers,
                activations=activations,
                learning_rate=lr
            )
            
            # Entraîner le modèle
            model.train(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # Évaluer le modèle
            test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
            
            # Récupérer l'historique
            history = model.get_history()
            final_train_acc = history['accuracy'][-1]
            final_val_acc = history['val_accuracy'][-1]
            
            elapsed_time = time.time() - start_time
            
            # Stocker les résultats
            result = {
                'layers': layers,
                'num_layers': len(layers),
                'total_neurons': sum(layers),
                'learning_rate': lr,
                'batch_size': batch_size,
                'epochs': epochs,
                'test_accuracy': test_accuracy,
                'test_loss': test_loss,
                'train_accuracy': final_train_acc,
                'val_accuracy': final_val_acc,
                'training_time': elapsed_time
            }
            
            results.append(result)
            
            print(f"Précision test: {test_accuracy:.4f}")
            print(f"Temps d'entraînement: {elapsed_time:.2f}s")
            
            # Vérifier le temps limite
            if elapsed_time > max_time_per_config:
                print(f"Configuration trop lente (>{max_time_per_config}s), passage à la suivante")
                
        except Exception as e:
            print(f"Erreur avec cette configuration: {e}")
            continue
    
    return results

# Fonction pour analyser les résultats
def analyze_results(results):
    """
    Analyse les résultats du grid search.
    """
    if not results:
        print("Aucun résultat à analyser!")
        return
    
    df = pd.DataFrame(results)
    
    print("\n" + "="*50)
    print("ANALYSE DES RÉSULTATS")
    print("="*50)
    
    # Meilleure configuration
    best_idx = df['test_accuracy'].idxmax()
    best_config = df.loc[best_idx]
    
    print(f"\n🏆 MEILLEURE CONFIGURATION:")
    print(f"Couches: {best_config['layers']}")
    print(f"Learning rate: {best_config['learning_rate']}")
    print(f"Batch size: {best_config['batch_size']}")
    print(f"Epochs: {best_config['epochs']}")
    print(f"Précision test: {best_config['test_accuracy']:.4f}")
    print(f"Temps d'entraînement: {best_config['training_time']:.2f}s")
    
    # Top 5 des configurations
    print(f"\n📊 TOP 5 DES CONFIGURATIONS:")
    top_5 = df.nlargest(5, 'test_accuracy')[['layers', 'learning_rate', 'batch_size', 'epochs', 'test_accuracy', 'training_time']]
    print(top_5.to_string(index=False))
    
    # Analyse par nombre de couches
    print(f"\n🔍 ANALYSE PAR NOMBRE DE COUCHES:")
    layer_analysis = df.groupby('num_layers').agg({
        'test_accuracy': ['mean', 'max', 'std'],
        'training_time': 'mean'
    }).round(4)
    print(layer_analysis)
    
    # Analyse par learning rate
    print(f"\n🔍 ANALYSE PAR LEARNING RATE:")
    lr_analysis = df.groupby('learning_rate').agg({
        'test_accuracy': ['mean', 'max', 'std'],
        'training_time': 'mean'
    }).round(4)
    print(lr_analysis)
    
    return df

# Fonction principale
def main():
    """
    Fonction principale pour exécuter le grid search sur MNIST.
    """
    
    # Charger les données MNIST
    print("Chargement des données MNIST...")
    (X_train, y_train), (X_test, y_test) = mnist.load_data()
    
    # Normaliser les données
    X_train = X_train / 255.0
    X_test = X_test / 255.0
    
    # Convertir les labels en format categorical
    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)
    
    print(f"Forme des données d'entraînement: {X_train.shape}")
    print(f"Forme des données de test: {X_test.shape}")
    
    # Utiliser un sous-ensemble pour accélérer les tests (optionnel)
    # X_train = X_train[:5000]
    # y_train = y_train[:5000]
    # X_test = X_test[:1000]
    # y_test = y_test[:1000]
    
    # Définir la grille de paramètres
    param_grid = {
        'layers': [
            [128],           # 1 couche cachée
            [256],           # 1 couche cachée plus large
            [128, 64],       # 2 couches cachées
            [256, 128],      # 2 couches cachées plus larges
            [512, 256],      # 2 couches cachées très larges
            [128, 64, 32],   # 3 couches cachées
            [256, 128, 64],  # 3 couches cachées plus larges
        ],
        'learning_rates': [0.001, 0.01, 0.1],
        'batch_sizes': [32, 64, 128],
        'epochs': [10, 20]
    }
    
    print("\nParamètres à tester:")
    for key, values in param_grid.items():
        print(f"- {key}: {values}")
    
    # Exécuter le grid search
    print("\nDémarrage du grid search...")
    results = grid_search_mnist(X_train, y_train, X_test, y_test, param_grid)
    
    # Analyser les résultats
    if results:
        df_results = analyze_results(results)
        
        # Sauvegarder les résultats
        df_results.to_csv('mnist_grid_search_results.csv', index=False)
        print(f"\nRésultats sauvegardés dans 'mnist_grid_search_results.csv'")
        
        return df_results
    else:
        print("Aucun résultat obtenu!")
        return None

# Exécuter le grid search
if __name__ == "__main__":
    results_df = main()