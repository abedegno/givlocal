import 'package:flutter/material.dart';

class GivLocalColors {
  static const Color solar = Color(0xFFFACC15);
  static const Color battery = Color(0xFF22C55E);
  static const Color home = Color(0xFF818CF8);
  static const Color grid = Color(0xFFF87171);
  static const Color accent = Color(0xFF818CF8);
  static const Color background = Color(0xFF0F172A);
  static const Color card = Color(0x0AFFFFFF); // rgba(255,255,255,0.04)
  static const Color cardBorder = Color(0x14FFFFFF); // rgba(255,255,255,0.08)
  static const Color textPrimary = Color(0xFFE2E8F0);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF7485A0);
}

class Spacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
}

final ThemeData darkTheme = ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: GivLocalColors.background,
  colorScheme: const ColorScheme.dark(
    primary: GivLocalColors.accent,
    secondary: GivLocalColors.solar,
    surface: GivLocalColors.card,
    onPrimary: GivLocalColors.textPrimary,
    onSecondary: GivLocalColors.background,
    onSurface: GivLocalColors.textPrimary,
  ),
  textTheme: const TextTheme(
    bodyLarge: TextStyle(color: GivLocalColors.textPrimary),
    bodyMedium: TextStyle(color: GivLocalColors.textSecondary),
    bodySmall: TextStyle(color: GivLocalColors.textMuted),
    titleLarge: TextStyle(color: GivLocalColors.textPrimary),
    titleMedium: TextStyle(color: GivLocalColors.textPrimary),
    titleSmall: TextStyle(color: GivLocalColors.textSecondary),
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: GivLocalColors.background,
    foregroundColor: GivLocalColors.textPrimary,
    elevation: 0,
  ),
  bottomNavigationBarTheme: const BottomNavigationBarThemeData(
    backgroundColor: GivLocalColors.background,
    selectedItemColor: GivLocalColors.accent,
    unselectedItemColor: GivLocalColors.textMuted,
    type: BottomNavigationBarType.fixed,
  ),
  cardTheme: CardThemeData(
    color: GivLocalColors.card,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
      side: const BorderSide(color: GivLocalColors.cardBorder),
    ),
  ),
  useMaterial3: true,
);
