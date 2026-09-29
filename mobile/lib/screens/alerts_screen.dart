import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../config/app_config.dart';

// ── Alert Model ──────────────────────────────────────────────────────────────

enum AlertSeverity { critical, warning, info, good }

class SensorAlert {
  final String title;
  final String message;
  final String recommendation;
  final AlertSeverity severity;
  final IconData icon;
  final Color color;
  final double currentValue;
  final String unit;
  final double optimalMin;
  final double optimalMax;

  const SensorAlert({
    required this.title,
    required this.message,
    required this.recommendation,
    required this.severity,
    required this.icon,
    required this.color,
    required this.currentValue,
    required this.unit,
    required this.optimalMin,
    required this.optimalMax,
  });
}

// ── Threshold Definitions ────────────────────────────────────────────────────

class _Threshold {
  final String sensor;
  final IconData icon;
  final String unit;
  final double criticalLow;
  final double warningLow;
  final double optimalLow;
  final double optimalHigh;
  final double warningHigh;
  final double criticalHigh;
  final String lowRecLow;
  final String lowRecMid;
  final String highRecMid;
  final String highRecHigh;

  const _Threshold({
    required this.sensor,
    required this.icon,
    required this.unit,
    required this.criticalLow,
    required this.warningLow,
    required this.optimalLow,
    required this.optimalHigh,
    required this.warningHigh,
    required this.criticalHigh,
    required this.lowRecLow,
    required this.lowRecMid,
    required this.highRecMid,
    required this.highRecHigh,
  });
}

const _thresholds = [
  _Threshold(
    sensor: 'Soil Moisture',
    icon: Icons.water_drop,
    unit: '%',
    criticalLow: 15,
    warningLow: 25,
    optimalLow: 30,
    optimalHigh: 70,
    warningHigh: 80,
    criticalHigh: 95,
    lowRecLow: 'Critically dry! Start irrigation immediately to prevent wilting.',
    lowRecMid: 'Soil is drying out. Consider watering within the next few hours.',
    highRecMid: 'Soil is quite wet. Reduce watering to prevent root rot.',
    highRecHigh: 'Waterlogged! Stop irrigation and ensure drainage is working.',
  ),
  _Threshold(
    sensor: 'Temperature',
    icon: Icons.thermostat,
    unit: '°C',
    criticalLow: 5,
    warningLow: 12,
    optimalLow: 18,
    optimalHigh: 32,
    warningHigh: 38,
    criticalHigh: 45,
    lowRecLow: 'Frost risk! Cover crops or activate heating immediately.',
    lowRecMid: 'Getting cold. Monitor closely, consider frost protection.',
    highRecMid: 'Heat stress zone. Increase shade or ventilation.',
    highRecHigh: 'Extreme heat! Activate cooling and misting systems now.',
  ),
  _Threshold(
    sensor: 'Humidity',
    icon: Icons.cloud,
    unit: '%',
    criticalLow: 20,
    warningLow: 30,
    optimalLow: 40,
    optimalHigh: 70,
    warningHigh: 85,
    criticalHigh: 95,
    lowRecLow: 'Very dry air. Activate misting or humidifiers immediately.',
    lowRecMid: 'Air is dry. Consider adding humidity to prevent leaf curl.',
    highRecMid: 'High humidity. Improve ventilation to prevent mold.',
    highRecHigh: 'Fungal disease risk! Maximize airflow and ventilation.',
  ),
  _Threshold(
    sensor: 'Light Level',
    icon: Icons.wb_sunny,
    unit: 'lux',
    criticalLow: 50,
    warningLow: 200,
    optimalLow: 300,
    optimalHigh: 800,
    warningHigh: 1000,
    criticalHigh: 1200,
    lowRecLow: 'Insufficient light! Move to brighter area or use grow lights.',
    lowRecMid: 'Light levels are low. Consider supplemental lighting.',
    highRecMid: 'Very bright. Check for leaf burn on sensitive plants.',
    highRecHigh: 'Excessive light! Add shade cloth to prevent scorching.',
  ),
];

// ── Screen ───────────────────────────────────────────────────────────────────

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late final ApiService _api;
  SensorData? _data;
  bool _loading = true;
  Timer? _refreshTimer;
  late AnimationController _staggerController;

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: AppConfig.baseUrl);
    _staggerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fetchData();
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) => _fetchData(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _staggerController.dispose();
    super.dispose();
  }

  Future<void> _fetchData() async {
    try {
      final data = await _api.getLatest();
      if (mounted && data != null) {
        setState(() {
          _data = data;
          _loading = false;
        });
        _staggerController.forward(from: 0);
      } else if (mounted) {
        setState(() => _loading = false);
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<SensorAlert> _generateAlerts() {
    if (_data == null) return [];
    final values = [_data!.soil, _data!.temp, _data!.humidity, _data!.light];
    final alerts = <SensorAlert>[];

    for (int i = 0; i < _thresholds.length; i++) {
      final t = _thresholds[i];
      final v = values[i];

      if (v < t.criticalLow) {
        alerts.add(SensorAlert(
          title: '${t.sensor} Critical Low',
          message: '${v.toStringAsFixed(1)}${t.unit} is far below safe range',
          recommendation: t.lowRecLow,
          severity: AlertSeverity.critical,
          icon: t.icon,
          color: AppColors.red500,
          currentValue: v,
          unit: t.unit,
          optimalMin: t.optimalLow,
          optimalMax: t.optimalHigh,
        ));
      } else if (v < t.warningLow) {
        alerts.add(SensorAlert(
          title: '${t.sensor} Low',
          message: '${v.toStringAsFixed(1)}${t.unit} is below optimal range',
          recommendation: t.lowRecMid,
          severity: AlertSeverity.warning,
          icon: t.icon,
          color: AppColors.amber500,
          currentValue: v,
          unit: t.unit,
          optimalMin: t.optimalLow,
          optimalMax: t.optimalHigh,
        ));
      } else if (v > t.criticalHigh) {
        alerts.add(SensorAlert(
          title: '${t.sensor} Critical High',
          message: '${v.toStringAsFixed(1)}${t.unit} is far above safe range',
          recommendation: t.highRecHigh,
          severity: AlertSeverity.critical,
          icon: t.icon,
          color: AppColors.red500,
          currentValue: v,
          unit: t.unit,
          optimalMin: t.optimalLow,
          optimalMax: t.optimalHigh,
        ));
      } else if (v > t.warningHigh) {
        alerts.add(SensorAlert(
          title: '${t.sensor} High',
          message: '${v.toStringAsFixed(1)}${t.unit} is above optimal range',
          recommendation: t.highRecMid,
          severity: AlertSeverity.warning,
          icon: t.icon,
          color: AppColors.amber500,
          currentValue: v,
          unit: t.unit,
          optimalMin: t.optimalLow,
          optimalMax: t.optimalHigh,
        ));
      }
    }

    // Sort criticals first
    alerts.sort((a, b) => a.severity.index.compareTo(b.severity.index));
    return alerts;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final alerts = _generateAlerts();

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.emerald500,
          onRefresh: _fetchData,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              SliverToBoxAdapter(child: _buildHeader()),
              SliverToBoxAdapter(child: _buildSummaryBanner(alerts, isDark)),
              if (_loading)
                const SliverFillRemaining(
                  child: Center(
                    child: CircularProgressIndicator(
                      color: AppColors.emerald500,
                    ),
                  ),
                )
              else if (alerts.isEmpty)
                SliverFillRemaining(child: _buildAllGood(isDark))
              else
                SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (ctx, i) => _buildAlertCard(alerts[i], i, isDark),
                    childCount: alerts.length,
                  ),
                ),
              const SliverToBoxAdapter(child: SizedBox(height: 24)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final subtitleColor =
        isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
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
                'SMART ALERTS',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Real-time crop health monitoring',
                style: GoogleFonts.inter(fontSize: 12, color: subtitleColor),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryBanner(List<SensorAlert> alerts, bool isDark) {
    final criticals =
        alerts.where((a) => a.severity == AlertSeverity.critical).length;
    final warnings =
        alerts.where((a) => a.severity == AlertSeverity.warning).length;
    final bannerBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        decoration: BoxDecoration(
          color: bannerBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            _summaryChip(
              Icons.error,
              '$criticals',
              'Critical',
              AppColors.red500,
              isDark,
            ),
            const Spacer(),
            _summaryChip(
              Icons.warning_amber_rounded,
              '$warnings',
              'Warning',
              AppColors.amber500,
              isDark,
            ),
            const Spacer(),
            _summaryChip(
              Icons.check_circle,
              '${4 - criticals - warnings}',
              'Healthy',
              AppColors.emerald500,
              isDark,
            ),
          ],
        ),
      ),
    );
  }

  Widget _summaryChip(
    IconData icon,
    String value,
    String label,
    Color color,
    bool isDark,
  ) {
    return Column(
      children: [
        Icon(icon, size: 20, color: color),
        const SizedBox(height: 4),
        Text(
          value,
          style: GoogleFonts.robotoMono(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: color,
          ),
        ),
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 10,
            color: isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4),
          ),
        ),
      ],
    );
  }

  Widget _buildAllGood(bool isDark) {
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: isDark
                    ? AppColors.emerald500.withValues(alpha: 0.15)
                    : AppColors.emerald50,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle_outline,
                size: 64,
                color: AppColors.emerald500,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'All Systems Healthy',
              style: GoogleFonts.inter(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: AppColors.emerald600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'All sensor readings are within optimal ranges.\nYour crops are in great condition!',
              style: GoogleFonts.inter(
                fontSize: 13,
                color: isDark ? Colors.white54 : Colors.black54,
                height: 1.6,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAlertCard(SensorAlert alert, int index, bool isDark) {
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final recBg = isDark
        ? alert.color.withValues(alpha: 0.08)
        : alert.color.withValues(alpha: 0.06);

    // Stagger animation
    final begin = (index * 0.15).clamp(0.0, 0.7);
    final end = (begin + 0.3).clamp(0.0, 1.0);
    final slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _staggerController,
      curve: Interval(begin, end, curve: Curves.easeOutCubic),
    ));
    final fadeAnim = CurvedAnimation(
      parent: _staggerController,
      curve: Interval(begin, end, curve: Curves.easeOut),
    );

    return FadeTransition(
      opacity: fadeAnim,
      child: SlideTransition(
        position: slideAnim,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Container(
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderColor),
              boxShadow: [
                BoxShadow(
                  color: alert.color.withValues(alpha: 0.08),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: alert.color.withValues(alpha: isDark ? 0.2 : 0.1),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(alert.icon, size: 20, color: alert.color),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              alert.title,
                              style: GoogleFonts.inter(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              alert.message,
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                color: isDark ? Colors.white54 : Colors.black54,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Severity badge
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: alert.color.withValues(alpha: isDark ? 0.2 : 0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          alert.severity == AlertSeverity.critical
                              ? 'CRITICAL'
                              : 'WARNING',
                          style: GoogleFonts.robotoMono(
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            color: alert.color,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Range bar
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: _buildRangeBar(alert, isDark),
                ),

                // Recommendation
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: recBg,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.lightbulb_outline,
                          size: 16,
                          color: alert.color,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            alert.recommendation,
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              color: isDark
                                  ? Colors.white.withValues(alpha: 0.7)
                                  : Colors.black.withValues(alpha: 0.7),
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRangeBar(SensorAlert alert, bool isDark) {
    final barBg = isDark
        ? Colors.white.withValues(alpha: 0.06)
        : Colors.black.withValues(alpha: 0.06);
    // Normalize current value position (0-1) within the display range
    final displayMin = alert.optimalMin * 0.5;
    final displayMax = alert.optimalMax * 1.5;
    final range = displayMax - displayMin;
    final normalizedValue =
        ((alert.currentValue - displayMin) / range).clamp(0.0, 1.0);
    final normalizedOptStart =
        ((alert.optimalMin - displayMin) / range).clamp(0.0, 1.0);
    final normalizedOptEnd =
        ((alert.optimalMax - displayMin) / range).clamp(0.0, 1.0);

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Current: ${alert.currentValue.toStringAsFixed(1)}${alert.unit}',
              style: GoogleFonts.robotoMono(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: alert.color,
              ),
            ),
            Text(
              'Optimal: ${alert.optimalMin.toStringAsFixed(0)}-${alert.optimalMax.toStringAsFixed(0)}${alert.unit}',
              style: GoogleFonts.robotoMono(
                fontSize: 11,
                color: isDark ? Colors.white38 : Colors.black38,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        SizedBox(
          height: 8,
          child: Stack(
            children: [
              // Background bar
              Container(
                decoration: BoxDecoration(
                  color: barBg,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              // Optimal zone
              Positioned(
                left: normalizedOptStart *
                    (MediaQuery.of(context).size.width - 64),
                width: (normalizedOptEnd - normalizedOptStart) *
                    (MediaQuery.of(context).size.width - 64),
                top: 0,
                bottom: 0,
                child: Container(
                  decoration: BoxDecoration(
                    color: AppColors.emerald500.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
              // Current value indicator
              Positioned(
                left: normalizedValue *
                        (MediaQuery.of(context).size.width - 64) -
                    4,
                top: 0,
                bottom: 0,
                child: Container(
                  width: 8,
                  decoration: BoxDecoration(
                    color: alert.color,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
