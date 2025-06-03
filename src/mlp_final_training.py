"""
MLP Final Training & Evaluation - Part 3/4 (Complete)
=====================================================

Contains:
1. Final model training with best parameters
2. Advanced training callbacks and monitoring
3. Model evaluation and visualization functions
4. Performance analysis tools

Author: Created for MNIST classification project
"""

import numpy as np
import tensorflow as tf
import time
import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# Import from our modules
from mlp_basic_models import create_advanced_mlp, compile_advanced_mlp

def train_final_mlp(best_config, X_train, y_train, X_val=None, y_val=None, 
                   epochs=100, save_path='best_mlp_model.h5', use_advanced_callbacks=True):
    """Train final MLP model with best configuration found from grid search"""
    print("="*80)
    print("TRAINING FINAL MLP MODEL")
    print("="*80)
    
    print(f"\nBest Configuration:")
    for key, value in best_config.items():
        if key not in ['best_val_accuracy', 'best_val_loss', 'final_train_accuracy', 
                      'training_time', 'epochs_trained', 'overfitting', 'total_params']:
            print(f"  {key}: {value}")
    
    # Create model
    model = create_advanced_mlp(best_config)
    model = compile_advanced_mlp(model, best_config)
    
    # Setup callbacks
    callbacks = [
        ModelCheckpoint(save_path, monitor='val_accuracy', save_best_only=True, verbose=1),
        EarlyStopping(monitor='val_loss', patience=20 if use_advanced_callbacks else 10, restore_best_weights=True, verbose=1)
    ]
    
    if use_advanced_callbacks:
        callbacks.append(ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=0.00001, verbose=1))
    
    print(f"\n=== Starting Final Training ===")
    start_time = time.time()
    
    if X_val is not None and y_val is not None:
        history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=epochs, 
                          batch_size=best_config.get('batch_size', 128), callbacks=callbacks, verbose=1)
    else:
        history = model.fit(X_train, y_train, validation_split=0.2, epochs=epochs,
                          batch_size=best_config.get('batch_size', 128), callbacks=callbacks, verbose=1)
    
    training_time = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"FINAL TRAINING COMPLETED")
    print(f"Training time: {training_time/60:.1f} minutes")
    print(f"Best validation accuracy: {max(history.history['val_accuracy']):.6f}")
    print(f"Model saved to: {save_path}")
    
    return model, history

def plot_mlp_training_history(history, title="MLP Training History", save_path=None):
    """Plot comprehensive training history for MLP model"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Accuracy plot
    axes[0,0].plot(history.history['accuracy'], label='Training Accuracy', linewidth=2, color='blue')
    axes[0,0].plot(history.history['val_accuracy'], label='Validation Accuracy', linewidth=2, color='red')
    axes[0,0].set_title('Model Accuracy', fontsize=14, fontweight='bold')
    axes[0,0].set_xlabel('Epoch')
    axes[0,0].set_ylabel('Accuracy')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].set_ylim([0.8, 1.0])
    
    # Loss plot
    axes[0,1].plot(history.history['loss'], label='Training Loss', linewidth=2, color='blue')
    axes[0,1].plot(history.history['val_loss'], label='Validation Loss', linewidth=2, color='red')
    axes[0,1].set_title('Model Loss', fontsize=14, fontweight='bold')
    axes[0,1].set_xlabel('Epoch')
    axes[0,1].set_ylabel('Loss')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # Learning rate plot (if available)
    if 'lr' in history.history:
        axes[1,0].plot(history.history['lr'], linewidth=2, color='orange')
        axes[1,0].set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
        axes[1,0].set_xlabel('Epoch')
        axes[1,0].set_ylabel('Learning Rate')
        axes[1,0].set_yscale('log')
        axes[1,0].grid(True, alpha=0.3)
    else:
        axes[1,0].text(0.5, 0.5, 'Learning Rate\\nNot Recorded', 
                      horizontalalignment='center', verticalalignment='center',
                      transform=axes[1,0].transAxes, fontsize=12)
        axes[1,0].set_title('Learning Rate')
    
    # Training summary
    best_val_acc = max(history.history['val_accuracy'])
    final_train_acc = history.history['accuracy'][-1]
    overfitting = final_train_acc - best_val_acc
    epochs_trained = len(history.history['accuracy'])
    
    summary_text = f'''Training Summary:

Best Validation Accuracy: {best_val_acc:.4f}
Final Training Accuracy: {final_train_acc:.4f}
Overfitting Gap: {overfitting:.4f}
Epochs Trained: {epochs_trained}

Status: '''
    
    if overfitting <= 0.01:
        status = "Excellent Fit"
        status_color = 'green'
    elif overfitting <= 0.02:
        status = "Good Fit"
        status_color = 'orange'
    else:
        status = "Overfitting"
        status_color = 'red'
    
    axes[1,1].text(0.05, 0.95, summary_text, transform=axes[1,1].transAxes, 
                   fontsize=11, verticalalignment='top', fontfamily='monospace')
    axes[1,1].text(0.05, 0.25, status, transform=axes[1,1].transAxes, 
                   fontsize=12, fontweight='bold', color=status_color)
    axes[1,1].axis('off')
    
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()
    return fig

def evaluate_mlp_model(model, X_test, y_test, class_names=None, model_name="MLP"):
    """Comprehensive evaluation of MLP model on test data"""
    print(f"\n{'='*60}")
    print(f"{model_name.upper()} MODEL EVALUATION")
    print(f"{'='*60}")
    
    if class_names is None:
        class_names = [str(i) for i in range(10)]
    
    # Basic evaluation
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"Test Results:")
    print(f"  Test Accuracy: {test_accuracy:.6f}")
    print(f"  Test Loss: {test_loss:.6f}")
    print(f"  Error Rate: {(1-test_accuracy)*100:.3f}%")
    
    # Predictions
    predictions = model.predict(X_test, verbose=0)
    predicted_classes = np.argmax(predictions, axis=1)
    true_classes = np.argmax(y_test, axis=1)
    
    # Per-class accuracy
    print(f"\n=== PER-CLASS PERFORMANCE ===")
    class_accuracy = {}
    for i, class_name in enumerate(class_names):
        class_mask = true_classes == i
        class_acc = np.mean(predicted_classes[class_mask] == i) if np.sum(class_mask) > 0 else 0
        class_accuracy[class_name] = class_acc
        print(f"  Digit {class_name}: {class_acc:.4f} ({np.sum(class_mask)} samples)")
    
    # Classification report
    print(f"\n=== CLASSIFICATION REPORT ===")
    report = classification_report(true_classes, predicted_classes, target_names=class_names, output_dict=True)
    print(classification_report(true_classes, predicted_classes, target_names=class_names))
    
    # Confusion matrix analysis
    cm = confusion_matrix(true_classes, predicted_classes)
    cm_no_diag = cm.copy()
    np.fill_diagonal(cm_no_diag, 0)
    
    if cm_no_diag.sum() > 0:
        max_confusion_idx = np.unravel_index(np.argmax(cm_no_diag), cm_no_diag.shape)
        print(f"\nMost confused pair: {max_confusion_idx[0]} → {max_confusion_idx[1]} ({cm_no_diag[max_confusion_idx]} errors)")
    
    # Confidence analysis
    max_probs = np.max(predictions, axis=1)
    correct_mask = predicted_classes == true_classes
    
    print(f"\n=== CONFIDENCE ANALYSIS ===")
    print(f"  Average confidence: {np.mean(max_probs):.4f}")
    print(f"  Confidence on correct: {np.mean(max_probs[correct_mask]):.4f}")
    if np.sum(~correct_mask) > 0:
        print(f"  Confidence on incorrect: {np.mean(max_probs[~correct_mask]):.4f}")
    
    results = {
        'test_accuracy': test_accuracy,
        'test_loss': test_loss,
        'predictions': predictions,
        'predicted_classes': predicted_classes,
        'true_classes': true_classes,
        'class_accuracy': class_accuracy,
        'confusion_matrix': cm,
        'classification_report': report
    }
    
    return results

def plot_confusion_matrix(cm, class_names=None, title="Confusion Matrix", normalize=False):
    """Plot confusion matrix with better visualization"""
    if class_names is None:
        class_names = [str(i) for i in range(len(cm))]
    
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        fmt = '.2f'
    else:
        fmt = 'd'
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=fmt, cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Count' if not normalize else 'Proportion'})
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.tight_layout()
    plt.show()

def analyze_misclassifications(X_test, y_test, predictions, n_examples=5):
    """Analyze and visualize misclassified examples"""
    predicted_classes = np.argmax(predictions, axis=1)
    true_classes = np.argmax(y_test, axis=1)
    
    misclassified_mask = predicted_classes != true_classes
    misclassified_indices = np.where(misclassified_mask)[0]
    
    if len(misclassified_indices) == 0:
        print("No misclassifications found!")
        return
    
    print(f"\n=== MISCLASSIFICATION ANALYSIS ===")
    print(f"Total misclassifications: {len(misclassified_indices)} / {len(X_test)} ({len(misclassified_indices)/len(X_test)*100:.2f}%)")
    
    # Group by error type
    error_types = {}
    for idx in misclassified_indices:
        true_label = true_classes[idx]
        pred_label = predicted_classes[idx]
        error_key = f"{true_label}→{pred_label}"
        
        if error_key not in error_types:
            error_types[error_key] = []
        error_types[error_key].append(idx)
    
    # Sort by frequency and display
    sorted_errors = sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"\nMost common error types:")
    for i, (error_type, indices) in enumerate(sorted_errors[:5]):
        print(f"  {i+1}. {error_type}: {len(indices)} cases")

if __name__ == "__main__":
    print("MLP Final Training & Evaluation Module Loaded Successfully!")
    print("\nAvailable functions:")
    print("- train_final_mlp() - Train final model with best config")
    print("- plot_mlp_training_history() - Visualize training progress")
    print("- evaluate_mlp_model() - Comprehensive model evaluation")
    print("- plot_confusion_matrix() - Visualize confusion matrix")
    print("- analyze_misclassifications() - Analyze prediction errors")
