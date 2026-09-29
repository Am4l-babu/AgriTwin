/// App-wide theme constants matching the Next.js dashboard design.

import 'package:flutter/material.dart';

class AppColors {
  // Core
  static const black = Color(0xFF000000);
  static const white = Color(0xFFFFFFFF);
  static const background = Color(0xFFF8FAFC); // slate-50
  static const surface = Color(0xFFFFFFFF);
  static const surfaceBorder = Color(0x14000000); // black/8

  // Sensor colors (from Tailwind palette)
  static const emerald50 = Color(0xFFECFDF5);
  static const emerald100 = Color(0xFFD1FAE5);
  static const emerald200 = Color(0xFFA7F3D0);
  static const emerald400 = Color(0xFF34D399);
  static const emerald500 = Color(0xFF10B981);
  static const emerald600 = Color(0xFF059669);

  static const amber50 = Color(0xFFFFFBEB);
  static const amber400 = Color(0xFFFBBF24);
  static const amber500 = Color(0xFFF59E0B);
  static const amber600 = Color(0xFFD97706);

  static const cyan50 = Color(0xFFECFEFF);
  static const cyan400 = Color(0xFF22D3EE);
  static const cyan500 = Color(0xFF06B6D4);
  static const cyan600 = Color(0xFF0891B2);

  static const yellow50 = Color(0xFFFEFCE8);
  static const yellow200 = Color(0xFFFDE68A);
  static const yellow500 = Color(0xFFEAB308);
  static const yellow600 = Color(0xFFCA8A04);

  static const violet50 = Color(0xFFF5F3FF);
  static const violet500 = Color(0xFF8B5CF6);
  static const violet600 = Color(0xFF7C3AED);

  static const red400 = Color(0xFFF87171);
  static const red500 = Color(0xFFEF4444);

  // Slate
  static const slate100 = Color(0xFFF1F5F9);
  static const slate200 = Color(0xFFE2E8F0);
  static const slate400 = Color(0xFF94A3B8);

  // Interpretation band colors
  static const bandVeryDry = Color(0xFFF87171); // red-400
  static const bandDry = Color(0xFFFB923C); // orange-400
  static const bandOptimal = Color(0xFF34D399); // emerald-400
  static const bandWet = Color(0xFF60A5FA); // blue-400
  static const bandSaturated = Color(0xFF2563EB); // blue-600
  static const bandVeryAcidic = Color(0xFFEF4444); // red-500
  static const bandAcidic = Color(0xFFFB923C); // orange-400
  static const bandAlkaline = Color(0xFF60A5FA); // blue-400
  static const bandVeryAlkaline = Color(0xFF6366F1); // indigo-500
}

class SensorMeta {
  final IconData icon;
  final String label;
  final String unit;
  final Color color;
  final Color bgColor;
  final Color borderColor;

  const SensorMeta({
    required this.icon,
    required this.label,
    required this.unit,
    required this.color,
    required this.bgColor,
    required this.borderColor,
  });
}

final Map<String, SensorMeta> sensorMetaMap = {
  'temperature': SensorMeta(
    icon: Icons.thermostat,
    label: 'Temperature',
    unit: '°C',
    color: AppColors.amber500,
    bgColor: AppColors.amber50,
    borderColor: AppColors.amber500.withValues(alpha: 0.2),
  ),
  'humidity': SensorMeta(
    icon: Icons.water_drop_outlined,
    label: 'Humidity',
    unit: '%',
    color: AppColors.cyan500,
    bgColor: AppColors.cyan50,
    borderColor: AppColors.cyan500.withValues(alpha: 0.2),
  ),
  'soil_moisture': SensorMeta(
    icon: Icons.water_drop,
    label: 'Soil Moisture',
    unit: '%',
    color: AppColors.emerald500,
    bgColor: AppColors.emerald50,
    borderColor: AppColors.emerald500.withValues(alpha: 0.2),
  ),
  'light': SensorMeta(
    icon: Icons.wb_sunny,
    label: 'Light (LDR)',
    unit: 'lux',
    color: AppColors.yellow500,
    bgColor: AppColors.yellow50,
    borderColor: AppColors.yellow500.withValues(alpha: 0.2),
  ),
  'ph': SensorMeta(
    icon: Icons.science,
    label: 'pH Sensor',
    unit: 'pH',
    color: AppColors.violet500,
    bgColor: AppColors.violet50,
    borderColor: AppColors.violet500.withValues(alpha: 0.2),
  ),
};

final Map<String, String> methodLabels = {
  'offset_correction': 'Offset Correction',
  'two_point_linear': 'Two-Point Linear',
  'three_point_polynomial': 'Three-Point Polynomial',
  'not_calibrated': 'Not Calibrated',
};

final Map<String, Color> bandColors = {
  'very_dry': AppColors.bandVeryDry,
  'dry': AppColors.bandDry,
  'optimal': AppColors.bandOptimal,
  'wet': AppColors.bandWet,
  'saturated': AppColors.bandSaturated,
  'very_acidic': AppColors.bandVeryAcidic,
  'acidic': AppColors.bandAcidic,
  'alkaline': AppColors.bandAlkaline,
  'very_alkaline': AppColors.bandVeryAlkaline,
};
