// lib/screens/dashboard_candidat.dart
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../utils/constants.dart';
import '../widgets/fasoia_logo.dart';

class DashboardCandidat extends StatefulWidget {
  const DashboardCandidat({super.key});

  @override
  State<DashboardCandidat> createState() => _DashboardCandidatState();
}

class _DashboardCandidatState extends State<DashboardCandidat>
    with TickerProviderStateMixin {
  
  bool _isLoading = true;
  int _navIndex = 0;
  
  // Données du candidat
  Map<String, dynamic> _profil = {};
  List<dynamic> _offresRecommandees = [];
  List<dynamic> _convocations = [];
  
  // Statistiques
  int _progression = 0;
  int _champsRemplis = 0;
  int _totalChamps = 0;
  int _candidaturesEnvoyees = 0;
  int _entretiensObtenus = 0;
  
  late AnimationController _fadeCtrl;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    print('🟢 DashboardCandidat.initState() - Démarrage');
    _fadeCtrl = AnimationController(
      vsync: this, 
      duration: const Duration(milliseconds: 500),
    );
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    
     _checkTokenAndLoad();
    }

    Future<void> _checkTokenAndLoad() async {
      final token = await StorageService.getAccessToken();
      print('🔑 Token présent: ${token != null}');
      
      if (token == null) {
        // Pas de token, rediriger vers login
        if (mounted) {
          Navigator.pushReplacementNamed(context, '/login');
        }
        return;
      }
    _loadData();
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
  print('🟢 _loadData() - DÉBUT');
  try {
    print('🟢 _loadData() - Appel ApiService.getCandidatProfil()');
    final profil = await ApiService.getCandidatProfil();
    print('🟢 _loadData() - Profil reçu: ${profil.keys}');
    print('📊 profil_complet reçu: ${profil['profil_complet']}');
    print('📊 offres_recommandees length: ${profil['offres_recommandees']?.length ?? 0}');
    print('📊 offres_recommandees: ${profil['offres_recommandees']}');

    print('🟢 _loadData() - Appel ApiService.getCandidatOffresRecommandees()');
    final offres = await ApiService.getCandidatOffresRecommandees();
    print('🟢 _loadData() - Offres reçues: ${offres.length}');
    
    print('🟢 _loadData() - Appel ApiService.getCandidatConvocations()');
    final convocations = await ApiService.getCandidatConvocations();
    print('🟢 _loadData() - Convocations reçues: ${convocations.length}');
    
    if (!mounted) return;
    
    setState(() {
      _profil = profil;
      _offresRecommandees = offres;
      _convocations = convocations;
      _progression = profil['progression'] ?? 0;
      _champsRemplis = profil['champs_remplis'] ?? 0;
      _totalChamps = profil['total_champs'] ?? 22;
      _candidaturesEnvoyees = profil['candidat']?['nb_candidatures_envoyees'] ?? 0;
      _entretiensObtenus = profil['convocations_obtenues'] ?? 0;
      _isLoading = false;
    });
    
    print('🟢 _loadData() - FIN, _offresRecommandees.length = ${_offresRecommandees.length}');
    _fadeCtrl.forward();
  } catch (e) {
    print('❌ _loadData() - ERREUR: $e');
    if (!mounted) return;
    setState(() => _isLoading = false);
  }
}

  String get _prenom => _profil['particulier']?['prenom'] ?? _profil['candidat']?['prenom'] ?? 'Candidat';
  String get _nom => _profil['particulier']?['nom'] ?? _profil['candidat']?['nom'] ?? '';
  String get _localisation => _profil['candidat']?['localisation_recherche'] ?? _profil['particulier']?['ville'] ?? 'Non définie';
  String get _typeContrat => _profil['candidat']?['type_contrat_recherche'] ?? 'Tous contrats';
  String get _disponibilite => _profil['candidat']?['disponibilite'] ?? '';
  bool   get _profilComplet => _profil['profil_complet'] ?? false;

  Future<void> _logout() async {
    await ApiService.logout();
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  Future<void> _repondreConvocation(int convId, String action) async {
    try {
      final result = await ApiService.repondreConvocation(convId, action);
      if (result['success'] && mounted) {
        _loadData();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(action == 'confirmee' ? 'Convocation confirmée' : 'Convocation refusée'),
            backgroundColor: action == 'confirmee' ? AppColors.teal : Colors.orange,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Erreur lors de la réponse'),
            backgroundColor: AppColors.red,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    print('🟢 DashboardCandidat.build() - isLoading: $_isLoading');
    if (_isLoading) return _buildLoader();
    print('🟢 DashboardCandidat.build() - offres length: ${_offresRecommandees.length}');
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
            children: [
              _buildAccueil(),
              _buildOffresPage(),
              _buildProfilPage(),
            ],
          ),
        ),
        bottomNavigationBar: _buildBottomNav(),
      ),
    );
  }

  Widget _buildBottomNav() {
    const items = [
      _NavItem(icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Accueil'),
      _NavItem(icon: Icons.work_outline, activeIcon: Icons.work, label: 'Offres'),
      _NavItem(icon: Icons.person_outline_rounded, activeIcon: Icons.person_rounded, label: 'Profil'),
    ];
    
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 62,
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
                        active ? items[i].activeIcon : items[i].icon,
                        color: active ? AppColors.red : AppColors.muted,
                        size: 24,
                      ),
                      const SizedBox(height: 3),
                      Text(
                        items[i].label,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                          color: active ? AppColors.red : AppColors.muted,
                        ),
                      ),
                      const SizedBox(height: 2),
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        height: 2,
                        width: active ? 20 : 0,
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

  Widget _buildAccueil() {
    print('🔍 _buildAccueil() - _profilComplet: $_profilComplet');
    print('🔍 _buildAccueil() - _offresRecommandees.length: ${_offresRecommandees.length}');
    final initiales = _prenom.isNotEmpty ? _prenom.substring(0, 1).toUpperCase() : 'C';
    final nomComplet = '$_prenom $_nom'.trim();
    
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          expandedHeight: 195,
          pinned: true,
          backgroundColor: AppColors.ink,
          elevation: 0,
          automaticallyImplyLeading: false,
          centerTitle: true,
          title: const FasoiaLogo(fontSize: 22, showSubtitle: true),
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
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.red.withOpacity(0.08),
                  ),
                )),
                Positioned(right: 20, bottom: 20, child: Container(
                  width: 60, height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.red.withOpacity(0.12),
                  ),
                )),
                Positioned(
                  top: 12,
                  left: 0,
                  right: 0,
                  child: SafeArea(
                    bottom: false,
                    child: const Column(children: [
                      SizedBox(height: 6),
                      //FasoiaLogo(fontSize: 22, showSubtitle: true),
                    ]),
                  ),
                ),
                Positioned(
                  left: 20,
                  bottom: 20,
                  right: 70,
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
                          child: Center(child: Text(
                            initiales,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                              fontSize: 16,
                            ),
                          )),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Bonjour,',
                              style: TextStyle(color: Colors.white54, fontSize: 12)),
                            Text(
                              nomComplet.isNotEmpty ? nomComplet : 'Candidat',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        )),
                      ]),
                      const SizedBox(height: 10),
                      if (_localisation.isNotEmpty)
                        _chip(Icons.location_on_outlined, _localisation),
                      if (_typeContrat.isNotEmpty && _typeContrat != 'Tous contrats') ...[
                        const SizedBox(height: 4),
                        _chip(Icons.work_outline, _typeContrat),
                      ],
                      if (_disponibilite.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        _chip(Icons.access_time_rounded, 'Dispo : $_disponibilite'),
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
              _buildStatsGrid(),
              
              const SizedBox(height: 12),
              if (_convocations.isNotEmpty) ...[
                _buildConvocationsSection(),
                const SizedBox(height: 16),
              ],
              if (!_profilComplet)
                _buildEmptyState(
                  Icons.lock_outline_rounded,
                  'Profil incomplet',
                  'Complétez votre profil pour recevoir des recommandations.',
                  actionLabel: 'Compléter',
                  onAction: () => setState(() => _navIndex = 2),
                )
              else if (_offresRecommandees.isEmpty)
                _buildEmptyState(
                  Icons.search_off_rounded,
                  'Aucune recommandation',
                  'Aucune offre disponible pour le moment.',
                )
              else
                ...(_offresRecommandees.take(3).map((o) => _buildOffreCard(o))),
              
              const SizedBox(height: 20),
              Row(children: [
                const Text('OFFRES RECOMMANDÉES', style: TextStyle(
                  fontSize: 11, fontWeight: FontWeight.w800,
                  color: AppColors.muted, letterSpacing: 1.2,
                )),
                const Spacer(),
                if (_offresRecommandees.isNotEmpty)
                  GestureDetector(
                    onTap: () => setState(() => _navIndex = 1),
                    child: const Text('Voir tout →', style: TextStyle(
                      fontSize: 12, color: AppColors.red, fontWeight: FontWeight.w600,
                    )),
                  ),
              ]),
              
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
      Text(label, style: const TextStyle(
        fontSize: 11, color: Colors.white60, fontWeight: FontWeight.w500,
      )),
    ],
  );

  Widget _buildStatsGrid() {
    final stats = [
      _StatData('$_candidaturesEnvoyees', 'Candidatures', Icons.send_rounded, false),
      _StatData('$_entretiensObtenus', 'Entretiens', Icons.calendar_today_rounded, true),
      _StatData('${_offresRecommandees.length}', 'Recommandées', Icons.local_offer_rounded, true),
      _StatData('$_champsRemplis/$_totalChamps', 'Champs profil', Icons.edit_note_rounded, false),
    ];
    
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      childAspectRatio: 1.7,
      children: stats.map((s) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
        decoration: BoxDecoration(
          color: s.accent ? AppColors.ink : Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: s.accent ? AppColors.ink : AppColors.border),
        ),
        child: 
          Row(
            children: [
              Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: s.accent ? AppColors.red.withOpacity(0.2) : AppColors.cream,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(s.icon, size: 18, color: s.accent ? AppColors.red : AppColors.muted),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(s.value, style: TextStyle(
                      fontSize: 18, 
                      fontWeight: FontWeight.w800,
                      color: s.accent ? Colors.white : AppColors.ink,
                    )),
                    Text(
                      s.label, 
                      style: TextStyle(
                        fontSize: 9, 
                        fontWeight: FontWeight.w600,
                        color: s.accent ? Colors.white54 : AppColors.muted,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ]
          ),
      )).toList(),
    );
  }

  Widget _buildConvocationsSection() {
    if (_convocations.isEmpty) return const SizedBox();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          const Icon(Icons.calendar_today_rounded, size: 14, color: AppColors.teal),
          const SizedBox(width: 6),
          const Text('MES CONVOCATIONS', style: TextStyle(
            fontSize: 11, fontWeight: FontWeight.w800,
            color: AppColors.muted, letterSpacing: 1.2,
          )),
        ]),
        const SizedBox(height: 10),
        ...(_convocations.take(2).map((c) => _buildConvocationCardCompact(c))),
        if (_convocations.length > 2)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: GestureDetector(
              onTap: () => setState(() => _navIndex = 2),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Voir toutes mes convocations →', style: TextStyle(
                    fontSize: 11, color: AppColors.red, fontWeight: FontWeight.w600,
                  )),
                ],
              ),
            ),
          ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildConvocationCardCompact(dynamic conv) {
    final date = conv['date_rdv'] ?? '';
    final heure = conv['heure_rdv'] ?? '';
    final poste = conv['poste'] ?? conv['dossier']?['offre']?['titre'] ?? 'Entretien';
    final organisation = conv['organisation'] ?? conv['recruteur']?['organisation'] ?? '';
    final statut = conv['statut'] ?? 'en_attente';
    final statusColor = statut == 'confirmee' ? AppColors.teal 
        : statut == 'annulee' ? Colors.red 
        : Colors.orange;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
        boxShadow: [BoxShadow(
          color: Colors.black.withOpacity(0.04),
          blurRadius: 6,
          offset: const Offset(0, 2),
        )],
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppColors.teal.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.calendar_today_rounded, size: 20, color: AppColors.teal),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  poste,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  organisation,
                  style: const TextStyle(fontSize: 11, color: AppColors.muted),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 10, color: AppColors.muted),
                    const SizedBox(width: 4),
                    Text(date, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
                    const SizedBox(width: 8),
                    const Icon(Icons.access_time, size: 10, color: AppColors.muted),
                    const SizedBox(width: 4),
                    Text(heure, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
                  ],
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: statusColor.withOpacity(0.3)),
            ),
            child: Text(
              statut == 'confirmee' ? 'Confirmée' : statut == 'annulee' ? 'Annulée' : 'En attente',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: statusColor),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOffresPage() {
    print('🔍 _buildOffresPage() - _offresRecommandees length: ${_offresRecommandees.length}');
    
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          pinned: true,
          backgroundColor: AppColors.ink,
          automaticallyImplyLeading: false,
          centerTitle: true,
          title: const FasoiaLogo(fontSize: 18, showSubtitle: false),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(3),
            child: Container(height: 3, color: AppColors.red),
          ),
        ),
        // ⚠️ VÉRIFIE CETTE PARTIE - La condition doit être sur _offresRecommandees
        if (_offresRecommandees.isEmpty)
          SliverFillRemaining(
            child: Center(
              child: _buildEmptyState(
                Icons.search_off_rounded,
                'Aucune offre',
                _profilComplet
                    ? 'Aucune recommandation disponible pour le moment.'
                    : 'Complétez votre profil pour recevoir des recommandations.',
                actionLabel: _profilComplet ? null : 'Compléter le profil',
                onAction: _profilComplet ? null : () => setState(() => _navIndex = 2),
              ),
            ),
          )
        else
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, i) {
                  print('🔍 Construction de la carte $i');
                  return _buildOffreCard(_offresRecommandees[i]);
                },
                childCount: _offresRecommandees.length,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildOffreCard(dynamic offre) {
    print('🔍 _buildOffreCard() - titre: ${offre['titre']}');
    
    final titre = offre['titre'] ?? 'Offre';
    final entreprise = offre['entreprise'] ?? offre['recruteur']?['organisation'] ?? 'Entreprise';
    final lieu = offre['ville'] ?? offre['localisation'] ?? 'Non spécifié';
    final typeContrat = offre['type_contrat'] ?? offre['get_type_contrat_display'] ?? 'Emploi';
    final score = (offre['score'] ?? 0).toDouble();
    final dateLimite = offre['date_limite'] ?? '';
    
    return GestureDetector(
      onTap: () => _showOffreDetails(offre),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
          boxShadow: [BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 3),
          )],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.red.withOpacity(0.06),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.red,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  typeContrat.toUpperCase(),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  titre,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppColors.ink,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              SizedBox(
                width: 38,
                height: 38,
                child: CustomPaint(
                  painter: _CircleProgressPainter(score / 100, AppColors.teal),
                  child: Center(
                    child: Text(
                      '${score.round()}%',
                      style: const TextStyle(
                        fontSize: 8,
                        fontWeight: FontWeight.w800,
                        color: AppColors.ink,
                      ),
                    ),
                  ),
                ),
              ),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.business_outlined, size: 12, color: AppColors.muted),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    entreprise,
                    style: const TextStyle(fontSize: 12, color: AppColors.muted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ]),
              const SizedBox(height: 6),
              Row(children: [
                const Icon(Icons.location_on_outlined, size: 12, color: AppColors.muted),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    lieu,
                    style: const TextStyle(fontSize: 12, color: AppColors.muted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ]),
              if (dateLimite.isNotEmpty) ...[
                const SizedBox(height: 10),
                Row(children: [
                  const Icon(Icons.schedule_rounded, size: 12, color: AppColors.muted),
                  const SizedBox(width: 4),
                  Text(
                    'Limite : $dateLimite',
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF862323),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => _showOffreDetails(offre),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                      decoration: BoxDecoration(
                        color: AppColors.red,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        'Voir →',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
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

  void _showOffreDetails(dynamic offre) {
    final titre = offre['titre'] ?? 'Offre';
    final entreprise = offre['entreprise'] ?? offre['recruteur']?['organisation'] ?? 'Non précisée';
    final lieu = offre['ville'] ?? offre['localisation'] ?? 'Non précisé';
    final typeContrat = offre['type_contrat'] ?? offre['get_type_contrat_display'] ?? 'Emploi';
    final description = offre['description'] ?? 'Aucune description';
    final dateLimite = offre['date_limite'] ?? 'Non spécifiée';
    final score = (offre['score'] ?? 0).toDouble();
    
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
          Container(
            margin: const EdgeInsets.only(top: 10),
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Container(
            padding: const EdgeInsets.fromLTRB(20, 14, 12, 14),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(children: [
              Expanded(
                child: Text(
                  titre,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.ink,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close_rounded, color: AppColors.muted, size: 20),
                onPressed: () => Navigator.pop(context),
              ),
            ]),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.cream,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(children: [
                    SizedBox(
                      width: 60,
                      height: 60,
                      child: CustomPaint(
                        painter: _CircleProgressPainter(score / 100, AppColors.teal),
                        child: Center(
                          child: Text(
                            '${score.round()}%',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                              color: AppColors.ink,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Score de correspondance',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: AppColors.ink,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Basé sur votre profil',
                          style: TextStyle(fontSize: 11, color: AppColors.muted),
                        ),
                      ],
                    ),
                  ]),
                ),
                const SizedBox(height: 20),
                _sheetField('Entreprise', entreprise),
                _sheetField('Lieu', lieu),
                _sheetField('Type de contrat', typeContrat),
                _sheetField('Date limite', dateLimite),
                _sheetField('Description', description),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.send_rounded, size: 16),
                    label: const Text('Postuler à cette offre'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ]),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _sheetField(String label, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(
        label.toUpperCase(),
        style: const TextStyle(
          fontSize: 10,
          letterSpacing: 1.2,
          color: AppColors.muted,
          fontWeight: FontWeight.w700,
        ),
      ),
      const SizedBox(height: 6),
      Text(
        value,
        style: const TextStyle(fontSize: 14, color: AppColors.ink, height: 1.5),
      ),
      const Divider(color: AppColors.border, height: 24),
    ]),
  );

    Widget _buildProfilPage() {
    final particulier = _profil['particulier'] ?? {};
    final candidat = _profil['candidat'] ?? {};
    
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverAppBar(
          pinned: true,
          backgroundColor: AppColors.ink,
          automaticallyImplyLeading: false,
          centerTitle: true,
          title: const FasoiaLogo(fontSize: 18, showSubtitle: true),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(3),
            child: Container(height: 3, color: AppColors.red),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              // Carte de progression
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: AppColors.ink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(children: [
                  SizedBox(
                    width: 64,
                    height: 64,
                    child: CustomPaint(
                      painter: _CircleProgressPainter(_progression / 100, AppColors.red),
                      child: Center(
                        child: Text(
                          '$_progression%',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _profilComplet ? 'Profil complet ✓' : 'Profil incomplet',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _profilComplet
                              ? 'Votre profil est visible par les recruteurs'
                              : 'Complétez votre profil pour recevoir des recommandations',
                          style: const TextStyle(color: Colors.white54, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ]),
              ),
              const SizedBox(height: 20),

              // Informations personnelles
              const Text(
                'INFORMATIONS PERSONNELLES',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppColors.muted,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 12),
              _buildInfoTile('Nom complet', '${particulier['prenom'] ?? ''} ${particulier['nom'] ?? ''}'.trim()),
              _buildInfoTile('Email', particulier['email'] ?? 'Non renseigné'),
              _buildInfoTile('Téléphone', particulier['telephone'] ?? 'Non renseigné'),
              _buildInfoTile('Ville', particulier['ville'] ?? 'Non renseignée'),
              _buildInfoTile('Pays', particulier['pays'] ?? 'Non renseigné'),
              const SizedBox(height: 16),

              // Profil professionnel
              const Text(
                'PROFIL PROFESSIONNEL',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppColors.muted,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 12),
              _buildInfoTile("Niveau d'étude", candidat['niveauEtude'] ?? 'Non renseigné'),
              _buildInfoTile("Années d'expérience", (candidat['anneesExperiences'] ?? 0).toString()),
              _buildInfoTile('Compétences', candidat['competences'] ?? 'Non renseignées'),
              _buildInfoTile('Langues', candidat['niveauLangues'] ?? 'Non renseignées'),
              _buildInfoTile('Disponibilité', candidat['disponibilite'] ?? 'Non renseignée'),
              const SizedBox(height: 16),

              // Recherche d'emploi
              const Text(
                'RECHERCHE D\'EMPLOI',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AppColors.muted,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 12),
              _buildInfoTile('Secteur recherché', candidat['secteur_recherche'] ?? 'Non renseigné'),
              _buildInfoTile('Type de contrat', candidat['type_contrat_recherche'] ?? 'Non renseigné'),
              _buildInfoTile('Localisation souhaitée', candidat['localisation_recherche'] ?? 'Non renseignée'),
              _buildInfoTile('Salaire souhaité', candidat['salaire_souhaite'] != null ? '${candidat['salaire_souhaite']} FCFA' : 'Non renseigné'),
              _buildInfoTile('Mobilité', candidat['mobilite'] == true ? 'Oui' : 'Non'),
              const SizedBox(height: 16),

              // Convocations détaillées
              if (_convocations.isNotEmpty) ...[
                const Text(
                  'MES CONVOCATIONS',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: AppColors.muted,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 12),
                ..._convocations.map((c) => _buildConvocationCardFull(c)),
              ],
              const SizedBox(height: 20),

              // Bouton déconnexion
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _logout,
                  icon: const Icon(Icons.logout_rounded, size: 16, color: AppColors.muted),
                  label: const Text(
                    'Se déconnecter',
                    style: TextStyle(color: AppColors.muted),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: AppColors.border),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
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

  Widget _buildInfoTile(String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.muted,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.ink,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConvocationCardFull(dynamic conv) {
    final date = conv['date_rdv'] ?? '';
    final heure = conv['heure_rdv'] ?? '';
    final poste = conv['poste'] ?? 'Entretien';
    final organisation = conv['organisation'] ?? '';
    final lieu = conv['lieu_rdv'] ?? '';
    final message = conv['message'] ?? '';
    final typeEntretien = conv['type_entretien'] ?? 'entretien';
    final statut = conv['statut'] ?? 'en_attente';
    final isOnline = lieu.toString().startsWith('http');
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.teal, width: 1.5),
        boxShadow: [BoxShadow(
          color: Colors.black.withOpacity(0.04),
          blurRadius: 8,
          offset: const Offset(0, 2),
        )],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.teal,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
            ),
            child: Row(
              children: [
                const Icon(Icons.calendar_today_rounded, size: 12, color: Colors.white),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    typeEntretien.toString().toUpperCase(),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: Colors.white),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    statut == 'confirmee' ? 'Confirmée' : statut == 'annulee' ? 'Annulée' : 'En attente',
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Column(
                    children: [
                      Text(
                        date,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.ink),
                      ),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.access_time_rounded, size: 14, color: AppColors.teal),
                          const SizedBox(width: 4),
                          Text(heure, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.teal)),
                        ],
                      ),
                    ],
                  ),
                ),
                Text(poste, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(organisation, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.cream,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 14, color: AppColors.teal),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          isOnline ? 'Lien de réunion' : lieu,
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: isOnline ? AppColors.teal : AppColors.ink),
                        ),
                      ),
                    ],
                  ),
                ),
                if (message.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.cream,
                      borderRadius: BorderRadius.circular(6),
                      border: const Border(left: BorderSide(color: AppColors.teal, width: 3)),
                    ),
                    child: Text('"$message"', style: const TextStyle(fontSize: 11, color: AppColors.muted, fontStyle: FontStyle.italic)),
                  ),
                ],
                const SizedBox(height: 12),
                const Divider(),
                const SizedBox(height: 12),
                if (isOnline)
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.videocam_rounded, size: 14, color: Colors.white),
                      label: const Text("Rejoindre l'entretien", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.red,
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                  )
                else if (statut == 'en_attente')
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _repondreConvocation(conv['id'], 'confirmee'),
                          icon: const Icon(Icons.check_rounded, size: 14, color: Colors.white),
                          label: const Text('Accepter', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.teal,
                            padding: const EdgeInsets.symmetric(vertical: 11),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _repondreConvocation(conv['id'], 'annulee'),
                          icon: const Icon(Icons.close_rounded, size: 14, color: Colors.white),
                          label: const Text('Refuser', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.red,
                            padding: const EdgeInsets.symmetric(vertical: 11),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                      ),
                    ],
                  )
                else
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    decoration: BoxDecoration(
                      color: statut == 'confirmee' ? AppColors.teal.withOpacity(0.08) : Colors.red.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: statut == 'confirmee' ? AppColors.teal.withOpacity(0.3) : Colors.red.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          statut == 'confirmee' ? Icons.check_circle_rounded : Icons.cancel_rounded,
                          size: 14,
                          color: statut == 'confirmee' ? AppColors.teal : Colors.red,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          statut == 'confirmee' ? 'Convocation confirmée' : 'Convocation annulée',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: statut == 'confirmee' ? AppColors.teal : Colors.red),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(IconData icon, String title, String subtitle,
      {String? actionLabel, VoidCallback? onAction}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            color: AppColors.cream,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Icon(icon, size: 30, color: AppColors.muted),
        ),
        const SizedBox(height: 14),
        Text(
          title,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: AppColors.ink,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          subtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 12, color: AppColors.muted),
        ),
        if (actionLabel != null && onAction != null) ...[
          const SizedBox(height: 16),
          GestureDetector(
            onTap: onAction,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.red,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                actionLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ),
          ),
        ],
      ]),
    );
  }

  Widget _buildLoader() => Scaffold(
    backgroundColor: AppColors.cream,
    body: Center(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: AppColors.ink,
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Center(
            child: CircularProgressIndicator(
              color: AppColors.red,
              strokeWidth: 2.5,
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Chargement...',
          style: TextStyle(color: AppColors.muted, fontSize: 13),
        ),
      ]),
    ),
  );
}

// ═══════════════════════════════════════════════════════════════════════
// MODÈLES INTERNES
// ═══════════════════════════════════════════════════════════════════════
class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _NavItem({required this.icon, required this.activeIcon, required this.label});
}

class _StatData {
  final String value;
  final String label;
  final IconData icon;
  final bool accent;
  const _StatData(this.value, this.label, this.icon, this.accent);
}

// ═══════════════════════════════════════════════════════════════════════
// PAINTER CERCLE PROGRESS
// ═══════════════════════════════════════════════════════════════════════
class _CircleProgressPainter extends CustomPainter {
  final double progress;
  final Color color;
  const _CircleProgressPainter(this.progress, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 3;
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..color = color.withOpacity(0.12)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.5,
    );
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      2 * math.pi * progress,
      false,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.5
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_CircleProgressPainter old) =>
      old.progress != progress || old.color != color;
}