import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../utils/constants.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    // Initialiser ApiService (charger les tokens)
    await ApiService.init();

    // Attendre 1.5 secondes
    await Future.delayed(const Duration(milliseconds: 1500));

    // Vérifier si l'utilisateur est connecté
    final token = await StorageService.getAccessToken();
    final userInfo = await StorageService.getUserInfo();
    final userType = userInfo['userType'];

    if (mounted) {
      if (token != null && userType != null) {
        // Utilisateur déjà connecté → redirection selon son type
        if (userType == 'entreprise') {
          Navigator.pushReplacementNamed(context, '/dashboard_entreprise');
        } else {
          Navigator.pushReplacementNamed(context, '/dashboard_particulier');
        }
      } else {
        // Non connecté → page de connexion
        Navigator.pushReplacementNamed(context, '/login');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.red,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(
                Icons.business_center_outlined,
                color: Colors.white,
                size: 40,
              ),
            ),
            const SizedBox(height: 24),
            // Titre
            const Text(
              'FASOIA',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.w800,
                color: AppColors.ink,
                letterSpacing: 4,
              ),
            ),
            const SizedBox(height: 8),
            // Sous-titre
            const Text(
              'Le réseau professionnel',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.muted,
              ),
            ),
            const SizedBox(height: 48),
            // Spinner de chargement
            const CircularProgressIndicator(
              color: AppColors.red,
            ),
          ],
        ),
      ),
    );
  }
}