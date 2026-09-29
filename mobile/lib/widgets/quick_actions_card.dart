import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../config/app_config.dart';

class QuickActionsCard extends StatefulWidget {
  const QuickActionsCard({super.key});

  @override
  State<QuickActionsCard> createState() => _QuickActionsCardState();
}

class _QuickActionsCardState extends State<QuickActionsCard> {
  bool _pumpOn = false;
  bool _lightOn = false;
  bool _pumpLoading = false;
  bool _lightLoading = false;

  late final ApiService _api;

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: AppConfig.baseUrl);
  }

  Future<void> _toggleRelay(String relay) async {
    HapticFeedback.mediumImpact();
    final isPump = relay == 'pump';
    final current = isPump ? _pumpOn : _lightOn;
    final newState = !current;

    setState(() {
      if (isPump)
        _pumpLoading = true;
      else
        _lightLoading = true;
    });

    final ok = await _api.controlRelay(
      relay: relay,
      state: newState ? 'on' : 'off',
    );

    if (!mounted) return;
    setState(() {
      if (isPump) {
        _pumpLoading = false;
        if (ok) _pumpOn = newState;
      } else {
        _lightLoading = false;
        if (ok) _lightOn = newState;
      }
    });
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
            'QUICK ACTIONS',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: labelColor,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _ActionButton(
                  icon: Icons.water_drop,
                  label: 'Pump',
                  isOn: _pumpOn,
                  loading: _pumpLoading,
                  activeColor: AppColors.cyan500,
                  isDark: isDark,
                  onTap: () => _toggleRelay('pump'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _ActionButton(
                  icon: Icons.lightbulb_outline,
                  label: 'Light',
                  isOn: _lightOn,
                  loading: _lightLoading,
                  activeColor: AppColors.yellow500,
                  isDark: isDark,
                  onTap: () => _toggleRelay('light'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool isOn;
  final bool loading;
  final Color activeColor;
  final bool isDark;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.isOn,
    this.loading = false,
    required this.activeColor,
    required this.isDark,
    required this.onTap,
  });

  @override
  State<_ActionButton> createState() => _ActionButtonState();
}

class _ActionButtonState extends State<_ActionButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  double _scale = 1.0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
  }

  @override
  void didUpdateWidget(covariant _ActionButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isOn != widget.isOn) {
      _controller.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bgColor = widget.isOn
        ? widget.activeColor.withValues(alpha: widget.isDark ? 0.2 : 0.12)
        : (widget.isDark
              ? Colors.white.withValues(alpha: 0.04)
              : Colors.black.withValues(alpha: 0.03));
    final iconColor = widget.isOn
        ? widget.activeColor
        : (widget.isDark ? Colors.white38 : Colors.black38);
    final labelColor = widget.isOn
        ? widget.activeColor
        : (widget.isDark ? Colors.white54 : Colors.black54);
    final statusColor = widget.isOn ? widget.activeColor : Colors.transparent;

    return GestureDetector(
      onTapDown: widget.loading ? null : (_) => setState(() => _scale = 0.92),
      onTapUp: widget.loading
          ? null
          : (_) {
              setState(() => _scale = 1.0);
              widget.onTap();
            },
      onTapCancel: () => setState(() => _scale = 1.0),
      child: AnimatedScale(
        scale: _scale,
        duration: const Duration(milliseconds: 100),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(12),
            border: widget.isOn
                ? Border.all(color: widget.activeColor.withValues(alpha: 0.3))
                : null,
          ),
          child: Column(
            children: [
              // Animated icon with bounce
              AnimatedBuilder(
                animation: _controller,
                builder: (_, child) {
                  final bounce = TweenSequence<double>([
                    TweenSequenceItem(
                      tween: Tween(begin: 1.0, end: 1.3),
                      weight: 40,
                    ),
                    TweenSequenceItem(
                      tween: Tween(begin: 1.3, end: 1.0),
                      weight: 60,
                    ),
                  ]).animate(_controller);

                  return Transform.scale(
                    scale: _controller.isAnimating ? bounce.value : 1.0,
                    child: child,
                  );
                },
                child: Icon(widget.icon, size: 24, color: iconColor),
              ),
              const SizedBox(height: 6),
              Text(
                widget.label,
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: labelColor,
                ),
              ),
              const SizedBox(height: 4),
              // Status dot or loading indicator
              widget.loading
                  ? SizedBox(
                      width: 12,
                      height: 12,
                      child: CircularProgressIndicator(
                        strokeWidth: 1.5,
                        color: widget.activeColor,
                      ),
                    )
                  : AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: statusColor,
                        shape: BoxShape.circle,
                        boxShadow: widget.isOn
                            ? [
                                BoxShadow(
                                  color: widget.activeColor.withValues(
                                    alpha: 0.5,
                                  ),
                                  blurRadius: 6,
                                ),
                              ]
                            : null,
                      ),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}
