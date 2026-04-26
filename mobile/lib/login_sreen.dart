import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  // ─── État ────────────────────────────────────────────────────────────────
  bool _isLoading = false;
  bool _obscurePassword = true;
  String? _errorMessage;

  // ─── Contrôleurs ─────────────────────────────────────────────────────────
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  // ─── Animation ───────────────────────────────────────────────────────────
  late final AnimationController _animController;
  late final Animation<double> _fadeAnim;
  late final Animation<Offset> _slideAnim;

  // ─── Couleurs (Identiques à Registration) ────────────────────────────────
  static const _red = Color(0xFFD32F2F);
  static const _cream = Color(0xFFF8F4ED);
  static const _ink = Color(0xFF2C1810);
  static const _muted = Color(0xFF8B7355);
  static const _border = Color(0xFFE0D8CC);

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animController, curve: Curves.easeOut));
    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  // ─── Logique de Connexion ────────────────────────────────────────────────
  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final url = Uri.parse('http://127.0.0.1:8000/api/login/');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': _emailController.text.trim(),
          'password': _passwordController.text,
        }),
      );

      final data = jsonDecode(response.body);
      debugPrint('STATUS: ${response.statusCode}');
      debugPrint('BODY: ${response.body}');
      
      if (response.statusCode == 200) {
        // Succès : Redirection vers le Dashboard de FASOIA
        if (mounted){

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Connexion réussie !'), backgroundColor: Colors.green),
          );
          // --- LOGIQUE DE REDIRECTION ---
          String profileType = data['user']['profile_type'];

          if (profileType == 'entreprise') {
            Navigator.pushReplacementNamed(context, '/dashboard/entreprise');
          }else {
            Navigator.pushReplacementNamed(context, '/dashboard/particulier');
          }
        } 
      } else {
        setState(() => _errorMessage = data['message'] ?? 'Identifiants incorrects.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Impossible de contacter le serveur.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _cream,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnim,
          child: SlideTransition(
            position: _slideAnim,
            child: Center( // On centre pour la connexion
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // ── Logo / En-tête ────────────────────────────────────
                      Center(
                        child: Column(
                          children: [
                            Container(
                              width: 56,
                              height: 56,
                              decoration: BoxDecoration(
                                color: _red,
                                borderRadius: BorderRadius.circular(14),
                                boxShadow: [
                                  BoxShadow(
                                    color: _red.withOpacity(0.3),
                                    blurRadius: 16,
                                    offset: const Offset(0, 6),
                                  ),
                                ],
                              ),
                              child: const Icon(Icons.lock_person_outlined,
                                  color: Colors.white, size: 28),
                            ),
                            const SizedBox(height: 12),
                            const Text(
                              'FASOIA',
                              style: TextStyle(
                                fontSize: 26,
                                fontWeight: FontWeight.w800,
                                color: _ink,
                                letterSpacing: 4,
                              ),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Bon retour parmi nous',
                              style: TextStyle(fontSize: 14, color: _muted),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 40),

                      // ── Champs ──────────────────────────────────────────────
                      _buildLabel('Adresse email'),
                      const SizedBox(height: 6),
                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(
                          hintText: 'votre@email.com',
                          prefixIcon: Icon(Icons.mail_outline, color: _muted),
                        ),
                        validator: (v) => (v == null || v.isEmpty) ? 'Email requis' : null,
                      ),

                      const SizedBox(height: 18),

                      _buildLabel('Mot de passe'),
                      const SizedBox(height: 6),
                      TextFormField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        decoration: InputDecoration(
                          hintText: '••••••••',
                          prefixIcon: const Icon(Icons.lock_outline, color: _muted),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscurePassword
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                              color: _muted,
                            ),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                        validator: (v) => (v == null || v.isEmpty) ? 'Mot de passe requis' : null,
                      ),

                      // ── Mot de passe oublié ─────────────────────────────────
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(
                          onPressed: () {},
                          child: const Text(
                            'Mot de passe oublié ?',
                            style: TextStyle(color: _muted, fontSize: 13),
                          ),
                        ),
                      ),

                      // ── Erreur ──────────────────────────────────────────────
                      if (_errorMessage != null) ...[
                        const SizedBox(height: 12),
                        _buildErrorBox(_errorMessage!),
                      ],

                      const SizedBox(height: 24),

                      // ── Bouton ──────────────────────────────────────────────
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 250),
                        child: _isLoading
                            ? _buildLoadingState()
                            : SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  onPressed: _login,
                                  child: const Text('Se connecter'),
                                ),
                              ),
                      ),

                      const SizedBox(height: 20),

                      // ── Inscription ─────────────────────────────────────────
                      Center(
                        child: TextButton(
                          onPressed: () {
                            Navigator.pushNamed(context, '/register');
                          },
                          child: RichText(
                            text: const TextSpan(
                              text: "Pas encore de compte ? ",
                              style: TextStyle(color: _muted, fontSize: 14),
                              children: [
                                TextSpan(
                                  text: "S'inscrire",
                                  style: TextStyle(
                                    color: _red,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ─── Helpers UI ────────────────────────────────────────────────────────────

  Widget _buildLabel(String text) {
    return Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: _muted));
  }

  Widget _buildErrorBox(String msg) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: Colors.red.shade700, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(msg, style: TextStyle(color: Colors.red.shade700, fontSize: 13))),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return Container(
      height: 50,
      width: double.infinity,
      decoration: BoxDecoration(color: _red.withOpacity(0.8), borderRadius: BorderRadius.circular(12)),
      child: const Center(child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))),
    );
  }
}