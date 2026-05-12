import 'package:flutter/material.dart';
import '../utils/constants.dart';

// ═══════════════════════════════════════════════════════════════════════
// WIDGET LOGO FASOIA — fichier indépendant, réutilisable partout
//
// UTILISATION :
//   const FasoiaLogo()                              → blanc / rouge (défaut)
//   const FasoiaLogo(mainColor: AppColors.ink)      → ink / rouge
//   const FasoiaLogo(accentColor: Colors.orange)    → blanc / orange
//   const FasoiaLogo(mainColor: AppColors.ink, accentColor: AppColors.teal)
// ═══════════════════════════════════════════════════════════════════════
class FasoiaLogo extends StatelessWidget {
  final double    fontSize;
  final bool      showSubtitle;
  final String    subtitle;
  final TextAlign textAlign;

  /// Couleur de "FASO" — défaut : blanc (pour fond sombre)
  final Color? mainColor;

  /// Couleur de "IA" — défaut : AppColors.red
  final Color? accentColor;

  /// Couleur du sous-titre — défaut : déduite de mainColor avec opacité
  final Color? subtitleColor;

  const FasoiaLogo({
    super.key,
    this.fontSize      = 22,
    this.showSubtitle  = true,
    this.subtitle      = 'Espace Carrière',
    this.textAlign     = TextAlign.center,
    this.mainColor,
    this.accentColor,
    this.subtitleColor,
  });

  @override
  Widget build(BuildContext context) {
    final resolvedMain     = mainColor     ?? Colors.white;
    final resolvedAccent   = accentColor   ?? AppColors.red;
    final resolvedSubtitle = subtitleColor ?? resolvedMain.withOpacity(0.35);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: textAlign == TextAlign.center
          ? CrossAxisAlignment.center
          : CrossAxisAlignment.start,
      children: [
        RichText(
          textAlign: textAlign,
          text: TextSpan(
            children: [
              TextSpan(
                text: 'FASO',
                style: TextStyle(
                  color:       resolvedMain,
                  fontSize:    fontSize,
                  fontWeight:  FontWeight.w900,
                  letterSpacing: 3,
                  height:      1,
                ),
              ),
              TextSpan(
                text: 'IA',
                style: TextStyle(
                  color:       resolvedAccent,
                  fontSize:    fontSize,
                  fontWeight:  FontWeight.w900,
                  letterSpacing: 3,
                  height:      1,
                ),
              ),
            ],
          ),
        ),
        if (showSubtitle) ...[
          const SizedBox(height: 2),
          Text(
            subtitle.toUpperCase(),
            textAlign: textAlign,
            style: TextStyle(
              color:         resolvedSubtitle,
              fontSize:      fontSize * 0.35,
              fontWeight:    FontWeight.w600,
              letterSpacing: 2.5,
            ),
          ),
        ],
      ],
    );
  }
}