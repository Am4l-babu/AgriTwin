import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/sensor_data.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../theme/app_theme.dart';
import '../widgets/metric_card.dart';
import '../widgets/connection_banner.dart';
import '../widgets/growth_stage_card.dart';
import '../widgets/environment_insights_card.dart';
import '../widgets/plant_dive_widget.dart';
import '../widgets/animated_components.dart';
import '../widgets/crop_health_widget.dart';
import '../widgets/quick_actions_card.dart';
import '../widgets/ml_prediction_card.dart';
import '../config/app_config.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  late final ApiService _api;
  late final WebSocketService _ws;
  StreamSubscription<SensorData>? _dataSub;
  StreamSubscription<bool>? _connSub;

  SensorData _data = const SensorData();
  bool _connected = false;
  bool _initialLoading = true;
  Timer? _pollTimer;
  late AnimationController _pulseController;
  DateTime? _lastUpdated;

  // ── ML Predictions ──
  IrrigationRecommendation? _irrigation;
  MlEnsembleResult? _mlEnsemble;
  bool _mlLoading = false;

  // ── Staggered entry animation ──
  late AnimationController _entryController;
  late Animation<double> _headerFade;
  late Animation<Offset> _headerSlide;
  // 4 metric cards — individual fade + slide
  late List<Animation<double>> _cardFades;
  late List<Animation<Offset>> _cardSlides;
  // Growth stage card
  late Animation<double> _growthFade;
  late Animation<Offset> _growthSlide;
  // Environment insights card
  late Animation<double> _insightsFade;
  late Animation<Offset> _insightsSlide;

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: AppConfig.baseUrl);
    _ws = WebSocketService(url: AppConfig.wsUrl);

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    // ── Entry stagger setup (1200ms total) ──
    _entryController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    // Header: 0.0 → 0.25
    _headerFade = CurvedAnimation(
      parent: _entryController,
      curve: const Interval(0.0, 0.25, curve: Curves.easeOut),
    );
    _headerSlide = Tween<Offset>(begin: const Offset(0, -0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entryController,
            curve: const Interval(0.0, 0.3, curve: Curves.easeOutCubic),
          ),
        );

    // 4 metric cards: staggered from 0.1 → 0.7
    _cardFades = List.generate(4, (i) {
      final start = 0.1 + i * 0.1;
      final end = (start + 0.3).clamp(0.0, 1.0);
      return CurvedAnimation(
        parent: _entryController,
        curve: Interval(start, end, curve: Curves.easeOut),
      );
    });
    _cardSlides = List.generate(4, (i) {
      final start = 0.1 + i * 0.1;
      final end = (start + 0.35).clamp(0.0, 1.0);
      return Tween<Offset>(
        begin: const Offset(0, 0.25),
        end: Offset.zero,
      ).animate(
        CurvedAnimation(
          parent: _entryController,
          curve: Interval(start, end, curve: Curves.easeOutCubic),
        ),
      );
    });

    // Growth stage: 0.45 → 0.8
    _growthFade = CurvedAnimation(
      parent: _entryController,
      curve: const Interval(0.45, 0.8, curve: Curves.easeOut),
    );
    _growthSlide = Tween<Offset>(begin: const Offset(0, 0.2), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entryController,
            curve: const Interval(0.45, 0.85, curve: Curves.easeOutCubic),
          ),
        );

    // Insights: 0.6 → 1.0
    _insightsFade = CurvedAnimation(
      parent: _entryController,
      curve: const Interval(0.6, 1.0, curve: Curves.easeOut),
    );
    _insightsSlide =
        Tween<Offset>(begin: const Offset(0, 0.2), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _entryController,
            curve: const Interval(0.6, 1.0, curve: Curves.easeOutCubic),
          ),
        );

    // Start the entry animation
    _entryController.forward();

    _dataSub = _ws.sensorStream.listen((d) {
      if (mounted) {
        setState(() {
          _data = d;
          _initialLoading = false;
          _lastUpdated = DateTime.now();
        });
      }
    });
    _connSub = _ws.connectionStream.listen((c) {
      if (mounted) setState(() => _connected = c);
    });

    _ws.connect();
    _fetchLatest();
    // Poll REST every 10 s so values stay fresh even if WS is quiet
    _pollTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) => _fetchLatest(),
    );
  }

  Future<void> _fetchLatest() async {
    try {
      final latest = await _api.getLatest();
      if (latest != null && mounted) {
        setState(() {
          _data = latest;
          _initialLoading = false;
          _lastUpdated = DateTime.now();
        });
        _fetchMlPredictions(latest);
      }
    } catch (_) {}
  }

  Future<void> _fetchMlPredictions(SensorData data) async {
    if (_mlLoading) return;
    if (mounted) setState(() => _mlLoading = true);
    try {
      final results = await Future.wait([
        _api.getMlEnsemble(data),
        _api.getIrrigationRecommendation(data),
      ]);
      if (mounted) {
        setState(() {
          _mlEnsemble = results[0] as MlEnsembleResult?;
          _irrigation = results[1] as IrrigationRecommendation?;
          _mlLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _mlLoading = false);
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _dataSub?.cancel();
    _connSub?.cancel();
    _ws.dispose();
    _pulseController.dispose();
    _entryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.emerald500,
          onRefresh: _fetchLatest,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              // ── Header (animated) ──
              SliverToBoxAdapter(
                child: FadeTransition(
                  opacity: _headerFade,
                  child: SlideTransition(
                    position: _headerSlide,
                    child: _buildHeader(),
                  ),
                ),
              ),

              // ── Connection Banner ──
              SliverToBoxAdapter(
                child: ConnectionBanner(connected: _connected),
              ),

              // ── Plant Animation Hero ──
              SliverToBoxAdapter(
                child: FadeTransition(
                  opacity: _headerFade,
                  child: const Padding(
                    padding: EdgeInsets.fromLTRB(16, 8, 16, 16),
                    child: PlantDiveWidget(),
                  ),
                ),
              ),

              // ── Metric Cards Grid (staggered) ──
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                sliver: SliverGrid(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 1.0,
                  ),
                  delegate: SliverChildListDelegate(
                    _buildAnimatedMetricCards(),
                  ),
                ),
              ),

              // ── Crop Health Score ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: CropHealthWidget(data: _data),
                ),
              ),

              // ── ML Insights ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: MlPredictionCard(
                    ensemble: _mlEnsemble,
                    irrigation: _irrigation,
                    isLoading: _mlLoading && _mlEnsemble == null,
                  ),
                ),
              ),

              // ── Growth Stage (animated) ──
              SliverToBoxAdapter(
                child: FadeTransition(
                  opacity: _growthFade,
                  child: SlideTransition(
                    position: _growthSlide,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: GrowthStageCard(data: _data),
                    ),
                  ),
                ),
              ),

              // ── Environment Insights (animated) ──
              SliverToBoxAdapter(
                child: FadeTransition(
                  opacity: _insightsFade,
                  child: SlideTransition(
                    position: _insightsSlide,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 0),
                      child: EnvironmentInsightsCard(data: _data),
                    ),
                  ),
                ),
              ),

              // ── Quick Actions ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                  child: const QuickActionsCard(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildAnimatedMetricCards() {
    final cards = [
      MetricCard(
        label: 'SOIL MOISTURE',
        value: _data.soil,
        unit: '%',
        icon: Icons.water_drop,
        color: AppColors.emerald500,
        bgColor: AppColors.emerald50,
        status: _soilStatus,
        statusColor: _soilStatusColor,
        isLoading: _initialLoading,
        pulseAnimation: _pulseController,
      ),
      MetricCard(
        label: 'TEMPERATURE',
        value: _data.temp,
        unit: '°C',
        icon: Icons.thermostat,
        color: AppColors.amber500,
        bgColor: AppColors.amber50,
        status: _tempStatus,
        statusColor: _tempStatusColor,
        isLoading: _initialLoading,
        pulseAnimation: _pulseController,
      ),
      MetricCard(
        label: 'HUMIDITY',
        value: _data.humidity,
        unit: '%',
        icon: Icons.cloud,
        color: AppColors.cyan500,
        bgColor: AppColors.cyan50,
        status: _humidityStatus,
        statusColor: _humidityStatusColor,
        isLoading: _initialLoading,
        pulseAnimation: _pulseController,
      ),
      MetricCard(
        label: 'LIGHT (LDR)',
        value: _data.light,
        unit: 'lux',
        icon: Icons.wb_sunny,
        color: AppColors.yellow500,
        bgColor: AppColors.yellow50,
        status: _lightStatus,
        statusColor: _lightStatusColor,
        isLoading: _initialLoading,
        pulseAnimation: _pulseController,
      ),
    ];

    return List.generate(cards.length, (i) {
      return FadeTransition(
        opacity: _cardFades[i],
        child: SlideTransition(position: _cardSlides[i], child: cards[i]),
      );
    });
  }

  Widget _buildHeader() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final subtitleColor = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final refreshBg = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.slate100;
    final refreshIconColor = isDark ? Colors.white70 : Colors.black54;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      child: Row(
        children: [
          Container(
            width: 3,
            height: 40,
            decoration: BoxDecoration(
              color: AppColors.emerald500,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'DIGITAL TWIN DASHBOARD',
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _lastUpdated != null
                      ? 'Last update: ${_formatTimeAgo(_lastUpdated!)}'
                      : 'ESP32 Smart Farming System',
                  style: GoogleFonts.inter(fontSize: 12, color: subtitleColor),
                ),
              ],
            ),
          ),
          // Animated refresh button
          GestureDetector(
            onTap: _fetchLatest,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: refreshBg,
                borderRadius: BorderRadius.circular(10),
              ),
              child: SpinIcon(
                icon: Icons.refresh,
                size: 18,
                color: refreshIconColor,
                onTap: _fetchLatest,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Live indicator
          AnimatedBuilder(
            animation: _pulseController,
            builder: (_, child) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: _connected
                    ? AppColors.emerald500.withValues(alpha: 0.1)
                    : AppColors.red500.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _connected
                          ? AppColors.emerald500.withValues(
                              alpha: 0.5 + _pulseController.value * 0.5,
                            )
                          : AppColors.red500,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    _connected ? 'LIVE' : 'OFFLINE',
                    style: GoogleFonts.robotoMono(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: _connected
                          ? AppColors.emerald600
                          : AppColors.red500,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Status helpers ──

  String get _soilStatus => _data.soil > 60
      ? 'High'
      : _data.soil > 30
      ? 'Optimal'
      : 'Low';
  Color get _soilStatusColor => _data.soil > 60
      ? AppColors.amber500
      : _data.soil > 30
      ? AppColors.emerald500
      : AppColors.red500;

  String get _tempStatus => _data.temp > 30
      ? 'High'
      : _data.temp >= 18
      ? 'Optimal'
      : 'Low';
  Color get _tempStatusColor => _data.temp > 30
      ? AppColors.red500
      : _data.temp >= 18
      ? AppColors.emerald500
      : AppColors.cyan500;

  String get _humidityStatus => _data.humidity > 70
      ? 'High'
      : _data.humidity >= 40
      ? 'Optimal'
      : 'Low';
  Color get _humidityStatusColor => _data.humidity > 70
      ? AppColors.cyan500
      : _data.humidity >= 40
      ? AppColors.emerald500
      : AppColors.amber500;

  String get _lightStatus => _data.light > 800
      ? 'High'
      : _data.light > 200
      ? 'Optimal'
      : 'Low';
  Color get _lightStatusColor => _data.light > 800
      ? AppColors.yellow500
      : _data.light > 200
      ? AppColors.emerald500
      : AppColors.slate400;

  String _formatTimeAgo(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inSeconds < 5) return 'just now';
    if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    return '${diff.inHours}h ago';
  }
}
