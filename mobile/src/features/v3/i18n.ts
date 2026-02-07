/**
 * Internationalization (i18n) — multi-language support for Sorce mobile.
 *
 * Supports EN, DE, FR, ES with lazy-loaded translations.
 * EU job board integration: StepStone (DE), Indeed DE/FR.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";

export type Locale = "en" | "de" | "fr" | "es";

const STORAGE_KEY = "sorce_locale";

const translations: Record<Locale, Record<string, string>> = {
  en: {
    "nav.dashboard": "Dashboard",
    "nav.jobs": "Jobs",
    "nav.applications": "Applications",
    "nav.profile": "Profile",
    "nav.marketplace": "Marketplace",
    "dashboard.greeting_morning": "Good morning",
    "dashboard.greeting_afternoon": "Good afternoon",
    "dashboard.greeting_evening": "Good evening",
    "dashboard.in_progress": "In Progress",
    "dashboard.need_input": "Need Input",
    "dashboard.today": "Today",
    "dashboard.this_week": "This Week",
    "dashboard.all_time": "All Time",
    "dashboard.recent_activity": "Recent Activity",
    "dashboard.quick_actions": "Quick Actions",
    "apps.status_queued": "Queued",
    "apps.status_processing": "Processing",
    "apps.status_hold": "Needs Input",
    "apps.status_applied": "Applied",
    "apps.status_failed": "Failed",
    "apps.hold_alert": "{count} application(s) need your input",
    "jobs.browse": "Browse Jobs",
    "jobs.swipe_right": "Apply",
    "jobs.swipe_left": "Skip",
    "jobs.no_more": "No more jobs — check back later!",
    "profile.upload_resume": "Upload Resume",
    "profile.smart_prefill": "Smart Pre-fill enabled",
    "billing.upgrade": "Upgrade Plan",
    "billing.annual_save": "Save 20% with annual billing",
    "marketplace.browse": "Browse Blueprints",
    "marketplace.install": "Install",
    "marketplace.installed": "Installed",
    "widget.in_progress": "{count} in progress",
    "widget.need_input": "{count} need your input",
  },
  de: {
    "nav.dashboard": "Übersicht",
    "nav.jobs": "Stellenangebote",
    "nav.applications": "Bewerbungen",
    "nav.profile": "Profil",
    "nav.marketplace": "Marktplatz",
    "dashboard.greeting_morning": "Guten Morgen",
    "dashboard.greeting_afternoon": "Guten Tag",
    "dashboard.greeting_evening": "Guten Abend",
    "dashboard.in_progress": "In Bearbeitung",
    "dashboard.need_input": "Eingabe nötig",
    "dashboard.today": "Heute",
    "dashboard.this_week": "Diese Woche",
    "dashboard.all_time": "Gesamt",
    "dashboard.recent_activity": "Letzte Aktivitäten",
    "dashboard.quick_actions": "Schnellaktionen",
    "apps.status_queued": "Warteschlange",
    "apps.status_processing": "Wird bearbeitet",
    "apps.status_hold": "Eingabe nötig",
    "apps.status_applied": "Beworben",
    "apps.status_failed": "Fehlgeschlagen",
    "apps.hold_alert": "{count} Bewerbung(en) brauchen Ihre Eingabe",
    "jobs.browse": "Jobs durchsuchen",
    "jobs.swipe_right": "Bewerben",
    "jobs.swipe_left": "Überspringen",
    "jobs.no_more": "Keine weiteren Jobs — schauen Sie später wieder vorbei!",
    "profile.upload_resume": "Lebenslauf hochladen",
    "profile.smart_prefill": "Intelligente Vorausfüllung aktiviert",
    "billing.upgrade": "Plan upgraden",
    "billing.annual_save": "20% sparen mit Jahresabrechnung",
    "marketplace.browse": "Blueprints durchsuchen",
    "marketplace.install": "Installieren",
    "marketplace.installed": "Installiert",
    "widget.in_progress": "{count} in Bearbeitung",
    "widget.need_input": "{count} brauchen Eingabe",
  },
  fr: {
    "nav.dashboard": "Tableau de bord",
    "nav.jobs": "Emplois",
    "nav.applications": "Candidatures",
    "nav.profile": "Profil",
    "nav.marketplace": "Marketplace",
    "dashboard.greeting_morning": "Bonjour",
    "dashboard.greeting_afternoon": "Bon après-midi",
    "dashboard.greeting_evening": "Bonsoir",
    "dashboard.in_progress": "En cours",
    "dashboard.need_input": "Action requise",
    "dashboard.today": "Aujourd'hui",
    "dashboard.this_week": "Cette semaine",
    "dashboard.all_time": "Total",
    "dashboard.recent_activity": "Activité récente",
    "dashboard.quick_actions": "Actions rapides",
    "apps.status_queued": "En attente",
    "apps.status_processing": "En traitement",
    "apps.status_hold": "Action requise",
    "apps.status_applied": "Candidature envoyée",
    "apps.status_failed": "Échoué",
    "apps.hold_alert": "{count} candidature(s) nécessitent votre attention",
    "jobs.browse": "Parcourir les emplois",
    "jobs.swipe_right": "Postuler",
    "jobs.swipe_left": "Passer",
    "jobs.no_more": "Plus d'offres — revenez plus tard !",
    "profile.upload_resume": "Télécharger le CV",
    "profile.smart_prefill": "Pré-remplissage intelligent activé",
    "billing.upgrade": "Mettre à niveau",
    "billing.annual_save": "Économisez 20% avec la facturation annuelle",
    "marketplace.browse": "Parcourir les blueprints",
    "marketplace.install": "Installer",
    "marketplace.installed": "Installé",
    "widget.in_progress": "{count} en cours",
    "widget.need_input": "{count} nécessitent votre attention",
  },
  es: {
    "nav.dashboard": "Panel",
    "nav.jobs": "Empleos",
    "nav.applications": "Solicitudes",
    "nav.profile": "Perfil",
    "nav.marketplace": "Marketplace",
    "dashboard.greeting_morning": "Buenos días",
    "dashboard.greeting_afternoon": "Buenas tardes",
    "dashboard.greeting_evening": "Buenas noches",
    "dashboard.in_progress": "En progreso",
    "dashboard.need_input": "Requiere acción",
    "dashboard.today": "Hoy",
    "dashboard.this_week": "Esta semana",
    "dashboard.all_time": "Total",
    "dashboard.recent_activity": "Actividad reciente",
    "dashboard.quick_actions": "Acciones rápidas",
    "apps.status_queued": "En cola",
    "apps.status_processing": "Procesando",
    "apps.status_hold": "Requiere acción",
    "apps.status_applied": "Aplicado",
    "apps.status_failed": "Fallido",
    "apps.hold_alert": "{count} solicitud(es) necesitan tu atención",
    "jobs.browse": "Buscar empleos",
    "jobs.swipe_right": "Aplicar",
    "jobs.swipe_left": "Saltar",
    "jobs.no_more": "No hay más empleos — ¡vuelve más tarde!",
    "profile.upload_resume": "Subir currículum",
    "profile.smart_prefill": "Auto-completado inteligente activado",
    "billing.upgrade": "Mejorar plan",
    "billing.annual_save": "Ahorra 20% con facturación anual",
    "marketplace.browse": "Explorar blueprints",
    "marketplace.install": "Instalar",
    "marketplace.installed": "Instalado",
    "widget.in_progress": "{count} en progreso",
    "widget.need_input": "{count} necesitan tu atención",
  },
};

let currentLocale: Locale = "en";

export async function initLocale(): Promise<Locale> {
  const saved = await AsyncStorage.getItem(STORAGE_KEY);
  if (saved && saved in translations) {
    currentLocale = saved as Locale;
  }
  return currentLocale;
}

export async function setLocale(locale: Locale): Promise<void> {
  currentLocale = locale;
  await AsyncStorage.setItem(STORAGE_KEY, locale);
}

export function getLocale(): Locale {
  return currentLocale;
}

export function t(key: string, params?: Record<string, string | number>): string {
  const dict = translations[currentLocale] || translations.en;
  let result = dict[key] || translations.en[key] || key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      result = result.replace(`{${k}}`, String(v));
    }
  }
  return result;
}

export const SUPPORTED_LOCALES: Array<{ code: Locale; label: string; flag: string }> = [
  { code: "en", label: "English", flag: "🇺🇸" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "es", label: "Español", flag: "🇪🇸" },
];

/** EU job board URLs by locale */
export const EU_JOB_BOARDS: Record<string, Array<{ name: string; url: string }>> = {
  de: [
    { name: "StepStone DE", url: "https://www.stepstone.de" },
    { name: "Indeed DE", url: "https://de.indeed.com" },
    { name: "XING Jobs", url: "https://www.xing.com/jobs" },
  ],
  fr: [
    { name: "Indeed FR", url: "https://fr.indeed.com" },
    { name: "Pole Emploi", url: "https://www.pole-emploi.fr" },
    { name: "Apec", url: "https://www.apec.fr" },
  ],
  es: [
    { name: "InfoJobs", url: "https://www.infojobs.net" },
    { name: "Indeed ES", url: "https://es.indeed.com" },
  ],
};
