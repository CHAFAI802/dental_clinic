"""Registre central des modules API et filtrage par rôle utilisateur."""

ROLE_PERMISSIONS = {
    'super_admin': {
        'IsSuperAdmin',
        'IsAdministrator',
        'IsClinicalStaff',
        'IsStaffMember',
        'IsAccountantOrAdmin',
    },
    'administrator': {
        'IsAdministrator',
        'IsClinicalStaff',
        'IsStaffMember',
        'IsAccountantOrAdmin',
    },
    'dentist': {'IsClinicalStaff', 'IsStaffMember'},
    'assistant': {'IsClinicalStaff', 'IsStaffMember'},
    'receptionist': {'IsStaffMember'},
    'accountant': {'IsAccountantOrAdmin', 'IsStaffMember'},
}

ROLE_LABELS = {
    'super_admin': 'Super Admin',
    'administrator': 'Administrateur',
    'dentist': 'Dentiste',
    'assistant': 'Assistant dentaire',
    'receptionist': 'Réceptionniste',
    'accountant': 'Comptable',
}

API_MODULES = [
    {
        'id': 'users',
        'name': 'Utilisateurs',
        'path': '/api/users/',
        'description': 'Gestion des comptes et rôles',
        'permission': 'IsAdministrator',
        'app': 'accounts',
    },
    {
        'id': 'audit-logs',
        'name': 'Journal d\'audit',
        'path': '/api/audit-logs/',
        'description': 'Historique des actions sensibles',
        'permission': 'IsSuperAdmin',
        'app': 'accounts',
    },
    {
        'id': 'patients',
        'name': 'Patients',
        'path': '/api/patients/',
        'description': 'Dossiers patients et informations médicales',
        'permission': 'IsClinicalStaff',
        'app': 'patients',
    },
    {
        'id': 'appointments',
        'name': 'Rendez-vous',
        'path': '/api/appointments/',
        'description': 'Planning et rendez-vous',
        'permission': 'IsStaffMember',
        'app': 'appointments',
    },
    {
        'id': 'rooms',
        'name': 'Salles',
        'path': '/api/rooms/',
        'description': 'Salles de consultation',
        'permission': 'IsStaffMember',
        'app': 'appointments',
    },
    {
        'id': 'odontograms',
        'name': 'Odontogrammes',
        'path': '/api/odontograms/',
        'description': 'Cartes dentaires des patients',
        'permission': 'IsClinicalStaff',
        'app': 'odontogram',
    },
    {
        'id': 'teeth',
        'name': 'Dents',
        'path': '/api/teeth/',
        'description': 'État et suivi des dents',
        'permission': 'IsClinicalStaff',
        'app': 'odontogram',
    },
    {
        'id': 'treatments',
        'name': 'Traitements',
        'path': '/api/treatments/',
        'description': 'Soins et interventions réalisés',
        'permission': 'IsClinicalStaff',
        'app': 'treatments',
    },
    {
        'id': 'treatment-plans',
        'name': 'Plans de traitement',
        'path': '/api/treatment-plans/',
        'description': 'Plans thérapeutiques multi-étapes',
        'permission': 'IsClinicalStaff',
        'app': 'treatment_plans',
    },
    {
        'id': 'prescriptions',
        'name': 'Ordonnances',
        'path': '/api/prescriptions/',
        'description': 'Prescriptions médicales',
        'permission': 'IsClinicalStaff',
        'app': 'prescriptions',
    },
    {
        'id': 'prescription-templates',
        'name': 'Modèles d\'ordonnance',
        'path': '/api/prescription-templates/',
        'description': 'Modèles réutilisables',
        'permission': 'IsClinicalStaff',
        'app': 'prescriptions',
    },
    {
        'id': 'invoices',
        'name': 'Factures',
        'path': '/api/invoices/',
        'description': 'Facturation et devis',
        'permission': 'IsAccountantOrAdmin',
        'app': 'billing',
    },
    {
        'id': 'payments',
        'name': 'Paiements',
        'path': '/api/payments/',
        'description': 'Encaissements et transactions',
        'permission': 'IsAccountantOrAdmin',
        'app': 'billing',
    },
    {
        'id': 'documents',
        'name': 'Documents',
        'path': '/api/documents/',
        'description': 'Documents patients',
        'permission': 'IsStaffMember',
        'app': 'documents',
    },
    {
        'id': 'document-templates',
        'name': 'Modèles de documents',
        'path': '/api/document-templates/',
        'description': 'Modèles de documents administratifs',
        'permission': 'IsStaffMember',
        'app': 'documents',
    },
    {
        'id': 'inventory-items',
        'name': 'Inventaire',
        'path': '/api/inventory-items/',
        'description': 'Stock et consommables',
        'permission': 'IsAccountantOrAdmin',
        'app': 'inventory',
    },
    {
        'id': 'staff',
        'name': 'Personnel',
        'path': '/api/staff/',
        'description': 'Profils et contrats du personnel',
        'permission': 'IsAdministrator',
        'app': 'staff',
    },
    {
        'id': 'reports',
        'name': 'Rapports',
        'path': '/api/reports/',
        'description': 'Rapports et statistiques',
        'permission': 'IsAdministrator',
        'app': 'reports',
    },
    {
        'id': 'notifications',
        'name': 'Notifications',
        'path': '/api/notifications/',
        'description': 'Messages et alertes envoyés',
        'permission': 'IsAdministrator',
        'app': 'notifications',
    },
    {
        'id': 'notification-templates',
        'name': 'Modèles de notification',
        'path': '/api/notification-templates/',
        'description': 'Modèles de messages',
        'permission': 'IsAdministrator',
        'app': 'notifications',
    },
    {
        'id': 'imaging-studies',
        'name': 'Études d\'imagerie',
        'path': '/api/imaging-studies/',
        'description': 'Radiographies et examens',
        'permission': 'IsClinicalStaff',
        'app': 'imaging',
    },
    {
        'id': 'imaging-instances',
        'name': 'Images médicales',
        'path': '/api/imaging-instances/',
        'description': 'Fichiers d\'imagerie',
        'permission': 'IsClinicalStaff',
        'app': 'imaging',
    },
]


def get_accessible_modules(user):
    if not user or not user.is_authenticated:
        return []
    permissions = ROLE_PERMISSIONS.get(user.role, set())
    return [module for module in API_MODULES if module['permission'] in permissions]


def get_role_label(role):
    return ROLE_LABELS.get(role, role)
