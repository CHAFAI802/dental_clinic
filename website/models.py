import copy

from django.db import models

from accounts.models import User


DEFAULT_SITE_CONFIG = {
    "branding": {
        "cabinetName": "Cabinet Dentaire ELQODS",
        "shortName": "ELQODS",
        "tagline": "Votre sourire, notre priorité",
        "logo": None,
        "favicon": None,
        "theme": {
            "primary": "#1d4ed8",
            "primaryHover": "#1e40af",
            "secondary": "#0f172a",
            "accent": "#14b8a6",
            "background": "#f8fafc",
            "surface": "#ffffff",
            "text": "#0f172a",
            "textMuted": "#475569",
            "border": "#e2e8f0",
        },
        "phone": "+33 1 23 45 67 89",
        "email": "contact@cabinet-elqods.fr",
        "address": "12 avenue de la Santé, 75013 Paris",
        "socials": [
            {"label": "Facebook", "url": "https://facebook.com"},
            {"label": "Instagram", "url": "https://instagram.com"},
            {"label": "LinkedIn", "url": "https://linkedin.com"},
        ],
    },
    "nav": {
        "links": [
            {"label": "Accueil", "to": "/"},
            {"label": "Services", "to": "/services"},
            {"label": "Équipe", "to": "/team"},
            {"label": "Contact", "to": "/contact"},
        ],
        "cta": {"label": "Prendre rendez-vous", "to": "/contact"},
        "showLogin": True,
        "loginLabel": "Connexion",
        "dashboardLabel": "Dashboard",
        "logoutLabel": "Déconnexion",
    },
    "hero": {
        "eyebrow": "Cabinet dentaire • Accueil sur rendez-vous",
        "title": "Des soins dentaires modernes, doux et humains",
        "subtitle": "Cabinet Dentaire ELQODS",
        "description": "Une équipe expérimentée, des technologies de pointe et un accompagnement clair à chaque étape pour préserver la santé de vos dents et la confiance de votre sourire.",
        "image": "/images/hero.jpg",
        "imageAlt": "Le chirurgien-dentiste examine les dents d’une patiente au fauteuil",
        "primaryButton": {"label": "Prendre rendez-vous", "to": "/contact"},
        "secondaryButton": {"label": "Découvrir nos services", "to": "/services"},
        "points": ["Prise en charge rapide", "Stérilisation contrôlée", "Devis transparent"],
        "badge": {"title": "Ouvert aujourd’hui", "text": "8h30 – 19h00"},
    },
    "home": {
        "sections": [
            {"key": "about", "enabled": True, "layout": "image-right"},
            {"key": "services", "enabled": True},
            {"key": "steps", "enabled": True},
            {"key": "team", "enabled": True},
            {"key": "technology", "enabled": True, "layout": "image-left"},
            {"key": "testimonials", "enabled": True},
            {"key": "info", "enabled": True, "layout": "image-right"},
            {"key": "cta", "enabled": True},
            {"key": "contact", "enabled": True},
        ]
    },
    "about": {
        "eyebrow": "Le cabinet",
        "title": "Un cabinet pensé pour votre confort",
        "paragraphs": [
            "Depuis son ouverture, le Cabinet Dentaire ELQODS accompagne les familles avec une approche simple : expliquer, prévenir et soigner dans la durée.",
            "Nos praticiens travaillent en équipe, avec des protocoles rigoureux et du matériel récent, pour des consultations calmes et sans mauvaise surprise.",
        ],
        "image": "/images/about.jpg",
        "imageAlt": "L’équipe du cabinet échange autour d’un plan de soins",
        "bullets": [
            "Consultation et bilan complet",
            "Prévention et hygiène dentaire",
            "Suivi personnalisé du patient",
        ],
        "highlights": [
            {"value": "15+", "label": "ans d’expérience"},
            {"value": "6", "label": "praticiens"},
            {"value": "4 000+", "label": "patients suivis"},
            {"value": "4.9/5", "label": "satisfaction"},
        ],
    },
    "services": {
        "eyebrow": "Nos services",
        "title": "Une prise en charge complète",
        "intro": "Du contrôle régulier aux soins plus complexes, le cabinet couvre l’ensemble des besoins dentaires de votre famille.",
        "image": None,
        "items": [
            {
                "icon": "shield",
                "title": "Prévention & contrôle",
                "description": "Bilan annuel, détartrage, fluorisation et conseils d’hygiène personnalisés.",
            },
            {
                "icon": "sparkles",
                "title": "Blanchiment & esthétique",
                "description": "Éclaircissement, facettes et corrections esthétiques pour un sourire naturel.",
            },
            {
                "icon": "tooth",
                "title": "Soins conservateurs",
                "description": "Traitement des caries, restaurations en composite et endodontie.",
            },
            {
                "icon": "activity",
                "title": "Orthodontie",
                "description": "Alignement dentaire adulte et enfant, solutions discrètes et progressives.",
            },
            {
                "icon": "layers",
                "title": "Implants & prothèses",
                "description": "Remplacement des dents absentes par des solutions durables et fidèles.",
            },
            {
                "icon": "clock",
                "title": "Urgences dentaires",
                "description": "Prise en charge rapide des douleurs, avec créneaux réservés dans la journée.",
            },
        ],
        "cta": {"label": "Voir toutes les prestations", "to": "/services"},
    },
    "team": {
        "eyebrow": "Notre équipe",
        "title": "Des praticiens à votre écoute",
        "intro": "Une équipe pluridisciplinaire qui partage la même exigence de soin et la même transparence.",
        "members": [
            {
                "name": "Dr Amina Belkacem",
                "role": "Chirurgien-dentiste",
                "description": "Soins conservateurs, prévention et suivi des patients adultes.",
                "photo": "/images/team-belkacem.jpg",
            },
            {
                "name": "Dr Karim Haddad",
                "role": "Implantologue",
                "description": "Implantologie, chirurgie orale et réhabilitations complètes.",
                "photo": "/images/team-haddad.jpg",
            },
            {
                "name": "Dr Léa Moreau",
                "role": "Orthodontiste",
                "description": "Alignement dentaire, appareils discrets et suivi de l’occlusion.",
                "photo": "/images/team-moreau.jpg",
            },
            {
                "name": "Sophie Nguyen",
                "role": "Assistante dentaire",
                "description": "Préparation des soins, stérilisation et accueil des patients.",
                "photo": "/images/team-nguyen.jpg",
            },
        ],
        "cta": {"label": "Rencontrer l’équipe", "to": "/team"},
    },
    "technology": {
        "eyebrow": "Nos technologies",
        "title": "Des équipements récents, au service de la précision",
        "paragraphs": [
            "Nous investissons dans des outils qui réduisent la durée des soins, améliorent le diagnostic et rendent les gestes plus confortables.",
        ],
        "image": "/images/technology.jpg",
        "imageAlt": "Fauteuil et équipement de la salle de soins du cabinet",
        "items": [
            {"title": "Radiologie numérique", "description": "Imagerie basse dose et lecture instantanée à l’écran."},
            {"title": "Empreinte optique", "description": "Fin des empreintes classiques pour les restaurations."},
            {"title": "Scanner intra-oral", "description": "Modèles 3D précis pour prothèses et aligneurs."},
            {"title": "Bloc opératoire équipé", "description": "Chaise réglable, aspiration performante et éclairage chirurgical."},
        ],
    },
    "steps": {
        "eyebrow": "Parcours patient",
        "title": "Comment se passe votre visite ?",
        "intro": "Un déroulé clair, du premier contact jusqu’au suivi de vos soins.",
        "items": [
            {"title": "Prise de rendez-vous", "description": "Par téléphone ou via le formulaire de contact, créneau confirmé sous 24 h."},
            {"title": "Bilan complet", "description": "Examen, imagerie si nécessaire et discussion de vos priorités."},
            {"title": "Plan de soins", "description": "Un plan expliqué, avec délais et coûts détaillés avant tout soin."},
            {"title": "Soins & suivi", "description": "Réalisations des soins puis rappels de contrôle réguliers."},
        ],
    },
    "testimonials": {
        "eyebrow": "Ils nous font confiance",
        "title": "Ce que disent nos patients",
        "items": [
            {
                "quote": "Accueil chaleureux et explications très claires. Je refais enfin mes visites chez le dentiste sans appréhension.",
                "author": "Sarah M.",
                "role": "Patiente depuis 2021",
                "stars": 5,
            },
            {
                "quote": "Implant posé sans douleur et suivi impeccable. Le plan de soins annoncé au centime près a été respecté.",
                "author": "Jean-Pierre L.",
                "role": "Patient implantologie",
                "stars": 5,
            },
            {
                "quote": "Mes deux enfants y vont sans stress. L’équipe prend le temps de tout expliquer à leur niveau.",
                "author": "Nadia B.",
                "role": "Parent de patients",
                "stars": 5,
            },
        ],
    },
    "info": {
        "eyebrow": "Informations pratiques",
        "title": "Tout est pensé pour que votre visite soit simple",
        "intro": "Des détails utiles pour venir sereinement et préparer votre consultation.",
        "items": [
            {"title": "Adresse", "description": "12 avenue de la Santé, 75013 Paris"},
            {"title": "Horaires", "description": "Lun–Ven : 8h30–19h00 | Sam : 9h00–13h00"},
            {"title": "Téléphone", "description": "+33 1 23 45 67 89"},
            {"title": "Paiement", "description": "Carte bleue, chéque, espèces et mutuelle"},
        ],
    },
    "cta": {
        "title": "Une consultation qui vous aide à prendre la bonne décision",
        "text": "Discutons de vos besoins, de vos priorités et de votre budget sans pression.",
        "button": {"label": "Nous contacter", "to": "/contact"},
    },
    "contact": {
        "title": "Contact & rendez-vous",
        "subject": "Demande de rendez-vous",
        "intro": "Contactez-nous pour prendre un rendez-vous ou obtenir des informations sur les soins.",
        "emergency": "Urgence dentaire : appelez-nous immédiatement pour un créneau prioritaire.",
        "hours": [
            {"label": "Lundi – Vendredi", "value": "8h30 – 19h00"},
            {"label": "Samedi", "value": "9h00 – 13h00"},
        ],
    },
    "footer": {
        "description": "Cabinet dentaire moderne et humain, au service de votre santé bucco-dentaire.",
        "copyright": "© 2026 Cabinet Dentaire ELQODS",
        "legal": "Mentions légales",
    },
}


def default_site_config():
    return copy.deepcopy(DEFAULT_SITE_CONFIG)


class SiteSettings(models.Model):
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        if self.pk is None and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance is allowed.")

        if self.pk is not None and SiteSettings.objects.exclude(pk=self.pk).exists():
            raise ValueError("Only one SiteSettings instance is allowed.")

        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        instance = cls.objects.order_by("pk").first()
        if instance is None:
            instance = cls.objects.create(config=default_site_config())
        return instance


class SiteImage(models.Model):
    key = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='site-images/%Y/%m/%d')
    alt = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key

    def get_absolute_url(self):
        if not self.image:
            return ''
        return self.image.url


class WorkingHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    practitioner = models.ForeignKey(
        "accounts.User",
        related_name="working_hours",
        on_delete=models.CASCADE,
        limit_choices_to={"role": User.Role.DENTIST},
    )
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["practitioner", "weekday", "start_time"]
        indexes = [
            models.Index(
                fields=["practitioner", "weekday", "is_active"],
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    end_time__gt=models.F("start_time"),
                ),
                name="working_hours_end_after_start",
            ),
            models.UniqueConstraint(
                fields=[
                    "practitioner",
                    "weekday",
                    "start_time",
                    "end_time",
                ],
                name="unique_practitioner_working_hours",
            ),
        ]

    def __str__(self):
        return (
            f"{self.practitioner} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time}-{self.end_time}"
        )