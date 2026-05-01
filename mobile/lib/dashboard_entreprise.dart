import 'package:flutter/material.dart';

class DashboardEntreprise extends StatelessWidget {
  const DashboardEntreprise({super.key});

  // Reprise de ta palette de couleurs
  static const _red = Color(0xFFD32F2F);
  static const _cream = Color(0xFFF8F4ED);
  static const _ink = Color(0xFF2C1810);
  static const _muted = Color(0xFF8B7355);
  static const _border = Color(0xFFE0D8CC);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _cream,
      appBar: _buildAppBar(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildWelcomeHeader(),
            const SizedBox(height: 24),
            _buildStatsGrid(),
            const SizedBox(height: 32),
            const Text(
              'Actions principales',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: _ink,
              ),
            ),
            const SizedBox(height: 16),
            _buildActionCard(
              title: "Publier un appel d'offres",
              subtitle: "Diffusez vos besoins aux partenaires",
              icon: Icons.add_business_outlined,
              onTap: () {},
            ),
            _buildActionCard(
              title: "Consulter les candidatures",
              subtitle: "Vous avez 0 nouvelle réponse",
              icon: Icons.people_outline,
              onTap: () {},
            ),
            _buildActionCard(
              title: "Paramètres du profil",
              subtitle: "Modifier l'IFU, logo et adresse",
              icon: Icons.settings_outlined,
              onTap: () {},
            ),
          ],
        ),
      ),
    );
  }

  // --- Éléments de l'UI ---

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
      title: const Text(
        'FASOIA Pro',
        style: TextStyle(color: _ink, fontWeight: FontWeight.w800, letterSpacing: 1.2),
      ),
      actions: [
        IconButton(
          onPressed: () {},
          icon: const Icon(Icons.notifications_none, color: _ink),
        ),
        const Padding(
          padding: EdgeInsets.only(right: 16),
          child: CircleAvatar(
            backgroundColor: _red,
            radius: 16,
            child: Icon(Icons.business, color: Colors.white, size: 18),
          ),
        ),
      ],
    );
  }

  Widget _buildWelcomeHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Bienvenue,',
          style: TextStyle(fontSize: 14, color: _muted),
        ),
        Text(
          'Espace Entreprise',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w800,
            color: _ink,
          ),
        ),
      ],
    );
  }

  Widget _buildStatsGrid() {
    return Row(
      children: [
        _buildStatItem('Mes Appels', '0', Colors.blue),
        const SizedBox(width: 16),
        _buildStatItem('Vues Profil', '12', Colors.orange),
      ],
    );
  }

  Widget _buildStatItem(String label, String value, Color accent) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: _ink)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 12, color: _muted, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard({required String title, required String subtitle, required IconData icon, required VoidCallback onTap}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _border),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: _cream, borderRadius: BorderRadius.circular(10)),
          child: Icon(icon, color: _red),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, color: _ink)),
        subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: _muted)),
        trailing: const Icon(Icons.chevron_right, color: _muted),
        onTap: onTap,
      ),
    );
  }
}