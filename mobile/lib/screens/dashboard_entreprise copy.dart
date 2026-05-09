import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

class DashboardEntreprise extends StatefulWidget {
  const DashboardEntreprise({super.key});

  @override
  State<DashboardEntreprise> createState() => _DashboardEntrepriseState();
}

class _DashboardEntrepriseState extends State<DashboardEntreprise>
    with TickerProviderStateMixin {
  // ─── État ────────────────────────────────────────────────────────────────
  bool _isLoading = true;
  bool _isSaving = false;
  bool _showProfileForm = false;
  int _currentTab = 0;
  String? _errorMessage;
  String? _successMessage;

  Map<String, dynamic> _profil = {};
  List<dynamic> _recommandations = [];

  // ─── Animations ──────────────────────────────────────────────────────────
  late final AnimationController _headerAnim;
  late final AnimationController _statsAnim;
  late final Animation<double> _headerFade;
  late final Animation<Offset> _headerSlide;
  late final Animation<double> _statsFade;

  // ─── Contrôleurs formulaire ───────────────────────────────────────────────
  final _formKey = GlobalKey<FormState>();
  final _domaineCtrl = TextEditingController();
  final _localisationCtrl = TextEditingController();
  final _tailleCtrl = TextEditingController();
  final _anneeCreationCtrl = TextEditingController();
  final _siteWebCtrl = TextEditingController();
  final _competencesClesCtrl = TextEditingController();
  final _anneesExpCtrl = TextEditingController();
  final _nbProjetsCtrl = TextEditingController();
  final _descriptionCtrl = TextEditingController();
  final _paysInterventionCtrl = TextEditingController();
  final _rayonActionCtrl = TextEditingController();
  final _chiffreAffairesCtrl = TextEditingController();
  final _capitalSocialCtrl = TextEditingController();
  final _montantMinCtrl = TextEditingController();
  final _montantMaxCtrl = TextEditingController();
  List<String> _typesOpportunites = [];

  final List<String> _tabLabels = [
    'Informations',
    'Compétences',
    'Zones',
    'Financier',
    'Préférences',
  ];

  final List<IconData> _tabIcons = [
    Icons.business_outlined,
    Icons.code_outlined,
    Icons.map_outlined,
    Icons.bar_chart_outlined,
    Icons.tune_outlined,
  ];

  @override
  void initState() {
    super.initState();

    _headerAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _statsAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _headerFade =
        CurvedAnimation(parent: _headerAnim, curve: Curves.easeOut);
    _headerSlide = Tween<Offset>(
      begin: const Offset(0, -0.05),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _headerAnim, curve: Curves.easeOut));
    _statsFade =
        CurvedAnimation(parent: _statsAnim, curve: Curves.easeOut);

    _loadData();
  }

  @override
  void dispose() {
    _headerAnim.dispose();
    _statsAnim.dispose();
    _domaineCtrl.dispose();
    _localisationCtrl.dispose();
    _tailleCtrl.dispose();
    _anneeCreationCtrl.dispose();
    _siteWebCtrl.dispose();
    _competencesClesCtrl.dispose();
    _anneesExpCtrl.dispose();
    _nbProjetsCtrl.dispose();
    _descriptionCtrl.dispose();
    _paysInterventionCtrl.dispose();
    _rayonActionCtrl.dispose();
    _chiffreAffairesCtrl.dispose();
    _capitalSocialCtrl.dispose();
    _montantMinCtrl.dispose();
    _montantMaxCtrl.dispose();
    super.dispose();
  }

  // ─── Chargement données ──────────────────────────────────────────────────
  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final profil = await ApiService.getEntrepriseProfil();
      final recos = await ApiService.getEntrepriseRecommandations();

      setState(() {
        _profil = profil;
        _recommandations = recos;
        _isLoading = false;
      });

      _populateControllers();
      _headerAnim.forward();
      Future.delayed(const Duration(milliseconds: 200),
          () => _statsAnim.forward());
    } catch (e) {
      setState(() {
        _errorMessage = 'Impossible de charger les données.';
        _isLoading = false;
      });
    }
  }

  void _populateControllers() {
    _domaineCtrl.text = _profil['domaineActive'] ?? '';
    _localisationCtrl.text = _profil['localisation'] ?? '';
    _tailleCtrl.text = _profil['taille']?.toString() ?? '';
    _anneeCreationCtrl.text = _profil['annee_creation']?.toString() ?? '';
    _siteWebCtrl.text = _profil['site_web'] ?? '';
    _competencesClesCtrl.text = _profil['competencesCles'] ?? '';
    _anneesExpCtrl.text = _profil['annees_experience']?.toString() ?? '';
    _nbProjetsCtrl.text = _profil['nb_projets_realises']?.toString() ?? '';
    _descriptionCtrl.text = _profil['description'] ?? '';

    final pays = _profil['pays_intervention'];
    if (pays is List) {
      _paysInterventionCtrl.text = pays.join(', ');
    } else {
      _paysInterventionCtrl.text = pays ?? '';
    }

    _rayonActionCtrl.text = _profil['rayon_action']?.toString() ?? '';
    _chiffreAffairesCtrl.text = _profil['chiffre_affaires']?.toString() ?? '';
    _capitalSocialCtrl.text = _profil['capital_social']?.toString() ?? '';
    _montantMinCtrl.text = _profil['montant_min']?.toString() ?? '';
    _montantMaxCtrl.text = _profil['montant_max']?.toString() ?? '';

    final types = _profil['types_opportunites'];
    if (types is List) {
      _typesOpportunites = List<String>.from(types);
    }
  }

  // ─── Calcul complétion profil ─────────────────────────────────────────────
  int get _pourcentageCompletion {
    final fields = [
      _profil['domaineActive'],
      _profil['localisation'],
      _profil['competencesCles'],
      _profil['pays_intervention'],
      _profil['chiffre_affaires'],
      _profil['types_opportunites'],
    ];
    final filled = fields.where((f) {
      if (f == null) return false;
      if (f is String) return f.isNotEmpty;
      if (f is List) return f.isNotEmpty;
      return true;
    }).length;
    return ((filled / fields.length) * 100).round();
  }

  bool get _profilComplet => _pourcentageCompletion == 100;

  // ─── Sauvegarde profil ───────────────────────────────────────────────────
  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isSaving = true;
      _errorMessage = null;
      _successMessage = null;
    });

    try {
      final paysRaw = _paysInterventionCtrl.text
          .split(',')
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList();

      final data = {
        'domaineActive': _domaineCtrl.text.trim(),
        'localisation': _localisationCtrl.text.trim(),
        if (_tailleCtrl.text.isNotEmpty)
          'taille': int.tryParse(_tailleCtrl.text),
        if (_anneeCreationCtrl.text.isNotEmpty)
          'annee_creation': int.tryParse(_anneeCreationCtrl.text),
        if (_siteWebCtrl.text.isNotEmpty) 'site_web': _siteWebCtrl.text.trim(),
        'competencesCles': _competencesClesCtrl.text.trim(),
        if (_anneesExpCtrl.text.isNotEmpty)
          'annees_experience': int.tryParse(_anneesExpCtrl.text),
        if (_nbProjetsCtrl.text.isNotEmpty)
          'nb_projets_realises': int.tryParse(_nbProjetsCtrl.text),
        if (_descriptionCtrl.text.isNotEmpty)
          'description': _descriptionCtrl.text.trim(),
        'pays_intervention': paysRaw,
        if (_rayonActionCtrl.text.isNotEmpty)
          'rayon_action': int.tryParse(_rayonActionCtrl.text),
        if (_chiffreAffairesCtrl.text.isNotEmpty)
          'chiffre_affaires': int.tryParse(_chiffreAffairesCtrl.text),
        if (_capitalSocialCtrl.text.isNotEmpty)
          'capital_social': int.tryParse(_capitalSocialCtrl.text),
        'types_opportunites': _typesOpportunites,
        if (_montantMinCtrl.text.isNotEmpty)
          'montant_min': int.tryParse(_montantMinCtrl.text),
        if (_montantMaxCtrl.text.isNotEmpty)
          'montant_max': int.tryParse(_montantMaxCtrl.text),
      };

      final updated = await ApiService.updateEntrepriseProfil(data);
      setState(() {
        _profil = updated;
        _successMessage = 'Profil mis à jour avec succès !';
        _showProfileForm = false;
      });

      await ApiService.getEntrepriseRecommandations().then((recos) {
        setState(() => _recommandations = recos);
      });
    } catch (e) {
      setState(() => _errorMessage = 'Erreur lors de la sauvegarde.');
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  // ─── Déconnexion ─────────────────────────────────────────────────────────
  Future<void> _logout() async {
    await ApiService.logout();
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  // ─── Modale détail reco ──────────────────────────────────────────────────
  void _showRecoDetail(Map<String, dynamic> reco) {
    final opp = reco['opportunite'] ?? {};
    showDialog(
      context: context,
      builder: (_) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        child: Container(
          width: 540,
          constraints: const BoxConstraints(maxHeight: 500),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header modal
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                color: AppColors.ink,
                child: Row(
                  children: [
                    const Text(
                      "Détails de l'opportunité",
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              // Body
              Flexible(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _modalField('Référence', '${opp['id'] ?? '-'}'),
                      _modalField('Description',
                          opp['description'] ?? 'Non spécifiée'),
                      _modalField('Score',
                          '${reco['score_global'] ?? '-'}%'),
                      _modalField(
                          'Date limite',
                          opp['date_limite'] ?? 'Non spécifiée'),
                    ],
                  ),
                ),
              ),
              // Footer
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  border: Border(
                      top: BorderSide(color: AppColors.border)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppColors.ink),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4)),
                      ),
                      child: const Text('Fermer',
                          style: TextStyle(color: AppColors.ink)),
                    ),
                    const SizedBox(width: 10),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.red,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4)),
                      ),
                      child: const Text('Postuler'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _modalField(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              fontSize: 10,
              letterSpacing: 1.2,
              color: AppColors.muted,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(value,
              style: const TextStyle(
                  fontSize: 14, color: AppColors.ink, height: 1.5)),
          const Divider(color: AppColors.border, height: 20),
        ],
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // BUILD
  // ═══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return _buildLoader();

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // ── En-tête ──────────────────────────────────────────
                    SlideTransition(
                      position: _headerSlide,
                      child: FadeTransition(
                        opacity: _headerFade,
                        child: _buildHeader(),
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // ── Stats ──────────────────────────────────────
                          FadeTransition(
                            opacity: _statsFade,
                            child: _buildStatsRow(),
                          ),

                          const SizedBox(height: 16),

                          // ── Messages ───────────────────────────────────
                          if (_successMessage != null)
                            _buildBanner(
                              _successMessage!,
                              AppColors.teal,
                              Icons.check_circle_outline,
                              onAction: () => setState(
                                  () => _showProfileForm = true),
                              actionLabel: 'Modifier',
                            ),
                          if (_errorMessage != null)
                            _buildBanner(
                              _errorMessage!,
                              AppColors.red,
                              Icons.error_outline,
                            ),

                          if (_profilComplet && !_showProfileForm)
                            _buildBanner(
                              'Profil entreprise complété à 100% — vous recevez des recommandations personnalisées.',
                              AppColors.teal,
                              Icons.verified_outlined,
                              onAction: () => setState(
                                  () => _showProfileForm = true),
                              actionLabel: 'Modifier',
                            ),

                          const SizedBox(height: 8),

                          // ── Formulaire ─────────────────────────────────
                          if (!_profilComplet || _showProfileForm)
                            _buildProfileCard(),

                          const SizedBox(height: 16),

                          // ── Recommandations ────────────────────────────
                          _buildRecommandationsCard(),

                          const SizedBox(height: 32),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ─── Top bar ──────────────────────────────────────────────────────────────
  Widget _buildTopBar() {
    return Container(
      color: AppColors.ink,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          const Text(
            'FASOIA',
            style: TextStyle(
              color: AppColors.red,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              letterSpacing: 4,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white60, size: 20),
            onPressed: _logout,
            tooltip: 'Déconnexion',
          ),
        ],
      ),
    );
  }

  // ─── En-tête dashboard ────────────────────────────────────────────────────
  Widget _buildHeader() {
    final raisonSociale = _profil['raisonSociale'] ?? 'Votre entreprise';
    final domaine = _profil['domaineActive'] ?? 'Domaine non défini';
    final localisation = _profil['localisation'] ?? 'Localisation non définie';
    final pct = _pourcentageCompletion;

    return Container(
      color: AppColors.ink,
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Texte gauche
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    RichText(
                      text: TextSpan(
                        text: 'Bienvenue, ',
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF862323),
                          height: 1.2,
                        ),
                        children: [
                          TextSpan(
                            text: raisonSociale,
                            style: const TextStyle(color: AppColors.red),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: [
                        _headerTag(Icons.business_outlined, domaine),
                        _headerTag(Icons.location_on_outlined, localisation),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              // Complétion droite
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  RichText(
                    text: TextSpan(
                      text: '$pct',
                      style: const TextStyle(
                        fontFamily: 'Poppins',
                        fontSize: 42,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                      children: const [
                        TextSpan(
                          text: '%',
                          style: TextStyle(color: AppColors.red, fontSize: 28),
                        ),
                      ],
                    ),
                  ),
                  const Text(
                    'PROFIL COMPLÉTÉ',
                    style: TextStyle(
                      fontSize: 9,
                      letterSpacing: 1.2,
                      color: AppColors.red,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: 120,
                    height: 3,
                    color: Colors.white12,
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: FractionallySizedBox(
                        widthFactor: pct / 100,
                        child: Container(color: AppColors.red),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          // Bordure rouge bas
          const SizedBox(height: 0),
          Container(height: 3, color: AppColors.red, margin: const EdgeInsets.only(top: 20)),
        ],
      ),
    );
  }

  Widget _headerTag(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.white24),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: Colors.white38),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.muted,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ─── Stats ────────────────────────────────────────────────────────────────
  Widget _buildStatsRow() {
    final stats = [
      {
        'n': '${_recommandations.length}',
        'l': 'Recommandations',
        'accent': false,
      },
      {
        'n': '${_profil['nb_candidatures_emises'] ?? 0}',
        'l': 'Candidatures',
        'accent': false,
      },
      {
        'n': '${_profil['taux_succes'] ?? 0}%',
        'l': 'Taux de succès',
        'accent': true,
      },
      {
        'n': '${_profil['nb_projets_realises'] ?? 0}',
        'l': 'Projets réalisés',
        'accent': false,
      },
    ];

    return Row(
      children: stats
          .map(
            (s) => Expanded(
              child: Container(
                margin: const EdgeInsets.only(right: 8),
                padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
                decoration: BoxDecoration(
                  color: (s['accent'] as bool) ? AppColors.ink : Colors.white,
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: [
                    Text(
                      s['n'] as String,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: (s['accent'] as bool)
                            ? AppColors.red
                            : AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      s['l'] as String,
                      style: TextStyle(
                        fontSize: 10,
                        color: (s['accent'] as bool)
                            ? Colors.white60
                            : AppColors.muted,
                        fontWeight: FontWeight.w600,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(),
    );
  }

  // ─── Bannière ─────────────────────────────────────────────────────────────
  Widget _buildBanner(
    String message,
    Color color,
    IconData icon, {
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(left: BorderSide(color: color, width: 3)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(fontSize: 13, color: AppColors.ink),
            ),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(width: 8),
            OutlinedButton(
              onPressed: onAction,
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: color),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                minimumSize: Size.zero,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4)),
              ),
              child: Text(
                actionLabel,
                style: TextStyle(color: color, fontSize: 12),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ─── Carte profil ─────────────────────────────────────────────────────────
  Widget _buildProfileCard() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Entête card
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: const BoxDecoration(
              border:
                  Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                Text(
                  _profilComplet
                      ? 'Modifier votre profil entreprise'
                      : 'Compléter votre profil entreprise',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppColors.ink,
                  ),
                ),
                const Spacer(),
                const Text(
                  '* Obligatoires',
                  style: TextStyle(fontSize: 11, color: AppColors.muted),
                ),
              ],
            ),
          ),

          // Onglets
          _buildTabsNav(),

          // Contenu onglet
          Form(
            key: _formKey,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(18),
                  child: _buildTabContent(),
                ),
                _buildFormFooter(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabsNav() {
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.ink, width: 2)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: List.generate(_tabLabels.length, (i) {
            final active = _currentTab == i;
            return GestureDetector(
              onTap: () => setState(() => _currentTab = i),
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: active ? AppColors.red : Colors.transparent,
                      width: 2,
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      _tabIcons[i],
                      size: 13,
                      color: active ? AppColors.ink : AppColors.muted,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _tabLabels[i].toUpperCase(),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                        color: active ? AppColors.ink : AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ),
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_currentTab) {
      case 0:
        return _tabInformations();
      case 1:
        return _tabCompetences();
      case 2:
        return _tabZones();
      case 3:
        return _tabFinancier();
      case 4:
        return _tabPreferences();
      default:
        return const SizedBox();
    }
  }

  // ─── Onglets formulaire ──────────────────────────────────────────────────

  Widget _tabInformations() {
    return Column(
      children: [
        Row(children: [
          Expanded(
              child: _formField(
                  'Domaine d\'activité *', _domaineCtrl,
                  hint: 'BTP, Technologies...', required: true)),
          const SizedBox(width: 14),
          Expanded(
              child: _formField('Localisation *', _localisationCtrl,
                  hint: 'Ouagadougou, BF', required: true)),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(
              child: _formField('Nb. employés', _tailleCtrl,
                  hint: '50', numeric: true)),
          const SizedBox(width: 14),
          Expanded(
              child: _formField('Année de création', _anneeCreationCtrl,
                  hint: '2010', numeric: true)),
        ]),
        const SizedBox(height: 14),
        _formField('Site web', _siteWebCtrl, hint: 'https://...'),
      ],
    );
  }

  Widget _tabCompetences() {
    return Column(
      children: [
        _formField('Compétences clés *', _competencesClesCtrl,
            hint: 'Génie civil, Dev web...', required: true, maxLines: 3,
            note: 'Séparez par des virgules'),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(
              child: _formField("Années d'expérience", _anneesExpCtrl,
                  hint: '10', numeric: true)),
          const SizedBox(width: 14),
          Expanded(
              child: _formField('Nb. projets réalisés', _nbProjetsCtrl,
                  hint: '25', numeric: true)),
        ]),
        const SizedBox(height: 14),
        _formField("Description de l'entreprise", _descriptionCtrl,
            hint: 'Présentez votre entreprise...', maxLines: 4),
      ],
    );
  }

  Widget _tabZones() {
    return Column(
      children: [
        _formField("Pays d'intervention *", _paysInterventionCtrl,
            hint: "Burkina Faso, Côte d'Ivoire...", required: true,
            note: 'Séparez par des virgules'),
        const SizedBox(height: 14),
        _formField('Rayon d\'action (km)', _rayonActionCtrl,
            hint: '500', numeric: true),
      ],
    );
  }

  Widget _tabFinancier() {
    return Column(
      children: [
        _formField("Chiffre d'affaires annuel (FCFA) *", _chiffreAffairesCtrl,
            hint: '100000000', required: true, numeric: true),
        const SizedBox(height: 14),
        _formField('Capital social (FCFA)', _capitalSocialCtrl,
            hint: '5000000', numeric: true),
      ],
    );
  }

  Widget _tabPreferences() {
    final options = ['AMI', 'APPEL_OFFRE', 'MARCHE_PUBLIC'];
    final labels = {
      'AMI': 'AMI',
      'APPEL_OFFRE': "Appel d'offres",
      'MARCHE_PUBLIC': 'Marché public',
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "TYPES D'OPPORTUNITÉS *",
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: AppColors.muted,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 8),
        ...options.map((opt) => CheckboxListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              title: Text(labels[opt]!,
                  style: const TextStyle(fontSize: 13, color: AppColors.ink)),
              value: _typesOpportunites.contains(opt),
              activeColor: AppColors.red,
              onChanged: (v) {
                setState(() {
                  if (v == true) {
                    _typesOpportunites.add(opt);
                  } else {
                    _typesOpportunites.remove(opt);
                  }
                });
              },
            )),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(
              child: _formField('Montant minimum (FCFA)', _montantMinCtrl,
                  hint: '1000000', numeric: true)),
          const SizedBox(width: 14),
          Expanded(
              child: _formField('Montant maximum (FCFA)', _montantMaxCtrl,
                  hint: '100000000', numeric: true)),
        ]),
      ],
    );
  }

  // ─── Footer formulaire ────────────────────────────────────────────────────
  Widget _buildFormFooter() {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          // Prev / Next
          OutlinedButton.icon(
            onPressed:
                _currentTab > 0 ? () => setState(() => _currentTab--) : null,
            icon: const Icon(Icons.arrow_back, size: 14),
            label: const Text('Précédent'),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.ink),
              foregroundColor: AppColors.ink,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4)),
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
          const SizedBox(width: 8),
          OutlinedButton.icon(
            onPressed: _currentTab < _tabLabels.length - 1
                ? () => setState(() => _currentTab++)
                : null,
            icon: const Icon(Icons.arrow_forward, size: 14),
            label: const Text('Suivant'),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.ink),
              foregroundColor: AppColors.ink,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4)),
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
          const Spacer(),
          // Save
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: _isSaving
                ? Container(
                    key: const ValueKey('loading'),
                    height: 44,
                    width: 160,
                    decoration: BoxDecoration(
                      color: AppColors.red.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2),
                      ),
                    ),
                  )
                : ElevatedButton.icon(
                    key: const ValueKey('save'),
                    onPressed: _saveProfile,
                    icon: const Icon(Icons.save_outlined, size: 16),
                    label: const Text('Enregistrer'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.red,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(4)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 18, vertical: 12),
                      textStyle: const TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w700),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  // ─── Carte recommandations ────────────────────────────────────────────────
  Widget _buildRecommandationsCard() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: const Text(
              'Opportunités recommandées pour vous',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.ink,
              ),
            ),
          ),
          if (!_profilComplet)
            const Padding(
              padding: EdgeInsets.all(40),
              child: Center(
                child: Text(
                  'Complétez votre profil (champs * obligatoires)\npour recevoir des recommandations personnalisées.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.muted,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            )
          else if (_recommandations.isEmpty)
            const Padding(
              padding: EdgeInsets.all(40),
              child: Center(
                child: Text(
                  'Aucune recommandation disponible pour le moment.',
                  style: TextStyle(fontSize: 13, color: AppColors.muted),
                ),
              ),
            )
          else
            _buildRecoTable(),
        ],
      ),
    );
  }

  Widget _buildRecoTable() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: WidgetStateProperty.all(AppColors.ink),
        headingTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
        dataTextStyle: const TextStyle(fontSize: 13, color: AppColors.ink),
        columnSpacing: 20,
        columns: const [
          DataColumn(label: Text('TYPE')),
          DataColumn(label: Text('RÉFÉRENCE')),
          DataColumn(label: Text('DESCRIPTION')),
          DataColumn(label: Text('SCORE')),
          DataColumn(label: Text('DATE LIMITE')),
          DataColumn(label: Text('ACTIONS')),
        ],
        rows: _recommandations.map<DataRow>((reco) {
          final opp = reco['opportunite'] ?? {};
          final isOffre = reco['opportunite_type'] == 'Offre_uemoa';
          final desc = (opp['description'] ?? '').toString();
          final shortDesc =
              desc.length > 70 ? '${desc.substring(0, 70)}…' : desc;

          return DataRow(
            cells: [
              DataCell(
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  color: isOffre ? const Color(0xFF862323) : AppColors.teal,
                  child: Text(
                    isOffre ? 'APPEL OFFRE' : 'AMI',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
              DataCell(Text(
                '${isOffre ? 'OFFRE' : 'AMI'}-${opp['id'] ?? '-'}',
                style: const TextStyle(
                  color: AppColors.red,
                  fontWeight: FontWeight.w600,
                  fontFamily: 'monospace',
                ),
              )),
              DataCell(Text(shortDesc)),
              DataCell(Text(
                '${reco['score_global'] ?? '-'}%',
                style: const TextStyle(
                  color: AppColors.teal,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              )),
              DataCell(Text(
                opp['date_limite'] ?? 'N/A',
                style: const TextStyle(
                  color: Color(0xFF862323),
                  fontWeight: FontWeight.w500,
                ),
              )),
              DataCell(Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutlinedButton(
                    onPressed: () =>
                        _showRecoDetail(reco as Map<String, dynamic>),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.ink),
                      foregroundColor: AppColors.ink,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(2)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      textStyle: const TextStyle(
                          fontSize: 11, fontWeight: FontWeight.w700),
                    ),
                    child: const Text('DÉTAILS'),
                  ),
                  const SizedBox(width: 6),
                  ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.red,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(2)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      textStyle: const TextStyle(
                          fontSize: 11, fontWeight: FontWeight.w700),
                    ),
                    child: const Text('POSTULER'),
                  ),
                ],
              )),
            ],
          );
        }).toList(),
      ),
    );
  }

  // ─── Loader global ────────────────────────────────────────────────────────
  Widget _buildLoader() {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: AppColors.red),
            SizedBox(height: 16),
            Text(
              'Chargement du tableau de bord...',
              style: TextStyle(color: AppColors.muted, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  // ─── Helper champ formulaire ──────────────────────────────────────────────
  Widget _formField(
    String label,
    TextEditingController controller, {
    String? hint,
    bool required = false,
    bool numeric = false,
    int maxLines = 1,
    String? note,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label.toUpperCase(),
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: AppColors.muted,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          maxLines: maxLines,
          keyboardType: numeric ? TextInputType.number : TextInputType.text,
          decoration: InputDecoration(
            hintText: hint,
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            filled: true,
            fillColor: AppColors.cream,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(4),
              borderSide: const BorderSide(color: AppColors.border),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(4),
              borderSide: const BorderSide(color: AppColors.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(4),
              borderSide: const BorderSide(color: AppColors.red, width: 1.5),
            ),
          ),
          validator: required
              ? (v) => (v == null || v.isEmpty) ? 'Champ requis' : null
              : null,
        ),
        if (note != null) ...[
          const SizedBox(height: 4),
          Text(
            note,
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
          ),
        ],
      ],
    );
  }
}