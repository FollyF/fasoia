// lib/screens/dashboard_candidat_test.dart
import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class DashboardCandidatTest extends StatefulWidget {
  const DashboardCandidatTest({super.key});

  @override
  State<DashboardCandidatTest> createState() => _DashboardCandidatTestState();
}

class _DashboardCandidatTestState extends State<DashboardCandidatTest> {
  bool _isLoading = true;
  String? _error;
  
  Map<String, dynamic> _profil = {};
  List<dynamic> _offres = [];
  List<dynamic> _convocations = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final profil = await ApiService.getCandidatProfil();
      final offres = await ApiService.getCandidatOffresRecommandees();
      final convocations = await ApiService.getCandidatConvocations();

      setState(() {
        _profil = profil;
        _offres = offres;
        _convocations = convocations;
        _isLoading = false;
      });

      print('=== PROFIL ===');
      print(_profil);
      print('=== OFFRES ===');
      print(_offres);
      print('=== CONVOCATIONS ===');
      print(_convocations);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard Candidat (TEST)'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ApiService.logout();
              if (mounted) {
                Navigator.pushReplacementNamed(context, '/login');
              }
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Erreur: $_error'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadData,
                        child: const Text('Réessayer'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // JSON brut du profil
                      _sectionTitle('PROFIL COMPLET (JSON)'),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        color: Colors.grey[200],
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Text(
                            _profil.toString(),
                            style: const TextStyle(fontSize: 10, fontFamily: 'monospace'),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Statistiques
                      _sectionTitle('STATISTIQUES'),
                      Card(
                        child: ListTile(
                          title: Text('Progression: ${_profil['progression'] ?? 0}%'),
                        ),
                      ),
                      Card(
                        child: ListTile(
                          title: Text('Champs remplis: ${_profil['champs_remplis'] ?? 0}/${_profil['total_champs'] ?? 22}'),
                        ),
                      ),
                      Card(
                        child: ListTile(
                          title: Text('Convocations obtenues: ${_profil['convocations_obtenues'] ?? 0}'),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Particulier
                      if (_profil['particulier'] != null) ...[
                        _sectionTitle('PARTICULIER'),
                        Card(
                          child: Column(
                            children: [
                              _infoTile('Nom', _profil['particulier']['nom']),
                              _infoTile('Prénom', _profil['particulier']['prenom']),
                              _infoTile('Email', _profil['particulier']['email']),
                              _infoTile('Téléphone', _profil['particulier']['telephone']),
                              _infoTile('Ville', _profil['particulier']['ville']),
                              _infoTile('Pays', _profil['particulier']['pays']),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 20),

                      // Candidat
                      if (_profil['candidat'] != null) ...[
                        _sectionTitle('CANDIDAT'),
                        Card(
                          child: Column(
                            children: [
                              _infoTile('Niveau étude', _profil['candidat']['niveauEtude']),
                              _infoTile('Années expérience', _profil['candidat']['anneesExperiences']?.toString()),
                              _infoTile('Compétences', _profil['candidat']['competences']),
                              _infoTile('Langues', _profil['candidat']['niveauLangues']),
                              _infoTile('Disponibilité', _profil['candidat']['disponibilite']),
                              _infoTile('Secteur recherché', _profil['candidat']['secteur_recherche']),
                              _infoTile('Type contrat', _profil['candidat']['type_contrat_recherche']),
                              _infoTile('Localisation', _profil['candidat']['localisation_recherche']),
                              _infoTile('Salaire souhaité', _profil['candidat']['salaire_souhaite']?.toString()),
                              _infoTile('Mobilité', _profil['candidat']['mobilite'] == true ? 'Oui' : 'Non'),
                              _infoTile('Candidatures', _profil['candidat']['nb_candidatures_envoyees']?.toString()),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 20),

                      // Offres
                      _sectionTitle('OFFRES (${_offres.length})'),
                      if (_offres.isEmpty)
                      Card(child: const ListTile(title: Text('Aucune offre'))),
                    ],
                  ),
                ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(
        title,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.red),
      ),
    );
  }

  Widget _infoTile(String label, dynamic value) {
    final displayValue = value != null && value.toString().isNotEmpty 
        ? value.toString() 
        : 'Non renseigné';
    return ListTile(
      dense: true,
      title: Text(label),
      trailing: Text(displayValue),
    );
  }
}