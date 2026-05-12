import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../utils/constants.dart';
import '../widgets/fasoia_logo.dart';

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

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: AppColors.cream,
        body: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            // ── AppBar avec logo FASOIA ──────────────────────────────
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

            SliverToBoxAdapter(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Bandeau de bienvenue ─────────────────────────
                  _buildHeader(),

                  // ── Cartes de rôle ───────────────────────────────
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Label section
                        const Text(
                          'CHOISISSEZ VOTRE RÔLE',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: AppColors.muted,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 14),

                        _buildRoleCard(
                          context: context,
                          title: 'Je cherche un emploi',
                          description:
                              'Accédez aux offres d\'emploi, postulez facilement et suivez vos candidatures.',
                          icon: Icons.search_rounded,
                          accentIcon: Icons.school_outlined,
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
                        const SizedBox(height: 14),

                        _buildRoleCard(
                          context: context,
                          title: 'Je recrute des talents',
                          description:
                              'Publiez vos offres, gérez les candidatures et trouvez les profils qui vous correspondent.',
                          icon: Icons.business_center_rounded,
                          accentIcon: Icons.business_outlined,
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
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Bandeau de bienvenue ──────────────────────────────────────────────
  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      color: AppColors.ink,
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 28),
      child: Stack(children: [
        // Cercles déco
        Positioned(right: -20, top: -20, child: Container(
          width: 120, height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.red.withOpacity(0.08),
          ),
        )),
        Positioned(right: 10, bottom: 0, child: Container(
          width: 55, height: 55,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.red.withOpacity(0.12),
          ),
        )),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Avatar + prénom
            Row(children: [
              Container(
                width: 46, height: 46,
                decoration: BoxDecoration(
                  color: AppColors.red,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    prenom.isNotEmpty
                        ? prenom.substring(0, 1).toUpperCase()
                        : 'U',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Bienvenue,',
                    style: TextStyle(color: Colors.white54, fontSize: 12)),
                  RichText(
                    text: TextSpan(
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                        height: 1.2,
                      ),
                      children: [
                        TextSpan(text: prenom),
                        if (nom.isNotEmpty)
                          TextSpan(
                            text: ' $nom',
                            style: const TextStyle(color: AppColors.red),
                          ),
                      ],
                    ),
                  ),
                ],
              )),
            ]),
            const SizedBox(height: 14),
            const Text(
              'Choisissez comment vous souhaitez utiliser FASOIA',
              style: TextStyle(
                fontSize: 12,
                color: Colors.white54,
                height: 1.5,
              ),
            ),
          ],
        ),
      ]),
    );
  }

  // ── Carte de rôle ─────────────────────────────────────────────────────
  Widget _buildRoleCard({
    required BuildContext context,
    required String title,
    required String description,
    required IconData icon,
    required IconData accentIcon,
    required bool isRecommended,
    required List<String> features,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isRecommended ? AppColors.red : AppColors.border,
            width: isRecommended ? 1.5 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header de la carte
            Container(
              padding: const EdgeInsets.fromLTRB(18, 16, 18, 14),
              decoration: BoxDecoration(
                color: isRecommended
                    ? AppColors.red.withOpacity(0.06)
                    : AppColors.cream,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: isRecommended
                          ? AppColors.red.withOpacity(0.12)
                          : AppColors.border.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(accentIcon,
                      color: isRecommended ? AppColors.red : AppColors.muted,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: AppColors.ink,
                          height: 1.2,
                        )),
                      const SizedBox(height: 3),
                      Text(description,
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.muted,
                          height: 1.5,
                        )),
                    ],
                  )),
                  if (isRecommended) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.ink,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.star_rounded, color: Colors.white, size: 9),
                          SizedBox(width: 3),
                          Text('RECOMMANDÉ',
                            style: TextStyle(
                              fontSize: 8,
                              fontWeight: FontWeight.w800,
                              color: Colors.white,
                              letterSpacing: 0.6,
                            )),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // Liste des fonctionnalités
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 4),
              child: Column(
                children: features.map((f) => _buildFeatureItem(f)).toList(),
              ),
            ),

            // Bouton commencer
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 18),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onTap,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isRecommended ? AppColors.red : AppColors.ink,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    elevation: 0,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(icon, size: 16, color: Colors.white),
                      const SizedBox(width: 8),
                      const Text('COMMENCER',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1,
                        )),
                      const SizedBox(width: 8),
                      const Icon(Icons.arrow_forward_rounded, size: 14, color: Colors.white),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(children: [
        Container(
          width: 20, height: 20,
          decoration: BoxDecoration(
            color: AppColors.teal.withOpacity(0.1),
            borderRadius: BorderRadius.circular(5),
          ),
          child: const Icon(Icons.check_rounded, color: AppColors.teal, size: 13),
        ),
        const SizedBox(width: 10),
        Expanded(child: Text(label,
          style: const TextStyle(
            fontSize: 13,
            color: AppColors.ink,
            height: 1.3,
          ))),
      ]),
    );
  }

  Widget _buildSkipButton(BuildContext context) {
    return Center(
      child: GestureDetector(
        onTap: () {
          // Navigator.pushNamedAndRemoveUntil(context, '/home', (r) => false);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 11),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.access_time_rounded, size: 14, color: AppColors.muted),
              SizedBox(width: 8),
              Text('Je choisis plus tard',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.muted,
                  letterSpacing: 0.3,
                )),
            ],
          ),
        ),
      ),
    );
  }
}