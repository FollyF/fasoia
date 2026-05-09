// lib/utils/constants.dart
import 'package:flutter/material.dart';

class AppColors {
  static const red = Color(0xFFD32F2F);
  static const cream = Color(0xFFF8F4ED);
  static const ink = Color(0xFF2C1810);
  static const muted = Color(0xFF8B7355);
  static const border = Color(0xFFE0D8CC);
  static const teal = Color(0xFF0D7377);
  static const white = Colors.white;
  static const green = Color(0xFF28A745);
  static const orange = Color(0xFFF59E0B);
}

class AppConstants {
  // Pour Android physique (avec adb reverse)
  static const String baseUrl = 'http://localhost:8000/api';
  // Pour Android Emulator :
  // static const String baseUrl = 'http://10.0.2.2:8000/api';
  // Pour Chrome :
  // static const String baseUrl = 'http://localhost:8000/api';
  
  // Clés SharedPreferences
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userTypeKey = 'user_type';
  static const String userEmailKey = 'user_email';
}