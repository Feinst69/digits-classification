# CNN Filters Visualization - Jupyter Notebook
# Copy each section into separate cells

# ===== CELL 1: Imports and Setup =====
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Input
from PIL import Image
import os
import seaborn as sns
from pathlib import Path

# Configure matplotlib
plt.style.use('default')
sns.set_palette("husl")

print(f"TensorFlow version: {tf.__version__}")
print(f"GPU available: {tf.config.list_physical_devices('GPU')}")

# ===== CELL 2: Load Model =====
# Adjust path to your model
MODEL_PATH = "models/best_cnn_model.keras"  
print(f"Loading model from: {MODEL_PATH}")

try:
    model = load_model(MODEL_PATH)
    print("✅ Model loaded successfully!")
    model.summary()
except Exception as e:
    print(f"❌ Loading error: {e}")
    # If error, use alternative path
    MODEL_PATH = input("Enter full path to your .keras model: ")
    model = load_model(MODEL_PATH)

# ===== CELL 3: Image Preparation =====
def load_and_preprocess_image(image_path):
    """Load and preprocess image for CNN model"""
    img = Image.open(image_path)
    
    # Display original image
    plt.figure(figsize=(8, 4))
    plt.subplot(1, 3, 1)
    plt.imshow(img, cmap='gray' if img.mode == 'L' else None)
    plt.title("Original Image")
    plt.axis('off')
    
    # Convert to grayscale if needed
    if img.mode != 'L':
        img = img.convert('L')
    
    # Resize to 28x28
    img_resized = img.resize((28, 28), Image.LANCZOS)
    
    plt.subplot(1, 3, 2)
    plt.imshow(img_resized, cmap='gray')
    plt.title("Resized (28x28)")
    plt.axis('off')
    
    # Convert to array and normalize
    img_array = np.array(img_resized)
    img_array = img_array / 255.0
    
    # Invert if needed (white background -> black like MNIST)
    if np.mean(img_array) > 0.5:
        img_array = 1 - img_array
    
    plt.subplot(1, 3, 3)
    plt.imshow(img_array, cmap='gray')
    plt.title("Preprocessed")
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Reshape for model (batch_size, height, width, channels)
    img_model = img_array.reshape(1, 28, 28, 1)
    
    return img_model, img_array

def create_test_digit():
    """Create a simple test digit"""
    img = np.zeros((28, 28))
    
    # Draw a simple "1"
    img[5:23, 13:15] = 1.0  # Vertical line
    img[5:8, 11:16] = 1.0   # Top of 1
    img[20:23, 10:17] = 1.0 # Base of 1
    
    plt.figure(figsize=(4, 4))
    plt.imshow(img, cmap='gray')
    plt.title("Test digit created")
    plt.axis('off')
    plt.show()
    
    return img.reshape(1, 28, 28, 1), img

# Choose your option:
print("Option 1: Load your own image")
print("Option 2: Use test digit")
choice = input("Enter 1 or 2: ")

if choice == "1":
    image_path = input("Enter path to your image: ")
    processed_image, display_image = load_and_preprocess_image(image_path)
else:
    processed_image, display_image = create_test_digit()

print(f"Image prepared - Shape: {processed_image.shape}")

# ===== CELL 4: Robust Feature Extractors =====
def create_feature_extractors_robust(model):
    """Create feature extractors with multiple fallback methods"""
    extractors = {}
    
    print("🔧 Creating feature extractors...")
    
    # Method 1: Try to create functional model
    try:
        print("Attempt 1: Functional model...")
        input_layer = Input(shape=(28, 28, 1), name='extractor_input')
        output = model(input_layer)
        functional_model = Model(inputs=input_layer, outputs=output)
        
        # Identify conv layers
        conv_layers = []
        for i, layer in enumerate(functional_model.layers):
            if 'conv' in layer.name.lower() or isinstance(layer, tf.keras.layers.Conv2D):
                conv_layers.append((i, layer.name, layer))
                print(f"  ✅ Conv layer found: {layer.name}")
        
        # Create extractors
        for i, (layer_idx, layer_name, layer) in enumerate(conv_layers):
            try:
                layer_output = functional_model.get_layer(layer_name).output
                extractor = Model(inputs=functional_model.input, outputs=layer_output)
                extractors[f"conv_{i+1}_{layer_name}"] = extractor
                print(f"  ✅ Extractor created: conv_{i+1}_{layer_name}")
            except Exception as e:
                print(f"  ❌ Failed extractor {layer_name}: {e}")
        
    except Exception as e:
        print(f"Method 1 failed: {e}")
        
        # Method 2: Manual reconstruction
        print("Attempt 2: Manual reconstruction...")
        try:
            # Make prediction to initialize model
            test_input = np.random.rand(1, 28, 28, 1)
            _ = model.predict(test_input, verbose=0)
            
            # Target layers (adjust according to your model)
            target_layers = ['conv2d_8', 'conv2d_9', 'conv2d_10', 'conv2d_11']
            
            input_layer = Input(shape=(28, 28, 1))
            
            for i, target_layer in enumerate(target_layers):
                try:
                    x = input_layer
                    for layer in model.layers:
                        x = layer(x)
                        if layer.name == target_layer:
                            extractor = Model(inputs=input_layer, outputs=x)
                            extractors[f"conv_{i+1}_{target_layer}"] = extractor
                            print(f"  ✅ Manual extractor created: conv_{i+1}_{target_layer}")
                            break
                except Exception as layer_error:
                    print(f"  ❌ Failed {target_layer}: {layer_error}")
                    
        except Exception as manual_error:
            print(f"Method 2 failed: {manual_error}")
    
    print(f"🎯 Total extractors created: {len(extractors)}")
    return extractors

# Create extractors
feature_extractors = create_feature_extractors_robust(model)

# Display available extractors
if feature_extractors:
    print("\n📋 Available extractors:")
    for name, extractor in feature_extractors.items():
        print(f"  - {name}: {extractor.output.shape}")
else:
    print("❌ No extractors created. Check your model.")

# ===== CELL 5: Feature Extraction =====
def extract_features(image, extractors):
    """Extract feature maps from all layers"""
    if not extractors:
        print("❌ No extractors available")
        return {}
    
    print("🔍 Extracting feature maps...")
    
    # First make prediction
    prediction = model.predict(image, verbose=0)
    predicted_class = np.argmax(prediction[0])
    confidence = prediction[0][predicted_class] * 100
    
    print(f"🎯 Prediction: {predicted_class} (confidence: {confidence:.2f}%)")
    
    # Extract features for each layer
    all_features = {}
    for name, extractor in extractors.items():
        try:
            features = extractor.predict(image, verbose=0)
            all_features[name] = features
            print(f"  ✅ {name}: shape {features.shape}")
        except Exception as e:
            print(f"  ❌ Error {name}: {e}")
    
    return all_features, predicted_class, confidence

# Extract features
if feature_extractors:
    feature_maps, prediction, confidence = extract_features(processed_image, feature_extractors)
else:
    feature_maps, prediction, confidence = {}, None, None

# ===== CELL 6: Visualization Functions =====
def create_filters_grid(features, n_filters):
    """Create grid of filters for display"""
    h, w = features.shape[:2]
    
    # Calculate grid layout
    cols = min(6, n_filters)
    rows = (n_filters + cols - 1) // cols
    
    # Create grid
    grid = np.zeros((rows * h, cols * w))
    
    for i in range(n_filters):
        row = i // cols
        col = i % cols
        
        # Normalize filter
        filter_map = features[:, :, i]
        if filter_map.max() > filter_map.min():
            filter_map = (filter_map - filter_map.min()) / (filter_map.max() - filter_map.min())
        
        # Place in grid
        grid[row*h:(row+1)*h, col*w:(col+1)*w] = filter_map
    
    return grid

def visualize_overview(original_image, features_dict, prediction, confidence):
    """Create overview visualization"""
    if not features_dict:
        print("❌ No feature maps to visualize")
        return
    
    n_layers = len(features_dict)
    
    # Overview figure
    fig = plt.figure(figsize=(20, 4 * n_layers))
    
    # Original image and prediction
    plt.subplot(n_layers + 1, 1, 1)
    plt.imshow(original_image, cmap='gray')
    plt.title(f"Original Image | Prediction: {prediction} (Confidence: {confidence:.1f}%)", 
              fontsize=16, fontweight='bold')
    plt.axis('off')
    
    # Feature maps for each layer
    for layer_idx, (layer_name, features) in enumerate(features_dict.items()):
        plt.subplot(n_layers + 1, 1, layer_idx + 2)
        
        # Take first filters for display
        n_filters_to_show = min(12, features.shape[-1])
        
        # Create filters grid
        filters_grid = create_filters_grid(features[0], n_filters_to_show)
        
        plt.imshow(filters_grid, cmap='viridis')
        plt.title(f"{layer_name} | Shape: {features.shape} | {n_filters_to_show} first filters", 
                  fontsize=14)
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

def visualize_layer_details(layer_name, features):
    """Detailed visualization of a layer"""
    print(f"\n🔬 Detailed analysis: {layer_name}")
    print(f"Shape: {features.shape}")
    
    n_filters = features.shape[-1]
    
    # Calculate filter statistics
    filter_stats = []
    for i in range(n_filters):
        filter_map = features[0, :, :, i]
        stats = {
            'filter': i,
            'mean': np.mean(filter_map),
            'std': np.std(filter_map),
            'max': np.max(filter_map),
            'min': np.min(filter_map),
            'variance': np.var(filter_map)
        }
        filter_stats.append(stats)
    
    # Sort by variance (activity)
    filter_stats.sort(key=lambda x: x['variance'], reverse=True)
    
    # Show most active filters
    n_show = min(9, n_filters)
    fig, axes = plt.subplots(3, 3, figsize=(12, 12))
    fig.suptitle(f"{layer_name} - Top {n_show} most active filters", fontsize=16)
    
    for i in range(n_show):
        row, col = i // 3, i % 3
        
        filter_idx = filter_stats[i]['filter']
        filter_map = features[0, :, :, filter_idx]
        
        # Normalize for display
        if filter_map.max() > filter_map.min():
            filter_map_norm = (filter_map - filter_map.min()) / (filter_map.max() - filter_map.min())
        else:
            filter_map_norm = filter_map
        
        axes[row, col].imshow(filter_map_norm, cmap='viridis')
        axes[row, col].set_title(f"Filter {filter_idx}\nVar: {filter_stats[i]['variance']:.4f}")
        axes[row, col].axis('off')
    
    # Hide unused axes
    for i in range(n_show, 9):
        row, col = i // 3, i % 3
        axes[row, col].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Statistics plots
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    variances = [s['variance'] for s in filter_stats]
    plt.bar(range(len(variances)), variances)
    plt.title("Variance per filter (activity)")
    plt.xlabel("Filter")
    plt.ylabel("Variance")
    
    plt.subplot(1, 3, 2)
    means = [s['mean'] for s in filter_stats]
    plt.bar(range(len(means)), means)
    plt.title("Mean activation per filter")
    plt.xlabel("Filter")
    plt.ylabel("Mean")
    
    plt.subplot(1, 3, 3)
    maxs = [s['max'] for s in filter_stats]
    plt.bar(range(len(maxs)), maxs)
    plt.title("Max activation per filter")
    plt.xlabel("Filter")
    plt.ylabel("Maximum")
    
    plt.tight_layout()
    plt.show()

def compare_layers(features_dict):
    """Compare activations between layers"""
    if len(features_dict) < 2:
        print("❌ Need at least 2 layers to compare")
        return
    
    layer_names = list(features_dict.keys())
    
    # Calculate statistics per layer
    stats = {}
    for name, features in features_dict.items():
        stats[name] = {
            'mean_activation': np.mean(features),
            'max_activation': np.max(features),
            'std_activation': np.std(features),
            'n_filters': features.shape[-1],
            'spatial_size': features.shape[1] * features.shape[2]
        }
    
    # Visualize comparisons
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Layer Comparison", fontsize=16)
    
    # Plot 1: Mean activation
    axes[0, 0].bar(range(len(layer_names)), [stats[name]['mean_activation'] for name in layer_names])
    axes[0, 0].set_title("Mean Activation per Layer")
    axes[0, 0].set_xticks(range(len(layer_names)))
    axes[0, 0].set_xticklabels([name.split('_')[-1] for name in layer_names], rotation=45)
    
    # Plot 2: Max activation
    axes[0, 1].bar(range(len(layer_names)), [stats[name]['max_activation'] for name in layer_names])
    axes[0, 1].set_title("Max Activation per Layer")
    axes[0, 1].set_xticks(range(len(layer_names)))
    axes[0, 1].set_xticklabels([name.split('_')[-1] for name in layer_names], rotation=45)
    
    # Plot 3: Number of filters
    axes[1, 0].bar(range(len(layer_names)), [stats[name]['n_filters'] for name in layer_names])
    axes[1, 0].set_title("Number of Filters per Layer")
    axes[1, 0].set_xticks(range(len(layer_names)))
    axes[1, 0].set_xticklabels([name.split('_')[-1] for name in layer_names], rotation=45)
    
    # Plot 4: Spatial size
    axes[1, 1].bar(range(len(layer_names)), [stats[name]['spatial_size'] for name in layer_names])
    axes[1, 1].set_title("Spatial Size per Layer")
    axes[1, 1].set_xticks(range(len(layer_names)))
    axes[1, 1].set_xticklabels([name.split('_')[-1] for name in layer_names], rotation=45)
    
    plt.tight_layout()
    plt.show()

# ===== CELL 7: Quick Visualizations =====
# Show overview
if feature_maps:
    visualize_overview(display_image, feature_maps, prediction, confidence)
else:
    print("❌ No feature maps to visualize")

# ===== CELL 8: Interactive Analysis =====
def interactive_analysis():
    """Interactive analysis menu"""
    if not feature_maps:
        print("❌ No feature maps available")
        return
    
    while True:
        print("\n🎮 Interactive Filter Analysis")
        print("=" * 40)
        print("1. Show all layers overview")
        print("2. Analyze specific layer")
        print("3. Compare layers")
        print("4. Show layer statistics")
        print("5. Exit")
        
        choice = input("\nYour choice (1-5): ")
        
        if choice == "1":
            visualize_overview(display_image, feature_maps, prediction, confidence)
        
        elif choice == "2":
            print("\nAvailable layers:")
            layer_names = list(feature_maps.keys())
            for i, name in enumerate(layer_names):
                print(f"  {i+1}. {name}")
            
            try:
                layer_choice = int(input("Choose layer (number): ")) - 1
                if 0 <= layer_choice < len(layer_names):
                    selected_layer = layer_names[layer_choice]
                    visualize_layer_details(selected_layer, feature_maps[selected_layer])
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == "3":
            compare_layers(feature_maps)
        
        elif choice == "4":
            print("\n📊 Layer Statistics:")
            for name, features in feature_maps.items():
                print(f"\n{name}:")
                print(f"  Shape: {features.shape}")
                print(f"  Min: {features.min():.4f}")
                print(f"  Max: {features.max():.4f}")
                print(f"  Mean: {features.mean():.4f}")
                print(f"  Std: {features.std():.4f}")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

# Start interactive analysis
interactive_analysis()

# ===== CELL 9: Save Results (Optional) =====
def save_visualizations():
    """Save all visualizations"""
    if not feature_maps:
        print("❌ No feature maps to save")
        return
    
    save_dir = input("Save directory (or Enter for './filter_outputs'): ").strip()
    if not save_dir:
        save_dir = "./filter_outputs"
    
    os.makedirs(save_dir, exist_ok=True)
    print(f"💾 Saving to: {save_dir}")
    
    # Save original image
    plt.figure(figsize=(6, 6))
    plt.imshow(display_image, cmap='gray')
    plt.title(f"Original Image - Predicted: {prediction}")
    plt.axis('off')
    plt.savefig(f"{save_dir}/original_image.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save feature maps for each layer
    for layer_name, features in feature_maps.items():
        # Filter grid
        n_filters = min(16, features.shape[-1])
        filters_grid = create_filters_grid(features[0], n_filters)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(filters_grid, cmap='viridis')
        plt.title(f"{layer_name} - Feature Maps")
        plt.axis('off')
        plt.savefig(f"{save_dir}/{layer_name}_grid.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {layer_name} saved")
    
    print(f"🎉 All visualizations saved to {save_dir}")

# Uncomment to save:
# save_visualizations()
