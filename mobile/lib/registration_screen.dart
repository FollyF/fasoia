import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen>
    with SingleTickerProviderStateMixin {
  // ─── État ────────────────────────────────────────────────────────────────
  String _profileType = 'particulier';
  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  String? _errorMessage;

  // ─── Contrôleurs ─────────────────────────────────────────────────────────
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _nameController = TextEditingController();

  // ─── Animation ───────────────────────────────────────────────────────────
  late final AnimationController _animController;
  late final Animation<double> _fadeAnim;
  late final Animation<Offset> _slideAnim;

  // ─── Couleurs ─────────────────────────────────────────────────────────────
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
    _confirmPasswordController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  // ─── Inscription ──────────────────────────────────────────────────────────
  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final url = Uri.parse('http://127.0.0.1:8000/api/register/');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'profile_type': _profileType,
          'email': _emailController.text.trim(),
          'password': _passwordController.text,
          'fullname': _profileType == 'particulier' ? _nameController.text.trim() : '',
          'raison_sociale': _profileType == 'entreprise' ? _nameController.text.trim() : '',
        }),
      );

      if (response.statusCode == 201) {
        if (mounted) _showSuccessSnackbar();
      } else {
        final body = jsonDecode(response.body);
        setState(() => _errorMessage = body['message'] ?? 'Une erreur est survenue.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Impossible de contacter le serveur.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showSuccessSnackbar() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Row(
          children: [
            Icon(Icons.check_circle_outline, color: Colors.white),
            SizedBox(width: 10),
            Text('Compte créé avec succès !'),
          ],
        ),
        backgroundColor: Colors.green.shade700,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

// ─── UI ───────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _cream,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnim,
          child: SlideTransition(
            position: _slideAnim,
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(), // ← ajouté
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20), // ← 32→20
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Logo / En-tête ──────────────────────────────────────
                    Center(
                      child: Column(
                        children: [
                          Container(
                            width: 56,  // ← 64→56
                            height: 56, // ← 64→56
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
                            child: const Icon(Icons.business_center_outlined,
                                color: Colors.white, size: 28), // ← 32→28
                          ),
                          const SizedBox(height: 12), // ← 16→12
                          const Text(
                            'FASOIA',
                            style: TextStyle(
                              fontSize: 26,            // ← 28→26
                              fontWeight: FontWeight.w800,
                              color: _ink,
                              letterSpacing: 4,
                            ),
                          ),
                          const SizedBox(height: 4),  // ← 6→4
                          const Text(
                            'Créez votre compte',
                            style: TextStyle(
                              fontSize: 14,            // ← 15→14
                              color: _muted,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24), // ← 36→24

                    // ── Sélecteur de profil ─────────────────────────────────
                    // (inchangé)
                    const Text(
                      'Type de compte',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: _muted,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 8),  // ← 10→8
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _border),
                      ),
                      padding: const EdgeInsets.all(4),
                      child: Row(
                        children: [
                          _ProfileTab(
                            label: 'Particulier',
                            icon: Icons.person_outline,
                            isSelected: _profileType == 'particulier',
                            onTap: () => setState(() {
                              _profileType = 'particulier';
                              _nameController.clear();
                            }),
                          ),
                          _ProfileTab(
                            label: 'Entreprise',
                            icon: Icons.business_outlined,
                            isSelected: _profileType == 'entreprise',
                            onTap: () => setState(() {
                              _profileType = 'entreprise';
                              _nameController.clear();
                            }),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 18), // ← 24→18

                    // ── Champs ──────────────────────────────────────────────
                    _buildLabel(_profileType == 'particulier' ? 'Nom complet' : 'Raison sociale'),
                    const SizedBox(height: 6), // ← 8→6
                    TextFormField(
                      controller: _nameController,
                      textCapitalization: TextCapitalization.words,
                      decoration: InputDecoration(
                        hintText: _profileType == 'particulier'
                            ? 'Ex : Konaté Ibrahim'
                            : 'Ex : SARL BurkinaTech',
                        prefixIcon: Icon(
                          _profileType == 'particulier'
                              ? Icons.person_outline
                              : Icons.business_outlined,
                          color: _muted,
                        ),
                      ),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? 'Ce champ est requis' : null,
                    ),

                    const SizedBox(height: 14), // ← 18→14
                    _buildLabel('Adresse email'),
                    const SizedBox(height: 6),  // ← 8→6
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        hintText: 'exemple@email.com',
                        prefixIcon: Icon(Icons.mail_outline, color: _muted),
                      ),
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) return 'L\'email est requis';
                        if (!v.contains('@')) return 'Email invalide';
                        return null;
                      },
                    ),

                    const SizedBox(height: 14), // ← 18→14
                    _buildLabel('Mot de passe'),
                    const SizedBox(height: 6),  // ← 8→6
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      decoration: InputDecoration(
                        hintText: 'Minimum 8 caractères',
                        prefixIcon: const Icon(Icons.lock_outline, color: _muted),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: _muted,
                          ),
                          onPressed: () =>
                              setState(() => _obscurePassword = !_obscurePassword),
                        ),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Le mot de passe est requis';
                        if (v.length < 8) return 'Minimum 8 caractères';
                        return null;
                      },
                    ),

                    const SizedBox(height: 14), // ← 18→14
                    _buildLabel('Confirmer le mot de passe'),
                    const SizedBox(height: 6),  // ← 8→6
                    TextFormField(
                      controller: _confirmPasswordController,
                      obscureText: _obscureConfirm,
                      decoration: InputDecoration(
                        hintText: 'Répétez votre mot de passe',
                        prefixIcon: const Icon(Icons.lock_outline, color: _muted),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscureConfirm
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: _muted,
                          ),
                          onPressed: () =>
                              setState(() => _obscureConfirm = !_obscureConfirm),
                        ),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Veuillez confirmer le mot de passe';
                        if (v != _passwordController.text) return 'Les mots de passe ne correspondent pas';
                        return null;
                      },
                    ),

                    // ── Message d'erreur ────────────────────────────────────
                    if (_errorMessage != null) ...[
                      const SizedBox(height: 12), // ← 16→12
                      Container(
                        padding: const EdgeInsets.all(10), // ← 12→10
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline,
                                color: Colors.red.shade700, size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _errorMessage!,
                                style: TextStyle(
                                    color: Colors.red.shade700, fontSize: 13),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 22), // ← 28→22

                    // ── Bouton ──────────────────────────────────────────────
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 250),
                      child: _isLoading
                          ? Container(
                              key: const ValueKey('loading'),
                              height: 50,  // ← 52→50
                              width: double.infinity, // ← ajouté
                              decoration: BoxDecoration(
                                color: _red.withOpacity(0.8),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Center(
                                child: SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    color: Colors.white,
                                    strokeWidth: 2.5,
                                  ),
                                ),
                              ),
                            )
                          : SizedBox(
                              width: double.infinity, // ← bouton pleine largeur garanti
                              child: ElevatedButton(
                                key: const ValueKey('button'),
                                onPressed: _register,
                                child: const Text('Créer mon compte'),
                              ),
                            ),
                    ),

                    const SizedBox(height: 16), // ← 20→16

                    // ── Connexion ───────────────────────────────────────────
                    Center(
                      child: TextButton(
                        onPressed: () {
                          Navigator.pushNamed(context, '/login');
                        },
                        child: RichText(
                          text: const TextSpan(
                            text: 'Déjà un compte ? ',
                            style: TextStyle(color: _muted, fontSize: 14),
                            children: [
                              TextSpan(
                                text: 'Se connecter',
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

                    const SizedBox(height: 8), // ← espace bas de sécurité
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: _muted,
        letterSpacing: 0.5,
      ),
    );
  }
}

// ─── Widget onglet profil ─────────────────────────────────────────────────────
class _ProfileTab extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _ProfileTab({
    required this.label,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 11),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFFD32F2F) : Colors.transparent,
            borderRadius: BorderRadius.circular(9),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon,
                  size: 16,
                  color: isSelected ? Colors.white : const Color(0xFF8B7355)),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isSelected ? Colors.white : const Color(0xFF8B7355),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}