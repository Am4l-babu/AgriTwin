import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// A reusable bounce-animated button wrapper.
/// Adds a satisfying scale animation on press with optional haptic feedback.
class BounceButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final double scaleDown;
  final bool haptic;

  const BounceButton({
    super.key,
    required this.child,
    this.onPressed,
    this.scaleDown = 0.95,
    this.haptic = true,
  });

  @override
  State<BounceButton> createState() => _BounceButtonState();
}

class _BounceButtonState extends State<BounceButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 120),
      reverseDuration: const Duration(milliseconds: 200),
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: widget.scaleDown,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
      reverseCurve: Curves.easeOutBack,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails _) {
    _controller.forward();
  }

  void _onTapUp(TapUpDetails _) {
    _controller.reverse();
    if (widget.haptic) HapticFeedback.lightImpact();
    widget.onPressed?.call();
  }

  void _onTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: widget.child,
      ),
    );
  }
}

/// An icon that spins on tap — perfect for refresh/settings icons.
class SpinIcon extends StatefulWidget {
  final IconData icon;
  final double size;
  final Color? color;
  final VoidCallback? onTap;
  final bool spinning;

  const SpinIcon({
    super.key,
    required this.icon,
    this.size = 20,
    this.color,
    this.onTap,
    this.spinning = false,
  });

  @override
  State<SpinIcon> createState() => _SpinIconState();
}

class _SpinIconState extends State<SpinIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    if (widget.spinning) _controller.repeat();
  }

  @override
  void didUpdateWidget(covariant SpinIcon oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.spinning && !oldWidget.spinning) {
      _controller.repeat();
    } else if (!widget.spinning && oldWidget.spinning) {
      _controller.forward().then((_) {
        if (mounted) _controller.reset();
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTap() {
    if (!_controller.isAnimating) {
      _controller.forward(from: 0).then((_) {
        if (mounted) _controller.reset();
      });
    }
    HapticFeedback.lightImpact();
    widget.onTap?.call();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _handleTap,
      child: RotationTransition(
        turns: _controller,
        child: Icon(widget.icon, size: widget.size, color: widget.color),
      ),
    );
  }
}

/// An icon that gives a jelly bounce on-appear or on-tap.
class BounceIcon extends StatefulWidget {
  final IconData icon;
  final double size;
  final Color? color;
  final bool animateOnAppear;

  const BounceIcon({
    super.key,
    required this.icon,
    this.size = 20,
    this.color,
    this.animateOnAppear = true,
  });

  @override
  State<BounceIcon> createState() => _BounceIconState();
}

class _BounceIconState extends State<BounceIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _bounceAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _bounceAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
    );
    if (widget.animateOnAppear) {
      _controller.forward();
    } else {
      _controller.value = 1.0;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _bounceAnimation,
      child: Icon(widget.icon, size: widget.size, color: widget.color),
    );
  }
}
