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
