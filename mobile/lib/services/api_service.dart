import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import 'storage_service.dart';

class ApiService {
  static String? _accessToken;
  static String? _refreshToken;
  
  static Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    return headers;
  }
  
  // Initialiser les tokens au démarrage
  static Future<void> init() async {
    _accessToken = await StorageService.getAccessToken();
    _refreshToken = await StorageService.getRefreshToken();
  }
  
  // Rafraîchir le token d'accès
  static Future<bool> refreshToken() async {
    if (_refreshToken == null) return false;
    
    try {
      final response = await http.post(
        Uri.parse('${AppConstants.baseUrl}/token/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': _refreshToken}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _accessToken = data['access'];
        await StorageService.saveTokens(
          access: _accessToken!,
          refresh: _refreshToken!,
        );
        return true;
      }
    } catch (e) {
      return false;
    }
    return false;
  }
  
  // Extraire le message d'erreur
  static String _extractErrorMessage(Map<String, dynamic> data) {
    if (data.containsKey('email')) {
      if (data['email'] is List) return data['email'][0];
      return data['email'].toString();
    }
    if (data.containsKey('error')) return data['error'];
    if (data.containsKey('detail')) return data['detail'];
    return 'Une erreur est survenue';
  }
  
  // ────────────────────────────────────────────────────────────
  // AUTHENTIFICATION
  // ────────────────────────────────────────────────────────────
  
  // Inscription
  static Future<Map<String, dynamic>> register({
    required String profileType,
    required String email,
    required String password,
    String? fullname,
    String? raisonSociale,
  }) async {
    print('📱 Tentative de connexion: $email');

    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/register/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'profile_type': profileType,
        'email': email,
        'password': password,
        if (fullname != null && fullname.isNotEmpty) 'fullname': fullname,
        if (raisonSociale != null && raisonSociale.isNotEmpty) 'raison_sociale': raisonSociale,
      }),
    );
    
    final data = jsonDecode(response.body);
    
    if (response.statusCode == 201) {
      if (data.containsKey('tokens')) {
        _accessToken = data['tokens']['access'];
        _refreshToken = data['tokens']['refresh'];
        await StorageService.saveTokens(
          access: _accessToken!,
          refresh: _refreshToken!,
        );
      }
      
      if (data.containsKey('user')) {
        await StorageService.saveUserInfo(
          userType: data['user']['profile_type'],
          email: data['user']['email'],
        );
      }
      
      return {'success': true, 'data': data};
    }
    
    return {'success': false, 'error': _extractErrorMessage(data)};
  }
  
  // Connexion
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    print('📱 Tentative de connexion: $email');
    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    
    print('📡 Status code: ${response.statusCode}');
    print('📦 Response body: ${response.body}');

    final data = jsonDecode(response.body);
    
    if (response.statusCode == 200) {
      if (data.containsKey('tokens')) {
        _accessToken = data['tokens']['access'];
        _refreshToken = data['tokens']['refresh']; 
        await StorageService.saveTokens(
          access: _accessToken!,
          refresh: _refreshToken!,
        );
      }
      
      if (data.containsKey('user')) {
        await StorageService.saveUserInfo(
          userType: data['user']['profile_type'],
          email: data['user']['email'],
        );
      }
      
      return {'success': true, 'data': data};
    }
    
    return {'success': false, 'error': _extractErrorMessage(data)};
  }
  
  // Déconnexion
  static Future<void> logout() async {
    _accessToken = null;
    _refreshToken = null;
    await StorageService.clearAll();
  }
  
  // Vérifier si l'utilisateur est connecté
  static Future<bool> isLoggedIn() async {
    final token = await StorageService.getAccessToken();
    return token != null;
  }
  
  // ────────────────────────────────────────────────────────────
  // ENTREPRISE
  // ────────────────────────────────────────────────────────────
  
  static Future<Map<String, dynamic>> getEntrepriseProfil() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/entreprise/profil/'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      if (await refreshToken()) {
        return getEntrepriseProfil();
      }
      throw Exception('Session expirée');
    }
    throw Exception('Erreur chargement profil');
  }
  
  static Future<Map<String, dynamic>> updateEntrepriseProfil(Map<String, dynamic> data) async {
    final response = await http.patch(
      Uri.parse('${AppConstants.baseUrl}/entreprise/profil/'),
      headers: _headers,
      body: jsonEncode(data),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      if (await refreshToken()) {
        return updateEntrepriseProfil(data);
      }
      throw Exception('Session expirée');
    }
    throw Exception('Erreur mise à jour');
  }
  
  static Future<List<dynamic>> getEntrepriseRecommandations() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/entreprise/recommandations/'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['recommandations'] ?? [];
    }
    throw Exception('Erreur chargement recommandations');
  }
  
  // ────────────────────────────────────────────────────────────
  // CANDIDAT (PARTICULIER)
  // ────────────────────────────────────────────────────────────
  
  static Future<Map<String, dynamic>> getCandidatProfil() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/candidat/profil/'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      if (await refreshToken()) {
        return getCandidatProfil();
      }
      throw Exception('Session expirée');
    }
    throw Exception('Erreur chargement profil');
  }
  
  static Future<Map<String, dynamic>> updateCandidatProfil(Map<String, dynamic> data) async {
    final response = await http.patch(
      Uri.parse('${AppConstants.baseUrl}/candidat/profil/'),
      headers: _headers,
      body: jsonEncode(data),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      if (await refreshToken()) {
        return updateCandidatProfil(data);
      }
      throw Exception('Session expirée');
    }
    throw Exception('Erreur mise à jour');
  }
  
  static Future<List<dynamic>> getCandidatOffresRecommandees() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/candidat/offres-recommandees/'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['offres'] ?? [];
    }
    throw Exception('Erreur chargement offres');
  }
  
  static Future<List<dynamic>> getCandidatConvocations() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/candidat/convocations/'),
      headers: _headers,
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['convocations'] ?? [];
    }
    throw Exception('Erreur chargement convocations');
  }
  
  static Future<Map<String, dynamic>> repondreConvocation(int convId, String action) async {
    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/candidat/convocations/$convId/repondre/'),
      headers: _headers,
      body: jsonEncode({'action': action}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      if (await refreshToken()) {
        return repondreConvocation(convId, action);
      }
      throw Exception('Session expirée');
    }
    throw Exception('Erreur réponse convocation');
  }
}