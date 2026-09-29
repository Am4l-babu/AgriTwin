/// Offline Cache Service
///
/// Provides local caching for sensor data so the app works
/// when the backend is unreachable. Uses shared_preferences
/// for small structured data and a bounded in-memory queue
/// that persists to disk.

import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/sensor_data.dart';

class OfflineCache {
  static const _latestKey = 'offline_latest_sensor';
  static const _historyKey = 'offline_history';
  static const _twinBrainKey = 'offline_twin_brain';
  static const _pendingCommandsKey = 'offline_pending_commands';
  static const int _maxHistoryItems = 500;

  // ── Latest sensor reading ───────────────────────────────────────────

  static Future<void> cacheLatest(SensorData data) async {
    final prefs = await SharedPreferences.getInstance();
    final json = {
      'temp': data.temp,
      'humidity': data.humidity,
      'light': data.light,
      'soil': data.soil,
      'cached_at': DateTime.now().toIso8601String(),
    };
    await prefs.setString(_latestKey, jsonEncode(json));
  }

  static Future<SensorData?> getCachedLatest() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_latestKey);
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return SensorData(
        temp: (json['temp'] ?? 0).toDouble(),
        humidity: (json['humidity'] ?? 0).toDouble(),
        light: (json['light'] ?? 0).toDouble(),
        soil: (json['soil'] ?? 0).toDouble(),
      );
    } catch (_) {
      return null;
    }
  }

  static Future<DateTime?> getCachedLatestTime() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_latestKey);
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return DateTime.tryParse(json['cached_at'] ?? '');
    } catch (_) {
      return null;
    }
  }

  // ── History buffer ──────────────────────────────────────────────────

  static Future<void> appendHistory(SensorData data) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey);
    List<dynamic> list = raw != null ? jsonDecode(raw) as List<dynamic> : [];

    list.add({
      'temp': data.temp,
      'humidity': data.humidity,
      'light': data.light,
      'soil': data.soil,
      'timestamp': DateTime.now().toIso8601String(),
    });

    // Keep bounded
    if (list.length > _maxHistoryItems) {
      list = list.sublist(list.length - _maxHistoryItems);
    }

    await prefs.setString(_historyKey, jsonEncode(list));
  }

  static Future<List<SensorData>> getCachedHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey);
    if (raw == null) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list.map((e) {
        final m = e as Map<String, dynamic>;
        return SensorData(
          temp: (m['temp'] ?? 0).toDouble(),
          humidity: (m['humidity'] ?? 0).toDouble(),
          light: (m['light'] ?? 0).toDouble(),
          soil: (m['soil'] ?? 0).toDouble(),
        );
      }).toList();
    } catch (_) {
      return [];
    }
  }

  // ── DT Brain cache ──────────────────────────────────────────────────

  static Future<void> cacheTwinBrain(Map<String, dynamic> brain) async {
    final prefs = await SharedPreferences.getInstance();
    brain['cached_at'] = DateTime.now().toIso8601String();
    await prefs.setString(_twinBrainKey, jsonEncode(brain));
  }

  static Future<Map<String, dynamic>?> getCachedTwinBrain() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_twinBrainKey);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  // ── Pending commands (relay control when offline) ───────────────────

  static Future<void> queueCommand(Map<String, dynamic> cmd) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_pendingCommandsKey);
    final list = raw != null ? jsonDecode(raw) as List<dynamic> : [];
    cmd['queued_at'] = DateTime.now().toIso8601String();
    list.add(cmd);
    await prefs.setString(_pendingCommandsKey, jsonEncode(list));
  }

  static Future<List<Map<String, dynamic>>> getPendingCommands() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_pendingCommandsKey);
    if (raw == null) return [];
    try {
      return (jsonDecode(raw) as List<dynamic>)
          .map((e) => e as Map<String, dynamic>)
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> clearPendingCommands() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_pendingCommandsKey);
  }

  // ── Utility ─────────────────────────────────────────────────────────

  static Future<bool> hasOfflineData() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey(_latestKey);
  }

  static Future<void> clearAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_latestKey);
    await prefs.remove(_historyKey);
    await prefs.remove(_twinBrainKey);
    await prefs.remove(_pendingCommandsKey);
  }
}
