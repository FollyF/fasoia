import 'package:flutter/material.dart';

class DashboardParticulier extends StatelessWidget {
  const DashboardParticulier({
    super.key,
    this.prenom = 'Utilisateur',
    this.nom = '',
    this.aProfilCandidat = false,
  });

  final String prenom;
  final String nom;
  final bool aProfilCandidat;

  static const _red    = Color(0xFFD32F2F);
  static const _cream  = Color(0xFFF8F4ED);
  static const _ink    = Color(0xFF2C1810);
  static const _muted  = Color(0xFF8B7355);
  static const _border = Color(0xFFE0D8CC);
  static const _teal   = Color(0xFF0D7377);
  static const _white  = Color(0xFFFFFFFF);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _cream,
      appBar: _buildAppBar(),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildRoleCard(
                    context: context,
                    title: 'Je cherche un emploi',
                    description:
                        'Accédez aux offres d\'emploi, postulez facilement et suivez vos candidatures.',
                    icon: Icons.school_outlined,
                    isRecommended: !aProfilCandidat,
                    features: const [
                      'Parcourir les offres d\'emploi',
                      'Postuler en un clic',
                      'Suivre vos candidatures',
                      'Recommandations par IA',
                      'Créer et gérer vos CV',
                    ],
                    onTap: () {
                      // Navigator.pushNamed(context, '/activer_candidat');
                    },
                  ),
                  const SizedBox(height: 16),
                  _buildRoleCard(
                    context: context,
                    title: 'Je recrute des talents',
                    description:
                        'Publiez vos offres, gérez les candidatures et trouvez les profils qui vous correspondent.',
                    icon: Icons.business_outlined,
                    isRecommended: false,
                    features: const [
                      'Publier des offres d\'emploi',
                      'Gérer les candidatures',
                      'Rechercher des talents',
                      'Développer votre réseau',
                      'Analyser les candidatures',
                    ],
                    onTap: () {
                      // Navigator.pushNamed(context, '/activer_recruteur');
                    },
                  ),
                  const SizedBox(height: 24),
                  _buildSkipButton(context),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: _white,
      elevation: 0,
      centerTitle: false,
      title: RichText(
        text: const TextSpan(
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.5,
            color: _ink,
          ),
          children: [
            TextSpan(text: 'FASO'),
            TextSpan(text: 'IA', style: TextStyle(color: _red)),
          ],
        ),
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(color: _border, height: 1),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      color: _ink,
      padding: const EdgeInsets.fromLTRB(24, 28, 24, 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          RichText(
            text: TextSpan(
              style: const TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.w800,
                color: _white,
                height: 1.2,
              ),
              children: [
                const TextSpan(text: 'Bienvenue, '),
                TextSpan(
                  text: prenom,
                  style: const TextStyle(color: _red),
                ),
                if (nom.isNotEmpty) TextSpan(text: ' $nom'),
              ],
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Choisissez comment vous souhaitez utiliser FASOIA',
            style: TextStyle(fontSize: 13, color: Color(0xFF8B7355), height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _buildRoleCard({
    required BuildContext context,
    required String title,
    required String description,
    required IconData icon,
    required bool isRecommended,
    required List<String> features,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: _white,
          border: Border(
            left: BorderSide.none,
            right: BorderSide.none,
            bottom: const BorderSide(color: _border, width: 1),
            top: BorderSide(color: isRecommended ? _red : _border, width: 3),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      border: Border.all(color: _border),
                    ),
                    child: Icon(icon, color: _muted, size: 22),
                  ),
                  if (isRecommended) ...[
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      color: _ink,
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.star, color: _white, size: 10),
                          SizedBox(width: 4),
                          Text(
                            'RECOMMANDÉ',
                            style: TextStyle(
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                              color: _white,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 16),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: _ink,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 13,
                  color: _muted,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 16),
              const Divider(color: _border, height: 1, thickness: 1),
              const SizedBox(height: 12),
              ...features.map((f) => _buildFeatureItem(f)),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: onTap,
                  icon: const Text(
                    'COMMENCER',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                      color: _white,
                    ),
                  ),
                  label: const Icon(Icons.arrow_forward, size: 14, color: _white),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _ink,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    elevation: 0,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          const Icon(Icons.check_circle, color: _teal, size: 15),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontSize: 13, color: _ink, height: 1.3),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSkipButton(BuildContext context) {
    return Center(
      child: GestureDetector(
        onTap: () {
          // Navigator.pushNamedAndRemoveUntil(context, '/home', (r) => false);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          decoration: BoxDecoration(
            border: Border.all(color: _border),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.access_time, size: 14, color: _muted),
              SizedBox(width: 8),
              Text(
                'Je choisis plus tard',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: _muted,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}