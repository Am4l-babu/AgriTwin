import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/sensor_data.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../config/app_config.dart';

class CalibrationScreen extends StatefulWidget {
  const CalibrationScreen({super.key});

  @override
  State<CalibrationScreen> createState() => _CalibrationScreenState();
}

class _CalibrationScreenState extends State<CalibrationScreen> {
  late final ApiService _api;
  List<CalibrationSummary> _profiles = [];
  CalibrationProfile? _selectedProfile;
  bool _loading = true;
  String? _selectedSensor;

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: AppConfig.baseUrl);
    _loadProfiles();
  }

  Future<void> _loadProfiles() async {
    try {
      final profiles = await _api.getCalibrationProfiles();
      if (mounted) {
        setState(() {
          _profiles = profiles;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadDetail(String sensorType) async {
    setState(() => _selectedSensor = sensorType);
    try {
      final profile = await _api.getCalibrationProfile(sensorType);
      if (mounted) setState(() => _selectedProfile = profile);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.emerald500,
          onRefresh: _loadProfiles,
          child: _loading
              ? const Center(
                  child: CircularProgressIndicator(color: AppColors.emerald500),
                )
              : _selectedProfile != null
              ? _buildDetail()
              : _buildGrid(),
        ),
      ),
    );
  }

  Widget _buildGrid() {
    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverToBoxAdapter(child: _buildHeader()),
        SliverPadding(
          padding: const EdgeInsets.all(16),
          sliver: SliverGrid(
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.85,
            ),
            delegate: SliverChildBuilderDelegate(
              (ctx, i) => _buildProfileCard(_profiles[i]),
              childCount: _profiles.length,
            ),
          ),
        ),

        // Wizard button
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            child: _buildWizardButton(),
          ),
        ),
      ],
    );
  }

  Widget _buildHeader() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final subtitleColor = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
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
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SENSOR CALIBRATION',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Configure & calibrate sensors',
                style: GoogleFonts.inter(fontSize: 12, color: subtitleColor),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileCard(CalibrationSummary profile) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final shadowColor = isDark
        ? Colors.black.withValues(alpha: 0.2)
        : Colors.black.withValues(alpha: 0.04);
    final methodColor = isDark
        ? Colors.white54
        : Colors.black.withValues(alpha: 0.5);
    final dateColor = isDark
        ? Colors.white30
        : Colors.black.withValues(alpha: 0.3);

    final meta = sensorMetaMap[profile.sensorType];
    final methodLabel = methodLabels[profile.method] ?? profile.method;
    final isCalibrated = profile.method != 'not_calibrated';

    return GestureDetector(
      onTap: () => _loadDetail(profile.sensorType),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _selectedSensor == profile.sensorType
                ? AppColors.emerald500
                : borderColor,
          ),
          boxShadow: [
            BoxShadow(
              color: shadowColor,
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon + status
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: isDark
                        ? (meta?.color ?? AppColors.slate400).withValues(
                            alpha: 0.15,
                          )
                        : meta?.bgColor ?? AppColors.slate100,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    meta?.icon ?? Icons.sensors,
                    size: 20,
                    color: meta?.color ?? AppColors.slate400,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: isCalibrated
                        ? (isDark
                              ? AppColors.emerald500.withValues(alpha: 0.15)
                              : AppColors.emerald50)
                        : (isDark
                              ? AppColors.amber500.withValues(alpha: 0.15)
                              : AppColors.amber50),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    isCalibrated ? 'Active' : 'Uncal.',
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: isCalibrated
                          ? AppColors.emerald600
                          : AppColors.amber600,
                    ),
                  ),
                ),
              ],
            ),
            const Spacer(),
            // Sensor name
            Text(
              meta?.label ?? profile.sensorType,
              style: GoogleFonts.inter(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            // Method
            Text(
              methodLabel,
              style: GoogleFonts.robotoMono(fontSize: 11, color: methodColor),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            if (profile.calibrationDate != null) ...[
              const SizedBox(height: 4),
              Text(
                profile.calibrationDate!.split('T').first,
                style: GoogleFonts.robotoMono(fontSize: 10, color: dateColor),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildWizardButton() {
    return GestureDetector(
      onTap: _showWizard,
      child: Container(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppColors.emerald500, AppColors.emerald600],
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: AppColors.emerald500.withValues(alpha: 0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.auto_fix_high, color: Colors.white, size: 20),
            const SizedBox(width: 10),
            Text(
              'Calibration Wizard',
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // â”€â”€ Detail View â”€â”€

  Widget _buildDetail() {
    final p = _selectedProfile!;
    final meta = sensorMetaMap[p.sensorType];
    final methodLabel = methodLabels[p.method] ?? p.method;

    return CustomScrollView(
      slivers: [
        // Back bar
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 8, 16, 0),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back_ios_new, size: 18),
                  onPressed: () => setState(() => _selectedProfile = null),
                ),
                Text(
                  meta?.label ?? p.sensorType,
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: meta?.bgColor ?? AppColors.slate100,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    methodLabel,
                    style: GoogleFonts.robotoMono(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: meta?.color ?? AppColors.slate400,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        // Description
        if (p.description != null)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Builder(
                builder: (context) {
                  final isDark =
                      Theme.of(context).brightness == Brightness.dark;
                  final descBg = isDark
                      ? const Color(0xFF1A1F2E)
                      : Colors.white;
                  final descBorder = isDark
                      ? Colors.white.withValues(alpha: 0.08)
                      : AppColors.surfaceBorder;
                  final descColor = isDark
                      ? Colors.white60
                      : Colors.black.withValues(alpha: 0.6);
                  return Container(
                    decoration: BoxDecoration(
                      color: descBg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: descBorder),
                    ),
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      p.description!,
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        color: descColor,
                        height: 1.5,
                      ),
                    ),
                  );
                },
              ),
            ),
          ),

        // Parameters
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: _buildParametersCard(p),
          ),
        ),

        // Calibration curve
        if (p.referencePoints != null && p.referencePoints!.isNotEmpty)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: _buildCalibrationCurve(p),
            ),
          ),

        // Interpretation bands
        if (p.interpretation != null && p.interpretation!.isNotEmpty)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              child: _buildInterpretationBands(p),
            ),
          ),

        const SliverToBoxAdapter(child: SizedBox(height: 24)),

        // Recalibrate button
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
            child: ElevatedButton.icon(
              onPressed: () => _showWizard(initialSensor: _selectedSensor),
              icon: const Icon(Icons.auto_fix_high, size: 18),
              label: Text(
                'Recalibrate ${sensorMetaMap[_selectedSensor!]?.label ?? _selectedSensor!}',
                style: GoogleFonts.inter(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.emerald500,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildParametersCard(CalibrationProfile p) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final sectionLabel = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final paramLabel = isDark
        ? Colors.white60
        : Colors.black.withValues(alpha: 0.6);

    final params = <MapEntry<String, String>>[];

    if (p.offset != null) params.add(MapEntry('Offset', p.offset.toString()));
    if (p.multiplier != null) {
      params.add(MapEntry('Multiplier', p.multiplier.toString()));
    }
    if (p.dryValue != null) {
      params.add(MapEntry('Dry Value', p.dryValue.toString()));
    }
    if (p.wetValue != null) {
      params.add(MapEntry('Wet Value', p.wetValue.toString()));
    }
    if (p.calibrationDate != null) {
      params.add(MapEntry('Calibrated', p.calibrationDate!.split('T').first));
    }

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
            'PARAMETERS',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: sectionLabel,
            ),
          ),
          const SizedBox(height: 12),
          ...params.map(
            (e) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    e.key,
                    style: GoogleFonts.inter(fontSize: 13, color: paramLabel),
                  ),
                  Text(
                    e.value,
                    style: GoogleFonts.robotoMono(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
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

  Widget _buildCalibrationCurve(CalibrationProfile p) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final sectionLabel = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final gridColor = isDark
        ? Colors.white.withValues(alpha: 0.06)
        : Colors.black.withValues(alpha: 0.05);
    final dotFillColor = isDark ? const Color(0xFF1A1F2E) : Colors.white;

    final points = p.referencePoints!;
    final spots = <FlSpot>[];
    for (final pt in points) {
      final raw = (pt['raw'] ?? pt['raw_value'] ?? 0).toDouble();
      final actual = (pt['actual'] ?? pt['actual_value'] ?? 0).toDouble();
      spots.add(FlSpot(raw, actual));
    }
    spots.sort((a, b) => a.x.compareTo(b.x));

    final meta = sensorMetaMap[p.sensorType];
    final color = meta?.color ?? AppColors.emerald500;

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
            'CALIBRATION CURVE',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: sectionLabel,
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 180,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (v) =>
                      FlLine(color: gridColor, strokeWidth: 1),
                ),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    axisNameWidget: Text(
                      'Raw',
                      style: GoogleFonts.robotoMono(fontSize: 10),
                    ),
                    sideTitles: const SideTitles(showTitles: false),
                  ),
                  leftTitles: AxisTitles(
                    axisNameWidget: Text(
                      'Actual',
                      style: GoogleFonts.robotoMono(fontSize: 10),
                    ),
                    sideTitles: const SideTitles(showTitles: false),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    color: color,
                    barWidth: 2.5,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                        radius: 4,
                        color: dotFillColor,
                        strokeWidth: 2,
                        strokeColor: color,
                      ),
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          color.withValues(alpha: 0.15),
                          color.withValues(alpha: 0.0),
                        ],
                      ),
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

  Widget _buildInterpretationBands(CalibrationProfile p) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : AppColors.surfaceBorder;
    final sectionLabel = isDark
        ? Colors.white38
        : Colors.black.withValues(alpha: 0.4);
    final rangeColor = isDark
        ? Colors.white54
        : Colors.black.withValues(alpha: 0.5);

    final bands = p.interpretation!;
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
            'INTERPRETATION BANDS',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: sectionLabel,
            ),
          ),
          const SizedBox(height: 12),
          ...bands.entries.map((e) {
            final range = e.value;
            final color = bandColors[e.key] ?? AppColors.slate400;
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      e.key.replaceAll('_', ' ').toUpperCase(),
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  Text(
                    range.length >= 2
                        ? '${range[0]} \u2013 ${range[1]}'
                        : range.toString(),
                    style: GoogleFonts.robotoMono(
                      fontSize: 12,
                      color: rangeColor,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  // â”€â”€ Calibration Wizard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  void _showWizard({String? initialSensor}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _WizardSheet(
        api: _api,
        initialSensor: initialSensor,
        onDone: () {
          Navigator.pop(ctx);
          _loadProfiles();
          if (_selectedSensor != null) _loadDetail(_selectedSensor!);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Calibration applied!'),
              backgroundColor: AppColors.emerald500,
            ),
          );
        },
      ),
    );
  }
}

// â”€â”€ Calibration Wizard Sheet â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _WizardSheet extends StatefulWidget {
  final ApiService api;
  final String? initialSensor;
  final VoidCallback onDone;

  const _WizardSheet({
    required this.api,
    this.initialSensor,
    required this.onDone,
  });

  @override
  State<_WizardSheet> createState() => _WizardSheetState();
}

class _WizardSheetState extends State<_WizardSheet> {
  String? _sensor;
  int _step = 0; // 0 = sensor picker  1 = calibration UI  2/3 = soil steps
  Map<String, dynamic>? _liveData;
  bool _loadingLive = false;
  bool _saving = false;
  String? _error;
  final _refCtrl = TextEditingController();
  int? _wetRaw;
  int? _dryRaw;
  Timer? _pollTimer;

  static const _soilSensor = 'soil_moisture';

  bool get _isSoil => _sensor == _soilSensor;
  bool get _soilStep1 => _isSoil && _step == 1;
  bool get _soilStep2 => _isSoil && _step == 2;
  bool get _soilStep3 => _isSoil && _step == 3;

  @override
  void initState() {
    super.initState();
    if (widget.initialSensor != null) {
      _selectSensor(widget.initialSensor!);
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _refCtrl.dispose();
    super.dispose();
  }

  void _selectSensor(String sensor) {
    setState(() {
      _sensor = sensor;
      _step = 1;
      _error = null;
      _wetRaw = null;
      _dryRaw = null;
    });
    _refCtrl.clear();
    _pollTimer?.cancel();
    _fetchLive();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchLive());
  }

  Future<void> _fetchLive() async {
    if (!mounted) return;
    setState(() => _loadingLive = true);
    final data = await widget.api.getLatestRaw();
    if (mounted) setState(() { _liveData = data; _loadingLive = false; });
  }

  double? get _liveValue {
    if (_liveData == null) return null;
    switch (_sensor) {
      case 'temperature':
        return (_liveData!['temperature'] as num?)?.toDouble();
      case 'humidity':
        return (_liveData!['humidity'] as num?)?.toDouble();
      case 'light':
        return (_liveData!['light_level'] as num?)?.toDouble();
      default:
        return null;
    }
  }

  int? get _liveRawSoil => (_liveData?['raw_soil'] as num?)?.toInt();
  SensorMeta? get _meta => _sensor == null ? null : sensorMetaMap[_sensor!];

  String get _referenceSubtitle {
    switch (_sensor) {
      case 'temperature':
        return 'Place a reference thermometer next to the sensor and read its value.';
      case 'humidity':
        return 'Check a reference hygrometer, weather station, or weather app for the current humidity.';
      case 'light':
        return 'Open a "Lux Meter" app on your phone and read the lux value at the sensor location.';
      default:
        return 'Enter the known correct value from a reference device.';
    }
  }

  String get _referenceHint {
    switch (_sensor) {
      case 'temperature':
        return 'e.g. 27.5 (from thermometer)';
      case 'humidity':
        return 'e.g. 65 (from hygrometer / weather app)';
      case 'light':
        return 'e.g. 500 (lux from phone light meter app)';
      default:
        return 'Known reference value';
    }
  }

  double? get _computedOffset {
    final live = _liveValue;
    final ref = double.tryParse(_refCtrl.text);
    if (live == null || ref == null) return null;
    return ref - live;
  }

  Future<void> _applyOffsetCalibration() async {
    final live = _liveValue;
    final ref = double.tryParse(_refCtrl.text);
    if (live == null || ref == null || _sensor == null) return;
    setState(() { _saving = true; _error = null; });
    try {
      await widget.api.runCalibrationWizard(
        sensorType: _sensor!,
        method: 'offset_correction',
        points: [
          {
            'raw': live,
            'actual': ref,
            'condition': 'Reference device measurement',
          },
        ],
        notes: 'Reference calibration â€” ${DateTime.now().toIso8601String().split('T').first}',
      );
      if (mounted) widget.onDone();
    } catch (e) {
      if (mounted) setState(() { _saving = false; _error = e.toString(); });
    }
  }

  Future<void> _applySoilCalibration() async {
    if (_wetRaw == null || _dryRaw == null) return;
    setState(() { _saving = true; _error = null; });
    try {
      await widget.api.runCalibrationWizard(
        sensorType: 'soil_moisture',
        method: 'two_point_linear',
        points: [
          {'raw': _wetRaw!.toDouble(), 'actual': 100.0, 'condition': 'Sensor fully submerged in water'},
          {'raw': _dryRaw!.toDouble(), 'actual': 0.0, 'condition': 'Sensor in open air'},
        ],
        notes: 'Two-point calibration â€” ${DateTime.now().toIso8601String().split('T').first}',
      );
      if (mounted) widget.onDone();
    } catch (e) {
      if (mounted) setState(() { _saving = false; _error = e.toString(); });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final sheetBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    return Container(
      decoration: BoxDecoration(
        color: sheetBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(
        24, 16, 24,
        MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle
            Center(
              child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(
                  color: isDark
                      ? Colors.white.withValues(alpha: 0.15)
                      : Colors.black.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Back + title
            Row(
              children: [
                if (_step > 0 && widget.initialSensor == null) ...[
                  GestureDetector(
                    onTap: () {
                      if (_step <= 1) {
                        _pollTimer?.cancel();
                        setState(() { _step = 0; _sensor = null; });
                      } else {
                        setState(() => _step = _step - 1);
                      }
                    },
                    child: const Padding(
                      padding: EdgeInsets.only(right: 12),
                      child: Icon(Icons.arrow_back_ios_new, size: 18),
                    ),
                  ),
                ],
                Expanded(
                  child: Text(
                    _step == 0
                        ? 'Choose Sensor to Calibrate'
                        : _isSoil
                            ? (_soilStep1
                                ? 'Soil Moisture â€” Step 1 / 2'
                                : _soilStep2
                                    ? 'Soil Moisture â€” Step 2 / 2'
                                    : 'Soil Moisture â€” Review')
                            : 'Calibrate ${sensorMetaMap[_sensor!]?.label ?? _sensor!}',
                    style: GoogleFonts.inter(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_step == 0) _buildSensorPicker() else _buildCalibrationUI(),
          ],
        ),
      ),
    );
  }

  Widget _buildSensorPicker() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    const sensors = [
      ('temperature', 'Use a reference thermometer near the sensor'),
      ('humidity', 'Use a hygrometer or weather station as reference'),
      ('light', 'Use your phone\'s light sensor (lux meter app)'),
      ('soil_moisture', 'Two-point: submerge in water, then hold in air'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Select the sensor you want to calibrate:',
          style: GoogleFonts.inter(
            fontSize: 13,
            color: isDark ? Colors.white54 : Colors.black54,
          ),
        ),
        const SizedBox(height: 16),
        ...sensors.map((entry) {
          final (s, hint) = entry;
          final meta = sensorMetaMap[s]!;
          return GestureDetector(
            onTap: () => _selectSensor(s),
            child: Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isDark
                    ? meta.color.withValues(alpha: 0.08)
                    : meta.bgColor,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: meta.color.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: meta.color.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(meta.icon, color: meta.color, size: 22),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(meta.label,
                            style: GoogleFonts.inter(
                                fontSize: 14, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 2),
                        Text(hint,
                            style: GoogleFonts.inter(
                                fontSize: 12,
                                color: isDark
                                    ? Colors.white38
                                    : Colors.black38)),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right, color: meta.color, size: 20),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildCalibrationUI() {
    if (_isSoil) return _buildSoilUI();
    return _buildOffsetCorrectionUI();
  }

  // â”€â”€ Offset Correction (Temperature / Humidity / Light) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildOffsetCorrectionUI() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final meta = _meta;
    if (meta == null) return const SizedBox();

    final liveValue = _liveValue;
    final computedOffset = _computedOffset;
    final canApply = liveValue != null && double.tryParse(_refCtrl.text) != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Info tip
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: meta.color.withValues(alpha: isDark ? 0.12 : 0.08),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: meta.color.withValues(alpha: 0.3)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.info_outline, color: meta.color, size: 18),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _referenceSubtitle,
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: isDark ? Colors.white70 : Colors.black54,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Current live reading
        _sectionLabel('CURRENT SENSOR READING'),
        const SizedBox(height: 8),
        Row(
          children: [
            Text(
              liveValue != null
                  ? '${liveValue.toStringAsFixed(1)} ${meta.unit}'
                  : 'â€”',
              style: GoogleFonts.robotoMono(
                fontSize: 32,
                fontWeight: FontWeight.w700,
                color: meta.color,
              ),
            ),
            const SizedBox(width: 12),
            _liveBadge(meta.color),
          ],
        ),
        const SizedBox(height: 20),

        // Reference input
        _sectionLabel('REFERENCE VALUE (from external device)'),
        const SizedBox(height: 8),
        TextField(
          controller: _refCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          style: GoogleFonts.robotoMono(fontSize: 18),
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            hintText: _referenceHint,
            hintStyle: GoogleFonts.inter(
              fontSize: 13,
              color: isDark ? Colors.white30 : Colors.black.withValues(alpha: 0.3),
            ),
            suffixText: meta.unit,
            suffixStyle: GoogleFonts.robotoMono(
              fontSize: 15,
              color: isDark ? Colors.white54 : Colors.black45,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                  color: isDark ? Colors.white12 : Colors.black12),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: meta.color, width: 1.5),
            ),
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
        ),

        // Computed offset preview
        if (computedOffset != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark
                  ? Colors.white.withValues(alpha: 0.05)
                  : Colors.black.withValues(alpha: 0.03),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.calculate_outlined, size: 16),
                    const SizedBox(width: 8),
                    Text('Computed Calibration',
                        style: GoogleFonts.inter(
                            fontSize: 12, fontWeight: FontWeight.w600)),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Offset',
                        style: GoogleFonts.inter(
                            fontSize: 13,
                            color: isDark ? Colors.white60 : Colors.black54)),
                    Text(
                      '${computedOffset >= 0 ? '+' : ''}${computedOffset.toStringAsFixed(2)} ${meta.unit}',
                      style: GoogleFonts.robotoMono(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: computedOffset.abs() < 0.01
                            ? Colors.grey
                            : computedOffset > 0
                                ? Colors.green
                                : Colors.orange,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  'calibrated = reading ${computedOffset >= 0 ? '+' : ''}${computedOffset.toStringAsFixed(2)}',
                  style: GoogleFonts.robotoMono(
                    fontSize: 11,
                    color: isDark ? Colors.white38 : Colors.black38,
                  ),
                ),
              ],
            ),
          ),
        ],

        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!,
              style: GoogleFonts.inter(fontSize: 13, color: AppColors.red500)),
        ],

        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: (canApply && !_saving) ? _applyOffsetCalibration : null,
            icon: _saving
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.check, size: 18),
            label: Text(
              _saving ? 'Applying...' : 'Apply Calibration',
              style: GoogleFonts.inter(
                  fontSize: 15, fontWeight: FontWeight.w600),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.emerald500,
              foregroundColor: Colors.white,
              disabledBackgroundColor:
                  Colors.grey.withValues(alpha: 0.3),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
          ),
        ),
      ],
    );
  }

  // â”€â”€ Soil Moisture Two-Point Calibration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildSoilUI() {
    if (_soilStep3) return _buildSoilReview();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isWetStep = _soilStep1;
    final rawAdc = _liveRawSoil;
    final hasRaw = rawAdc != null;
    final meta = sensorMetaMap['soil_moisture']!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Step progress
        Row(
          children: [
            _stepDot(1, isActive: isWetStep, isDone: !isWetStep && _step > 1),
            Expanded(
              child: Container(
                height: 2,
                color: isWetStep
                    ? Colors.grey.withValues(alpha: 0.25)
                    : meta.color,
              ),
            ),
            _stepDot(2, isActive: _soilStep2, isDone: false),
          ],
        ),
        const SizedBox(height: 24),

        // Instruction card
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: meta.color.withValues(alpha: isDark ? 0.12 : 0.08),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: meta.color.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              Icon(
                isWetStep ? Icons.water : Icons.air,
                color: isWetStep ? const Color(0xFF3B82F6) : Colors.orange,
                size: 36,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isWetStep
                          ? 'Submerge sensor in water'
                          : 'Hold sensor in open air',
                      style: GoogleFonts.inter(
                          fontSize: 15, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      isWetStep
                          ? 'Place the probe fully in water and wait ~10 seconds for the reading to stabilise.'
                          : 'Remove the sensor from water and hold it in open air. Wait ~10 seconds.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: isDark ? Colors.white60 : Colors.black54,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Live raw ADC
        _sectionLabel('LIVE RAW ADC READING'),
        const SizedBox(height: 8),
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              hasRaw ? '$rawAdc' : 'â€”',
              style: GoogleFonts.robotoMono(
                fontSize: 36,
                fontWeight: FontWeight.w700,
                color: hasRaw ? meta.color : Colors.grey,
              ),
            ),
            const SizedBox(width: 8),
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text('/ 4095',
                  style: GoogleFonts.inter(
                      fontSize: 14,
                      color: isDark ? Colors.white38 : Colors.black38)),
            ),
            const Spacer(),
            _liveBadge(meta.color),
          ],
        ),

        if (!hasRaw) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.amber500.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                  color: AppColors.amber500.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_outlined,
                    color: AppColors.amber600, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Raw ADC not available yet. Ensure the updated ESP32 firmware is running.',
                    style: GoogleFonts.inter(
                        fontSize: 12, color: AppColors.amber600),
                  ),
                ),
              ],
            ),
          ),
        ],

        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!,
              style:
                  GoogleFonts.inter(fontSize: 13, color: AppColors.red500)),
        ],

        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: !hasRaw
                ? null
                : () {
                    if (isWetStep) {
                      setState(() { _wetRaw = rawAdc; _step = 2; _error = null; });
                    } else {
                      setState(() { _dryRaw = rawAdc; _step = 3; _error = null; });
                    }
                  },
            icon: Icon(isWetStep ? Icons.water_drop : Icons.air, size: 18),
            label: Text(
              isWetStep
                  ? 'Record Wet Point  (${hasRaw ? '$rawAdc ADC' : 'â€”'})'
                  : 'Record Dry Point  (${hasRaw ? '$rawAdc ADC' : 'â€”'})',
              style: GoogleFonts.inter(
                  fontSize: 15, fontWeight: FontWeight.w600),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: isWetStep
                  ? const Color(0xFF3B82F6)
                  : Colors.orange,
              foregroundColor: Colors.white,
              disabledBackgroundColor:
                  Colors.grey.withValues(alpha: 0.3),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSoilReview() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final meta = sensorMetaMap['soil_moisture']!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionLabel('CALIBRATION SUMMARY'),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: meta.color.withValues(alpha: isDark ? 0.1 : 0.06),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: meta.color.withValues(alpha: 0.3)),
          ),
          child: Column(
            children: [
              _soilReviewRow(
                icon: Icons.water,
                iconColor: const Color(0xFF3B82F6),
                label: 'Wet point (100%)',
                value: '${_wetRaw} ADC',
                valueColor: const Color(0xFF3B82F6),
              ),
              const SizedBox(height: 12),
              _soilReviewRow(
                icon: Icons.air,
                iconColor: Colors.orange,
                label: 'Dry point (0%)',
                value: '${_dryRaw} ADC',
                valueColor: Colors.orange,
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isDark
                ? Colors.white.withValues(alpha: 0.05)
                : Colors.black.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            'Formula: moisture% = (raw âˆ’ ${_dryRaw}) / (${_wetRaw} âˆ’ ${_dryRaw}) Ã— 100',
            style: GoogleFonts.robotoMono(
              fontSize: 11,
              color: isDark ? Colors.white54 : Colors.black45,
            ),
          ),
        ),

        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!,
              style:
                  GoogleFonts.inter(fontSize: 13, color: AppColors.red500)),
        ],

        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () =>
                    setState(() { _step = 1; _wetRaw = null; }),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
                child: Text('Start Over',
                    style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: ElevatedButton.icon(
                onPressed: _saving ? null : _applySoilCalibration,
                icon: _saving
                    ? const SizedBox(
                        width: 18, height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.check, size: 18),
                label: Text(
                  _saving ? 'Applying...' : 'Apply Calibration',
                  style: GoogleFonts.inter(
                      fontSize: 15, fontWeight: FontWeight.w600),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.emerald500,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _sectionLabel(String text) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Text(
      text,
      style: GoogleFonts.inter(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.5,
        color: isDark ? Colors.white38 : Colors.black38,
      ),
    );
  }

  Widget _liveBadge(Color color) {
    return GestureDetector(
      onTap: _fetchLive,
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: _loadingLive
              ? Colors.grey.withValues(alpha: 0.1)
              : AppColors.emerald500.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: _loadingLive
                ? Colors.grey.withValues(alpha: 0.3)
                : AppColors.emerald500.withValues(alpha: 0.4),
          ),
        ),
        child: _loadingLive
            ? SizedBox(
                width: 14, height: 14,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: color))
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 6, height: 6,
                    decoration: const BoxDecoration(
                      color: AppColors.emerald500,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 5),
                  Text('LIVE',
                      style: GoogleFonts.inter(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppColors.emerald500,
                        letterSpacing: 0.5,
                      )),
                ],
              ),
      ),
    );
  }

  Widget _stepDot(int number,
      {bool isActive = false, bool isDone = false}) {
    final meta = sensorMetaMap['soil_moisture']!;
    return Container(
      width: 32, height: 32,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isActive || isDone
            ? meta.color
            : Colors.grey.withValues(alpha: 0.25),
        border: Border.all(
          color: isActive ? meta.color : Colors.transparent,
          width: 2,
        ),
      ),
      child: Center(
        child: isDone
            ? const Icon(Icons.check, size: 16, color: Colors.white)
            : Text(
                '$number',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: isActive ? Colors.white : Colors.grey,
                ),
              ),
      ),
    );
  }

  Widget _soilReviewRow({
    required IconData icon,
    required Color iconColor,
    required String label,
    required String value,
    required Color valueColor,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Icon(icon, color: iconColor, size: 20),
            const SizedBox(width: 8),
            Text(label, style: GoogleFonts.inter(fontSize: 13)),
          ],
        ),
        Text(value,
            style: GoogleFonts.robotoMono(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: valueColor)),
      ],
    );
  }
}
