import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'theme/app_theme.dart';
import 'theme/theme_notifier.dart';
import 'screens/splash_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/history_screen.dart';
import 'screens/calibration_screen.dart';
import 'screens/alerts_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/ai_assistant_screen.dart';
import 'screens/dt_brain_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await themeNotifier.load();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  runApp(const SmartFarmApp());
}

class SmartFarmApp extends StatelessWidget {
  const SmartFarmApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: themeNotifier,
      builder: (context, _) {
        final isDark = themeNotifier.isDark;

        // Update system UI overlay style based on theme
        SystemChrome.setSystemUIOverlayStyle(
          isDark ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark,
        );

        return MaterialApp(
          title: 'AgriTwin',
          debugShowCheckedModeBanner: false,
          themeMode: themeNotifier.mode,

          // ── Light Theme ──
          theme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: AppColors.emerald500,
            brightness: Brightness.light,
            scaffoldBackgroundColor: AppColors.background,
            textTheme: GoogleFonts.interTextTheme(
              ThemeData(brightness: Brightness.light).textTheme,
            ),
            appBarTheme: AppBarTheme(
              backgroundColor: Colors.white,
              foregroundColor: Colors.black,
              elevation: 0,
              scrolledUnderElevation: 1,
              titleTextStyle: GoogleFonts.inter(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.black,
              ),
            ),
            cardTheme: CardThemeData(
              color: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.surfaceBorder),
              ),
            ),
            pageTransitionsTheme: const PageTransitionsTheme(
              builders: {
                TargetPlatform.android: CupertinoPageTransitionsBuilder(),
                TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
              },
            ),
          ),

          // ── Dark Theme ──
          darkTheme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: AppColors.emerald500,
            brightness: Brightness.dark,
            scaffoldBackgroundColor: const Color(0xFF0F1419),
            textTheme: GoogleFonts.interTextTheme(
              ThemeData(brightness: Brightness.dark).textTheme,
            ),
            appBarTheme: AppBarTheme(
              backgroundColor: const Color(0xFF1A1F2E),
              foregroundColor: Colors.white,
              elevation: 0,
              scrolledUnderElevation: 1,
              titleTextStyle: GoogleFonts.inter(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            cardTheme: CardThemeData(
              color: const Color(0xFF1A1F2E),
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
              ),
            ),
            pageTransitionsTheme: const PageTransitionsTheme(
              builders: {
                TargetPlatform.android: CupertinoPageTransitionsBuilder(),
                TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
              },
            ),
          ),

          home: SplashScreen(nextScreen: const AppShell()),
        );
      },
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> with TickerProviderStateMixin {
  int _currentIndex = 0;
  late final List<AnimationController> _iconControllers;
  late PageController _pageController;

  final _pages = const [
    DashboardScreen(),
    HistoryScreen(),
    CameraScreen(),
    CalibrationScreen(),
    AiAssistantScreen(),
    DtBrainScreen(),
    AlertsScreen(),
    SettingsScreen(),
  ];

  static const _navItems = [
    _NavItem(Icons.dashboard_outlined, Icons.dashboard, 'Dashboard'),
    _NavItem(Icons.show_chart_outlined, Icons.show_chart, 'History'),
    _NavItem(Icons.camera_alt_outlined, Icons.camera_alt, 'Camera'),
    _NavItem(Icons.tune_outlined, Icons.tune, 'Calibrate'),
    _NavItem(Icons.auto_awesome_outlined, Icons.auto_awesome, 'AI'),
    _NavItem(Icons.psychology_outlined, Icons.psychology, 'DT Brain'),
    _NavItem(Icons.notifications_outlined, Icons.notifications, 'Alerts'),
    _NavItem(Icons.settings_outlined, Icons.settings, 'Settings'),
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: 0);
    _iconControllers = List.generate(
      8,
      (i) => AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 400),
      ),
    );
    _iconControllers[0].forward(from: 0);
  }

  @override
  void dispose() {
    _pageController.dispose();
    for (final c in _iconControllers) {
      c.dispose();
    }
    super.dispose();
  }

  void _onNavTap(int index) {
    if (index == _currentIndex) return;
    HapticFeedback.lightImpact();
    _iconControllers[index].forward(from: 0);
    setState(() => _currentIndex = index);
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final navBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final unselectedColor = isDark ? Colors.white54 : Colors.black54;
    final unselectedLabelColor = isDark ? Colors.white38 : Colors.black45;

    return Scaffold(
      body: PageView(
        controller: _pageController,
        physics: const NeverScrollableScrollPhysics(),
        children: _pages,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: navBg,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: isDark ? 0.3 : 0.05),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.start,
              children: List.generate(8, (i) {
                final item = _navItems[i];
                final isSelected = i == _currentIndex;
                return SizedBox(
                  width: 72,
                  child: _AnimatedNavItem(
                    item: item,
                    isSelected: isSelected,
                    controller: _iconControllers[i],
                    onTap: () => _onNavTap(i),
                    unselectedColor: unselectedColor,
                    unselectedLabelColor: unselectedLabelColor,
                  ),
                );
              }),
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  final IconData outlinedIcon;
  final IconData filledIcon;
  final String label;

  const _NavItem(this.outlinedIcon, this.filledIcon, this.label);
}

class _AnimatedNavItem extends StatelessWidget {
  final _NavItem item;
  final bool isSelected;
  final AnimationController controller;
  final VoidCallback onTap;
  final Color unselectedColor;
  final Color unselectedLabelColor;

  const _AnimatedNavItem({
    required this.item,
    required this.isSelected,
    required this.controller,
    required this.onTap,
    required this.unselectedColor,
    required this.unselectedLabelColor,
  });

  @override
  Widget build(BuildContext context) {
    final bounceAnimation = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 1.3), weight: 40),
      TweenSequenceItem(tween: Tween(begin: 1.3, end: 0.9), weight: 30),
      TweenSequenceItem(tween: Tween(begin: 0.9, end: 1.0), weight: 30),
    ]).animate(CurvedAnimation(parent: controller, curve: Curves.easeInOut));

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.emerald500.withValues(alpha: 0.1)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedBuilder(
              animation: controller,
              builder: (context, child) {
                return Transform.scale(
                  scale: controller.isAnimating ? bounceAnimation.value : 1.0,
                  child: child,
                );
              },
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                transitionBuilder: (child, animation) {
                  return ScaleTransition(scale: animation, child: child);
                },
                child: Icon(
                  isSelected ? item.filledIcon : item.outlinedIcon,
                  key: ValueKey(isSelected),
                  size: 22,
                  color: isSelected ? AppColors.emerald600 : unselectedColor,
                ),
              ),
            ),
            const SizedBox(height: 4),
            AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: GoogleFonts.inter(
                fontSize: isSelected ? 11 : 10,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                color: isSelected ? AppColors.emerald600 : unselectedLabelColor,
              ),
              child: Text(item.label),
            ),
          ],
        ),
      ),
    );
  }
}
