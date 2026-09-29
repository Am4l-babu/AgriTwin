import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kThemeKey = 'dark_mode';

/// Global theme mode notifier — persists dark mode choice across app launches.
class ThemeNotifier extends ChangeNotifier {
  ThemeMode _mode = ThemeMode.light;

  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;

  /// Load saved preference from disk. Call once at app startup.
  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final dark = prefs.getBool(_kThemeKey) ?? false;
    _mode = dark ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
  }

  void toggle() {
    _mode = _mode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    _save();
    notifyListeners();
  }

  void setMode(ThemeMode mode) {
    _mode = mode;
    _save();
    notifyListeners();
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kThemeKey, isDark);
  }
}

/// Singleton instance
final themeNotifier = ThemeNotifier();
