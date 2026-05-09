import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class DashboardCandidat extends StatefulWidget {
  const DashboardCandidat({super.key});

  @override
  State<DashboardCandidat> createState() => _DashboardCandidatState();
}

class _DashboardCandidatState extends State<DashboardCandidat>
    with SingleTickerProviderStateMixin {
  // ── Palette ──────────────────────────────────
  static const _red    = Color(0xFFD32F2F);
  static const _cream  = Color(0xFFF8F4ED);
  static const _ink    = Color(0xFF2C1810);
  static const _muted  = Color(0xFF8B7355);
  static const _border = Color(0xFFE0D8CC);
  static const _teal   = Color(0xFF0D7377);
  static const _white  = Colors.white;

  // ── État API ─────────────────────────────────
  bool _loading = true;
  String? _error;

  Map<String, dynamic> _candidat = {};
  int _progression = 0;
  List<Map<String, dynamic>> _offres = [];
  List<Map<String, dynamic>> _convocations = [];

  // ── Formulaire ───────────────────────────────
  late TabController _tabController;
  final _formKey = GlobalKey<FormState>();

  final _nomCtrl           = TextEditingController();
  final _prenomCtrl        = TextEditingController();
  final _emailCtrl         = TextEditingController();
  final _telCtrl           = TextEditingController();
  final _villeCtrl         = TextEditingController();
  final _paysCtrl          = TextEditingController();
  final _niveauEtudeCtrl   = TextEditingController();
  final _anneesExpCtrl     = TextEditingController();
  final _competencesCtrl   = TextEditingController();
  final _languesCtrl       = TextEditingController();
  final _secteurCtrl       = TextEditingController();
  final _salaireCtrl       = TextEditingController();
  final _localisationCtrl  = TextEditingController();
  String _disponibilite    = '';
  String _typeContrat      = '';
  bool   _mobilite         = false;
  bool   _profilExpanded   = false;

  // ── Config API ───────────────────────────────
  // Remplacez par votre URL de base
  static const _baseUrl = 'https://votre-domaine.com/api';

  // Remplacez par votre token auth (ex: récupéré depuis SharedPreferences)
  static const _token = 'VOTRE_TOKEN_ICI';

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Token $_token',
  };

  // ─────────────────────────────────────────────
  // CYCLE DE VIE
  // ─────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _fetchData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    for (final c in [
      _nomCtrl, _prenomCtrl, _emailCtrl, _telCtrl, _villeCtrl, _paysCtrl,
      _niveauEtudeCtrl, _anneesExpCtrl, _competencesCtrl, _languesCtrl,
      _secteurCtrl, _salaireCtrl, _localisationCtrl,
    ]) { c.dispose(); }
    super.dispose();
  }

  // ─────────────────────────────────────────────
  // APPELS API
  // ─────────────────────────────────────────────
  Future<void> _fetchData() async {
    setState(() { _loading = true; _error = null; });
    try {
      // Appels parallèles
      final results = await Future.wait([
        http.get(Uri.parse('$_baseUrl/candidat/profil/'), headers: _headers),
        http.get(Uri.parse('$_baseUrl/candidat/offres-recommandees/'), headers: _headers),
        http.get(Uri.parse('$_baseUrl/candidat/convocations/'), headers: _headers),
      ]);

      if (results[0].statusCode == 200) {
        final data = jsonDecode(utf8.decode(results[0].bodyBytes));
        setState(() {
          _candidat    = Map<String, dynamic>.from(data['candidat'] ?? {});
          _progression = data['progression'] ?? 0;
        });
        _remplirFormulaire();
      }

      if (results[1].statusCode == 200) {
        final data = jsonDecode(utf8.decode(results[1].bodyBytes));
        setState(() {
          _offres = List<Map<String, dynamic>>.from(data['offres'] ?? []);
        });
      }

      if (results[2].statusCode == 200) {
        final data = jsonDecode(utf8.decode(results[2].bodyBytes));
        setState(() {
          _convocations = List<Map<String, dynamic>>.from(data['convocations'] ?? []);
        });
      }
    } catch (e) {
      setState(() => _error = 'Erreur de connexion au serveur');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _remplirFormulaire() {
    _nomCtrl.text          = _candidat['nom']                   ?? '';
    _prenomCtrl.text       = _candidat['prenom']                ?? '';
    _emailCtrl.text        = _candidat['email']                 ?? '';
    _telCtrl.text          = _candidat['telephone']             ?? '';
    _villeCtrl.text        = _candidat['ville']                 ?? '';
    _paysCtrl.text         = _candidat['pays']                  ?? '';
    _niveauEtudeCtrl.text  = _candidat['niveauEtude']           ?? '';
    _anneesExpCtrl.text    = (_candidat['anneesExperiences'] ?? '').toString();
    _competencesCtrl.text  = _candidat['competences']           ?? '';
    _languesCtrl.text      = _candidat['niveauLangues']         ?? '';
    _secteurCtrl.text      = _candidat['secteur_recherche']     ?? '';
    _salaireCtrl.text      = (_candidat['salaire_souhaite'] ?? '').toString();
    _localisationCtrl.text = _candidat['localisation_recherche'] ?? '';
    _disponibilite         = _candidat['disponibilite']         ?? '';
    _typeContrat           = _candidat['type_contrat_recherche'] ?? '';
    _mobilite              = _candidat['mobilite']              ?? false;
  }

  Future<void> _submitProfil() async {
    if (!_formKey.currentState!.validate()) return;

    final body = jsonEncode({
      'nom':                    _nomCtrl.text,
      'prenom':                 _prenomCtrl.text,
      'email':                  _emailCtrl.text,
      'telephone':              _telCtrl.text,
      'ville':                  _villeCtrl.text,
      'pays':                   _paysCtrl.text,
      'niveauEtude':            _niveauEtudeCtrl.text,
      'anneesExperiences':      int.tryParse(_anneesExpCtrl.text) ?? 0,
      'competences':            _competencesCtrl.text,
      'niveauLangues':          _languesCtrl.text,
      'secteur_recherche':      _secteurCtrl.text,
      'salaire_souhaite':       int.tryParse(_salaireCtrl.text) ?? 0,
      'localisation_recherche': _localisationCtrl.text,
      'disponibilite':          _disponibilite,
      'type_contrat_recherche': _typeContrat,
      'mobilite':               _mobilite,
    });

    try {
      final res = await http.patch(
        Uri.parse('$_baseUrl/candidat/profil/'),
        headers: _headers,
        body: body,
      );
      if (res.statusCode == 200) {
        _showSnack('Profil enregistré avec succès', success: true);
        _fetchData();
      } else {
        _showSnack('Erreur lors de l\'enregistrement');
      }
    } catch (_) {
      _showSnack('Erreur de connexion');
    }
  }

  Future<void> _repondreConvocation(int id, String statut) async {
    try {
      final res = await http.post(
        Uri.parse('$_baseUrl/candidat/convocations/$id/repondre/'),
        headers: _headers,
        body: jsonEncode({'action': statut}),
      );
      if (res.statusCode == 200) {
        _showSnack(
          statut == 'confirmee' ? 'Convocation confirmée' : 'Convocation refusée',
          success: statut == 'confirmee',
        );
        _fetchData();
      }
    } catch (_) {
      _showSnack('Erreur de connexion');
    }
  }

  void _showSnack(String msg, {bool success = false}) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: success ? _teal : _red,
    ));
  }

  // ─────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        backgroundColor: Color(0xFFF8F4ED),
        body: Center(child: CircularProgressIndicator(color: Color(0xFFD32F2F))),
      );
    }
    if (_error != null) {
      return Scaffold(
        backgroundColor: _cream,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off, size: 48, color: _muted),
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: _muted)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchData,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _ink,
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                ),
                child: const Text('Réessayer', style: TextStyle(color: _white)),
              ),
            ],
          ),
        ),
      );
    }

    final bool profilComplet = _progression >= 100;

    return Scaffold(
      backgroundColor: _cream,
      appBar: _buildAppBar(),
      body: RefreshIndicator(
        color: _red,
        onRefresh: _fetchData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              _buildStatsRow(),
              if (profilComplet) _buildSuccessBanner(),
              if (!profilComplet || _profilExpanded) _buildProfilForm(),
              if (_convocations.isNotEmpty) _buildConvocationsSection(),
              _buildOffresSection(),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────
  // APPBAR
  // ─────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar() {
    final prenom = _candidat['prenom'] ?? '';
    return AppBar(
      backgroundColor: _white,
      elevation: 0,
      centerTitle: false,
      title: RichText(
        text: const TextSpan(
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
              letterSpacing: 1.5, color: _ink),
          children: [
            TextSpan(text: 'FASO'),
            TextSpan(text: 'IA', style: TextStyle(color: _red)),
          ],
        ),
      ),
      actions: [
        IconButton(onPressed: () {},
            icon: const Icon(Icons.notifications_none, color: _ink)),
        Padding(
          padding: const EdgeInsets.only(right: 16),
          child: CircleAvatar(
            backgroundColor: _red,
            radius: 16,
            child: Text(
              prenom.isNotEmpty ? prenom[0].toUpperCase() : 'C',
              style: const TextStyle(color: _white,
                  fontWeight: FontWeight.w800, fontSize: 14),
            ),
          ),
        ),
      ],
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(color: _border, height: 1),
      ),
    );
  }

  // ─────────────────────────────────────────────
  // HEADER
  // ─────────────────────────────────────────────
  Widget _buildHeader() {
    final prenom      = _candidat['prenom']                  ?? '';
    final nom         = _candidat['nom']                     ?? '';
    final localisation= _candidat['localisation_recherche']  ?? '';
    final contrat     = _candidat['type_contrat_recherche']  ?? '';
    final dispo       = _candidat['disponibilite']           ?? '';

    return Container(
      color: _ink,
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                RichText(
                  text: TextSpan(
                    style: const TextStyle(fontSize: 22,
                        fontWeight: FontWeight.w800, color: _white, height: 1.2),
                    children: [
                      const TextSpan(text: 'Bonjour, '),
                      TextSpan(text: prenom,
                          style: const TextStyle(color: _red)),
                      TextSpan(text: ' $nom'),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8, runSpacing: 6,
                  children: [
                    if (localisation.isNotEmpty)
                      _buildTag(Icons.location_on_outlined, localisation),
                    if (contrat.isNotEmpty)
                      _buildTag(Icons.work_outline, contrat),
                    if (dispo.isNotEmpty)
                      _buildTag(Icons.access_time, 'Dispo : $dispo'),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 40,
                      fontWeight: FontWeight.w800, color: _white, height: 1),
                  children: [
                    TextSpan(text: '$_progression'),
                    const TextSpan(text: '%',
                        style: TextStyle(color: _red, fontSize: 26)),
                  ],
                ),
              ),
              const SizedBox(height: 4),
              const Text('PROFIL COMPLÉTÉ',
                  style: TextStyle(fontSize: 9, color: _red,
                      letterSpacing: 1, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              SizedBox(
                width: 100,
                child: LinearProgressIndicator(
                  value: _progression / 100,
                  backgroundColor: Colors.white12,
                  valueColor: const AlwaysStoppedAnimation<Color>(_red),
                  minHeight: 3,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTag(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(border: Border.all(color: Colors.white24)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: Colors.white38),
          const SizedBox(width: 5),
          Text(label, style: const TextStyle(fontSize: 11,
              color: Colors.white70, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────
  // STATS
  // ─────────────────────────────────────────────
  Widget _buildStatsRow() {
    final nbCandidatures = _candidat['nb_candidatures_envoyees'] ?? 0;
    final nbEntretiens   = _candidat['convocations_obtenues']    ?? 0;
    final champsRemplis  = _candidat['champs_remplis']           ?? 0;
    final totalChamps    = _candidat['total_champs']             ?? 12;

    return Container(
      color: _white,
      child: Row(
        children: [
          _buildStatCell('$nbCandidatures',        'Candidatures',   false),
          _buildStatDivider(),
          _buildStatCell('$nbEntretiens',           'Entretiens',     true),
          _buildStatDivider(),
          _buildStatCell('${_offres.length}',       'Recommandées',   true),
          _buildStatDivider(),
          _buildStatCell('$champsRemplis/$totalChamps', 'Champs profil', false),
        ],
      ),
    );
  }

  Widget _buildStatCell(String value, String label, bool accent) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: const BoxDecoration(
            border: Border(bottom: BorderSide(color: _border))),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 20,
                fontWeight: FontWeight.w800,
                color: accent ? _red : _ink)),
            const SizedBox(height: 3),
            Text(label, textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 9, color: _muted),
                maxLines: 2),
          ],
        ),
      ),
    );
  }

  Widget _buildStatDivider() =>
      Container(width: 1, height: 54, color: _border);

  // ─────────────────────────────────────────────
  // BANNIÈRE SUCCÈS
  // ─────────────────────────────────────────────
  Widget _buildSuccessBanner() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: _white,
        border: Border(left: BorderSide(color: _teal, width: 3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle, color: _teal, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Profil complété à $_progression%',
                    style: const TextStyle(fontWeight: FontWeight.w700,
                        fontSize: 13, color: _ink)),
                const SizedBox(height: 2),
                const Text('Votre profil est visible par les recruteurs.',
                    style: TextStyle(fontSize: 12, color: _muted)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => setState(() => _profilExpanded = !_profilExpanded),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(border: Border.all(color: _ink)),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.edit, size: 12, color: _ink),
                  SizedBox(width: 5),
                  Text('Modifier', style: TextStyle(fontSize: 10,
                      fontWeight: FontWeight.w800, color: _ink)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────
  // FORMULAIRE PROFIL
  // ─────────────────────────────────────────────
  Widget _buildProfilForm() {
    final profilComplet = _progression >= 100;
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      decoration: BoxDecoration(
          color: _white, border: Border.all(color: _border)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
            decoration: const BoxDecoration(
                border: Border(bottom: BorderSide(color: _border))),
            child: Row(
              children: [
                Text(profilComplet ? 'Modifier votre profil' : 'Compléter votre profil',
                    style: const TextStyle(fontSize: 16,
                        fontWeight: FontWeight.w800, color: _ink)),
                const Spacer(),
                const Text('* Requis',
                    style: TextStyle(fontSize: 10, color: _muted)),
              ],
            ),
          ),
          TabBar(
            controller: _tabController,
            isScrollable: true,
            labelColor: _ink,
            unselectedLabelColor: _muted,
            indicatorColor: _red,
            indicatorWeight: 2,
            labelStyle: const TextStyle(fontSize: 10,
                fontWeight: FontWeight.w800, letterSpacing: 0.5),
            tabs: const [
              Tab(text: 'PERSONNEL'),
              Tab(text: 'PROFIL PRO'),
              Tab(text: 'RECHERCHE'),
              Tab(text: 'DOCUMENTS'),
            ],
          ),
          SizedBox(
            height: 440,
            child: Form(
              key: _formKey,
              child: TabBarView(
                controller: _tabController,
                children: [
                  _tabPersonnel(),
                  _tabProfessionnel(),
                  _tabRecherche(),
                  _tabDocuments(),
                ],
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: _border))),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _submitProfil,
                icon: const Icon(Icons.save_outlined, size: 16, color: _white),
                label: const Text('ENREGISTRER',
                    style: TextStyle(fontSize: 11,
                        fontWeight: FontWeight.w800, color: _white)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _ink,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: BorderRadius.zero),
                  elevation: 0,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tabPersonnel() => SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(children: [
      _row([_field('Nom *', _nomCtrl, required: true),
            _field('Prénom *', _prenomCtrl, required: true)]),
      _row([_field('Email *', _emailCtrl,
                type: TextInputType.emailAddress, required: true),
            _field('Téléphone *', _telCtrl,
                type: TextInputType.phone, required: true)]),
      _row([_field('Ville', _villeCtrl, hint: 'Ex : Ouagadougou'),
            _field('Pays', _paysCtrl, hint: 'Ex : Burkina Faso')]),
    ]),
  );

  Widget _tabProfessionnel() => SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _row([_field("Niveau d'étude *", _niveauEtudeCtrl,
                hint: 'Ex : Bac+5', required: true),
            _field("Années d'expérience *", _anneesExpCtrl,
                type: TextInputType.number, required: true)]),
      _label('Compétences *'),
      _textarea(_competencesCtrl, 'Python, Django, Gestion de projet…'),
      const SizedBox(height: 4),
      const Text('Séparez par des virgules',
          style: TextStyle(fontSize: 10, color: _muted)),
      const SizedBox(height: 14),
      _row([_field('Langues *', _languesCtrl,
                hint: 'Français (courant)', required: true),
            _dropdown('Disponibilité *', _disponibilite,
                ['immédiate', '1 semaine', '2 semaines', '1 mois'],
                (v) => setState(() => _disponibilite = v!))]),
    ]),
  );

  Widget _tabRecherche() => SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _row([_field('Secteur recherché *', _secteurCtrl,
                hint: 'Informatique, Finance…', required: true),
            _dropdown('Type de contrat', _typeContrat,
                ['CDI', 'CDD', 'Stage', 'Alternance'],
                (v) => setState(() => _typeContrat = v!))]),
      _row([_field('Localisation *', _localisationCtrl,
                hint: 'Ex : Ouagadougou', required: true),
            _field('Salaire souhaité (FCFA)', _salaireCtrl,
                type: TextInputType.number)]),
      const SizedBox(height: 8),
      GestureDetector(
        onTap: () => setState(() => _mobilite = !_mobilite),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(border: Border.all(color: _border)),
          child: Row(
            children: [
              Checkbox(
                value: _mobilite,
                onChanged: (v) => setState(() => _mobilite = v!),
                activeColor: _ink,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              const SizedBox(width: 8),
              const Expanded(
                child: Text('Disponible pour mobilité géographique',
                    style: TextStyle(fontSize: 13, color: _ink)),
              ),
            ],
          ),
        ),
      ),
    ]),
  );

  Widget _tabDocuments() => SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _label('CV *'),
      _uploadZone('PDF, DOC, DOCX'),
      const SizedBox(height: 16),
      _label('Lettre de motivation (optionnel)'),
      _uploadZone('PDF, DOC, DOCX'),
    ]),
  );

  // ─────────────────────────────────────────────
  // HELPERS FORMULAIRE
  // ─────────────────────────────────────────────
  Widget _row(List<Widget> children) => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: Row(
      children: children.map((w) => Expanded(
        child: Padding(padding: const EdgeInsets.only(right: 8), child: w),
      )).toList(),
    ),
  );

  Widget _label(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 5),
    child: Text(text, style: const TextStyle(fontSize: 10,
        fontWeight: FontWeight.w700, color: _muted, letterSpacing: 0.8)),
  );

  InputDecoration get _inputDeco => const InputDecoration(
    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    filled: true, fillColor: _white,
    border: OutlineInputBorder(borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: _border)),
    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: _border)),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: _ink)),
    errorBorder: OutlineInputBorder(borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: _red)),
  );

  Widget _field(String label, TextEditingController ctrl,
      {TextInputType type = TextInputType.text,
       String? hint,
       bool required = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label(label),
        TextFormField(
          controller: ctrl,
          keyboardType: type,
          style: const TextStyle(fontSize: 13, color: _ink),
          decoration: _inputDeco.copyWith(hintText: hint,
              hintStyle: const TextStyle(fontSize: 12, color: _muted)),
          validator: required
              ? (v) => (v == null || v.trim().isEmpty) ? 'Requis' : null
              : null,
        ),
      ],
    );
  }

  Widget _textarea(TextEditingController ctrl, String hint) =>
      TextFormField(
        controller: ctrl, maxLines: 3,
        style: const TextStyle(fontSize: 13, color: _ink),
        decoration: _inputDeco.copyWith(hintText: hint,
            hintStyle: const TextStyle(fontSize: 12, color: _muted),
            contentPadding: const EdgeInsets.all(12)),
      );

  Widget _dropdown(String label, String value, List<String> items,
      ValueChanged<String?> onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label(label),
        DropdownButtonFormField<String>(
          initialValue: value.isEmpty ? null : value,
          hint: const Text('Sélectionnez…',
              style: TextStyle(fontSize: 12, color: _muted)),
          items: items.map((i) => DropdownMenuItem(
            value: i,
            child: Text(i, style: const TextStyle(fontSize: 13, color: _ink)),
          )).toList(),
          onChanged: onChanged,
          decoration: _inputDeco,
        ),
      ],
    );
  }

  Widget _uploadZone(String hint) => GestureDetector(
    onTap: () {},
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 24),
      decoration: BoxDecoration(
        border: Border.all(color: _border),
        color: _cream,
      ),
      child: Column(
        children: [
          const Icon(Icons.upload_file_outlined, color: _muted, size: 28),
          const SizedBox(height: 8),
          const Text('Appuyer pour uploader',
              style: TextStyle(fontSize: 13, color: _muted)),
          const SizedBox(height: 4),
          Text(hint, style: const TextStyle(fontSize: 11, color: _muted)),
        ],
      ),
    ),
  );

  // ─────────────────────────────────────────────
  // CONVOCATIONS
  // ─────────────────────────────────────────────
  Widget _buildConvocationsSection() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      decoration: BoxDecoration(
          color: _white, border: Border.all(color: _border)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionHead(Icons.calendar_today, 'Mes convocations', color: _teal),
          ..._convocations.map((c) => _buildConvocationCard(c)),
        ],
      ),
    );
  }

  Widget _buildConvocationCard(Map<String, dynamic> conv) {
    final String statut = conv['statut'] ?? 'en_attente';
    final bool isUrl    = (conv['lieu_rdv'] ?? '').toString().startsWith('http');

    String statusLabel;
    if (statut == 'confirmee') {
      statusLabel = '✓ Confirmée';
    } else if (statut == 'annulee') statusLabel = '✗ Annulée';
    else                          statusLabel = '⏳ En attente';

    return Container(
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 14),
      decoration: BoxDecoration(border: Border.all(color: _teal, width: 1.5)),
      child: Column(
        children: [
          // Bande teal
          Container(
            color: _teal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.calendar_today, color: _white, size: 12),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    (conv['type_entretien'] ?? '').toString().toUpperCase(),
                    style: const TextStyle(fontSize: 10,
                        fontWeight: FontWeight.w800, color: _white),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: Colors.white20,
                      borderRadius: BorderRadius.circular(20)),
                  child: Text(statusLabel,
                      style: const TextStyle(fontSize: 9, color: _white)),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Date
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.only(bottom: 10),
                  decoration: const BoxDecoration(
                      border: Border(bottom: BorderSide(color: _border))),
                  child: Column(children: [
                    Text(conv['date_rdv'] ?? '',
                        style: const TextStyle(fontSize: 22,
                            fontWeight: FontWeight.w800, color: _ink)),
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      const Icon(Icons.access_time, size: 14, color: _teal),
                      const SizedBox(width: 4),
                      Text(conv['heure_rdv'] ?? '',
                          style: const TextStyle(fontSize: 16,
                              fontWeight: FontWeight.w700, color: _teal)),
                    ]),
                  ]),
                ),
                const SizedBox(height: 10),
                Text(conv['poste'] ?? '',
                    style: const TextStyle(fontSize: 14,
                        fontWeight: FontWeight.w800, color: _ink)),
                const SizedBox(height: 4),
                Row(children: [
                  const Icon(Icons.business, size: 12, color: _muted),
                  const SizedBox(width: 5),
                  Text(conv['organisation'] ?? '',
                      style: const TextStyle(fontSize: 12, color: _muted)),
                ]),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: _cream,
                      border: Border.all(color: _border),
                      borderRadius: BorderRadius.circular(4)),
                  child: Row(children: [
                    const Icon(Icons.location_on, size: 14, color: _teal),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        isUrl ? 'Lien de réunion' : (conv['lieu_rdv'] ?? ''),
                        style: TextStyle(fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: isUrl ? _teal : _ink),
                      ),
                    ),
                  ]),
                ),
                if ((conv['message'] ?? '').isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(color: _cream,
                        border: Border(left: BorderSide(color: _teal, width: 3))),
                    child: Text('"${conv['message']}"',
                        style: const TextStyle(fontSize: 11, color: _muted,
                            fontStyle: FontStyle.italic)),
                  ),
                ],
                const SizedBox(height: 10),
                const Divider(color: _border, height: 1),
                const SizedBox(height: 10),
                // Actions
                if (isUrl)
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.videocam, size: 14, color: _white),
                      label: const Text("Rejoindre l'entretien",
                          style: TextStyle(fontSize: 11,
                              fontWeight: FontWeight.w800, color: _white)),
                      style: ElevatedButton.styleFrom(backgroundColor: _red,
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero), elevation: 0),
                    ),
                  )
                else if (statut == 'en_attente')
                  Row(children: [
                    Expanded(child: ElevatedButton(
                      onPressed: () => _repondreConvocation(conv['id'], 'confirmee'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green,
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero), elevation: 0),
                      child: const Text('✓ Accepter',
                          style: TextStyle(fontSize: 11,
                              fontWeight: FontWeight.w800, color: _white)),
                    )),
                    const SizedBox(width: 8),
                    Expanded(child: ElevatedButton(
                      onPressed: () => _repondreConvocation(conv['id'], 'annulee'),
                      style: ElevatedButton.styleFrom(backgroundColor: _red,
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero), elevation: 0),
                      child: const Text('✗ Refuser',
                          style: TextStyle(fontSize: 11,
                              fontWeight: FontWeight.w800, color: _white)),
                    )),
                  ])
                else
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: statut == 'confirmee'
                          ? const Color(0xFFD4EDDA)
                          : const Color(0xFFF8D7DA),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      statut == 'confirmee'
                          ? '✓ Convocation confirmée'
                          : '✗ Convocation annulée',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 12,
                          color: statut == 'confirmee'
                              ? const Color(0xFF155724)
                              : const Color(0xFF721C24)),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────
  // OFFRES RECOMMANDÉES
  // ─────────────────────────────────────────────
  Widget _buildOffresSection() {
    final bool profilComplet = _progression >= 100;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      decoration: BoxDecoration(
          color: _white, border: Border.all(color: _border)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
            decoration: const BoxDecoration(
                border: Border(bottom: BorderSide(color: _border))),
            child: Row(
              children: [
                const Text('Offres recommandées',
                    style: TextStyle(fontSize: 16,
                        fontWeight: FontWeight.w800, color: _ink)),
                const Spacer(),
                GestureDetector(
                  onTap: () {},
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(border: Border.all(color: _ink)),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('Toutes', style: TextStyle(fontSize: 10,
                            fontWeight: FontWeight.w800, color: _ink)),
                        SizedBox(width: 4),
                        Icon(Icons.arrow_forward, size: 12, color: _ink),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (!profilComplet)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(
                child: Text(
                    'Complétez votre profil pour recevoir des recommandations.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: _muted,
                        fontStyle: FontStyle.italic)),
              ),
            )
          else if (_offres.isEmpty)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: Text('Aucune recommandation disponible.',
                  style: TextStyle(fontSize: 13, color: _muted))),
            )
          else
            ..._offres.map((o) => _buildOffreCard(o)),
        ],
      ),
    );
  }

  Widget _buildOffreCard(Map<String, dynamic> offre) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: _border))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: Text(offre['titre'] ?? '',
                  style: const TextStyle(fontSize: 14,
                      fontWeight: FontWeight.w800, color: _ink)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              color: _ink,
              child: Text(offre['type_contrat'] ?? '',
                  style: const TextStyle(fontSize: 9,
                      fontWeight: FontWeight.w800, color: _white)),
            ),
          ]),
          const SizedBox(height: 6),
          Row(children: [
            const Icon(Icons.business, size: 12, color: _muted),
            const SizedBox(width: 4),
            Text(offre['entreprise'] ?? '',
                style: const TextStyle(fontSize: 12, color: _muted)),
            const SizedBox(width: 12),
            const Icon(Icons.location_on, size: 12, color: _muted),
            const SizedBox(width: 4),
            Text(offre['ville'] ?? offre['localisation'] ?? '',
                style: const TextStyle(fontSize: 12, color: _muted)),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Text('${offre['score'] ?? 0}%',
                style: const TextStyle(fontSize: 18,
                    fontWeight: FontWeight.w800, color: _teal)),
            const SizedBox(width: 6),
            const Text('compatibilité',
                style: TextStyle(fontSize: 11, color: _muted)),
            const Spacer(),
            const Icon(Icons.calendar_today, size: 11, color: _muted),
            const SizedBox(width: 4),
            Text(offre['date_limite'] ?? '',
                style: const TextStyle(fontSize: 11,
                    color: Color(0xFF862323), fontWeight: FontWeight.w600)),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: GestureDetector(
                onTap: () => _showOffreDetails(offre),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 9),
                  decoration: BoxDecoration(border: Border.all(color: _ink)),
                  child: const Center(child: Text('DÉTAILS',
                      style: TextStyle(fontSize: 10,
                          fontWeight: FontWeight.w800, color: _ink))),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: GestureDetector(
                onTap: () {},
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 9),
                  color: _red,
                  child: const Center(child: Text('POSTULER',
                      style: TextStyle(fontSize: 10,
                          fontWeight: FontWeight.w800, color: _white))),
                ),
              ),
            ),
          ]),
        ],
      ),
    );
  }

  void _showOffreDetails(Map<String, dynamic> offre) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      builder: (_) => DraggableScrollableSheet(
        expand: false, initialChildSize: 0.75,
        builder: (_, ctrl) => Column(children: [
          Container(
            padding: const EdgeInsets.all(16),
            color: _ink,
            child: Row(children: [
              Expanded(child: Text(offre['titre'] ?? '',
                  style: const TextStyle(fontSize: 15,
                      fontWeight: FontWeight.w800, color: _white))),
              GestureDetector(onTap: () => Navigator.pop(context),
                  child: const Icon(Icons.close, color: _white)),
            ]),
          ),
          Expanded(child: ListView(
            controller: ctrl, padding: const EdgeInsets.all(16),
            children: [
              _modalRow('Entreprise', offre['entreprise'] ?? ''),
              _modalRow('Lieu', offre['ville'] ?? offre['localisation'] ?? ''),
              _modalRow('Contrat', offre['type_contrat'] ?? ''),
              _modalRow('Score', '${offre['score'] ?? 0}%'),
              _modalRow('Date limite', offre['date_limite'] ?? ''),
              _modalRow('Description', offre['description'] ?? ''),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.send, size: 14, color: _white),
                label: const Text('POSTULER', style: TextStyle(fontSize: 11,
                    fontWeight: FontWeight.w800, color: _white)),
                style: ElevatedButton.styleFrom(backgroundColor: _red,
                    shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero), elevation: 0),
              ),
            ],
          )),
        ]),
      ),
    );
  }

  Widget _modalRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label.toUpperCase(), style: const TextStyle(fontSize: 9,
            fontWeight: FontWeight.w700, color: _muted, letterSpacing: 1)),
        const SizedBox(height: 3),
        Text(value, style: const TextStyle(fontSize: 13, color: _ink, height: 1.5)),
        const Divider(color: _border, height: 16),
      ]),
    );
  }

  // ─────────────────────────────────────────────
  // HELPER SECTION HEAD
  // ─────────────────────────────────────────────
  Widget _sectionHead(IconData icon, String title, {Color color = _ink}) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: _border))),
      child: Row(children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Text(title, style: const TextStyle(fontSize: 16,
            fontWeight: FontWeight.w800, color: _ink)),
      ]),
    );
  }
}