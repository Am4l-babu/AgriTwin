import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../theme/app_theme.dart';

class CropHealthWidget extends StatefulWidget {
  final SensorData data;

  const CropHealthWidget({super.key, required this.data});

  @override
  State<CropHealthWidget> createState() => _CropHealthWidgetState();
}

class _CropHealthWidgetState extends State<CropHealthWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..forward();
  }

  @override
  void didUpdateWidget(covariant CropHealthWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  double _calculateScore() {
    // Individual sensor scores (0-100 each)
    final soilScore = _rangeScore(widget.data.soil, 30, 70, 15, 95);
    final tempScore = _rangeScore(widget.data.temp, 18, 32, 5, 45);
    final humidityScore = _rangeScore(widget.data.humidity, 40, 70, 20, 95);
    final lightScore = _rangeScore(
      widget.data.light,
      30,
      80,
      5,
      100,
    ); // light is 0-100%

    // Weighted average
    return (soilScore * 0.35 +
            tempScore * 0.25 +
            humidityScore * 0.20 +
            lightScore * 0.20)
        .clamp(0, 100);
  }

  double _rangeScore(
    double value,
    double optLow,
    double optHigh,
    double min,
    double max,
  ) {
    if (value >= optLow && value <= optHigh) return 100;
    if (value < optLow) {
      if (value <= min) return 0;
      return ((value - min) / (optLow - min) * 100).clamp(0, 100);
    }
    if (value >= max) return 0;
    return ((max - value) / (max - optHigh) * 100).clamp(0, 100);
  }

  String _label(double score) {
    if (score >= 85) return 'Excellent';
    if (score >= 65) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  }

  Color _scoreColor(double score) {
    if (score >= 85) return AppColors.emerald500;
    if (score >= 65) return AppColors.cyan500;
    if (score >= 40) return AppColors.amber500;
    return AppColors.red500;
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

    final score = _calculateScore();
    final color = _scoreColor(score);
    final label = _label(score);

    // Individual scores for the breakdown
    final soilScore = _rangeScore(widget.data.soil, 30, 70, 15, 95);
    final tempScore = _rangeScore(widget.data.temp, 18, 32, 5, 45);
    final humScore = _rangeScore(widget.data.humidity, 40, 70, 20, 95);
    final lightScore = _rangeScore(
      widget.data.light,
      30,
      80,
      5,
      100,
    ); // light is 0-100%

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor),
      ),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          // Circular gauge
          SizedBox(
            width: 100,
            height: 100,
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final animatedScore =
                    score *
                    CurvedAnimation(
                      parent: _controller,
                      curve: Curves.easeOutCubic,
                    ).value;
                return CustomPaint(
                  painter: _HealthGaugePainter(
                    progress: animatedScore / 100,
                    color: color,
                    bgColor: isDark
                        ? Colors.white.withValues(alpha: 0.06)
                        : Colors.black.withValues(alpha: 0.06),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TweenAnimationBuilder<double>(
                          tween: Tween(end: score),
                          duration: const Duration(milliseconds: 1200),
                          curve: Curves.easeOutCubic,
                          builder: (_, val, __) => Text(
                            val.toStringAsFixed(0),
                            style: GoogleFonts.inter(
                              fontSize: 26,
                              fontWeight: FontWeight.w800,
                              color: color,
                              height: 1,
                            ),
                          ),
                        ),
                        Text(
                          label,
                          style: GoogleFonts.inter(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: color,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(width: 16),

          // Breakdown
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'CROP HEALTH',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                    color: subtitleColor,
                  ),
                ),
                const SizedBox(height: 10),
                _miniBar('Soil', soilScore, AppColors.emerald500, isDark),
                const SizedBox(height: 6),
                _miniBar('Temp', tempScore, AppColors.amber500, isDark),
                const SizedBox(height: 6),
                _miniBar('Humidity', humScore, AppColors.cyan500, isDark),
                const SizedBox(height: 6),
                _miniBar('Light', lightScore, AppColors.yellow500, isDark),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _miniBar(String label, double score, Color color, bool isDark) {
    final labelColor = isDark
        ? Colors.white54
        : Colors.black.withValues(alpha: 0.5);
    final barBg = isDark
        ? Colors.white.withValues(alpha: 0.06)
        : Colors.black.withValues(alpha: 0.06);

    return Row(
      children: [
        SizedBox(
          width: 52,
          child: Text(
            label,
            style: GoogleFonts.inter(fontSize: 11, color: labelColor),
          ),
        ),
        Expanded(
          child: TweenAnimationBuilder<double>(
            tween: Tween(end: score / 100),
            duration: const Duration(milliseconds: 900),
            curve: Curves.easeOutCubic,
            builder: (_, val, __) => ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: SizedBox(
                height: 5,
                child: Stack(
                  children: [
                    Container(color: barBg),
                    FractionallySizedBox(
                      widthFactor: val,
                      child: Container(
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 6),
        SizedBox(
          width: 28,
          child: Text(
            '${score.toStringAsFixed(0)}',
            style: GoogleFonts.robotoMono(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: color,
            ),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    );
  }
}

// ── Custom Arc Painter ─────────────────────────────────────────────────────

class _HealthGaugePainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color bgColor;

  _HealthGaugePainter({
    required this.progress,
    required this.color,
    required this.bgColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 6;
    const startAngle = -math.pi * 0.75;
    const sweepTotal = math.pi * 1.5;

    // Background arc
    final bgPaint = Paint()
      ..color = bgColor
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepTotal,
      false,
      bgPaint,
    );

    // Progress arc with gradient
    if (progress > 0) {
      final sweep = sweepTotal * progress;
      final gradientPaint = Paint()
        ..strokeWidth = 8
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke
        ..shader = SweepGradient(
          startAngle: startAngle,
          endAngle: startAngle + sweep,
          colors: [color.withValues(alpha: 0.5), color],
        ).createShader(Rect.fromCircle(center: center, radius: radius));

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweep,
        false,
        gradientPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _HealthGaugePainter old) =>
      old.progress != progress || old.color != color;
}
