// lib/services/storage_service.dart
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class StorageService {
  // Sauvegarder les tokens JWT
  static Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.accessTokenKey, access);
    await prefs.setString(AppConstants.refreshTokenKey, refresh);
    print('✅ Tokens sauvegardés');
  }
  
  // Récupérer le token d'accès
  static Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(AppConstants.accessTokenKey);
    print('🔑 Access token: ${token != null ? 'présent' : 'absent'}');
    return token;
  }
  
  // Récupérer le token de rafraîchissement
  static Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.refreshTokenKey);
  }
  
  // Sauvegarder les infos utilisateur
  static Future<void> saveUserInfo({
    required String userType,
    required String email,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.userTypeKey, userType);
    await prefs.setString(AppConstants.userEmailKey, email);
    print('👤 User info sauvegardées: $userType - $email');
  }
  
  // Récupérer les infos utilisateur
  static Future<Map<String, String?>> getUserInfo() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'userType': prefs.getString(AppConstants.userTypeKey),
      'email': prefs.getString(AppConstants.userEmailKey),
    };
  }
  
  // Récupérer le type d'utilisateur
  static Future<String?> getUserType() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.userTypeKey);
  }
  
  // Récupérer l'email
  static Future<String?> getUserEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.userEmailKey);
  }
  
  // Vérifier si l'utilisateur est connecté
  static Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null;
  }
  
  // Tout effacer (déconnexion)
  static Future<void> clearAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    print('🗑️ Toutes les données effacées');
  }
}