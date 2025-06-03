"""
MLP Complete Implementation - Part 4/4 (Main Orchestration)
===========================================================

This is the main file that orchestrates all MLP functionality.
Contains:
1. Complete usage guide with execution order
2. Main orchestration functions
3. Step-by-step workflow examples
4. Performance comparison utilities

Author: Created for MNIST classification project
"""

import sys
import os
import time
import numpy as np

# Import all our MLP modules


print("Hey hoe !")
try:
    # Starting Imports
    from mlp_basic_models import (
        create_basic_mlp, train_basic_mlp,
        create_advanced_mlp, compile_advanced_mlp, get_default_advanced_config
    )
    # imported Basic MLP model
    from mlp_grid_search import (
        mlp_grid_search, quick_mlp_search, analyze_mlp_results, get_parameter_grids
    )
    # imported Final MLP model
    from mlp_final_training import (
        train_final_mlp, plot_mlp_training_history, evaluate_mlp_model,
        plot_confusion_matrix, analyze_misclassifications
    )
    print("✓ All MLP modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all MLP module files are in the same directory.")

def run_basic_mlp_workflow(X_train, y_train, X_test, y_test, epochs=30):
    """Complete workflow for basic MLP model"""
    print("\n" + "="*80)
    print("RUNNING BASIC MLP WORKFLOW")
    print("="*80)

    print("\n=== STEP 1: Creating Basic MLP Model ===")
    basic_model = create_basic_mlp()

    print("\n=== STEP 2: Training Basic MLP Model ===")
    basic_history = train_basic_mlp(basic_model, X_train, y_train, epochs=epochs, batch_size=128)

    print("\n=== STEP 3: Evaluating Basic MLP Model ===")
    basic_results = evaluate_mlp_model(basic_model, X_test, y_test, model_name="Basic MLP")

    print("\n=== STEP 4: Visualizing Results ===")
    plot_mlp_training_history(basic_history, "Basic MLP Training")
    plot_confusion_matrix(basic_results['confusion_matrix'], title="Basic MLP Confusion Matrix")

    return {'model': basic_model, 'history': basic_history, 'evaluation': basic_results}

def run_complete_mlp_workflow(X_train, y_train, X_test, y_test, search_type='quick', final_epochs=100):
    """Complete end-to-end MLP workflow: Basic → Grid Search → Final Training → Evaluation"""
    print("\n" + "="*100)
    print("RUNNING COMPLETE MLP WORKFLOW - ALL STAGES")
    print("="*100)

    workflow_start_time = time.time()
    results = {}

    print("\n🚀 STAGE 1: BASIC MLP BASELINE")
    basic_results = run_basic_mlp_workflow(X_train, y_train, X_test, y_test, epochs=20)
    results['basic'] = basic_results

    print("\n🔍 STAGE 2: HYPERPARAMETER GRID SEARCH")
    search_results = mlp_grid_search(X_train, y_train, search_type=search_type)
    best_config, analysis_df = analyze_mlp_results(search_results)
    results['grid_search'] = {'search_results': search_results, 'best_config': best_config}

    print("\n🎯 STAGE 3: FINAL MODEL TRAINING")
    final_model, final_history = train_final_mlp(
        best_config, X_train, y_train, epochs=final_epochs, save_path='final_mlp_model.h5'
    )

    print("\n📊 STAGE 4: FINAL MODEL EVALUATION")
    final_evaluation = evaluate_mlp_model(final_model, X_test, y_test, model_name="Final Optimized MLP")

    results['final'] = {
        'model': final_model, 'history': final_history,
        'evaluation': final_evaluation, 'config': best_config
    }

    print("\n📈 STAGE 5: COMPREHENSIVE ANALYSIS")
    plot_mlp_training_history(final_history, "Final Optimized MLP Training")
    plot_confusion_matrix(final_evaluation['confusion_matrix'], title="Final Optimized MLP Confusion Matrix")
    analyze_misclassifications(X_test, y_test, final_evaluation['predictions'])

    print("\n=== PERFORMANCE COMPARISON ===")
    print(f"Basic MLP Test Accuracy: {basic_results['evaluation']['test_accuracy']:.6f}")
    print(f"Final MLP Test Accuracy: {final_evaluation['test_accuracy']:.6f}")
    print(f"Improvement: {(final_evaluation['test_accuracy'] - basic_results['evaluation']['test_accuracy'])*100:.3f}%")

    total_time = time.time() - workflow_start_time
    print(f"\n⏱️ Total workflow time: {total_time/60:.1f} minutes")

    return results

def quick_mlp_comparison(X_train, y_train, X_test, y_test):
    """Quick comparison of basic vs advanced MLP configurations"""
    print("\n" + "="*80)
    print("QUICK MLP COMPARISON - BASIC VS ADVANCED")
    print("="*80)

    results = {}

    print("\n=== Testing Basic MLP ===")
    basic_model = create_basic_mlp()
    basic_history = train_basic_mlp(basic_model, X_train, y_train, epochs=15, verbose=0)
    basic_eval = evaluate_mlp_model(basic_model, X_test, y_test, model_name="Basic")
    results['basic'] = basic_eval

    print("\n=== Testing Quick Predefined Search ===")
    quick_results = quick_mlp_search(X_train, y_train)
    best_quick, _ = analyze_mlp_results(quick_results)

    quick_model = create_advanced_mlp(best_quick)
    quick_model = compile_advanced_mlp(quick_model, best_quick)

    from tensorflow.keras.callbacks import EarlyStopping
    callbacks = [EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)]

    quick_history = quick_model.fit(
        X_train, y_train, validation_split=0.2, epochs=15,
        batch_size=best_quick['batch_size'], callbacks=callbacks, verbose=0
    )

    quick_eval = evaluate_mlp_model(quick_model, X_test, y_test, model_name="Quick Optimized")
    results['quick_optimized'] = quick_eval

    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    for name, result in results.items():
        print(f"{name:15}: {result['test_accuracy']:.6f}")

    return results

def print_complete_usage_guide():
    """Print comprehensive usage guide for all MLP functionality"""
    print("\n" + "="*100)
    print("MLP COMPLETE IMPLEMENTATION - USAGE GUIDE")
    print("="*100)

    print("""
🚀 EXECUTION ORDER FOR DIFFERENT TASKS:

1️⃣ BASIC MLP MODEL (Simple Implementation)
   ==========================================

   # Quick start - basic model
   basic_results = run_basic_mlp_workflow(X_train, y_cat_train, X_test, y_cat_test)

   # Or step by step:
   basic_model = create_basic_mlp()
   basic_history = train_basic_mlp(basic_model, X_train, y_cat_train, epochs=30)
   basic_eval = evaluate_mlp_model(basic_model, X_test, y_cat_test, "Basic MLP")
   plot_mlp_training_history(basic_history, "Basic MLP Training")

2️⃣ ADVANCED MLP MODEL (Well-Optimized)
   =====================================

   # Use default advanced configuration:
   config = get_default_advanced_config()
   advanced_model = create_advanced_mlp(config)
   advanced_model = compile_advanced_mlp(advanced_model, config)

   # Or with custom configuration:
   custom_config = {
       'hidden_layers': [512, 256, 128],
       'dropout_rates': [0.3, 0.4, 0.5],
       'batch_norm': True,
       'l2_reg': 0.001,
       'activation': 'relu',
       'optimizer': 'adam',
       'learning_rate': 0.001,
       'batch_size': 64
   }

3️⃣ GRID SEARCH PROCESS (Hyperparameter Tuning)
   ==============================================

   # Quick search (8 combinations, ~10-15 minutes)
   quick_results = mlp_grid_search(X_train, y_cat_train, search_type='quick')
   best_config, _ = analyze_mlp_results(quick_results)

   # Medium search (20 combinations, ~30-45 minutes)
   medium_results = mlp_grid_search(X_train, y_cat_train, search_type='medium')

   # Extensive search (50 combinations, ~2-3 hours)
   extensive_results = mlp_grid_search(X_train, y_cat_train, search_type='extensive')

   # Quick predefined search (~5-8 minutes)
   quick_predefined = quick_mlp_search(X_train, y_cat_train)
   best_predefined, _ = analyze_mlp_results(quick_predefined)

4️⃣ FINAL MODEL TRAINING (Best Parameters)
   ========================================

   # Train final model with best config from grid search
   final_model, final_history = train_final_mlp(
       best_config,  # From grid search
       X_train, y_cat_train,
       epochs=100,
       save_path='final_mlp_model.h5'
   )

   # Comprehensive evaluation
   final_eval = evaluate_mlp_model(final_model, X_test, y_cat_test, "Final MLP")

   # Visualizations
   plot_mlp_training_history(final_history, "Final MLP Training")
   plot_confusion_matrix(final_eval['confusion_matrix'], "Final MLP Confusion Matrix")
   analyze_misclassifications(X_test, y_cat_test, final_eval['predictions'])

🔄 COMPLETE END-TO-END WORKFLOW (RECOMMENDED)
   ============================================

   # Run everything automatically
   complete_results = run_complete_mlp_workflow(
       X_train, y_cat_train,
       X_test, y_cat_test,
       search_type='quick',  # or 'medium', 'extensive'
       final_epochs=100
   )

⚡ QUICK COMPARISON
   ================

   # Compare basic vs optimized quickly
   comparison = quick_mlp_comparison(X_train, y_cat_train, X_test, y_cat_test)

📊 EXPECTED PERFORMANCE ON MNIST:
   ===============================

   Basic MLP:          ~97.5-98.5% accuracy
   Grid Search Best:   ~99.0-99.3% accuracy
   Final Optimized:    ~99.2-99.5% accuracy

   Training times:
   - Basic: ~2-5 minutes
   - Grid Search: 10 minutes - 3 hours (depending on type)
   - Final Training: ~15-30 minutes

💡 TIPS:
   ======

   - Start with quick grid search to get good baseline
   - Use medium search for better results with reasonable time
   - Use extensive search only if you need state-of-the-art performance
   - Always run final training with more epochs for best results
   - Monitor overfitting gap (should be < 0.02 for good generalization)
""")

if __name__ == "__main__":
    print("MLP Complete Implementation Loaded Successfully!")
    print("\nMain functions available:")
    print("- run_basic_mlp_workflow() - Basic MLP pipeline")
    print("- run_complete_mlp_workflow() - Complete end-to-end pipeline")
    print("- quick_mlp_comparison() - Quick comparison of different approaches")

    print_complete_usage_guide()

    print("\n" + "="*80)
    print("READY TO USE - EXAMPLE EXECUTION")
    print("="*80)

    print("""
Make sure you have your data loaded as:
- X_train, y_cat_train: Training data (images and one-hot labels)
- X_test, y_cat_test: Test data (images and one-hot labels)

Then run:

# For quick results (15-20 minutes total):
complete_results = run_complete_mlp_workflow(
    X_train, y_cat_train, X_test, y_cat_test,
    search_type='quick', final_epochs=50
)

# For best results (1-2 hours total):
complete_results = run_complete_mlp_workflow(
    X_train, y_cat_train, X_test, y_cat_test,
    search_type='medium', final_epochs=100
)

# For just a quick comparison:
comparison = quick_mlp_comparison(X_train, y_cat_train, X_test, y_cat_test)
""")
