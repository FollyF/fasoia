import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/fasoia_logo.dart';

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

  // ─── Logique de Connexion avec ApiService ────────────────────────────────
  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await ApiService.login(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );

      if (result['success']) {
        final userData = result['data']['user'];
        final profileType = userData['profile_type'];
        
        if (mounted) {
          switch (profileType) {
            case 'entreprise':
              Navigator.pushReplacementNamed(context, '/dashboard_entreprise');
              break;
            case 'candidat':
              Navigator.pushReplacementNamed(context, '/dashboard_candidat');
              break;
            case 'recruteur':
              Navigator.pushReplacementNamed(context, '/dashboard_recruteur');
              break;
            default:
              // 'particulier' ou tout autre cas
              Navigator.pushReplacementNamed(context, '/dashboard_particulier');
              break;
          }
        }
      } else {
        setState(() => _errorMessage = result['error']);
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
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnim,
          child: SlideTransition(
            position: _slideAnim,
            child: Center(
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
                            const SizedBox(height: 12),
                            const FasoiaLogo(mainColor: AppColors.ink, fontSize: 42),
                            const SizedBox(height: 4),
                            //const Text(
                            //  'Bon retour parmi nous',
                            //  style: TextStyle(fontSize: 10, color: AppColors.muted),
                            //),
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
                          hintText: 'exemple@email.com',
                          prefixIcon: Icon(Icons.mail_outline, color: AppColors.muted),
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
                          prefixIcon: const Icon(Icons.lock_outline, color: AppColors.muted),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscurePassword
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                              color: AppColors.muted,
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
                          onPressed: () {
                            // TODO: Ajouter la page de réinitialisation
                          },
                          child: const Text(
                            'Mot de passe oublié ?',
                            style: TextStyle(color: AppColors.muted, fontSize: 13),
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
                            Navigator.pushReplacementNamed(context, '/register');
                          },
                          child: RichText(
                            text: const TextSpan(
                              text: "Pas encore de compte ? ",
                              style: TextStyle(color: AppColors.muted, fontSize: 14),
                              children: [
                                TextSpan(
                                  text: "S'inscrire",
                                  style: TextStyle(
                                    color: AppColors.red,
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
    return Text(
      text,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: AppColors.muted,
      ),
    );
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
          Expanded(
            child: Text(
              msg,
              style: TextStyle(color: Colors.red.shade700, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return Container(
      height: 50,
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.red.withOpacity(0.8),
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
    );
  }
}