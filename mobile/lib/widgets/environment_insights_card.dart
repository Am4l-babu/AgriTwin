import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../theme/app_theme.dart';

class EnvironmentInsightsCard extends StatefulWidget {
  final SensorData data;

  const EnvironmentInsightsCard({super.key, required this.data});

  @override
  State<EnvironmentInsightsCard> createState() =>
      _EnvironmentInsightsCardState();
}

class _EnvironmentInsightsCardState extends State<EnvironmentInsightsCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _staggerController;

  @override
  void initState() {
    super.initState();
    _staggerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..forward();
  }

  @override
  void dispose() {
    _staggerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final labelColor = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);

    // Derived environmental metrics
    final vpd = _calculateVPD(widget.data.temp, widget.data.humidity);
    // DLI: light% × 0.389 mol/m²/day
    // Assumes 100% ≈ 900 μmol/m²/s PPFD, 12hr photoperiod:
    // DLI = (light/100 × 900) × 12 × 3600 / 1e6 = light × 0.389
    final dli = (widget.data.light * 0.389).clamp(0.0, 60.0);
    final et = _calculateET(
      widget.data.temp,
      widget.data.humidity,
      widget.data.light,
    );

    return Container(
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
            'ENVIRONMENT INSIGHTS',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: labelColor,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStaggeredTile(
                  index: 0,
                  label: 'VPD',
                  value: '${vpd.toStringAsFixed(2)} kPa',
                  icon: Icons.air,
                  color: AppColors.violet500,
                  bgColor: AppColors.violet50,
                  status: _vpdStatus(vpd),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStaggeredTile(
                  index: 1,
                  label: 'DLI',
                  value: '${dli.toStringAsFixed(1)} mol',
                  icon: Icons.wb_sunny_outlined,
                  color: AppColors.yellow500,
                  bgColor: AppColors.yellow50,
                  status: _dliStatus(dli),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStaggeredTile(
                  index: 2,
                  label: 'ET',
                  value: '${et.toStringAsFixed(1)} mm',
                  icon: Icons.opacity,
                  color: AppColors.cyan500,
                  bgColor: AppColors.cyan50,
                  status: _etStatus(et),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStaggeredTile({
    required int index,
    required String label,
    required String value,
    required IconData icon,
    required Color color,
    required Color bgColor,
    required String status,
  }) {
    // Each tile has a staggered interval
    final begin = index * 0.2;
    final end = (begin + 0.6).clamp(0.0, 1.0);

    final slideAnimation =
        Tween<Offset>(begin: const Offset(0.0, 0.3), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _staggerController,
            curve: Interval(begin, end, curve: Curves.easeOutCubic),
          ),
        );

    final fadeAnimation = CurvedAnimation(
      parent: _staggerController,
      curve: Interval(begin, end, curve: Curves.easeOut),
    );

    return AnimatedBuilder(
      animation: _staggerController,
      builder: (context, _) {
        return FadeTransition(
          opacity: fadeAnimation,
          child: SlideTransition(
            position: slideAnimation,
            child: _insightTile(label, value, icon, color, bgColor, status),
          ),
        );
      },
    );
  }

  Widget _insightTile(
    String label,
    String value,
    IconData icon,
    Color color,
    Color bgColor,
    String status,
  ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tileBg = isDark
        ? color.withValues(alpha: 0.12)
        : bgColor.withValues(alpha: 0.5);
    final tileLabel = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final statusBg = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : Colors.white.withValues(alpha: 0.7);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: tileBg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(height: 8),
          Text(
            value,
            style: GoogleFonts.robotoMono(
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 1,
              color: tileLabel,
            ),
          ),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: statusBg,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              status,
              style: GoogleFonts.inter(
                fontSize: 9,
                fontWeight: FontWeight.w500,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // VPD = Vapor Pressure Deficit using Tetens formula
  double _calculateVPD(double temp, double humidity) {
    final svp = 0.6108 * math.exp(17.27 * temp / (temp + 237.3));
    return svp * (1 - humidity / 100);
  }

  // Simplified Penman-Monteith evapotranspiration (mm/day)
  // Calibrated: at T=28°C, H=62%, L=80% → ~4mm/day
  double _calculateET(double temp, double humidity, double light) {
    return (0.288 * (temp + 17.8) * (light / 100) * (100 - humidity) / 100)
        .clamp(0, 20);
  }

  String _vpdStatus(double vpd) {
    if (vpd < 0.4) return 'Low';
    if (vpd < 1.2) return 'Optimal';
    return 'High';
  }

  String _dliStatus(double dli) {
    if (dli < 10) return 'Low';
    if (dli < 30) return 'Optimal';
    return 'High';
  }

  String _etStatus(double et) {
    if (et < 2) return 'Low';
    if (et < 6) return 'Normal';
    return 'High';
  }
}
