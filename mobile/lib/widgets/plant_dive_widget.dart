import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

/// Total number of rotation frames (same 96 PNGs used by the web dashboard).
const int _totalFrames = 96;

/// Build the asset path for frame index (0-based).
String _framePath(int index) {
  final frameNumber = index + 1; // 1..96
  return 'assets/frames/frame_${frameNumber.toString().padLeft(4, '0')}.png';
}

/// Precache all frames to avoid loading lag.
Future<void> _precacheFrames(BuildContext context) async {
  for (int i = 0; i < _totalFrames; i++) {
    precacheImage(AssetImage(_framePath(i)), context);
  }
}

/// A hero plant animation widget for the dashboard.
/// Auto-plays the frame sequence in a loop, smooth and flicker-free.
/// Users can also swipe/drag to scrub through frames manually.
class PlantDiveWidget extends StatefulWidget {
  const PlantDiveWidget({super.key});

  @override
  State<PlantDiveWidget> createState() => _PlantDiveWidgetState();
}

class _PlantDiveWidgetState extends State<PlantDiveWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  int _currentFrame = 0;
  bool _userDragging = false;
  bool _precached = false;

  // Overlay metrics matching the web dashboard PlantDive
  static const _metrics = [
    {
      'label': 'GROWTH STAGE',
      'value': 'Vegetative',
      'sub': 'Day 14',
      'color': 'emerald',
    },
    {'label': 'WATER DEFICIT', 'value': '12.3', 'sub': 'mm', 'color': 'cyan'},
    {
      'label': 'EVAPOTRANSPIRATION',
      'value': '4.2',
      'sub': 'mm/day',
      'color': 'amber',
    },
    {'label': 'GDD', 'value': '284', 'sub': '°C·d', 'color': 'violet'},
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    );

    _controller.addListener(() {
      if (!_userDragging) {
        final frame = (_controller.value * (_totalFrames - 1)).round().clamp(
          0,
          _totalFrames - 1,
        );
        if (frame != _currentFrame && mounted) {
          setState(() => _currentFrame = frame);
        }
      }
    });

    _controller.repeat();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_precached) {
      _precached = true;
      _precacheFrames(context);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onHorizontalDragStart(DragStartDetails _) {
    _userDragging = true;
    _controller.stop();
  }

  void _onHorizontalDragUpdate(DragUpdateDetails details) {
    final width = context.size?.width ?? 300;
    final delta = details.delta.dx / width;
    final newFrame = (_currentFrame + (delta * _totalFrames).round()).clamp(
      0,
      _totalFrames - 1,
    );
    if (newFrame != _currentFrame) {
      setState(() => _currentFrame = newFrame);
    }
  }

  void _onHorizontalDragEnd(DragEndDetails _) {
    _userDragging = false;
    _controller.value = _currentFrame / (_totalFrames - 1);
    _controller.repeat();
  }

  @override
  Widget build(BuildContext context) {
    final progress = _currentFrame / (_totalFrames - 1);
    // Metrics fade in during the last 30% of the animation
    final metricOpacity = ((progress - 0.7) / 0.3).clamp(0.0, 1.0);

    return GestureDetector(
      onHorizontalDragStart: _onHorizontalDragStart,
      onHorizontalDragUpdate: _onHorizontalDragUpdate,
      onHorizontalDragEnd: _onHorizontalDragEnd,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Container(
          color: Colors.black,
          child: AspectRatio(
            aspectRatio: 16 / 10,
            child: Stack(
              fit: StackFit.expand,
              children: [
                // Frame image — NO AnimatedSwitcher, gaplessPlayback prevents flicker
                Image.asset(
                  _framePath(_currentFrame),
                  fit: BoxFit.cover,
                  gaplessPlayback: true,
                ),

                // Subtle vignette gradient at top & bottom edges
                Positioned.fill(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withValues(alpha: 0.35),
                          Colors.transparent,
                          Colors.transparent,
                          Colors.black.withValues(alpha: 0.5),
                        ],
                        stops: const [0.0, 0.2, 0.7, 1.0],
                      ),
                    ),
                  ),
                ),

                // Corner metrics (appear in last 30% of animation)
                if (metricOpacity > 0) ...[
                  Positioned(
                    top: 10,
                    left: 10,
                    child: Opacity(
                      opacity: metricOpacity,
                      child: _buildMetric(
                        _metrics[0],
                        CrossAxisAlignment.start,
                      ),
                    ),
                  ),
                  Positioned(
                    top: 10,
                    right: 10,
                    child: Opacity(
                      opacity: metricOpacity,
                      child: _buildMetric(_metrics[1], CrossAxisAlignment.end),
                    ),
                  ),
                  Positioned(
                    bottom: 24,
                    left: 10,
                    child: Opacity(
                      opacity: metricOpacity,
                      child: _buildMetric(
                        _metrics[2],
                        CrossAxisAlignment.start,
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 24,
                    right: 10,
                    child: Opacity(
                      opacity: metricOpacity,
                      child: _buildMetric(_metrics[3], CrossAxisAlignment.end),
                    ),
                  ),
                ],

                // Minimal progress bar pinned to bottom
                Positioned(
                  bottom: 6,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Container(
                      width: 80,
                      height: 3,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: FractionallySizedBox(
                          widthFactor: progress,
                          child: Container(
                            decoration: BoxDecoration(
                              color: AppColors.emerald400,
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                      ),
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

  Widget _buildMetric(
    Map<String, String> metric,
    CrossAxisAlignment alignment,
  ) {
    final colorMap = {
      'emerald': AppColors.emerald400,
      'cyan': AppColors.cyan400,
      'amber': AppColors.amber400,
      'violet': AppColors.violet500,
    };
    final color = colorMap[metric['color']] ?? Colors.white;

    return Column(
      crossAxisAlignment: alignment,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          metric['label']!,
          style: GoogleFonts.inter(
            fontSize: 8,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
            color: Colors.white.withValues(alpha: 0.6),
          ),
        ),
        const SizedBox(height: 2),
        Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              metric['value']!,
              style: GoogleFonts.robotoMono(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 3),
            Text(
              metric['sub']!,
              style: GoogleFonts.inter(fontSize: 10, color: color),
            ),
          ],
        ),
      ],
    );
  }
}
