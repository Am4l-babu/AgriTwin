#!/bin/bash
# Complete TinyML Pipeline Test Script

echo "========================================="
echo "TinyML Complete Pipeline Test"
echo "========================================="

# Step 1: Generate data
echo -e "\n[1/4] Generating training data..."
python generate_training_data.py
if [ $? -ne 0 ]; then
    echo "❌ Data generation failed!"
    exit 1
fi
echo "✓ Data generation complete"

# Step 2: Train model
echo -e "\n[2/4] Training model..."
python train_model.py
if [ $? -ne 0 ]; then
    echo "❌ Model training failed!"
    exit 1
fi
echo "✓ Model training complete"

# Step 3: Convert to TFLite
echo -e "\n[3/4] Converting to TensorFlow Lite..."
python convert_to_tflite.py
if [ $? -ne 0 ]; then
    echo "❌ TFLite conversion failed!"
    exit 1
fi
echo "✓ TFLite conversion complete"

# Step 4: Copy to ESP32 project
echo -e "\n[4/4] Copying model to ESP32 project..."
cp models/model_data.h ../edge/include/
if [ $? -ne 0 ]; then
    echo "❌ File copy failed!"
    exit 1
fi
echo "✓ Model copied to edge/include/"

echo -e "\n========================================="
echo "✅ Pipeline Complete!"
echo "========================================="
echo "Next steps:"
echo "  1. cd ../edge"
echo "  2. pio run --target upload"
echo "  3. pio device monitor"
