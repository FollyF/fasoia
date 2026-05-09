import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

class DashboardEntreprise extends StatefulWidget {
  const DashboardEntreprise({super.key});
  @override
  State<DashboardEntreprise> createState() => _DashboardEntrepriseState();
}

class _DashboardEntrepriseState extends State<DashboardEntreprise>
    with TickerProviderStateMixin {
  bool _isLoading = true;
  int _navIndex = 0;
  Map<String, dynamic> _profil = {};
  List<dynamic> _recommandations = [];

  late final AnimationController _fadeCtrl;
  late final Animation<double> _fadeAnim;

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

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    _loadData();
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    for (final c in [_domaineCtrl, _localisationCtrl, _tailleCtrl, _anneeCreationCtrl,
      _siteWebCtrl, _competencesClesCtrl, _anneesExpCtrl, _nbProjetsCtrl,
      _descriptionCtrl, _paysInterventionCtrl, _rayonActionCtrl,
      _chiffreAffairesCtrl, _capitalSocialCtrl, _montantMinCtrl, _montantMaxCtrl]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final profil = await ApiService.getEntrepriseProfil();
      final recos = await ApiService.getEntrepriseRecommandations();
      setState(() { _profil = profil; _recommandations = recos; _isLoading = false; });
      _populateControllers();
      _fadeCtrl.forward();
    } catch (e) {
      setState(() => _isLoading = false);
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
    _paysInterventionCtrl.text = pays is List ? pays.join(', ') : (pays ?? '');
    _rayonActionCtrl.text = _profil['rayon_action']?.toString() ?? '';
    _chiffreAffairesCtrl.text = _profil['chiffre_affaires']?.toString() ?? '';
    _capitalSocialCtrl.text = _profil['capital_social']?.toString() ?? '';
    _montantMinCtrl.text = _profil['montant_min']?.toString() ?? '';
    _montantMaxCtrl.text = _profil['montant_max']?.toString() ?? '';
    final types = _profil['types_opportunites'];
    if (types is List) _typesOpportunites = List<String>.from(types);
  }

  int get _completion {
    final fields = [_profil['domaineActive'], _profil['localisation'],
      _profil['competencesCles'], _profil['pays_intervention'],
      _profil['chiffre_affaires'], _profil['types_opportunites']];
    final filled = fields.where((f) {
      if (f == null) return false;
      if (f is String) return f.isNotEmpty;
      if (f is List) return f.isNotEmpty;
      return true;
    }).length;
    return ((filled / fields.length) * 100).round();
  }

  bool get _profilComplet => _completion == 100;

  Future<void> _logout() async {
    await ApiService.logout();
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  Future<void> _saveProfile(Map<String, dynamic> data) async {
    try {
      final updated = await ApiService.updateEntrepriseProfil(data);
      final recos = await ApiService.getEntrepriseRecommandations();
      setState(() { _profil = updated; _recommandations = recos; });
      _populateControllers();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: const Row(children: [
            Icon(Icons.check_circle_outline, color: Colors.white, size: 16),
            SizedBox(width: 8),
            Text('Profil mis à jour avec succès'),
          ]),
          backgroundColor: AppColors.teal,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: const Text('Erreur lors de la sauvegarde'),
          backgroundColor: AppColors.red,
          behavior: SnackBarBehavior.floating,
        ));
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // BUILD
  // ═══════════════════════════════════════════════════════════════════════
  @override
  Widget build(BuildContext context) {
    if (_isLoading) return _buildLoader();
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: AppColors.cream,
        body: FadeTransition(
          opacity: _fadeAnim,
          child: IndexedStack(
            index: _navIndex,
            children: [_buildAccueil(), _buildOpportunites(), _buildProfil()],
          ),
        ),
        bottomNavigationBar: _buildBottomNav(),
      ),
    );
  }

  Widget _buildBottomNav() {
    final items = [
      {'icon': Icons.dashboard_outlined, 'active': Icons.dashboard_rounded, 'label': 'Accueil'},
      {'icon': Icons.bolt_outlined, 'active': Icons.bolt_rounded, 'label': 'Opportunités'},
      {'icon': Icons.person_outline_rounded, 'active': Icons.person_rounded, 'label': 'Profil'},
    ];
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 60,
          child: Row(
            children: List.generate(items.length, (i) {
              final active = _navIndex == i;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _navIndex = i),
                  behavior: HitTestBehavior.opaque,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        active ? items[i]['active'] as IconData : items[i]['icon'] as IconData,
                        color: active ? AppColors.red : AppColors.muted,
                        size: 22,
                      ),
                      const SizedBox(height: 3),
                      Text(
                        items[i]['label'] as String,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                          color: active ? AppColors.red : AppColors.muted,
                        ),
                      ),
                      const SizedBox(height: 2),
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        height: 2, width: active ? 20 : 0,
                        decoration: BoxDecoration(
                          color: AppColors.red,
                          borderRadius: BorderRadius.circular(1),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PAGE ACCUEIL
  // ═══════════════════════════════════════════════════════════════════════
  Widget _buildAccueil() {
    final raisonSociale = _profil['raisonSociale'] ?? 'Votre entreprise';
    final initiales = raisonSociale.length >= 2
        ? raisonSociale.substring(0, 2).toUpperCase()
        : raisonSociale.toUpperCase();

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          expandedHeight: 175,
          pinned: true,
          backgroundColor: AppColors.ink,
          elevation: 0,
          automaticallyImplyLeading: false,
          actions: [
            IconButton(
              icon: const Icon(Icons.logout_rounded, color: Colors.white54, size: 20),
              onPressed: _logout,
            ),
          ],
          flexibleSpace: FlexibleSpaceBar(
            background: Container(
              color: AppColors.ink,
              child: Stack(children: [
                Positioned(right: -30, top: -30, child: Container(
                  width: 160, height: 160,
                  decoration: BoxDecoration(shape: BoxShape.circle,
                      color: AppColors.red.withOpacity(0.08)),
                )),
                Positioned(right: 20, bottom: 20, child: Container(
                  width: 60, height: 60,
                  decoration: BoxDecoration(shape: BoxShape.circle,
                      color: AppColors.red.withOpacity(0.12)),
                )),
                Positioned(
                  left: 20, bottom: 20, right: 70,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Container(
                          width: 44, height: 44,
                          decoration: BoxDecoration(
                            color: AppColors.red,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Center(child: Text(initiales,
                            style: const TextStyle(color: Colors.white,
                                fontWeight: FontWeight.w800, fontSize: 16))),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Bonjour,', style: TextStyle(color: Colors.white54, fontSize: 12)),
                            Text(raisonSociale,
                              style: const TextStyle(color: Colors.white,
                                  fontSize: 17, fontWeight: FontWeight.w700),
                              maxLines: 1, overflow: TextOverflow.ellipsis),
                          ],
                        )),
                      ]),
                      const SizedBox(height: 12),
                      if (_profil['domaineActive'] != null)
                        _chip(Icons.business_outlined, _profil['domaineActive']),
                      if (_profil['localisation'] != null) ...[
                        const SizedBox(height: 4),
                        _chip(Icons.location_on_outlined, _profil['localisation']),
                      ],
                    ],
                  ),
                ),
              ]),
            ),
          ),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(0),
            child: Container(height: 3, color: AppColors.red),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              if (!_profilComplet) ...[_buildCompletionCard(), const SizedBox(height: 16)],
              _buildStatsGrid(),
              const SizedBox(height: 20),
              Row(children: [
                const Text('OPPORTUNITÉS RÉCENTES', style: TextStyle(
                  fontSize: 11, fontWeight: FontWeight.w800,
                  color: AppColors.muted, letterSpacing: 1.2)),
                const Spacer(),
                if (_recommandations.isNotEmpty)
                  GestureDetector(
                    onTap: () => setState(() => _navIndex = 1),
                    child: const Text('Voir tout →', style: TextStyle(
                      fontSize: 12, color: AppColors.red, fontWeight: FontWeight.w600)),
                  ),
              ]),
              const SizedBox(height: 12),
              if (!_profilComplet)
                _buildEmptyState(Icons.lock_outline_rounded, 'Profil incomplet',
                  'Complétez votre profil pour recevoir des recommandations.',
                  actionLabel: 'Compléter', onAction: () => setState(() => _navIndex = 2))
              else if (_recommandations.isEmpty)
                _buildEmptyState(Icons.search_off_rounded, 'Aucune opportunité',
                  'Aucune recommandation disponible pour le moment.')
              else
                ..._recommandations.take(3).map((r) => _buildRecoCard(r)),
              const SizedBox(height: 24),
            ]),
          ),
        ),
      ],
    );
  }

  Widget _chip(IconData icon, String label) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(icon, size: 11, color: Colors.white38),
      const SizedBox(width: 5),
      Text(label, style: const TextStyle(fontSize: 11, color: Colors.white60, fontWeight: FontWeight.w500)),
    ],
  );

  Widget _buildCompletionCard() {
    final pct = _completion;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.ink, borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        SizedBox(width: 52, height: 52,
          child: CustomPaint(
            painter: _CircleProgressPainter(pct / 100, AppColors.red),
            child: Center(child: Text('$pct%', style: const TextStyle(
              color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800))),
          ),
        ),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Profil incomplet', style: TextStyle(
            color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
          const SizedBox(height: 2),
          const Text('Complétez votre profil pour recevoir des recommandations',
            style: TextStyle(color: Colors.white54, fontSize: 11)),
        ])),
        const SizedBox(width: 8),
        GestureDetector(
          onTap: () => setState(() => _navIndex = 2),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
            decoration: BoxDecoration(color: AppColors.red, borderRadius: BorderRadius.circular(6)),
            child: const Text('Compléter', style: TextStyle(
              color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
          ),
        ),
      ]),
    );
  }

  Widget _buildStatsGrid() {
    final stats = [
      {'n': '${_recommandations.length}', 'l': 'Recommandations', 'icon': Icons.bolt_rounded, 'accent': true},
      {'n': '${_profil['nb_candidatures_emises'] ?? 0}', 'l': 'Candidatures', 'icon': Icons.send_rounded, 'accent': false},
      {'n': '${_profil['taux_succes'] ?? 0}%', 'l': 'Taux succès', 'icon': Icons.trending_up_rounded, 'accent': false},
      {'n': '${_profil['nb_projets_realises'] ?? 0}', 'l': 'Projets', 'icon': Icons.check_circle_outline_rounded, 'accent': false},
    ];
    return GridView.count(
      crossAxisCount: 2, shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 10, mainAxisSpacing: 10, childAspectRatio: 1.7,
      children: stats.map((s) {
        final accent = s['accent'] as bool;
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: accent ? AppColors.ink : Colors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: accent ? AppColors.ink : AppColors.border),
          ),
          child: Row(children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(
                color: accent ? AppColors.red.withOpacity(0.2) : AppColors.cream,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(s['icon'] as IconData, size: 18,
                color: accent ? AppColors.red : AppColors.muted),
            ),
            const SizedBox(width: 10),
            Column(crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(s['n'] as String, style: TextStyle(
                  fontSize: 20, fontWeight: FontWeight.w800,
                  color: accent ? Colors.white : AppColors.ink)),
                Text(s['l'] as String, style: TextStyle(
                  fontSize: 10, fontWeight: FontWeight.w600,
                  color: accent ? Colors.white54 : AppColors.muted)),
              ]),
          ]),
        );
      }).toList(),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PAGE OPPORTUNITÉS
  // ═══════════════════════════════════════════════════════════════════════
  Widget _buildOpportunites() {
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          pinned: true,
          backgroundColor: AppColors.ink,
          automaticallyImplyLeading: false,
          title: const Text('Opportunités', style: TextStyle(
            color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(3),
            child: Container(height: 3, color: AppColors.red),
          ),
        ),
        if (_recommandations.isEmpty)
          SliverFillRemaining(child: Center(child: _buildEmptyState(
            Icons.search_off_rounded, 'Aucune opportunité',
            _profilComplet
                ? 'Aucune recommandation disponible pour le moment.'
                : 'Complétez votre profil pour recevoir des recommandations.',
            actionLabel: _profilComplet ? null : 'Compléter le profil',
            onAction: _profilComplet ? null : () => setState(() => _navIndex = 2),
          )))
        else
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(delegate: SliverChildBuilderDelegate(
              (_, i) => _buildRecoCard(_recommandations[i]),
              childCount: _recommandations.length,
            )),
          ),
      ],
    );
  }

  Widget _buildRecoCard(dynamic reco) {
    final opp = reco['opportunite'] ?? {};
    final isOffre = reco['opportunite_type'] == 'Offre_uemoa';
    final score = (reco['score_global'] ?? 0).toDouble();
    final desc = (opp['description'] ?? '').toString();
    final ref = '${isOffre ? 'OFFRE' : 'AMI'}-${opp['id'] ?? '-'}';
    final badgeColor = isOffre ? const Color(0xFF862323) : AppColors.teal;

    return GestureDetector(
      onTap: () => _showRecoSheet(reco),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
          boxShadow: [BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10, offset: const Offset(0, 3))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: badgeColor.withOpacity(0.06),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: badgeColor, borderRadius: BorderRadius.circular(4)),
                child: Text(isOffre ? 'APPEL D\'OFFRE' : 'AMI',
                  style: const TextStyle(color: Colors.white, fontSize: 9,
                      fontWeight: FontWeight.w800, letterSpacing: 0.5)),
              ),
              const SizedBox(width: 8),
              Text(ref, style: TextStyle(fontSize: 11, color: badgeColor,
                fontWeight: FontWeight.w700, fontFamily: 'monospace')),
              const Spacer(),
              SizedBox(width: 38, height: 38,
                child: CustomPaint(
                  painter: _CircleProgressPainter(score / 100, badgeColor),
                  child: Center(child: Text('${score.round()}%',
                    style: const TextStyle(fontSize: 8,
                        fontWeight: FontWeight.w800, color: AppColors.ink))),
                ),
              ),
            ]),
          ),
          // Body
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(desc.length > 100 ? '${desc.substring(0, 100)}…' : desc,
                style: const TextStyle(fontSize: 13, color: AppColors.ink, height: 1.4)),
              if (opp['date_limite'] != null) ...[
                const SizedBox(height: 10),
                Row(children: [
                  const Icon(Icons.schedule_rounded, size: 12, color: AppColors.muted),
                  const SizedBox(width: 4),
                  Text('Limite : ${opp['date_limite']}',
                    style: const TextStyle(fontSize: 11, color: AppColors.muted, fontWeight: FontWeight.w500)),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => _showRecoSheet(reco),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                      decoration: BoxDecoration(color: AppColors.red, borderRadius: BorderRadius.circular(6)),
                      child: const Text('Voir →', style: TextStyle(
                        color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                    ),
                  ),
                ]),
              ],
            ]),
          ),
        ]),
      ),
    );
  }

  void _showRecoSheet(dynamic reco) {
    final opp = reco['opportunite'] ?? {};
    final isOffre = reco['opportunite_type'] == 'Offre_uemoa';
    final score = (reco['score_global'] ?? 0).toDouble();
    final badgeColor = isOffre ? const Color(0xFF862323) : AppColors.teal;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        height: MediaQuery.of(context).size.height * 0.75,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(children: [
          Container(margin: const EdgeInsets.only(top: 10), width: 36, height: 4,
            decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2))),
          Container(
            padding: const EdgeInsets.fromLTRB(20, 14, 12, 14),
            decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: badgeColor, borderRadius: BorderRadius.circular(4)),
                child: Text(isOffre ? 'APPEL D\'OFFRE' : 'AMI',
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800)),
              ),
              const SizedBox(width: 10),
              const Text('Détails', style: TextStyle(fontSize: 16,
                fontWeight: FontWeight.w700, color: AppColors.ink)),
              const Spacer(),
              IconButton(icon: const Icon(Icons.close_rounded, color: AppColors.muted, size: 20),
                onPressed: () => Navigator.pop(context)),
            ]),
          ),
          Expanded(child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: AppColors.cream, borderRadius: BorderRadius.circular(10)),
                child: Row(children: [
                  SizedBox(width: 60, height: 60,
                    child: CustomPaint(
                      painter: _CircleProgressPainter(score / 100, badgeColor),
                      child: Center(child: Text('${score.round()}%',
                        style: const TextStyle(fontSize: 12,
                            fontWeight: FontWeight.w800, color: AppColors.ink))),
                    ),
                  ),
                  const SizedBox(width: 14),
                  const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Score de correspondance', style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.ink)),
                    SizedBox(height: 2),
                    Text('Basé sur votre profil', style: TextStyle(fontSize: 11, color: AppColors.muted)),
                  ]),
                ]),
              ),
              const SizedBox(height: 20),
              _sheetField('Référence', '${isOffre ? 'OFFRE' : 'AMI'}-${opp['id'] ?? '-'}'),
              _sheetField('Description', opp['description'] ?? 'Non spécifiée'),
              if (opp['date_limite'] != null) _sheetField('Date limite', opp['date_limite']),
              const SizedBox(height: 24),
              SizedBox(width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.send_rounded, size: 16),
                  label: const Text('Postuler à cette opportunité'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.red, foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                  ),
                ),
              ),
            ]),
          )),
        ]),
      ),
    );
  }

  Widget _sheetField(String label, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label.toUpperCase(), style: const TextStyle(
        fontSize: 10, letterSpacing: 1.2, color: AppColors.muted, fontWeight: FontWeight.w700)),
      const SizedBox(height: 6),
      Text(value, style: const TextStyle(fontSize: 14, color: AppColors.ink, height: 1.5)),
      const Divider(color: AppColors.border, height: 24),
    ]),
  );

  // ═══════════════════════════════════════════════════════════════════════
  // PAGE PROFIL
  // ═══════════════════════════════════════════════════════════════════════
  Widget _buildProfil() {
    final pct = _completion;
    final sections = [
      {'title': 'Informations générales', 'icon': Icons.business_outlined,
        'fields': ['domaineActive', 'localisation', 'taille', 'annee_creation', 'site_web'], 'tab': 0},
      {'title': 'Compétences & Expérience', 'icon': Icons.code_outlined,
        'fields': ['competencesCles', 'annees_experience', 'nb_projets_realises'], 'tab': 1},
      {'title': 'Zones d\'intervention', 'icon': Icons.map_outlined,
        'fields': ['pays_intervention', 'rayon_action'], 'tab': 2},
      {'title': 'Capacité financière', 'icon': Icons.bar_chart_outlined,
        'fields': ['chiffre_affaires', 'capital_social'], 'tab': 3},
      {'title': 'Préférences', 'icon': Icons.tune_outlined,
        'fields': ['types_opportunites', 'montant_min', 'montant_max'], 'tab': 4},
    ];

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          pinned: true, backgroundColor: AppColors.ink,
          automaticallyImplyLeading: false,
          title: const Text('Mon Profil', style: TextStyle(
            color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(3),
            child: Container(height: 3, color: AppColors.red)),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              // Complétion
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(color: AppColors.ink, borderRadius: BorderRadius.circular(12)),
                child: Row(children: [
                  SizedBox(width: 64, height: 64,
                    child: CustomPaint(
                      painter: _CircleProgressPainter(pct / 100, AppColors.red),
                      child: Center(child: Text('$pct%', style: const TextStyle(
                        color: Colors.white, fontSize: 13, fontWeight: FontWeight.w800))),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(_profilComplet ? 'Profil complet ✓' : 'Profil incomplet',
                      style: const TextStyle(color: Colors.white,
                          fontWeight: FontWeight.w700, fontSize: 15)),
                    const SizedBox(height: 4),
                    Text(
                      _profilComplet
                          ? 'Vous recevez des recommandations personnalisées'
                          : 'Complétez les sections * pour débloquer les recommandations',
                      style: const TextStyle(color: Colors.white54, fontSize: 11)),
                  ])),
                ]),
              ),
              const SizedBox(height: 20),
              const Text('SECTIONS DU PROFIL', style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.w800,
                color: AppColors.muted, letterSpacing: 1.2)),
              const SizedBox(height: 10),

              ...sections.map((s) {
                final tab = s['tab'] as int;
                final fields = s['fields'] as List<String>;
                final filled = fields.where((f) {
                  final v = _profil[f];
                  if (v == null) return false;
                  if (v is String) return v.isNotEmpty;
                  if (v is List) return v.isNotEmpty;
                  return true;
                }).length;
                final sectionPct = (filled / fields.length * 100).round();
                final required = tab <= 3;

                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    leading: Container(
                      width: 38, height: 38,
                      decoration: BoxDecoration(
                        color: sectionPct == 100
                            ? AppColors.teal.withOpacity(0.1) : AppColors.cream,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(s['icon'] as IconData, size: 18,
                        color: sectionPct == 100 ? AppColors.teal : AppColors.muted),
                    ),
                    title: Row(children: [
                      Text(s['title'] as String, style: const TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.ink)),
                      if (required) ...[
                        const SizedBox(width: 4),
                        const Text('*', style: TextStyle(color: AppColors.red, fontWeight: FontWeight.w800)),
                      ],
                    ]),
                    subtitle: Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Row(children: [
                        Expanded(child: ClipRRect(
                          borderRadius: BorderRadius.circular(2),
                          child: LinearProgressIndicator(
                            value: sectionPct / 100,
                            backgroundColor: AppColors.border,
                            color: sectionPct == 100 ? AppColors.teal : AppColors.red,
                            minHeight: 3,
                          ),
                        )),
                        const SizedBox(width: 8),
                        Text('$sectionPct%', style: const TextStyle(
                          fontSize: 10, color: AppColors.muted, fontWeight: FontWeight.w600)),
                      ]),
                    ),
                    trailing: const Icon(Icons.edit_outlined, size: 16, color: AppColors.muted),
                    onTap: () => _openProfileSheet(tab),
                  ),
                );
              }),

              const SizedBox(height: 12),
              SizedBox(width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _logout,
                  icon: const Icon(Icons.logout_rounded, size: 16, color: AppColors.muted),
                  label: const Text('Se déconnecter', style: TextStyle(color: AppColors.muted)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: AppColors.border),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ]),
          ),
        ),
      ],
    );
  }

  void _openProfileSheet(int tab) {
    final titles = ['Informations générales', 'Compétences & Expérience',
      'Zones d\'intervention', 'Capacité financière', 'Préférences'];
    final formKey = GlobalKey<FormState>();
    bool saving = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => Container(
          height: MediaQuery.of(context).size.height * 0.85,
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(children: [
            Container(margin: const EdgeInsets.only(top: 10), width: 36, height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2))),
            Container(
              padding: const EdgeInsets.fromLTRB(20, 14, 12, 14),
              decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
              child: Row(children: [
                Text(titles[tab], style: const TextStyle(
                  fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.ink)),
                const Spacer(),
                IconButton(icon: const Icon(Icons.close_rounded, color: AppColors.muted, size: 20),
                  onPressed: () => Navigator.pop(ctx)),
              ]),
            ),
            Expanded(child: SingleChildScrollView(
              padding: EdgeInsets.only(
                left: 20, right: 20, top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20),
              child: Form(key: formKey, child: _buildSectionForm(tab, setS)),
            )),
            Container(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: AppColors.border)),
                color: Colors.white),
              child: SizedBox(width: double.infinity,
                child: ElevatedButton(
                  onPressed: saving ? null : () async {
                    if (!formKey.currentState!.validate()) return;
                    setS(() => saving = true);
                    final data = _collectSectionData(tab);
                    await _saveProfile(data);
                    if (ctx.mounted) Navigator.pop(ctx);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.red,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: saving
                      ? const SizedBox(width: 20, height: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Enregistrer', style: TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w700)),
                ),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _buildSectionForm(int tab, StateSetter setS) {
    switch (tab) {
      case 0:
        return Column(children: [
          _field('Domaine d\'activité *', _domaineCtrl, hint: 'BTP, Technologies...', required: true),
          _field('Localisation *', _localisationCtrl, hint: 'Ouagadougou, BF', required: true),
          Row(children: [
            Expanded(child: _field('Nb. employés', _tailleCtrl, hint: '50', numeric: true)),
            const SizedBox(width: 12),
            Expanded(child: _field('Année création', _anneeCreationCtrl, hint: '2010', numeric: true)),
          ]),
          _field('Site web', _siteWebCtrl, hint: 'https://...'),
        ]);
      case 1:
        return Column(children: [
          _field('Compétences clés *', _competencesClesCtrl,
            hint: 'Génie civil, Dev web...', required: true, maxLines: 3,
            note: 'Séparez par des virgules'),
          _field('Description', _descriptionCtrl,
            hint: 'Présentez votre entreprise...', maxLines: 4),
          Row(children: [
            Expanded(child: _field('Années d\'exp.', _anneesExpCtrl, hint: '10', numeric: true)),
            const SizedBox(width: 12),
            Expanded(child: _field('Nb. projets', _nbProjetsCtrl, hint: '25', numeric: true)),
          ]),
        ]);
      case 2:
        return Column(children: [
          _field('Pays d\'intervention *', _paysInterventionCtrl,
            hint: 'Burkina Faso, Côte d\'Ivoire...', required: true, note: 'Séparez par des virgules'),
          _field('Rayon d\'action (km)', _rayonActionCtrl, hint: '500', numeric: true),
        ]);
      case 3:
        return Column(children: [
          _field('Chiffre d\'affaires (FCFA) *', _chiffreAffairesCtrl,
            hint: '100000000', required: true, numeric: true),
          _field('Capital social (FCFA)', _capitalSocialCtrl, hint: '5000000', numeric: true),
        ]);
      case 4:
        final options = {'AMI': 'AMI', 'APPEL_OFFRE': 'Appel d\'offres', 'MARCHE_PUBLIC': 'Marché public'};
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('TYPES D\'OPPORTUNITÉS *', style: TextStyle(
            fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.muted, letterSpacing: 0.8)),
          const SizedBox(height: 8),
          ...options.entries.map((e) => CheckboxListTile(
            dense: true, contentPadding: EdgeInsets.zero,
            title: Text(e.value, style: const TextStyle(fontSize: 13, color: AppColors.ink)),
            value: _typesOpportunites.contains(e.key),
            activeColor: AppColors.red,
            onChanged: (v) => setS(() {
              if (v == true) {
                _typesOpportunites.add(e.key);
              } else {
                _typesOpportunites.remove(e.key);
              }
            }),
          )),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: _field('Montant min (FCFA)', _montantMinCtrl, hint: '1000000', numeric: true)),
            const SizedBox(width: 12),
            Expanded(child: _field('Montant max (FCFA)', _montantMaxCtrl, hint: '100000000', numeric: true)),
          ]),
        ]);
      default:
        return const SizedBox();
    }
  }

  Map<String, dynamic> _collectSectionData(int tab) {
    switch (tab) {
      case 0: return {
        'domaineActive': _domaineCtrl.text.trim(),
        'localisation': _localisationCtrl.text.trim(),
        if (_tailleCtrl.text.isNotEmpty) 'taille': int.tryParse(_tailleCtrl.text),
        if (_anneeCreationCtrl.text.isNotEmpty) 'annee_creation': int.tryParse(_anneeCreationCtrl.text),
        if (_siteWebCtrl.text.isNotEmpty) 'site_web': _siteWebCtrl.text.trim(),
      };
      case 1: return {
        'competencesCles': _competencesClesCtrl.text.trim(),
        if (_descriptionCtrl.text.isNotEmpty) 'description': _descriptionCtrl.text.trim(),
        if (_anneesExpCtrl.text.isNotEmpty) 'annees_experience': int.tryParse(_anneesExpCtrl.text),
        if (_nbProjetsCtrl.text.isNotEmpty) 'nb_projets_realises': int.tryParse(_nbProjetsCtrl.text),
      };
      case 2: return {
        'pays_intervention': _paysInterventionCtrl.text
            .split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList(),
        if (_rayonActionCtrl.text.isNotEmpty) 'rayon_action': int.tryParse(_rayonActionCtrl.text),
      };
      case 3: return {
        if (_chiffreAffairesCtrl.text.isNotEmpty) 'chiffre_affaires': int.tryParse(_chiffreAffairesCtrl.text),
        if (_capitalSocialCtrl.text.isNotEmpty) 'capital_social': int.tryParse(_capitalSocialCtrl.text),
      };
      case 4: return {
        'types_opportunites': _typesOpportunites,
        if (_montantMinCtrl.text.isNotEmpty) 'montant_min': int.tryParse(_montantMinCtrl.text),
        if (_montantMaxCtrl.text.isNotEmpty) 'montant_max': int.tryParse(_montantMaxCtrl.text),
      };
      default: return {};
    }
  }

  Widget _buildEmptyState(IconData icon, String title, String subtitle,
      {String? actionLabel, VoidCallback? onAction}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 64, height: 64,
          decoration: BoxDecoration(color: AppColors.cream, borderRadius: BorderRadius.circular(16)),
          child: Icon(icon, size: 30, color: AppColors.muted)),
        const SizedBox(height: 14),
        Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink)),
        const SizedBox(height: 6),
        Text(subtitle, textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 12, color: AppColors.muted)),
        if (actionLabel != null && onAction != null) ...[
          const SizedBox(height: 16),
          GestureDetector(onTap: onAction,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(color: AppColors.red, borderRadius: BorderRadius.circular(8)),
              child: Text(actionLabel, style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
            ),
          ),
        ],
      ]),
    );
  }

  Widget _field(String label, TextEditingController ctrl,
      {String? hint, bool required = false, bool numeric = false,
        int maxLines = 1, String? note}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label.toUpperCase(), style: const TextStyle(
          fontSize: 10, fontWeight: FontWeight.w700,
          color: AppColors.muted, letterSpacing: 0.6)),
        const SizedBox(height: 6),
        TextFormField(
          controller: ctrl,
          maxLines: maxLines,
          keyboardType: numeric ? TextInputType.number : TextInputType.text,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: AppColors.muted, fontSize: 13),
            filled: true, fillColor: AppColors.cream,
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.border)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.border)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.red, width: 1.5)),
          ),
          validator: required ? (v) => (v == null || v.isEmpty) ? 'Champ requis' : null : null,
        ),
        if (note != null) ...[
          const SizedBox(height: 4),
          Text(note, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
        ],
      ]),
    );
  }

  Widget _buildLoader() => Scaffold(
    backgroundColor: AppColors.cream,
    body: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(width: 56, height: 56,
        decoration: BoxDecoration(color: AppColors.ink, borderRadius: BorderRadius.circular(14)),
        child: const Center(child: CircularProgressIndicator(color: AppColors.red, strokeWidth: 2.5))),
      const SizedBox(height: 16),
      const Text('Chargement...', style: TextStyle(color: AppColors.muted, fontSize: 13)),
    ])),
  );
}

// ─── Painter cercle progress ───────────────────────────────────────────────
class _CircleProgressPainter extends CustomPainter {
  final double progress;
  final Color color;
  const _CircleProgressPainter(this.progress, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 3;
    canvas.drawCircle(center, radius,
      Paint()..color = color.withOpacity(0.12)
        ..style = PaintingStyle.stroke..strokeWidth = 3.5);
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2, 2 * math.pi * progress, false,
      Paint()..color = color..style = PaintingStyle.stroke
        ..strokeWidth = 3.5..strokeCap = StrokeCap.round);
  }

  @override
  bool shouldRepaint(_CircleProgressPainter old) =>
      old.progress != progress || old.color != color;
}