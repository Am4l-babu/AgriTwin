import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

class DtBrainScreen extends StatefulWidget {
  const DtBrainScreen({super.key});

  @override
  State<DtBrainScreen> createState() => _DtBrainScreenState();
}

class _DtBrainScreenState extends State<DtBrainScreen> {
  Map<String, dynamic>? _brain;
  bool _loading = true;
  String? _error;
  int _hours = 24;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _fetch();
    _refreshTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetch());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetch() async {
    try {
      final uri = Uri.parse(
          '${AppConfig.baseUrl}/api/v1/twin-accuracy/brain?farm_id=farm_001&hours=$_hours');
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        setState(() {
          _brain = jsonDecode(res.body);
          _loading = false;
          _error = null;
        });
      }
    } catch (e) {
      if (_brain == null) {
        setState(() {
          _loading = false;
          _error = 'Cannot reach backend';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? const Color(0xFF0F1219) : const Color(0xFFF8FAFC);
    final cardBg = isDark ? const Color(0xFF1A1F2E) : Colors.white;
    final textColor = isDark ? Colors.white : Colors.black87;
    final subText = isDark ? Colors.white60 : Colors.black54;

    return Scaffold(
      backgroundColor: bg,
      appBar: AppBar(
        title: Text('Digital Twin Brain',
            style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
        backgroundColor: isDark ? const Color(0xFF141825) : Colors.white,
        elevation: 0,
        actions: [
          PopupMenuButton<int>(
            icon: Icon(Icons.access_time, color: subText),
            onSelected: (v) {
              setState(() {
                _hours = v;
                _loading = true;
              });
              _fetch();
            },
            itemBuilder: (_) => [1, 6, 12, 24, 48]
                .map((h) => PopupMenuItem(value: h, child: Text('$h hours')))
                .toList(),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: subText),
            onPressed: _fetch,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _brain == null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
                      const SizedBox(height: 12),
                      Text(_error!, style: TextStyle(color: subText)),
                      const SizedBox(height: 12),
                      ElevatedButton(
                          onPressed: _fetch, child: const Text('Retry')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _fetch,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildAccuracyRing(cardBg, textColor, subText),
                      const SizedBox(height: 16),
                      _buildStatCards(cardBg, textColor, subText),
                      const SizedBox(height: 16),
                      _buildLatestPrediction(cardBg, textColor, subText),
                      const SizedBox(height: 24),
                      Text('Physics Models — DT Brain',
                          style: GoogleFonts.inter(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: textColor)),
                      const SizedBox(height: 12),
                      ..._buildPhysicsCards(cardBg, textColor, subText),
                    ],
                  ),
                ),
    );
  }

  Widget _buildAccuracyRing(Color cardBg, Color textColor, Color subText) {
    final accuracy = (_brain?['twin_accuracy_pct'] ?? 0).toDouble();
    final count = _brain?['sample_count'] ?? 0;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          SizedBox(
            width: 140,
            height: 140,
            child: Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 140,
                  height: 140,
                  child: CircularProgressIndicator(
                    value: accuracy / 100,
                    strokeWidth: 10,
                    backgroundColor: Colors.white12,
                    valueColor:
                        AlwaysStoppedAnimation(_accuracyColor(accuracy)),
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('${accuracy.toStringAsFixed(1)}%',
                        style: GoogleFonts.inter(
                            fontSize: 28,
                            fontWeight: FontWeight.w700,
                            color: _accuracyColor(accuracy))),
                    Text('Twin Accuracy',
                        style: TextStyle(fontSize: 11, color: subText)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text('$count predictions tracked',
              style: TextStyle(fontSize: 12, color: subText)),
        ],
      ),
    );
  }

  Widget _buildStatCards(Color cardBg, Color textColor, Color subText) {
    final avgErr = (_brain?['avg_prediction_error'] ?? 0).toDouble();
    final reliability = (_brain?['model_reliability_pct'] ?? 0).toDouble();
    final latest = _brain?['latest_prediction'] as Map<String, dynamic>?;
    final deficit = latest != null
        ? ((_brain?['physics_models']?['1_soil_moisture_balance']
                    ?['water_deficit_mm'] ??
                0)
            .toDouble())
        : 0.0;

    return Row(
      children: [
        Expanded(
            child: _statTile(cardBg, textColor, subText, 'Avg Error',
                '${avgErr.toStringAsFixed(1)}%', Colors.orange)),
        const SizedBox(width: 10),
        Expanded(
            child: _statTile(cardBg, textColor, subText, 'Reliability',
                '${reliability.toStringAsFixed(1)}%', Colors.cyan)),
        const SizedBox(width: 10),
        Expanded(
            child: _statTile(cardBg, textColor, subText, 'Water Deficit',
                '${deficit.toStringAsFixed(1)} mm', Colors.blue)),
      ],
    );
  }

  Widget _statTile(Color cardBg, Color textColor, Color subText, String label,
      String value, Color accent) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border(left: BorderSide(color: accent, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 11, color: subText)),
          const SizedBox(height: 4),
          Text(value,
              style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: textColor)),
        ],
      ),
    );
  }

  Widget _buildLatestPrediction(
      Color cardBg, Color textColor, Color subText) {
    final latest = _brain?['latest_prediction'] as Map<String, dynamic>?;
    if (latest == null) return const SizedBox.shrink();

    final predicted = (latest['predicted_soil_moisture'] ?? 0).toDouble();
    final actual = (latest['actual_soil_moisture'] ?? 0).toDouble();
    final error = (latest['error'] ?? 0).toDouble();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Latest Prediction',
              style: GoogleFonts.inter(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: textColor)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Column(
                  children: [
                    Text('Twin Predicted',
                        style: TextStyle(fontSize: 11, color: subText)),
                    Text('${predicted.toStringAsFixed(1)}%',
                        style: GoogleFonts.inter(
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                            color: Colors.cyan)),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  children: [
                    Text('Actual',
                        style: TextStyle(fontSize: 11, color: subText)),
                    Text('${actual.toStringAsFixed(1)}%',
                        style: GoogleFonts.inter(
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                            color: Colors.green)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: (predicted / 100).clamp(0.0, 1.0),
            backgroundColor: Colors.green.withOpacity(0.2),
            valueColor: const AlwaysStoppedAnimation(Colors.cyan),
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
          ),
          const SizedBox(height: 6),
          Text('Error: ${error.toStringAsFixed(1)}%',
              style: TextStyle(fontSize: 12, color: Colors.orange)),
        ],
      ),
    );
  }

  List<Widget> _buildPhysicsCards(
      Color cardBg, Color textColor, Color subText) {
    final models =
        _brain?['physics_models'] as Map<String, dynamic>? ?? {};

    final config = <String, _PhysicsConfig>{
      '1_soil_moisture_balance': _PhysicsConfig(
          '1. Soil Moisture Balance', Icons.water_drop, Colors.blue),
      '2_evaporation_model': _PhysicsConfig(
          '2. Evaporation Model', Icons.waves, Colors.orange),
      '3_plant_water_uptake': _PhysicsConfig(
          '3. Plant Water Uptake', Icons.eco, Colors.green),
      '4_light_influence': _PhysicsConfig(
          '4. Light Influence', Icons.wb_sunny, Colors.amber),
      '5_temperature_effect': _PhysicsConfig(
          '5. Temperature Effect', Icons.thermostat, Colors.red),
      '6_time_evolution': _PhysicsConfig(
          '6. Time Evolution', Icons.timeline, Colors.purple),
    };

    final widgets = <Widget>[];
    for (final entry in config.entries) {
      final data = models[entry.key] as Map<String, dynamic>?;
      if (data == null) continue;
      final cfg = entry.value;

      widgets.add(Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border(left: BorderSide(color: cfg.color, width: 3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(cfg.icon, size: 20, color: cfg.color),
                const SizedBox(width: 8),
                Text(cfg.title,
                    style: GoogleFonts.inter(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: textColor)),
              ],
            ),
            if (data['equation'] != null) ...[
              const SizedBox(height: 4),
              Text(data['equation'].toString(),
                  style: GoogleFonts.firaCode(
                      fontSize: 11, color: cfg.color.withOpacity(0.8))),
            ],
            const SizedBox(height: 10),
            ...data.entries
                .where((e) => e.key != 'equation')
                .map((e) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(_formatKey(e.key),
                              style:
                                  TextStyle(fontSize: 12, color: subText)),
                          Text(_formatValue(e.value),
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: textColor)),
                        ],
                      ),
                    )),
          ],
        ),
      ));
    }
    return widgets;
  }

  String _formatKey(String key) {
    return key
        .replaceAll('_', ' ')
        .replaceFirstMapped(
            RegExp(r'^[a-z]'), (m) => m.group(0)!.toUpperCase());
  }

  String _formatValue(dynamic v) {
    if (v is double) return v.toStringAsFixed(2);
    return v.toString();
  }

  Color _accuracyColor(double pct) {
    if (pct >= 80) return Colors.green;
    if (pct >= 60) return Colors.orange;
    return Colors.red;
  }
}

class _PhysicsConfig {
  final String title;
  final IconData icon;
  final Color color;
  const _PhysicsConfig(this.title, this.icon, this.color);
}
