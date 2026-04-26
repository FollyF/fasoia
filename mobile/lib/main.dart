import 'package:flutter/material.dart';
import 'registration_screen.dart';
import 'login_sreen.dart';
import 'dashboard_entreprise.dart';
import 'dashboard_particulier.dart';


void main() {
  runApp(const FasoiaApp());
}

class FasoiaApp extends StatelessWidget {
  const FasoiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FASOIA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD32F2F),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF8F4ED),
        fontFamily: 'Georgia',
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFE0D8CC)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFE0D8CC)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFD32F2F), width: 2),
          ),
          labelStyle: const TextStyle(color: Color(0xFF8B7355)),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFD32F2F),
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 52),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ),
      ),
      // On définit la page de démarrage (Connexion)
      initialRoute: '/login',

      // On liste les écrans disponibles
      routes: {
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegistrationScreen(),
        '/dashboard/entreprise': (context) => const DashboardEntreprise(),
        '/dashboard/particulier': (context) => const DashboardParticulier(),
      },
    );
  }
}