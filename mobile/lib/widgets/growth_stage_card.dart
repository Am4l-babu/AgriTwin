import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../theme/app_theme.dart';

class GrowthStageCard extends StatelessWidget {
  final SensorData data;

  const GrowthStageCard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final labelColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);
    final iconBg = isDark
        ? AppColors.emerald500.withValues(alpha: 0.15)
        : AppColors.emerald50;

    // Derive growth metrics from sensor data
    final biomass =
        ((data.soil * 0.4 + data.humidity * 0.3 + (data.light / 10) * 0.3))
            .clamp(0, 100)
            .toDouble() /
        100;
    final rootDensity =
        ((data.soil * 0.7 + data.temp * 0.3)).clamp(0, 100).toDouble() / 100;
    final leafArea =
        ((data.light / 10 * 0.5 + data.humidity * 0.5))
            .clamp(0, 100)
            .toDouble() /
        100;

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
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.eco,
                  size: 18,
                  color: AppColors.emerald500,
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'GROWTH STAGE',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                      color: labelColor,
                    ),
                  ),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 400),
                    child: Text(
                      _growthPhase,
                      key: ValueKey(_growthPhase),
                      style: GoogleFonts.inter(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.emerald600,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Animated progress bars
          _AnimatedProgressRow(
            label: 'Biomass',
            progress: biomass,
            color: AppColors.emerald500,
            delay: Duration.zero,
          ),
          const SizedBox(height: 10),
          _AnimatedProgressRow(
            label: 'Root Density',
            progress: rootDensity,
            color: AppColors.amber500,
            delay: const Duration(milliseconds: 150),
          ),
          const SizedBox(height: 10),
          _AnimatedProgressRow(
            label: 'Leaf Area',
            progress: leafArea,
            color: AppColors.cyan500,
            delay: const Duration(milliseconds: 300),
          ),
        ],
      ),
    );
  }

  String get _growthPhase {
    if (data.soil > 50 && data.temp > 20 && data.light > 300) {
      return 'Vegetative Growth';
    } else if (data.soil > 30 && data.temp > 15) {
      return 'Early Growth';
    } else {
      return 'Seedling';
    }
  }
}

/// A progress row that animates its bar width from 0 → target
class _AnimatedProgressRow extends StatefulWidget {
  final String label;
  final double progress;
  final Color color;
  final Duration delay;

  const _AnimatedProgressRow({
    required this.label,
    required this.progress,
    required this.color,
    required this.delay,
  });

  @override
  State<_AnimatedProgressRow> createState() => _AnimatedProgressRowState();
}

class _AnimatedProgressRowState extends State<_AnimatedProgressRow>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
    // Start with a delay for stagger effect
    Future.delayed(widget.delay, () {
      if (mounted) {
        _started = true;
        _controller.forward();
      }
    });
  }

  @override
  void didUpdateWidget(covariant _AnimatedProgressRow oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.progress != widget.progress && _started) {
      _controller.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final labelColor = isDark ? Colors.white54 : Colors.black.withValues(alpha: 0.5);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              widget.label,
              style: GoogleFonts.inter(
                fontSize: 12,
                color: labelColor,
              ),
            ),
            TweenAnimationBuilder<double>(
              tween: Tween<double>(end: widget.progress * 100),
              duration: const Duration(milliseconds: 800),
              curve: Curves.easeOutCubic,
              builder: (context, value, _) {
                return Text(
                  '${value.toStringAsFixed(0)}%',
                  style: GoogleFonts.robotoMono(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: widget.color,
                  ),
                );
              },
            ),
          ],
        ),
        const SizedBox(height: 4),
        AnimatedBuilder(
          animation: _animation,
          builder: (context, _) {
            return ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: SizedBox(
                height: 6,
                child: Stack(
                  children: [
                    // Background
                    Container(
                      decoration: BoxDecoration(
                        color: widget.color.withValues(alpha: isDark ? 0.15 : 0.1),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    // Animated fill
                    FractionallySizedBox(
                      widthFactor: widget.progress * _animation.value,
                      child: Container(
                        decoration: BoxDecoration(
                          color: widget.color,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }
}
