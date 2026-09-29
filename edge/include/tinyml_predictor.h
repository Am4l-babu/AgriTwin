/**
 * @file tinyml_predictor.h
 * @brief TinyML Soil Moisture Predictor for ESP32
 * 
 * Runs TensorFlow Lite model on ESP32 for edge AI inference
 */

#ifndef TINYML_PREDICTOR_H
#define TINYML_PREDICTOR_H

#include <Arduino.h>

// Configuration
#define LOOKBACK_STEPS 4        // Number of past readings to use
#define N_FEATURES 4            // temp, humidity, light, hour
#define PREDICTION_INTERVAL 900000  // 15 minutes in ms

class TinyMLPredictor {
public:
    TinyMLPredictor();
    
    /**
     * Initialize TensorFlow Lite interpreter
     * @return true if successful
     */
    bool begin();
    
    /**
     * Add new sensor reading to history buffer
     * @param temperature Temperature in °C
     * @param humidity Relative humidity in %
     * @param lightLevel Light level (0-100)
     * @param hour Hour of day (0-23.99)
     */
    void addReading(float temperature, float humidity, float lightLevel, float hour);
    
    /**
     * Predict soil moisture for next timestep
     * @return Predicted soil moisture (0-100%) or -1 if error
     */
    float predict();
    
    /**
     * Check if enough data for prediction
     * @return true if ready
     */
    bool isReady();
    
    /**
     * Get last prediction
     * @return Last predicted value
     */
    float getLastPrediction();
    
    /**
     * Get inference time in milliseconds
     * @return Inference time
     */
    float getInferenceTime();
    
    /**
     * Reset history buffer
     */
    void reset();

private:
    // History buffers (circular)
    float tempHistory[LOOKBACK_STEPS];
    float humidityHistory[LOOKBACK_STEPS];
    float lightHistory[LOOKBACK_STEPS];
    float hourHistory[LOOKBACK_STEPS];
    
    int bufferIndex;
    int readingsCount;
    
    float lastPrediction;
    float lastInferenceTime;
    
    // Normalization parameters (from training)
    float featureMins[N_FEATURES];
    float featureRanges[N_FEATURES];
    
    /**
     * Normalize input features
     */
    void normalizeFeatures(float* features);
    
    /**
     * Run TFLite inference
     */
    float runInference();
};

#endif // TINYML_PREDICTOR_H
