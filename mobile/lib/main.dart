import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/dashboard_entreprise.dart';
import 'screens/dashboard_particulier.dart';
import 'screens/dashboard_candidat.dart';
import 'screens/dashboard_candidat_test.dart';
import 'utils/constants.dart';
import 'services/storage_service.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService.init();
  
  String initialRoute = '/';
  final isLoggedIn = await ApiService.isLoggedIn();
  
  if (isLoggedIn) {
    final isValid = await ApiService.checkAndRestoreSession();
    if (isValid) {
      final dashboardRoute = await StorageService.getDashboardRoute();
      initialRoute = dashboardRoute ?? '/dashboard_particulier';
      print('🔐 Session restaurée, redirection vers: $initialRoute');
    } else {
      await ApiService.logout();
      print('🔐 Token invalide, déconnexion');
    }
  }
  
  runApp(FasoiaApp(initialRoute: initialRoute));
}

class FasoiaApp extends StatelessWidget {
  
  final String initialRoute;

  const FasoiaApp({super.key, required this.initialRoute});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FASOIA',
      debugShowCheckedModeBanner: false,
      initialRoute: initialRoute,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.red,
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: AppColors.cream,
        fontFamily: 'Poppins',
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.white,
          contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.red, width: 2),
          ),
          labelStyle: const TextStyle(color: AppColors.muted),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.red,
            foregroundColor: AppColors.white,
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
      
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/dashboard_entreprise': (context) => const DashboardEntreprise(),
        '/dashboard_particulier': (context) => const DashboardParticulier(),
        '/dashboard_candidat': (context) => const DashboardCandidat(),
        '/dashboard_candidat_test': (context) => const DashboardCandidatTest(),
      },
    );
  }
}