/*
 * CONFIGURATION DU SITE PUBLIC
 * -----------------------------
 * Toute la présentation du site public (textes, images, ordre des sections,
 * couleurs, coordonnées) est lue depuis ce fichier. Aucun composant ne doit
 * contenir de contenu en dur dans son JSX.
 *
 * Cette configuration est la base par défaut. Elle peut être surchargée :
 *   - localement par l'utilisateur via /settings/site (stockage navigateur),
 *   - à terme par une API d'administration du site (backend non modifié ici :
 *     il suffira de remplacer `loadSiteConfig()` par un appel API).
 *
 * Schéma :
 *   branding  → identité (nom, logo, couleurs, coordonnées)
 *   nav       → liens de la navbar + bouton de prise de rendez-vous
 *   hero      → bandeau principal de l'accueil
 *   home      → ordre / visibilité / disposition des sections
 *   about, services, team, technology, steps, testimonials, info, cta, contact
 *             → contenu de chaque section (réutilisé par les pages dédiées)
 *   footer    → contenu du pied de page
 */

import { DEFAULT_THEME } from './theme.js'

export const SITE_CONFIG_STORAGE_KEY = 'dental-site-config.v1'

export const SECTION_LABELS = {
  about: 'Présentation du cabinet',
  services: 'Services',
  team: 'Équipe',
  technology: 'Technologies',
  steps: 'Parcours patient',
  testimonials: 'Témoignages',
  info: 'Informations pratiques',
  cta: 'Appel à l’action',
  contact: 'Contact',
}

/** Sections image + texte : la disposition (left/right) est configurable. */
export const MEDIA_SECTIONS = ['about', 'technology']

export const defaultSiteConfig = {
  /* ---------------- Identité ---------------- */
  branding: {
    cabinetName: 'Cabinet Dentaire ELQODS',
    shortName: 'ELQODS',
    tagline: 'Votre sourire, notre priorité',
    logo: null, // URL d'un logo (null → monogramme généré)
    favicon: null,
    theme: { ...DEFAULT_THEME },
    phone: '+33 1 23 45 67 89',
    email: 'contact@cabinet-elqods.fr',
    address: '12 avenue de la Santé, 75013 Paris',
    socials: [
      { label: 'Facebook', url: 'https://facebook.com' },
      { label: 'Instagram', url: 'https://instagram.com' },
      { label: 'LinkedIn', url: 'https://linkedin.com' },
    ],
  },

  /* ---------------- Navigation ---------------- */
  nav: {
    links: [
      { label: 'Accueil', to: '/' },
      { label: 'Services', to: '/services' },
      { label: 'Équipe', to: '/team' },
      { label: 'Contact', to: '/contact' },
    ],
    cta: { label: 'Prendre rendez-vous', to: '/contact' },
    showLogin: true,
    loginLabel: 'Connexion',
    dashboardLabel: 'Dashboard',
    logoutLabel: 'Déconnexion',
  },

  /* ---------------- Hero ---------------- */
  hero: {
    eyebrow: 'Cabinet dentaire • Accueil sur rendez-vous',
    title: 'Des soins dentaires modernes, doux et humains',
    subtitle: 'Cabinet Dentaire ELQODS',
    description:
      'Une équipe expérimentée, des technologies de pointe et un accompagnement clair à chaque étape pour préserver la santé de vos dents et la confiance de votre sourire.',
    image: '/images/hero.jpg',
    imageAlt: 'Le chirurgien-dentiste examine les dents d’une patiente au fauteuil',
    primaryButton: { label: 'Prendre rendez-vous', to: '/contact' },
    secondaryButton: { label: 'Découvrir nos services', to: '/services' },
    points: ['Prise en charge rapide', 'Stérilisation contrôlée', 'Devis transparent'],
    badge: { title: 'Ouvert aujourd’hui', text: '8h30 – 19h00' },
  },

  /* ---------------- Sections de l'accueil ----------------
   * L'ordre du tableau définit l'ordre d'affichage.
   * `enabled` permet de masquer une section sans la supprimer.
   * `layout` (sections image/texte) : 'image-left' | 'image-right'.
   */
  home: {
    sections: [
      { key: 'about', enabled: true, layout: 'image-right' },
      { key: 'services', enabled: true },
      { key: 'steps', enabled: true },
      { key: 'team', enabled: true },
      { key: 'technology', enabled: true, layout: 'image-left' },
      { key: 'testimonials', enabled: true },
      { key: 'info', enabled: true, layout: 'image-right' },
      { key: 'cta', enabled: true },
      { key: 'contact', enabled: true },
    ],
  },

  /* ---------------- Présentation du cabinet ---------------- */
  about: {
    eyebrow: 'Le cabinet',
    title: 'Un cabinet pensé pour votre confort',
    paragraphs: [
      'Depuis son ouverture, le Cabinet Dentaire ELQODS accompagne les familles avec une approche simple : expliquer, prévenir et soigner dans la durée.',
      'Nos praticiens travaillent en équipe, avec des protocoles rigoureux et du matériel récent, pour des consultations calmes et sans mauvaise surprise.',
    ],
    image: '/images/about.jpg',
    imageAlt: 'L’équipe du cabinet échange autour d’un plan de soins',
    bullets: [
      'Consultation et bilan complet',
      'Prévention et hygiène dentaire',
      'Suivi personnalisé du patient',
    ],
    highlights: [
      { value: '15+', label: 'ans d’expérience' },
      { value: '6', label: 'praticiens' },
      { value: '4 000+', label: 'patients suivis' },
      { value: '4.9/5', label: 'satisfaction' },
    ],
  },

  /* ---------------- Services ---------------- */
  services: {
    eyebrow: 'Nos services',
    title: 'Une prise en charge complète',
    intro:
      'Du contrôle régulier aux soins plus complexes, le cabinet couvre l’ensemble des besoins dentaires de votre famille.',
    image: null,
    items: [
      {
        icon: 'shield',
        title: 'Prévention & contrôle',
        description: 'Bilan annuel, détartrage, fluorisation et conseils d’hygiène personnalisés.',
      },
      {
        icon: 'sparkles',
        title: 'Blanchiment & esthétique',
        description: 'Éclaircissement, facettes et corrections esthétiques pour un sourire naturel.',
      },
      {
        icon: 'tooth',
        title: 'Soins conservateurs',
        description: 'Traitement des caries, restaurations en composite et endodontie.',
      },
      {
        icon: 'activity',
        title: 'Orthodontie',
        description: 'Alignement dentaire adulte et enfant, solutions discrètes et progressives.',
      },
      {
        icon: 'layers',
        title: 'Implants & prothèses',
        description: 'Remplacement des dents absentes par des solutions durables et fidèles.',
      },
      {
        icon: 'clock',
        title: 'Urgences dentaires',
        description: 'Prise en charge rapide des douleurs, avec créneaux réservés dans la journée.',
      },
    ],
    cta: { label: 'Voir toutes les prestations', to: '/services' },
  },

  /* ---------------- Équipe ---------------- */
  team: {
    eyebrow: 'Notre équipe',
    title: 'Des praticiens à votre écoute',
    intro: 'Une équipe pluridisciplinaire qui partage la même exigence de soin et la même transparence.',
    members: [
      {
        name: 'Dr Amina Belkacem',
        role: 'Chirurgien-dentiste',
        description: 'Soins conservateurs, prévention et suivi des patients adultes.',
        photo: '/images/team-belkacem.jpg',
      },
      {
        name: 'Dr Karim Haddad',
        role: 'Implantologue',
        description: 'Implantologie, chirurgie orale et réhabilitations complètes.',
        photo: '/images/team-haddad.jpg',
      },
      {
        name: 'Dr Léa Moreau',
        role: 'Orthodontiste',
        description: 'Alignement dentaire, appareils discrets et suivi de l’occlusion.',
        photo: '/images/team-moreau.jpg',
      },
      {
        name: 'Sophie Nguyen',
        role: 'Assistante dentaire',
        description: 'Préparation des soins, stérilisation et accueil des patients.',
        photo: '/images/team-nguyen.jpg',
      },
    ],
    cta: { label: 'Rencontrer l’équipe', to: '/team' },
  },

  /* ---------------- Technologies ---------------- */
  technology: {
    eyebrow: 'Nos technologies',
    title: 'Des équipements récents, au service de la précision',
    paragraphs: [
      'Nous investissons dans des outils qui réduisent la durée des soins, améliorent le diagnostic et rendent les gestes plus confortables.',
    ],
    image: '/images/technology.jpg',
    imageAlt: 'Fauteuil et équipement de la salle de soins du cabinet',
    items: [
      { title: 'Radiologie numérique', description: 'Imagerie basse dose et lecture instantanée à l’écran.' },
      { title: 'Empreinte optique', description: 'Fin des empreintes classiques pour les restaurations.' },
      { title: 'Scanner intra-oral', description: 'Modèles 3D précis pour prothèses et aligneurs.' },
      { title: 'Bloc opératoire équipé', description: 'Chaise réglable, aspiration performante et éclairage chirurgical.' },
    ],
  },

  /* ---------------- Parcours patient ---------------- */
  steps: {
    eyebrow: 'Parcours patient',
    title: 'Comment se passe votre visite ?',
    intro: 'Un déroulé clair, du premier contact jusqu’au suivi de vos soins.',
    items: [
      { title: 'Prise de rendez-vous', description: 'Par téléphone ou via le formulaire de contact, créneau confirmé sous 24 h.' },
      { title: 'Bilan complet', description: 'Examen, imagerie si nécessaire et discussion de vos priorités.' },
      { title: 'Plan de soins', description: 'Un plan expliqué, avec délais et coûts détaillés avant tout soin.' },
      { title: 'Soins & suivi', description: 'Réalisations des soins puis rappels de contrôle réguliers.' },
    ],
  },

  /* ---------------- Témoignages ---------------- */
  testimonials: {
    eyebrow: 'Ils nous font confiance',
    title: 'Ce que disent nos patients',
    items: [
      {
        quote: 'Accueil chaleureux et explications très claires. Je refais enfin mes visites chez le dentiste sans appréhension.',
        author: 'Sarah M.',
        role: 'Patiente depuis 2021',
        stars: 5,
      },
      {
        quote: 'Implant posé sans douleur et suivi impeccable. Le plan de soins annoncé au centime près a été respecté.',
        author: 'Jean-Pierre L.',
        role: 'Patient implantologie',
        stars: 5,
      },
      {
        quote: 'Mes deux enfants y vont sans stress. L’équipe prend le temps de tout expliquer à leur niveau.',
        author: 'Nadia B.',
        role: 'Parent de patients',
        stars: 5,
      },
    ],
  },

  /* ---------------- Informations pratiques ---------------- */
  info: {
    eyebrow: 'Informations pratiques',
    title: 'Venir au cabinet',
    paragraphs: ['Tout ce qu’il faut savoir avant votre visite : accès, horaires et modalités de paiement.'],
    items: [
      { icon: 'mapPin', title: 'Accès', text: 'Métro ligne 7 à 3 minutes à pied. Parking public à 100 m.' },
      { icon: 'creditCard', title: 'Paiement', text: 'Carte bancaire, espèces, chèques et tiers payant possible.' },
      { icon: 'accessibility', title: 'Accessibilité', text: 'Locaux accessibles PMR, chaise adaptée et ascenseur.' },
      { icon: 'bell', title: 'Rappels', text: 'Rappel automatique par SMS avant chaque rendez-vous.' },
    ],
  },

  /* ---------------- Appel à l'action ---------------- */
  cta: {
    title: 'Prêt à prendre soin de votre sourire ?',
    text: 'Réservez votre consultation dès maintenant. Nous vous répondons sous 24 heures ouvrées.',
    primaryButton: { label: 'Prendre rendez-vous', to: '/contact' },
    secondaryButton: { label: 'Nous appeler', href: 'tel:+33123456789' },
  },

  /* ---------------- Contact ---------------- */
  contact: {
    eyebrow: 'Contact',
    title: 'Contactez le cabinet',
    intro:
      'Une question, un rendez-vous ou une urgence ? Écrivez-nous : le formulaire ouvre votre messagerie, aucune donnée n’est envoyée à un serveur pour l’instant.',
    email: 'contact@cabinet-elqods.fr',
    phone: '+33 1 23 45 67 89',
    address: '12 avenue de la Santé, 75013 Paris',
    subject: 'Demande depuis le site du cabinet',
    hours: [
      { label: 'Lundi – Jeudi', value: '8h30 – 19h00' },
      { label: 'Vendredi', value: '8h30 – 17h00' },
      { label: 'Samedi', value: '9h00 – 13h00' },
      { label: 'Dimanche', value: 'Fermé' },
    ],
    emergency: 'Urgence dentaire en dehors des horaires : 15 (SAMU).',
  },

  /* ---------------- Pied de page ---------------- */
  footer: {
    description:
      'Cabinet dentaire familial : prévention, soins, esthétique et implantologie au cœur de Paris.',
    columns: [
      {
        title: 'Navigation',
        links: [
          { label: 'Accueil', to: '/' },
          { label: 'Services', to: '/services' },
          { label: 'Équipe', to: '/team' },
          { label: 'Contact', to: '/contact' },
        ],
      },
      {
        title: 'Horaires',
        items: [
          { label: 'Lun – Jeu', value: '8h30 – 19h00' },
          { label: 'Vendredi', value: '8h30 – 17h00' },
          { label: 'Samedi', value: '9h00 – 13h00' },
          { label: 'Dimanche', value: 'Fermé' },
        ],
      },
    ],
    showSocials: true,
    copyright: 'Tous droits réservés.',
    legal: 'Site d’information : il ne remplace pas une consultation dentaire.',
  },
}

/* ------------------------------------------------------------------ */
/* Utilitaires de chargement / fusion / persistance                    */
/* ------------------------------------------------------------------ */

function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Fusion profonde : les valeurs de `override` remplacent celles de `base`. */
export function mergeSiteConfig(base, override) {
  if (override === undefined) return base
  // Les tableaux (liens, sections, listes) sont remplacés tels quels.
  if (!isPlainObject(base) || !isPlainObject(override)) return override

  const result = { ...base }
  Object.entries(override).forEach(([key, value]) => {
    result[key] = mergeSiteConfig(base[key], value)
  })
  return result
}

export function loadSiteConfig() {
  try {
    const raw = localStorage.getItem(SITE_CONFIG_STORAGE_KEY)
    if (!raw) return defaultSiteConfig
    return mergeSiteConfig(defaultSiteConfig, JSON.parse(raw))
  } catch {
    return defaultSiteConfig
  }
}

export function saveSiteConfig(config) {
  try {
    localStorage.setItem(SITE_CONFIG_STORAGE_KEY, JSON.stringify(config))
    return true
  } catch {
    return false
  }
}

export function clearSiteConfig() {
  try {
    localStorage.removeItem(SITE_CONFIG_STORAGE_KEY)
  } catch {
    // Stockage indisponible : on ignore silencieusement.
  }
}
