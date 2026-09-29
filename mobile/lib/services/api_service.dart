/// API service for communicating with the FastAPI cloud backend.
/// Includes offline caching: successful responses are cached locally,
/// and cached data is returned when the backend is unreachable.

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/sensor_data.dart';
import 'offline_cache.dart';

class ApiService {
  final String baseUrl;

  ApiService({required this.baseUrl});

  // ── Sensors ─────────────────────────────────────────────────────────────

  Future<List<SensorReading>> getHistory({
    String farmId = 'farm_001',
    int hours = 1,
    int limit = 500,
  }) async {
    final uri = Uri.parse(
      '$baseUrl/api/v1/sensors/history?farm_id=$farmId&hours=$hours&limit=$limit',
    );
    final res = await http.get(uri);
    if (res.statusCode != 200) throw Exception('Failed to fetch history');
    final data = json.decode(res.body);
    return (data['readings'] as List)
        .map((e) => SensorReading.fromJson(e))
        .toList();
  }

  Future<SensorStats> getStats({
    String farmId = 'farm_001',
    int hours = 1,
  }) async {
    final uri = Uri.parse(
      '$baseUrl/api/v1/sensors/stats?farm_id=$farmId&hours=$hours',
    );
    final res = await http.get(uri);
    if (res.statusCode != 200) throw Exception('Failed to fetch stats');
    return SensorStats.fromJson(json.decode(res.body));
  }

  Future<SensorData?> getLatest({String farmId = 'farm_001'}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/sensors/latest?farm_id=$farmId');
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return await OfflineCache.getCachedLatest();
      final data = json.decode(res.body);
      if (data['error'] != null) return await OfflineCache.getCachedLatest();
      final sensor = SensorData(
        temp: (data['temperature'] ?? 0).toDouble(),
        humidity: (data['humidity'] ?? 0).toDouble(),
        light: (data['light_level'] ?? 0).toDouble(),
        soil: (data['soil_moisture'] ?? 0).toDouble(),
      );
      // Cache for offline use
      await OfflineCache.cacheLatest(sensor);
      await OfflineCache.appendHistory(sensor);
      return sensor;
    } catch (_) {
      // Offline fallback
      return await OfflineCache.getCachedLatest();
    }
  }

  /// Returns latest sensor values plus raw ADC readings (raw_ldr, raw_soil)
  /// used by the calibration wizard.
  Future<Map<String, dynamic>?> getLatestRaw({
    String farmId = 'farm_001',
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/sensors/latest/raw?farm_id=$farmId');
    try {
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return null;
      final data = json.decode(res.body) as Map<String, dynamic>;
      if (data['error'] != null) return null;
      return data;
    } catch (_) {
      return null;
    }
  }

  // ── Calibration ─────────────────────────────────────────────────────────

  Future<List<CalibrationSummary>> getCalibrationProfiles() async {
    final uri = Uri.parse('$baseUrl/api/v1/calibration/profiles');
    final res = await http.get(uri);
    if (res.statusCode != 200)
      throw Exception('Failed to fetch calibration profiles');
    final data = json.decode(res.body);
    return (data['profiles'] as List)
        .map((e) => CalibrationSummary.fromJson(e))
        .toList();
  }

  Future<CalibrationProfile> getCalibrationProfile(String sensorType) async {
    final uri = Uri.parse('$baseUrl/api/v1/calibration/profiles/$sensorType');
    final res = await http.get(uri);
    if (res.statusCode != 200) throw Exception('Profile not found');
    return CalibrationProfile.fromJson(json.decode(res.body));
  }

  Future<CalibrationProfile> updateCalibrationProfile(
    String sensorType,
    Map<String, dynamic> update,
  ) async {
    final uri = Uri.parse('$baseUrl/api/v1/calibration/profiles/$sensorType');
    final res = await http.put(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode(update),
    );
    if (res.statusCode != 200) throw Exception('Save failed');
    final data = json.decode(res.body);
    return CalibrationProfile.fromJson(data['profile']);
  }

  Future<CalibrationProfile> runCalibrationWizard({
    required String sensorType,
    required String method,
    required List<Map<String, dynamic>> points,
    String notes = '',
  }) async {
    final uri = Uri.parse('$baseUrl/api/v1/calibration/wizard');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'sensor_type': sensorType,
        'method': method,
        'points': points,
        'notes': notes,
      }),
    );
    if (res.statusCode != 200) {
      final err = json.decode(res.body);
      throw Exception(err['detail'] ?? 'Calibration failed');
    }
    final data = json.decode(res.body);
    return CalibrationProfile.fromJson(data['profile']);
  }

  // ── ML Predictions ──────────────────────────────────────────────────────

  Future<IrrigationRecommendation?> getIrrigationRecommendation(
    SensorData data,
  ) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/ml/recommend/irrigation');
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'soil_moisture': data.soil,
              'temperature': data.temp,
              'humidity': data.humidity,
              'light': data.light,
            }),
          )
          .timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return null;
      return IrrigationRecommendation.fromJson(json.decode(res.body));
    } catch (_) {
      return null;
    }
  }

  Future<MlEnsembleResult?> getMlEnsemble(SensorData data) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/ml/predict/ensemble');
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'soil_moisture': data.soil,
              'temperature': data.temp,
              'humidity': data.humidity,
              'light': data.light,
            }),
          )
          .timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return null;
      return MlEnsembleResult.fromJson(json.decode(res.body));
    } catch (_) {
      return null;
    }
  }

  // ── Health ──────────────────────────────────────────────────────────────

  Future<bool> healthCheck() async {
    try {
      final uri = Uri.parse('$baseUrl/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>?> getHealthDetails() async {
    try {
      final uri = Uri.parse('$baseUrl/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return null;
      return json.decode(res.body) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  // ── Relay Control ────────────────────────────────────────────────────────

  /// Send relay ON/OFF command to ESP32 via backend.
  /// [relay] = 'pump' | 'light'   [state] = 'on' | 'off'
  /// If the backend is unreachable, the command is queued locally
  /// and will be retried when connectivity returns.
  Future<bool> controlRelay({
    required String relay,
    required String state,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/relay/control');
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'relay': relay, 'state': state}),
          )
          .timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) {
        await OfflineCache.queueCommand({'relay': relay, 'state': state});
        return false;
      }
      final data = json.decode(res.body) as Map<String, dynamic>;
      return data['success'] == true;
    } catch (_) {
      // Offline: queue command for later
      await OfflineCache.queueCommand({'relay': relay, 'state': state});
      return false;
    }
  }

  /// Flush any queued offline commands to the backend.
  Future<int> flushPendingCommands() async {
    final pending = await OfflineCache.getPendingCommands();
    if (pending.isEmpty) return 0;
    int sent = 0;
    for (final cmd in pending) {
      try {
        final uri = Uri.parse('$baseUrl/api/v1/relay/control');
        final res = await http
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: json.encode({'relay': cmd['relay'], 'state': cmd['state']}),
            )
            .timeout(const Duration(seconds: 5));
        if (res.statusCode == 200) sent++;
      } catch (_) {
        break; // Still offline, stop trying
      }
    }
    if (sent == pending.length) {
      await OfflineCache.clearPendingCommands();
    }
    return sent;
  }
}
