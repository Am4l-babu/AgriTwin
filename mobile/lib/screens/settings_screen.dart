import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../theme/theme_notifier.dart';
import '../config/app_config.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController(text: AppConfig.host);
  bool _checking = false;
  bool? _serverOk;
  Map<String, dynamic>? _healthData;

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _checking = true;
      _serverOk = null;
      _healthData = null;
    });
    try {
      AppConfig.host = _urlController.text;
      final api = ApiService(baseUrl: AppConfig.baseUrl);
      final health = await api.getHealthDetails();
      if (mounted)
        setState(() {
          _serverOk = health != null;
          _healthData = health;
          _checking = false;
        });
    } catch (_) {
      if (mounted)
        setState(() {
          _serverOk = false;
          _checking = false;
        });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final subtitleColor = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final sectionLabelColor = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final infoLabelColor = isDark
        ? Colors.white54
        : Colors.black.withValues(alpha: 0.5);
    final tipsBg = isDark
        ? AppColors.emerald500.withValues(alpha: 0.1)
        : AppColors.emerald50;
    final tipsBorderColor = isDark
        ? AppColors.emerald500.withValues(alpha: 0.2)
        : AppColors.emerald500.withValues(alpha: 0.2);
    final errorFeedbackBg = isDark
        ? const Color(0xFF2D1B1B)
        : const Color(0xFFFEF2F2);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Header
            Container(
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                children: [
                  Container(
                    width: 3,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.emerald500,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SETTINGS',
                        style: GoogleFonts.inter(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'App configuration',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          color: subtitleColor,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // ── Dark Mode Toggle ──
            Container(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: borderColor),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'APPEARANCE',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                      color: sectionLabelColor,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: isDark
                              ? Colors.white.withValues(alpha: 0.08)
                              : AppColors.slate100,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          isDark ? Icons.dark_mode : Icons.light_mode,
                          size: 20,
                          color: isDark ? Colors.amber : AppColors.amber500,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Dark Mode',
                              style: GoogleFonts.inter(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text(
                              isDark
                                  ? 'Currently enabled'
                                  : 'Currently disabled',
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                color: subtitleColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Switch(
                        value: isDark,
                        activeColor: AppColors.emerald500,
                        onChanged: (_) => themeNotifier.toggle(),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Server URL
            Container(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: borderColor),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'SERVER CONNECTION',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                      color: sectionLabelColor,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _urlController,
                    decoration: InputDecoration(
                      labelText: 'Server Address',
                      hintText: '192.168.x.x:8000',
                      prefixText: 'http://',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                    ),
                    style: GoogleFonts.robotoMono(fontSize: 14),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _checking ? null : _testConnection,
                          icon: _checking
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.wifi_find, size: 18),
                          label: const Text('Test Connection'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.emerald500,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (_serverOk != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: _serverOk!
                            ? (isDark
                                  ? AppColors.emerald500.withValues(alpha: 0.15)
                                  : AppColors.emerald50)
                            : errorFeedbackBg,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _serverOk!
                                ? Icons.check_circle
                                : Icons.error_outline,
                            size: 18,
                            color: _serverOk!
                                ? AppColors.emerald500
                                : AppColors.red500,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _serverOk!
                                ? 'Connected successfully!'
                                : 'Connection failed',
                            style: GoogleFonts.inter(
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                              color: _serverOk!
                                  ? AppColors.emerald600
                                  : AppColors.red500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Info card
            Container(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: borderColor),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ABOUT',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                      color: sectionLabelColor,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _infoRow('App', 'AgriTwin Digital Twin', infoLabelColor),
                  _infoRow('Version', '1.1.0', infoLabelColor),
                  _infoRow('Backend', 'FastAPI + SQLite', infoLabelColor),
                  _infoRow('Hardware', 'ESP32 + DHT11 + LDR', infoLabelColor),
                  _infoRow('Protocol', 'MQTT → WebSocket', infoLabelColor),
                  if (_healthData != null) ...[
                    const Divider(height: 20),
                    Text(
                      'SERVER STATUS',
                      style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.5,
                        color: sectionLabelColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _infoRow(
                      'Uptime',
                      _healthData!['uptime'] ?? 'N/A',
                      infoLabelColor,
                    ),
                    _infoRow(
                      'Total Readings',
                      '${_healthData!['database']?['total_readings'] ?? 0}',
                      infoLabelColor,
                    ),
                    _infoRow(
                      'DB Size',
                      '${_healthData!['database']?['size_mb'] ?? 0} MB',
                      infoLabelColor,
                    ),
                    _infoRow(
                      'MQTT',
                      (_healthData!['mqtt_connected'] == true)
                          ? 'Connected'
                          : 'Disconnected',
                      infoLabelColor,
                    ),
                    _infoRow(
                      'ML Module',
                      (_healthData!['modules']?['ml_predictions'] == true)
                          ? 'Active'
                          : 'Inactive',
                      infoLabelColor,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Tips
            Container(
              decoration: BoxDecoration(
                color: tipsBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: tipsBorderColor),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.info_outline,
                        size: 16,
                        color: AppColors.emerald600,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Connection Tips',
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.emerald600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '• Use your computer\'s LAN IP (e.g. 192.168.1.x)\n'
                    '• Make sure the backend server is running\n'
                    '• Phone must be on the same WiFi network\n'
                    '• Default port is 8000',
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: AppColors.emerald600.withValues(alpha: 0.8),
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(String label, String value, Color labelColor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: GoogleFonts.inter(fontSize: 13, color: labelColor),
          ),
          Text(
            value,
            style: GoogleFonts.robotoMono(
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
