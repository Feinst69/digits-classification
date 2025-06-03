"""
MLP Basic Models - Part 1/4
============================

Contains:
1. Basic MLP Model (simple implementation)
2. Advanced MLP Model creation functions

Author: Created for MNIST classification project
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras import layers
from tensorflow.keras.optimizers import Adam, RMSprop, SGD
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.regularizers import l1, l2, l1_l2

# ================================================================
# 1. BASIC MLP MODEL (SIMPLE)
# ================================================================

def create_basic_mlp(input_shape=(784,), num_classes=10):
    """
    Create a basic MLP model with minimal configuration
    
    Architecture:
    - Input layer (784 neurons for flattened 28x28 images)
    - 2 Hidden layers (128, 64 neurons)
    - Output layer (10 neurons for digits 0-9)
    - Basic ReLU activation and dropout
    
    Args:
        input_shape: Shape of input data (default: 784 for MNIST)
        num_classes: Number of output classes (default: 10 for digits)
    
    Returns:
        model: Compiled Keras model
    """
    print("Creating Basic MLP Model...")
    
    model = Sequential([
        # Input layer - handles both flattened and image inputs
        layers.Flatten(input_shape=(28, 28, 1)),
        
        # First hidden layer
        layers.Dense(128, activation='relu', name='hidden_1'),
        layers.Dropout(0.2, name='dropout_1'),
        
        # Second hidden layer  
        layers.Dense(64, activation='relu', name='hidden_2'),
        layers.Dropout(0.2, name='dropout_2'),
        
        # Output layer
        layers.Dense(num_classes, activation='softmax', name='output')
    ])
    
    # Compile with basic configuration
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("Basic MLP Model Summary:")
    model.summary()
    
    return model

def train_basic_mlp(model, X_train, y_train, X_val=None, y_val=None, 
                   epochs=20, batch_size=128, verbose=1):
    """
    Train the basic MLP model with simple configuration
    
    Args:
        model: Compiled Keras model
        X_train, y_train: Training data
        X_val, y_val: Validation data (optional)
        epochs: Number of training epochs
        batch_size: Training batch size
        verbose: Training verbosity
    
    Returns:
        history: Training history
    """
    print(f"\nTraining Basic MLP for {epochs} epochs...")
    print(f"Batch size: {batch_size}")
    print(f"Training samples: {len(X_train)}")
    
    # Simple early stopping
    callbacks = [
        EarlyStopping(
            monitor='val_loss', 
            patience=5, 
            restore_best_weights=True,
            verbose=1
        )
    ]
    
    # Train model
    if X_val is not None and y_val is not None:
        print("Using provided validation set...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
    else:
        print("Using validation split (20%)...")
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
    
    # Print results
    best_val_acc = max(history.history['val_accuracy'])
    final_train_acc = history.history['accuracy'][-1]
    epochs_trained = len(history.history['accuracy'])
    
    print(f"\n=== BASIC MLP TRAINING COMPLETE ===")
    print(f"Epochs trained: {epochs_trained}")
    print(f"Best Validation Accuracy: {best_val_acc:.4f}")
    print(f"Final Training Accuracy: {final_train_acc:.4f}")
    print(f"Overfitting gap: {final_train_acc - best_val_acc:.4f}")
    
    return history

# ================================================================
# 2. ADVANCED MLP MODEL (WELL-OPTIMIZED)
# ================================================================

def create_advanced_mlp(params):
    """
    Create an advanced MLP model with sophisticated architecture and regularization
    
    Features:
    - Configurable number of layers and neurons
    - Batch normalization for stable training
    - Advanced dropout patterns
    - L1/L2 regularization options
    - Flexible activation functions
    
    Args:
        params: Dictionary containing model parameters:
            - hidden_layers: List of neurons per layer [256, 128, 64]
            - dropout_rates: List of dropout rates [0.3, 0.4, 0.5]
            - batch_norm: Boolean, use batch normalization
            - l1_reg: L1 regularization strength
            - l2_reg: L2 regularization strength
            - activation: Activation function ('relu', 'elu', 'leaky_relu')
    
    Returns:
        model: Uncompiled Keras model
    """
    print("Creating Advanced MLP Model...")
    print(f"Configuration: {params}")
    
    # Extract parameters with defaults
    hidden_layers = params.get('hidden_layers', [256, 128, 64])
    dropout_rates = params.get('dropout_rates', [0.3, 0.4, 0.5])
    batch_norm = params.get('batch_norm', True)
    l1_reg = params.get('l1_reg', 0.0)
    l2_reg = params.get('l2_reg', 0.001)
    activation = params.get('activation', 'relu')
    
    # Ensure dropout_rates matches hidden_layers length
    if len(dropout_rates) != len(hidden_layers):
        if len(dropout_rates) < len(hidden_layers):
            # Extend dropout_rates by repeating the last value
            dropout_rates = dropout_rates + [dropout_rates[-1]] * (len(hidden_layers) - len(dropout_rates))
        else:
            # Truncate dropout_rates
            dropout_rates = dropout_rates[:len(hidden_layers)]
    
    print(f"Architecture: {len(hidden_layers)} hidden layers")
    print(f"Neurons per layer: {hidden_layers}")
    print(f"Dropout rates: {dropout_rates}")
    print(f"Batch normalization: {batch_norm}")
    print(f"L1 regularization: {l1_reg}")
    print(f"L2 regularization: {l2_reg}")
    print(f"Activation: {activation}")
    
    # Create regularizer
    if l1_reg > 0 and l2_reg > 0:
        regularizer = l1_l2(l1=l1_reg, l2=l2_reg)
        reg_info = f"L1+L2 (l1={l1_reg}, l2={l2_reg})"
    elif l1_reg > 0:
        regularizer = l1(l1_reg)
        reg_info = f"L1 ({l1_reg})"
    elif l2_reg > 0:
        regularizer = l2(l2_reg)
        reg_info = f"L2 ({l2_reg})"
    else:
        regularizer = None
        reg_info = "None"
    
    print(f"Regularization: {reg_info}")
    
    # Build model
    model = Sequential()
    
    # Input layer
    model.add(layers.Flatten(input_shape=(28, 28, 1), name='flatten'))
    
    # Hidden layers
    for i, (neurons, dropout) in enumerate(zip(hidden_layers, dropout_rates)):
        layer_name = f'layer_{i+1}'
        
        # Dense layer with regularization
        model.add(layers.Dense(
            neurons, 
            kernel_regularizer=regularizer,
            name=f'dense_{layer_name}'
        ))
        
        # Batch normalization
        if batch_norm:
            model.add(layers.BatchNormalization(name=f'bn_{layer_name}'))
        
        # Activation
        if activation == 'leaky_relu':
            model.add(layers.LeakyReLU(alpha=0.1, name=f'leaky_relu_{layer_name}'))
        elif activation == 'elu':
            model.add(layers.ELU(alpha=1.0, name=f'elu_{layer_name}'))
        else:  # relu
            model.add(layers.Activation('relu', name=f'relu_{layer_name}'))
        
        # Dropout
        model.add(layers.Dropout(dropout, name=f'dropout_{layer_name}'))
    
    # Output layer (no regularization on output)
    model.add(layers.Dense(10, activation='softmax', name='output'))
    
    print(f"\nAdvanced MLP Architecture Created:")
    print(f"Total parameters: {model.count_params():,}")
    model.summary()
    
    return model

def compile_advanced_mlp(model, params):
    """
    Compile advanced MLP with sophisticated optimizer configuration
    
    Args:
        model: Keras model to compile
        params: Dictionary with compilation parameters:
            - optimizer: 'adam', 'rmsprop', 'sgd'
            - learning_rate: Learning rate value
            - beta_1, beta_2: Adam parameters
            - momentum: SGD momentum
            - rho: RMSprop parameter
    
    Returns:
        model: Compiled model
    """
    optimizer_name = params.get('optimizer', 'adam')
    learning_rate = params.get('learning_rate', 0.001)
    
    print(f"\nCompiling model with {optimizer_name} optimizer...")
    
    # Create optimizer with advanced parameters
    if optimizer_name == 'adam':
        optimizer = Adam(
            learning_rate=learning_rate,
            beta_1=params.get('beta_1', 0.9),
            beta_2=params.get('beta_2', 0.999),
            epsilon=params.get('epsilon', 1e-07)
        )
        opt_info = f"Adam (lr={learning_rate}, β1={params.get('beta_1', 0.9)}, β2={params.get('beta_2', 0.999)})"
        
    elif optimizer_name == 'rmsprop':
        optimizer = RMSprop(
            learning_rate=learning_rate,
            rho=params.get('rho', 0.9),
            epsilon=params.get('epsilon', 1e-07)
        )
        opt_info = f"RMSprop (lr={learning_rate}, ρ={params.get('rho', 0.9)})"
        
    elif optimizer_name == 'sgd':
        optimizer = SGD(
            learning_rate=learning_rate,
            momentum=params.get('momentum', 0.9),
            nesterov=params.get('nesterov', True)
        )
        opt_info = f"SGD (lr={learning_rate}, momentum={params.get('momentum', 0.9)}, nesterov={params.get('nesterov', True)})"
        
    else:
        optimizer = Adam(learning_rate=learning_rate)
        opt_info = f"Adam (default, lr={learning_rate})"
    
    # Compile model
    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print(f"Model compiled successfully!")
    print(f"Optimizer: {opt_info}")
    print(f"Loss function: categorical_crossentropy")
    print(f"Metrics: accuracy")
    
    return model

def get_default_advanced_config():
    """
    Get a default configuration for advanced MLP
    
    Returns:
        config: Dictionary with default parameters
    """
    return {
        'hidden_layers': [512, 256, 128],
        'dropout_rates': [0.3, 0.4, 0.5],
        'batch_norm': True,
        'l1_reg': 0.0,
        'l2_reg': 0.001,
        'activation': 'relu',
        'optimizer': 'adam',
        'learning_rate': 0.001,
        'batch_size': 64,
        'beta_1': 0.9,
        'beta_2': 0.999,
        'epsilon': 1e-07
    }

# ================================================================
# USAGE EXAMPLES
# ================================================================

def example_basic_usage():
    """
    Example of how to use basic MLP functions
    """
    print("="*60)
    print("BASIC MLP USAGE EXAMPLE")
    print("="*60)
    
    print("""
# Example usage for Basic MLP:

# 1. Create basic model
basic_model = create_basic_mlp()

# 2. Train the model
basic_history = train_basic_mlp(
    basic_model, 
    X_train, y_cat_train,
    epochs=30,
    batch_size=128
)

# 3. The model is ready for evaluation
""")

def example_advanced_usage():
    """
    Example of how to use advanced MLP functions
    """
    print("="*60)
    print("ADVANCED MLP USAGE EXAMPLE")
    print("="*60)
    
    print("""
# Example usage for Advanced MLP:

# 1. Get default configuration or create custom
config = get_default_advanced_config()

# Or create custom configuration:
# config = {
#     'hidden_layers': [256, 128, 64],
#     'dropout_rates': [0.3, 0.4, 0.5],
#     'batch_norm': True,
#     'l2_reg': 0.001,
#     'activation': 'relu',
#     'optimizer': 'adam',
#     'learning_rate': 0.001,
#     'batch_size': 64
# }

# 2. Create and compile model
advanced_model = create_advanced_mlp(config)
advanced_model = compile_advanced_mlp(advanced_model, config)

# 3. Train with custom callbacks
callbacks = [
    EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)
]

advanced_history = advanced_model.fit(
    X_train, y_cat_train,
    validation_split=0.2,
    epochs=50,
    batch_size=config['batch_size'],
    callbacks=callbacks,
    verbose=1
)
""")

if __name__ == "__main__":
    print("MLP Basic Models Module Loaded Successfully!")
    print("\nAvailable functions:")
    print("- create_basic_mlp()")
    print("- train_basic_mlp()")
    print("- create_advanced_mlp()")
    print("- compile_advanced_mlp()")
    print("- get_default_advanced_config()")
    
    example_basic_usage()
    example_advanced_usage()
