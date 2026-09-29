/// Sensor data models shared across the app.

class SensorData {
  final double temp;
  final double humidity;
  final double light;
  final double soil;

  const SensorData({
    this.temp = 0,
    this.humidity = 0,
    this.light = 0,
    this.soil = 0,
  });

  factory SensorData.fromJson(Map<String, dynamic> json) {
    return SensorData(
      temp: (json['temp'] ?? json['temperature'] ?? 0).toDouble(),
      humidity: (json['humidity'] ?? 0).toDouble(),
      light: (json['light'] ?? json['light_level'] ?? 0).toDouble(),
      soil: (json['soil'] ?? json['soil_moisture'] ?? 0).toDouble(),
    );
  }
}

class SensorReading {
  final String timestamp;
  final double temperature;
  final double humidity;
  final double lightLevel;
  final double soilMoisture;

  const SensorReading({
    required this.timestamp,
    required this.temperature,
    required this.humidity,
    required this.lightLevel,
    required this.soilMoisture,
  });

  factory SensorReading.fromJson(Map<String, dynamic> json) {
    return SensorReading(
      timestamp: json['timestamp'] ?? '',
      temperature: (json['temperature'] ?? 0).toDouble(),
      humidity: (json['humidity'] ?? 0).toDouble(),
      lightLevel: (json['light_level'] ?? 0).toDouble(),
      soilMoisture: (json['soil_moisture'] ?? 0).toDouble(),
    );
  }
}

class SensorStats {
  final int totalReadings;
  final double avgTemp, minTemp, maxTemp;
  final double avgHumidity, minHumidity, maxHumidity;
  final double avgLight, minLight, maxLight;
  final double avgSoil, minSoil, maxSoil;

  const SensorStats({
    this.totalReadings = 0,
    this.avgTemp = 0,
    this.minTemp = 0,
    this.maxTemp = 0,
    this.avgHumidity = 0,
    this.minHumidity = 0,
    this.maxHumidity = 0,
    this.avgLight = 0,
    this.minLight = 0,
    this.maxLight = 0,
    this.avgSoil = 0,
    this.minSoil = 0,
    this.maxSoil = 0,
  });

  factory SensorStats.fromJson(Map<String, dynamic> json) {
    return SensorStats(
      totalReadings: json['total_readings'] ?? 0,
      avgTemp: (json['avg_temperature'] ?? 0).toDouble(),
      minTemp: (json['min_temperature'] ?? 0).toDouble(),
      maxTemp: (json['max_temperature'] ?? 0).toDouble(),
      avgHumidity: (json['avg_humidity'] ?? 0).toDouble(),
      minHumidity: (json['min_humidity'] ?? 0).toDouble(),
      maxHumidity: (json['max_humidity'] ?? 0).toDouble(),
      avgLight: (json['avg_light'] ?? 0).toDouble(),
      minLight: (json['min_light'] ?? 0).toDouble(),
      maxLight: (json['max_light'] ?? 0).toDouble(),
      avgSoil: (json['avg_soil'] ?? 0).toDouble(),
      minSoil: (json['min_soil'] ?? 0).toDouble(),
      maxSoil: (json['max_soil'] ?? 0).toDouble(),
    );
  }
}

class CalibrationProfile {
  final String sensorType;
  final String method;
  final String? calibrationDate;
  final String? description;
  final String? notes;
  final double? offset;
  final double? multiplier;
  final int? dryValue;
  final int? wetValue;
  final Map<String, dynamic>? point1;
  final Map<String, dynamic>? point2;
  final Map<String, dynamic>? point3;
  final List<Map<String, dynamic>>? referencePoints;
  final Map<String, List<double>>? interpretation;
  final Map<String, dynamic>? conversion;
  final Map<String, dynamic>? temperatureCompensation;

  CalibrationProfile({
    required this.sensorType,
    required this.method,
    this.calibrationDate,
    this.description,
    this.notes,
    this.offset,
    this.multiplier,
    this.dryValue,
    this.wetValue,
    this.point1,
    this.point2,
    this.point3,
    this.referencePoints,
    this.interpretation,
    this.conversion,
    this.temperatureCompensation,
  });

  factory CalibrationProfile.fromJson(Map<String, dynamic> json) {
    Map<String, List<double>>? interp;
    if (json['interpretation'] != null) {
      interp = {};
      (json['interpretation'] as Map<String, dynamic>).forEach((k, v) {
        if (v is List) {
          interp![k] = v.map((e) => (e as num).toDouble()).toList();
        }
      });
    }

    List<Map<String, dynamic>>? refPts;
    if (json['reference_points'] != null) {
      refPts = (json['reference_points'] as List)
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }

    return CalibrationProfile(
      sensorType: json['sensor_type'] ?? '',
      method: json['calibration_method'] ?? json['method'] ?? 'unknown',
      calibrationDate: json['calibration_date'],
      description: json['description'],
      notes: json['notes'],
      offset: json['offset']?.toDouble(),
      multiplier: json['multiplier']?.toDouble(),
      dryValue: json['dry_value'],
      wetValue: json['wet_value'],
      point1: json['point1'] != null
          ? Map<String, dynamic>.from(json['point1'])
          : null,
      point2: json['point2'] != null
          ? Map<String, dynamic>.from(json['point2'])
          : null,
      point3: json['point3'] != null
          ? Map<String, dynamic>.from(json['point3'])
          : null,
      referencePoints: refPts,
      interpretation: interp,
      conversion: json['conversion'] != null
          ? Map<String, dynamic>.from(json['conversion'])
          : null,
      temperatureCompensation: json['temperature_compensation'] != null
          ? Map<String, dynamic>.from(json['temperature_compensation'])
          : null,
    );
  }
}

// ── ML Prediction Models ──────────────────────────────────────────────────────

class IrrigationRecommendation {
  final String action;
  final int actionId;
  final double confidence;
  final int waterAmount;
  final String reason;

  const IrrigationRecommendation({
    required this.action,
    required this.actionId,
    required this.confidence,
    required this.waterAmount,
    required this.reason,
  });

  factory IrrigationRecommendation.fromJson(Map<String, dynamic> json) {
    return IrrigationRecommendation(
      action: json['action'] ?? 'none',
      actionId: json['action_id'] ?? 0,
      confidence: (json['confidence'] ?? 0).toDouble(),
      waterAmount: json['water_amount'] ?? 0,
      reason: json['reason'] ?? '',
    );
  }
}

class MlEnsembleResult {
  final bool irrigate;
  final bool fertilize;
  final double confidence;

  const MlEnsembleResult({
    required this.irrigate,
    required this.fertilize,
    required this.confidence,
  });

  String get plantHealthLabel {
    if (!irrigate && !fertilize) return 'Healthy';
    if (irrigate && fertilize) return 'High Stress';
    return 'Moderate Stress';
  }

  factory MlEnsembleResult.fromJson(Map<String, dynamic> json) {
    final ruleB = json['rule_based'] as Map<String, dynamic>? ?? {};
    return MlEnsembleResult(
      irrigate: ruleB['irrigate'] ?? false,
      fertilize: ruleB['fertilize'] ?? false,
      confidence: (ruleB['confidence'] ?? 0.8).toDouble(),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────

class CalibrationSummary {
  final String sensorType;
  final String method;
  final String? calibrationDate;
  final String description;
  final bool hasInterpretation;
  final bool hasReferencePoints;

  CalibrationSummary({
    required this.sensorType,
    required this.method,
    this.calibrationDate,
    required this.description,
    required this.hasInterpretation,
    required this.hasReferencePoints,
  });

  factory CalibrationSummary.fromJson(Map<String, dynamic> json) {
    return CalibrationSummary(
      sensorType: json['sensor_type'] ?? '',
      method: json['method'] ?? 'not_calibrated',
      calibrationDate: json['calibration_date'],
      description: json['description'] ?? '',
      hasInterpretation: json['has_interpretation'] ?? false,
      hasReferencePoints: json['has_reference_points'] ?? false,
    );
  }
}
