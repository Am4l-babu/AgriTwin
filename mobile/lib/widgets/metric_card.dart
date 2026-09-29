import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shimmer/shimmer.dart';
import '../theme/app_theme.dart';
import 'animated_components.dart';

class MetricCard extends StatefulWidget {
  final String label;
  final double value;
  final String unit;
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String status;
  final Color statusColor;
  final bool isLoading;
  final AnimationController pulseAnimation;

  const MetricCard({
    super.key,
    required this.label,
    required this.value,
    required this.unit,
    required this.icon,
    required this.color,
    required this.bgColor,
    required this.status,
    required this.statusColor,
    required this.isLoading,
    required this.pulseAnimation,
  });

  @override
  State<MetricCard> createState() => _MetricCardState();
}

class _MetricCardState extends State<MetricCard> {
  double _scale = 1.0;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final labelColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);
    final unitColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);
    final shimmerBase = isDark ? const Color(0xFF1A1F2E) : AppColors.slate100;
    final shimmerHighlight = isDark ? const Color(0xFF252B3B) : Colors.white;
    // In dark mode, use a slightly tinted bg for the icon
    final iconBg = isDark
        ? widget.color.withValues(alpha: 0.15)
        : widget.bgColor;

    if (widget.isLoading) {
      return Shimmer.fromColors(
        baseColor: shimmerBase,
        highlightColor: shimmerHighlight,
        child: Container(
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      );
    }

    return GestureDetector(
      onTapDown: (_) => setState(() => _scale = 0.96),
      onTapUp: (_) => setState(() => _scale = 1.0),
      onTapCancel: () => setState(() => _scale = 1.0),
      child: AnimatedScale(
        scale: _scale,
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOutCubic,
        child: AnimatedBuilder(
          animation: widget.pulseAnimation,
          builder: (context, child) {
            return Container(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: borderColor),
                boxShadow: [
                  BoxShadow(
                    color: widget.color.withValues(
                      alpha: 0.06 + widget.pulseAnimation.value * 0.04,
                    ),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top: icon + status badge
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: iconBg,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: BounceIcon(icon: widget.icon, size: 20, color: widget.color),
                      ),
                      const Spacer(),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 300),
                        transitionBuilder: (child, animation) {
                          return FadeTransition(
                            opacity: animation,
                            child: SlideTransition(
                              position: Tween<Offset>(
                                begin: const Offset(0.0, -0.3),
                                end: Offset.zero,
                              ).animate(animation),
                              child: child,
                            ),
                          );
                        },
                        child: Container(
                          key: ValueKey(widget.status),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: widget.statusColor.withValues(alpha: isDark ? 0.2 : 0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            widget.status,
                            style: GoogleFonts.inter(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: widget.statusColor,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Label
                  Text(
                    widget.label,
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.5,
                      color: labelColor,
                    ),
                  ),
                  const SizedBox(height: 4),
                  // Animated value (number ticker)
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Flexible(
                        child: TweenAnimationBuilder<double>(
                          tween: Tween<double>(end: widget.value),
                          duration: const Duration(milliseconds: 600),
                          curve: Curves.easeOutCubic,
                          builder: (context, animatedValue, _) {
                            return Text(
                              animatedValue.toStringAsFixed(1),
                              style: GoogleFonts.inter(
                                fontSize: 28,
                                fontWeight: FontWeight.w500,
                                height: 1,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            );
                          },
                        ),
                      ),
                      const SizedBox(width: 4),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 3),
                        child: Text(
                          widget.unit,
                          style: GoogleFonts.robotoMono(
                            fontSize: 13,
                            color: unitColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
