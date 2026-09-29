import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../models/sensor_data.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../config/app_config.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late final ApiService _api;
  List<SensorReading> _readings = [];
  SensorStats? _stats;
  bool _loading = true;
  int _selectedHours = 1;
  Timer? _refreshTimer;

  final _timeRanges = [1, 6, 12, 24, 48];

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: AppConfig.baseUrl);
    _loadData();
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _loadData(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final results = await Future.wait([
        _api.getHistory(hours: _selectedHours),
        _api.getStats(hours: _selectedHours),
      ]);
      if (mounted) {
        setState(() {
          _readings = results[0] as List<SensorReading>;
          _stats = results[1] as SensorStats;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.emerald500,
          onRefresh: _loadData,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              // Header
              SliverToBoxAdapter(child: _buildHeader()),

              // Time range selector
              SliverToBoxAdapter(child: _buildTimeSelector()),

              // Stats bar
              if (_stats != null) SliverToBoxAdapter(child: _buildStatsBar()),

              // Charts
              if (_loading)
                const SliverFillRemaining(
                  child: Center(
                    child: CircularProgressIndicator(
                      color: AppColors.emerald500,
                    ),
                  ),
                )
              else ...[
                SliverToBoxAdapter(
                  child: _buildChart(
                    'Soil Moisture',
                    '%',
                    AppColors.emerald500,
                    AppColors.emerald100,
                    _readings.map((r) => r.soilMoisture).toList(),
                  ),
                ),
                SliverToBoxAdapter(
                  child: _buildChart(
                    'Temperature',
                    '°C',
                    AppColors.amber500,
                    AppColors.amber50,
                    _readings.map((r) => r.temperature).toList(),
                  ),
                ),
                SliverToBoxAdapter(
                  child: _buildChart(
                    'Humidity',
                    '%',
                    AppColors.cyan500,
                    AppColors.cyan50,
                    _readings.map((r) => r.humidity).toList(),
                  ),
                ),
                SliverToBoxAdapter(
                  child: _buildChart(
                    'Light Level',
                    'lux',
                    AppColors.yellow500,
                    AppColors.yellow50,
                    _readings.map((r) => r.lightLevel).toList(),
                  ),
                ),
                const SliverToBoxAdapter(child: SizedBox(height: 24)),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final subtitleColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);

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
                'SENSOR HISTORY',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Historical sensor data & trends',
                style: GoogleFonts.inter(
                  fontSize: 12,
                  color: subtitleColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTimeSelector() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final containerBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark ? Colors.white.withValues(alpha: 0.08) : AppColors.surfaceBorder;
    final unselectedTextColor = isDark ? Colors.white54 : Colors.black.withValues(alpha: 0.5);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        decoration: BoxDecoration(
          color: containerBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        padding: const EdgeInsets.all(4),
        child: Row(
          children: _timeRanges.map((h) {
            final selected = h == _selectedHours;
            return Expanded(
              child: GestureDetector(
                onTap: () {
                  setState(() {
                    _selectedHours = h;
                    _loading = true;
                  });
                  _loadData();
                },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: selected ? AppColors.emerald500 : Colors.transparent,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    '${h}h',
                    style: GoogleFonts.robotoMono(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: selected
                          ? Colors.white
                          : unselectedTextColor,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildStatsBar() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final containerBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark ? Colors.white.withValues(alpha: 0.08) : AppColors.surfaceBorder;

    final s = _stats!;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        decoration: BoxDecoration(
          color: containerBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            _statChip(Icons.data_usage, '${s.totalReadings}', 'Readings'),
            const Spacer(),
            _statChip(
              Icons.thermostat,
              '${s.avgTemp.toStringAsFixed(1)}°',
              'Avg Temp',
            ),
            const Spacer(),
            _statChip(
              Icons.water_drop,
              '${s.avgSoil.toStringAsFixed(1)}%',
              'Avg Soil',
            ),
            const Spacer(),
            _statChip(
              Icons.cloud,
              '${s.avgHumidity.toStringAsFixed(1)}%',
              'Avg Hum',
            ),
          ],
        ),
      ),
    );
  }

  Widget _statChip(IconData icon, String value, String label) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final labelColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);

    return Column(
      children: [
        Icon(icon, size: 16, color: AppColors.emerald500),
        const SizedBox(height: 4),
        Text(
          value,
          style: GoogleFonts.robotoMono(
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 10,
            color: labelColor,
          ),
        ),
      ],
    );
  }

  Widget _buildChart(
    String title,
    String unit,
    Color lineColor,
    Color fillColor,
    List<double> values,
  ) {
    if (values.isEmpty) return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final containerBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final borderColor = isDark ? Colors.white.withValues(alpha: 0.08) : AppColors.surfaceBorder;
    final unitColor = isDark ? Colors.white38 : Colors.black.withValues(alpha: 0.4);
    final gridColor = isDark ? Colors.white.withValues(alpha: 0.06) : Colors.black.withValues(alpha: 0.05);
    final axisLabelColor = isDark ? Colors.white30 : Colors.black.withValues(alpha: 0.35);

    final spots = <FlSpot>[];
    for (int i = 0; i < values.length; i++) {
      spots.add(FlSpot(i.toDouble(), values[i]));
    }

    final minY = values.reduce((a, b) => a < b ? a : b);
    final maxY = values.reduce((a, b) => a > b ? a : b);
    final range = maxY - minY;
    final chartMinY = (minY - range * 0.1).clamp(0, double.infinity);
    final chartMaxY = maxY + range * 0.1;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Container(
        decoration: BoxDecoration(
          color: containerBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderColor),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: lineColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                ),
                const Spacer(),
                Text(
                  unit,
                  style: GoogleFonts.robotoMono(
                    fontSize: 11,
                    color: unitColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 160,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: range > 0 ? range / 4 : 1,
                    getDrawingHorizontalLine: (v) => FlLine(
                      color: gridColor,
                      strokeWidth: 1,
                    ),
                  ),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 22,
                        interval: values.length > 10
                            ? (values.length / 5).roundToDouble()
                            : 1,
                        getTitlesWidget: (val, _) {
                          final idx = val.toInt();
                          if (idx < 0 || idx >= _readings.length) {
                            return const SizedBox.shrink();
                          }
                          try {
                            final ts = DateTime.parse(_readings[idx].timestamp);
                            return Text(
                              DateFormat.Hm().format(ts),
                              style: GoogleFonts.robotoMono(
                                fontSize: 9,
                                color: axisLabelColor,
                              ),
                            );
                          } catch (_) {
                            return const SizedBox.shrink();
                          }
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        interval: range > 0 ? range / 4 : 1,
                        getTitlesWidget: (val, _) {
                          return Text(
                            val.toStringAsFixed(range > 10 ? 0 : 1),
                            style: GoogleFonts.robotoMono(
                              fontSize: 9,
                              color: axisLabelColor,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  minY: chartMinY.toDouble(),
                  maxY: chartMaxY,
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      curveSmoothness: 0.3,
                      color: lineColor,
                      barWidth: 2,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            lineColor.withValues(alpha: 0.15),
                            lineColor.withValues(alpha: 0.0),
                          ],
                        ),
                      ),
                    ),
                  ],
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (spots) {
                        return spots.map((s) {
                          return LineTooltipItem(
                            '${s.y.toStringAsFixed(1)} $unit',
                            GoogleFonts.robotoMono(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                ),
                duration: const Duration(milliseconds: 300),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
