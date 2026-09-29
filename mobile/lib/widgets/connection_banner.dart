import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_theme.dart';

class ConnectionBanner extends StatelessWidget {
  final bool connected;

  const ConnectionBanner({super.key, required this.connected});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bannerBg = isDark ? const Color(0xFF2D1B1B) : const Color(0xFFFEF2F2);

    return AnimatedSlide(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeInOut,
      offset: connected ? const Offset(0, -1) : Offset.zero,
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
        opacity: connected ? 0.0 : 1.0,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 400),
          curve: Curves.easeInOut,
          height: connected ? 0 : 40,
          child: connected
              ? const SizedBox.shrink()
              : Container(
                  margin:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  decoration: BoxDecoration(
                    color: bannerBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: AppColors.red400.withValues(alpha: 0.3),
                    ),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.cloud_off,
                        size: 14,
                        color: AppColors.red500,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'No server connection — check Settings',
                          style: GoogleFonts.inter(
                            fontSize: 12,
                            color: AppColors.red500,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
