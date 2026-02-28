type Dict = Record<string, Record<string, string>>;

const dictionaries: Dict = {
  en: {
    "dashboard.activeRadar": "Active Radar",
    "dashboard.swipeRight": "Swipe right to let AI apply for you.",
    "dashboard.resetFilters": "Reset filters and rescan",
    "dashboard.loadMore": "Load more matches",
    "dashboard.loadingMore": "Loading more",
    "dashboard.noMatches": "You've reviewed all matches for your current filters. Try broadening your location, lowering salary floors, or clearing keywords to discover more leads.",
    "dashboard.reviewSwipes": "Review Swipes",
    "dashboard.filterPlaceholder": "Filter location...",
    "dashboard.matchAlert": "Match Alert! High-fit role detected.",
    "dashboard.sweepComplete": "Radar Sweep Complete",

    "holds.responseRequired": "RESPONSE REQUIRED",

    "app.loading": "Loading...",
    "app.error": "Something went wrong",
    "app.retry": "Try Again",
    "app.save": "Save",
    "app.cancel": "Cancel",
    "app.delete": "Delete",
    "app.confirm": "Confirm",
    "nav.dashboard": "Dashboard",
    "nav.jobs": "Jobs",
    "nav.applications": "Applications",
    "nav.settings": "Settings",
    "nav.billing": "Billing",
    "nav.team": "Team",
    "status.applied": "Applied",
    "status.needsInput": "Needs Input",
    "status.failed": "Failed",
    "status.queued": "Queued",
    "status.processing": "Processing",

    "cookies.description": "We use cookies for analytics to improve your experience. By clicking \"Accept analytics\", you consent to analytics cookies. \"Reject all\" uses only essential cookies. Press Escape to reject. See our",
    "cookies.privacyPolicy": "Privacy Policy",
    "cookies.forDetails": "for details.",
    "cookies.rejectAll": "Reject all",
    "cookies.managePreferences": "Manage preferences",
    "cookies.acceptAnalytics": "Accept analytics",
    "cookies.title": "Cookie consent",
  },
  fr: {
    "dashboard.activeRadar": "Radar actif",
    "dashboard.swipeRight": "Faites glisser à droite pour laisser l'IA postuler pour vous.",
    "dashboard.resetFilters": "Réinitialiser les filtres et relancer",
    "dashboard.loadMore": "Charger plus d'offres",
    "dashboard.loadingMore": "Chargement...",
    "dashboard.noMatches": "Vous avez examiné toutes les offres pour ces filtres. Élargissez la localisation ou abaissez le salaire minimum pour en trouver plus.",
    "dashboard.reviewSwipes": "Revoir les swipes",
    "dashboard.filterPlaceholder": "Filtrer par localisation...",
    "dashboard.matchAlert": "Alerte match ! Offre très adaptée détectée.",
    "dashboard.sweepComplete": "Balayage terminé",

    "holds.responseRequired": "RÉPONSE REQUISE",

    "app.loading": "Chargement...",
    "app.error": "Une erreur est survenue",
    "app.retry": "Réessayer",
    "app.save": "Enregistrer",
    "app.cancel": "Annuler",
    "app.delete": "Supprimer",
    "app.confirm": "Confirmer",
    "nav.dashboard": "Tableau de bord",
    "nav.jobs": "Emplois",
    "nav.applications": "Candidatures",
    "nav.settings": "Paramètres",
    "nav.billing": "Facturation",
    "nav.team": "Équipe",
    "status.applied": "Candidaté",
    "status.needsInput": "Saisie requise",
    "status.failed": "Échoué",
    "status.queued": "En file d'attente",
    "status.processing": "En cours",

    "cookies.description": "Nous utilisons des cookies pour l'analyse afin d'améliorer votre expérience. En cliquant sur \"Accepter l'analyse\", vous consentez aux cookies d'analyse. \"Tout refuser\" n'utilise que les cookies essentiels. Appuyez sur Échap pour refuser. Consultez notre",
    "cookies.privacyPolicy": "Politique de confidentialité",
    "cookies.forDetails": "pour plus de détails.",
    "cookies.rejectAll": "Tout refuser",
    "cookies.managePreferences": "Gérer les préférences",
    "cookies.acceptAnalytics": "Accepter l'analyse",
    "cookies.title": "Consentement aux cookies",
  },
};

const rtlLocales = ["ar", "he", "fa", "ur"];

export function getLocale(): string {
  if (typeof navigator !== "undefined") {
    return navigator.language || navigator.languages?.[0] || "en";
  }
  return "en";
}

export function isRTL(locale?: string): boolean {
  const lang = (locale || getLocale()).split("-")[0].toLowerCase();
  return rtlLocales.includes(lang);
}

export function t(key: string, locale?: string): string {
  const lang = (locale || getLocale()).split("-")[0].toLowerCase();
  const dict = dictionaries[lang] || dictionaries.en;
  return dict[key] || dictionaries.en[key] || key;
}
