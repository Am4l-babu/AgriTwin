import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../theme/app_theme.dart';

/// Displays ML-powered plant health and irrigation insights.
class MlPredictionCard extends StatelessWidget {
  final MlEnsembleResult? ensemble;
  final IrrigationRecommendation? irrigation;
  final bool isLoading;

  const MlPredictionCard({
    super.key,
    this.ensemble,
    this.irrigation,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1E1E2E) : AppColors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final labelColor = isDark ? Colors.white54 : Colors.black45;

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.3 : 0.06),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ──
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(7),
                  decoration: BoxDecoration(
                    color: AppColors.violet50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.psychology,
                    color: AppColors.violet500,
                    size: 16,
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  'ML INSIGHTS',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.0,
                    color: isDark ? Colors.white : Colors.black87,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.violet500.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'AI',
                    style: GoogleFonts.robotoMono(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: AppColors.violet600,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 14),

            if (isLoading) ...[
              _LoadingRow(),
              const SizedBox(height: 10),
              _LoadingRow(width: 200),
            ] else if (ensemble == null && irrigation == null) ...[
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    'ML predictions unavailable — check server',
                    style: GoogleFonts.inter(fontSize: 12, color: labelColor),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ] else ...[
              // ── Plant Health ──
              if (ensemble != null) ...[
                _SectionLabel(label: 'PLANT HEALTH', labelColor: labelColor),
                const SizedBox(height: 6),
                _HealthBadge(result: ensemble!),
                const SizedBox(height: 14),
              ],

              // ── Irrigation ──
              if (irrigation != null) ...[
                _SectionLabel(
                  label: 'IRRIGATION RECOMMENDATION',
                  labelColor: labelColor,
                ),
                const SizedBox(height: 6),
                _IrrigationRow(rec: irrigation!),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

// ── Sub-widgets ──────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  final Color labelColor;
  const _SectionLabel({required this.label, required this.labelColor});

  @override
  Widget build(BuildContext context) => Text(
    label,
    style: GoogleFonts.inter(
      fontSize: 10,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.8,
      color: labelColor,
    ),
  );
}

class _HealthBadge extends StatelessWidget {
  final MlEnsembleResult result;
  const _HealthBadge({required this.result});

  Color get _color {
    switch (result.plantHealthLabel) {
      case 'Healthy':
        return AppColors.emerald500;
      case 'Moderate Stress':
        return AppColors.amber500;
      default:
        return AppColors.red500;
    }
  }

  IconData get _icon {
    switch (result.plantHealthLabel) {
      case 'Healthy':
        return Icons.check_circle_outline;
      case 'Moderate Stress':
        return Icons.warning_amber_outlined;
      default:
        return Icons.error_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(_icon, color: _color, size: 20),
        const SizedBox(width: 8),
        Text(
          result.plantHealthLabel,
          style: GoogleFonts.inter(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: _color,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '${(result.confidence * 100).toStringAsFixed(0)}% confidence',
          style: GoogleFonts.inter(
            fontSize: 11,
            color: _color.withValues(alpha: 0.7),
          ),
        ),
      ],
    );
  }
}

class _IrrigationRow extends StatelessWidget {
  final IrrigationRecommendation rec;
  const _IrrigationRow({required this.rec});

  Color get _actionColor {
    switch (rec.actionId) {
      case 0:
        return AppColors.emerald500;
      case 1:
        return AppColors.cyan500;
      case 2:
        return AppColors.amber500;
      default:
        return AppColors.red500;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _actionColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.water_drop, color: _actionColor, size: 14),
                  const SizedBox(width: 5),
                  Text(
                    rec.action.toUpperCase(),
                    style: GoogleFonts.robotoMono(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: _actionColor,
                    ),
                  ),
                ],
              ),
            ),
            if (rec.waterAmount > 0) ...[
              const SizedBox(width: 8),
              Text(
                '${rec.waterAmount} mL',
                style: GoogleFonts.inter(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: _actionColor,
                ),
              ),
            ],
          ],
        ),
        const SizedBox(height: 6),
        Text(
          rec.reason,
          style: GoogleFonts.inter(
            fontSize: 12,
            color: isDark ? Colors.white60 : Colors.black54,
          ),
        ),
      ],
    );
  }
}

class _LoadingRow extends StatelessWidget {
  final double width;
  const _LoadingRow({this.width = 150});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 14,
      width: width,
      decoration: BoxDecoration(
        color: AppColors.slate200,
        borderRadius: BorderRadius.circular(7),
      ),
    );
  }
}
