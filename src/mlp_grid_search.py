"""
MLP Grid Search - Part 2/4 (Complete)
======================================

Contains:
1. Grid search functionality for MLP hyperparameters  
2. Parameter grid definitions
3. Results analysis functions

Author: Created for MNIST classification project
"""

import numpy as np
import tensorflow as tf
from sklearn.model_selection import ParameterGrid
import time
import pandas as pd
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Import from our basic models module
from mlp_basic_models import create_advanced_mlp, compile_advanced_mlp

def get_parameter_grids():
    """Get predefined parameter grids for different search intensities"""
    grids = {
        'quick': {
            'hidden_layers': [[128, 64], [256, 128], [512, 256, 128]],
            'dropout_rates': [[0.2, 0.3], [0.3, 0.4], [0.4, 0.5]],
            'learning_rate': [0.001, 0.002],
            'batch_size': [64, 128],
            'batch_norm': [True],
            'l2_reg': [0.0, 0.001],
            'optimizer': ['adam'],
            'activation': ['relu']
        },
        'medium': {
            'hidden_layers': [[128, 64], [256, 128, 64], [512, 256, 128], [256, 256, 128, 64]],
            'dropout_rates': [[0.2, 0.3], [0.3, 0.4], [0.4, 0.5], [0.2, 0.3, 0.4, 0.5]],
            'learning_rate': [0.0005, 0.001, 0.002],
            'batch_size': [32, 64, 128],
            'batch_norm': [True, False],
            'l1_reg': [0.0],
            'l2_reg': [0.0, 0.001, 0.01],
            'optimizer': ['adam', 'rmsprop'],
            'activation': ['relu', 'elu']
        },
        'extensive': {
            'hidden_layers': [[128, 64], [256, 128, 64], [512, 256, 128], [256, 256, 128, 64], [512, 256, 128, 64], [1024, 512, 256]],
            'dropout_rates': [[0.2, 0.3], [0.3, 0.4], [0.4, 0.5], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5], [0.1, 0.2, 0.3, 0.4]],
            'learning_rate': [0.0001, 0.0005, 0.001, 0.002, 0.005],
            'batch_size': [32, 64, 128, 256],
            'batch_norm': [True, False],
            'l1_reg': [0.0, 0.0001, 0.001],
            'l2_reg': [0.0, 0.001, 0.01, 0.1],
            'optimizer': ['adam', 'rmsprop', 'sgd'],
            'activation': ['relu', 'elu', 'leaky_relu']
        }
    }
    return grids

def mlp_grid_search(X_train, y_train, X_val=None, y_val=None, search_type='quick'):
    """Perform grid search for MLP hyperparameters"""
    print("="*80)
    print(f"STARTING {search_type.upper()} MLP GRID SEARCH")
    print("="*80)
    
    grids = get_parameter_grids()
    param_grid = grids[search_type]
    
    config = {
        'quick': {'max_epochs': 15, 'max_combinations': 8, 'patience': 3},
        'medium': {'max_epochs': 20, 'max_combinations': 20, 'patience': 5},
        'extensive': {'max_epochs': 30, 'max_combinations': 50, 'patience': 7}
    }
    
    max_epochs = config[search_type]['max_epochs']
    max_combinations = config[search_type]['max_combinations']
    patience = config[search_type]['patience']
    
    print(f"Search configuration:")
    print(f"- Max epochs per model: {max_epochs}")
    print(f"- Early stopping patience: {patience}")
    print(f"- Max combinations: {max_combinations}")
    
    grid = list(ParameterGrid(param_grid))
    print(f"\nTotal possible combinations: {len(grid)}")
    
    if len(grid) > max_combinations:
        np.random.seed(42)
        grid = np.random.choice(grid, max_combinations, replace=False)
        print(f"Randomly sampling {len(grid)} combinations for execution")
    
    results = []
    total_start_time = time.time()
    
    for i, params in enumerate(grid):
        print(f"\n{'='*60}")
        print(f"Grid Search Progress: {i+1}/{len(grid)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            hidden_layers = params['hidden_layers']
            dropout_rates = params['dropout_rates']
            
            if len(dropout_rates) < len(hidden_layers):
                dropout_rates = dropout_rates + [dropout_rates[-1]] * (len(hidden_layers) - len(dropout_rates))
            elif len(dropout_rates) > len(hidden_layers):
                dropout_rates = dropout_rates[:len(hidden_layers)]
            
            params['dropout_rates'] = dropout_rates
            
            model = create_advanced_mlp(params)
            model = compile_advanced_mlp(model, params)
            
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=max(2, patience//2), min_lr=0.00001, verbose=0)
            ]
            
            if X_val is not None and y_val is not None:
                history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=max_epochs, batch_size=params['batch_size'], callbacks=callbacks, verbose=0)
            else:
                history = model.fit(X_train, y_train, validation_split=0.2, epochs=max_epochs, batch_size=params['batch_size'], callbacks=callbacks, verbose=0)
            
            best_val_acc = max(history.history['val_accuracy'])
            best_val_loss = min(history.history['val_loss'])
            final_train_acc = history.history['accuracy'][-1]
            training_time = time.time() - start_time
            epochs_trained = len(history.history['accuracy'])
            overfitting = final_train_acc - best_val_acc
            
            result = {
                **params,
                'best_val_accuracy': best_val_acc,
                'best_val_loss': best_val_loss,
                'final_train_accuracy': final_train_acc,
                'overfitting': overfitting,
                'training_time': training_time,
                'epochs_trained': epochs_trained,
                'total_params': model.count_params()
            }
            
            results.append(result)
            
            print(f"\nResults:")
            print(f"  Best Val Accuracy: {best_val_acc:.4f}")
            print(f"  Training Time: {training_time:.1f}s")
            print(f"  Epochs Trained: {epochs_trained}")
            print(f"  Overfitting: {overfitting:.4f}")
            
            del model
            tf.keras.backend.clear_session()
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            continue
    
    total_time = time.time() - total_start_time
    print(f"\n{'='*80}")
    print(f"GRID SEARCH COMPLETED - {total_time/60:.1f} minutes")
    print(f"Successful configurations: {len(results)}/{len(grid)}")
    
    return results

def analyze_mlp_results(results):
    """Analyze MLP grid search results with comprehensive statistics"""
    if not results:
        print("No results to analyze!")
        return None, None
    
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('best_val_accuracy', ascending=False)
    
    print("\n" + "="*80)
    print("MLP GRID SEARCH ANALYSIS")
    print("="*80)
    
    print(f"\n=== SUMMARY STATISTICS ===")
    print(f"Total configurations tested: {len(results)}")
    print(f"Best validation accuracy: {df['best_val_accuracy'].max():.6f}")
    print(f"Average validation accuracy: {df['best_val_accuracy'].mean():.6f}")
    print(f"Standard deviation: {df['best_val_accuracy'].std():.6f}")
    
    print(f"\n=== TOP 5 CONFIGURATIONS ===")
    top_cols = ['hidden_layers', 'learning_rate', 'batch_size', 'batch_norm', 'l2_reg', 'best_val_accuracy', 'overfitting', 'training_time']
    available_cols = [col for col in top_cols if col in df.columns]
    print(df_sorted.head()[available_cols].round(4).to_string(index=False))
    
    best_params = df_sorted.iloc[0].to_dict()
    
    print(f"\n=== BEST CONFIGURATION DETAILS ===")
    print(f"Architecture: {best_params['hidden_layers']}")
    print(f"Dropout rates: {best_params['dropout_rates']}")
    print(f"Learning rate: {best_params['learning_rate']}")
    print(f"Batch size: {best_params['batch_size']}")
    print(f"Best validation accuracy: {best_params['best_val_accuracy']:.6f}")
    print(f"Overfitting gap: {best_params['overfitting']:.6f}")
    print(f"Training time: {best_params['training_time']:.1f}s")
    
    return best_params, df_sorted

def quick_mlp_search(X_train, y_train, X_val=None, y_val=None):
    """Quick MLP search with predefined good configurations"""
    print("="*60)
    print("QUICK MLP SEARCH - PREDEFINED CONFIGURATIONS")
    print("="*60)
    
    quick_configs = [
        {'hidden_layers': [256, 128], 'dropout_rates': [0.3, 0.4], 'batch_norm': True, 'l2_reg': 0.001, 'activation': 'relu', 'optimizer': 'adam', 'learning_rate': 0.001, 'batch_size': 64},
        {'hidden_layers': [512, 256, 128], 'dropout_rates': [0.2, 0.3, 0.4], 'batch_norm': True, 'l2_reg': 0.0, 'activation': 'relu', 'optimizer': 'adam', 'learning_rate': 0.002, 'batch_size': 32},
        {'hidden_layers': [128, 64], 'dropout_rates': [0.4, 0.5], 'batch_norm': False, 'l2_reg': 0.01, 'activation': 'elu', 'optimizer': 'rmsprop', 'learning_rate': 0.001, 'batch_size': 128},
        {'hidden_layers': [256, 256, 128], 'dropout_rates': [0.25, 0.35, 0.45], 'batch_norm': True, 'l2_reg': 0.001, 'activation': 'relu', 'optimizer': 'adam', 'learning_rate': 0.0005, 'batch_size': 64}
    ]
    
    results = []
    
    for i, config in enumerate(quick_configs):
        print(f"\n{'='*50}")
        print(f"Quick Test {i+1}/{len(quick_configs)}")
        print(f"Configuration: {config['hidden_layers']}, LR: {config['learning_rate']}")
        
        try:
            start_time = time.time()
            
            model = create_advanced_mlp(config)
            model = compile_advanced_mlp(model, config)
            
            callbacks = [EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=0)]
            
            if X_val is not None and y_val is not None:
                history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=20, batch_size=config['batch_size'], callbacks=callbacks, verbose=0)
            else:
                history = model.fit(X_train, y_train, validation_split=0.2, epochs=20, batch_size=config['batch_size'], callbacks=callbacks, verbose=0)
            
            best_val_acc = max(history.history['val_accuracy'])
            training_time = time.time() - start_time
            
            result = {
                **config,
                'best_val_accuracy': best_val_acc,
                'best_val_loss': min(history.history['val_loss']),
                'final_train_accuracy': history.history['accuracy'][-1],
                'training_time': training_time,
                'epochs_trained': len(history.history['accuracy'])
            }
            
            results.append(result)
            print(f"Val Accuracy: {best_val_acc:.4f}, Time: {training_time:.1f}s")
            
            del model
            tf.keras.backend.clear_session()
            
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    return results

if __name__ == "__main__":
    print("MLP Grid Search Module Loaded Successfully!")
    print("\nAvailable functions:")
    print("- mlp_grid_search() - Main grid search function")
    print("- quick_mlp_search() - Fast predefined search")
    print("- analyze_mlp_results() - Comprehensive analysis")
    print("- get_parameter_grids() - Get parameter definitions")
