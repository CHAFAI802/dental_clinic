"""Structured content for the administrator guide.

This content is served only through the administrator-protected API.
"""

ADMIN_GUIDE_CONTENT = {
    "title": "Guide administrateur Dental Clinic",
    "version": "1.0",
    "sections": [
        {
            "id": "role",
            "title": "1. Rôle et périmètre",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Ce guide s'adresse aux administrateurs fonctionnels "
                        "et aux super administrateurs. Il décrit les opérations "
                        "de configuration et de contrôle qui relèvent de leurs "
                        "responsabilités dans Dental Clinic."
                    ),
                },
                {
                    "type": "note",
                    "text": (
                        "Le rôle ADMINISTRATOR correspond à l'administration "
                        "fonctionnelle du cabinet. Le rôle SUPER_ADMIN dispose "
                        "de responsabilités techniques et de gestion des accès "
                        "plus étendues. Les deux rôles ne sont pas interchangeables."
                    ),
                },
            ],
        },
        {
            "id": "access",
            "title": "2. Accès et comptes utilisateurs",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Les rôles applicatifs sont SUPER_ADMIN, ADMINISTRATOR, "
                        "DENTIST, ASSISTANT, RECEPTIONIST et ACCOUNTANT. "
                        "Les autorisations sont contrôlées côté serveur : "
                        "masquer une action dans l'interface ne remplace jamais "
                        "une vérification backend."
                    ),
                },
                {
                    "type": "note",
                    "text": (
                        "La gestion des comptes utilisateurs est réservée au "
                        "SUPER_ADMIN selon les contrôles d'accès du projet. "
                        "Un ADMINISTRATOR ne doit pas être considéré comme "
                        "autorisé à créer ou modifier les comptes."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Attribuer uniquement le rôle nécessaire à chaque personne.",
                        "Désactiver les comptes qui ne doivent plus accéder à l'application.",
                        "Ne jamais partager un compte ou un mot de passe.",
                        "Vérifier les droits après tout changement de rôle.",
                    ],
                },
            ],
        },
        {
            "id": "configuration",
            "title": "3. Paramètres métier",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Les paramètres métier doivent être configurés avant "
                        "leur utilisation opérationnelle. Toute modification "
                        "peut avoir des conséquences sur les actes, les tarifs, "
                        "les documents ou la facturation."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Vérifier les catégories de prestations utilisées par le cabinet.",
                        "Vérifier les prestations rattachées à chaque catégorie.",
                        "Contrôler les tarifs actifs et leur cohérence.",
                        "Tester les changements dans un contexte maîtrisé avant leur usage courant.",
                    ],
                },
            ],
        },
        {
            "id": "services",
            "title": "4. Catégories, prestations et tarifs",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Les catégories permettent d'organiser les prestations. "
                        "Les prestations et leurs tarifs constituent des données "
                        "de référence utilisées dans les opérations métier."
                    ),
                },
                {
                    "type": "note",
                    "text": (
                        "Avant de modifier ou désactiver une prestation ou un tarif, "
                        "vérifier les conséquences sur les rendez-vous, les actes "
                        "déjà enregistrés et les opérations de facturation. "
                        "Ne pas supposer qu'une modification de tarif recalcule "
                        "les opérations historiques."
                    ),
                },
            ],
        },
        {
            "id": "templates",
            "title": "5. Modèles Word et prescriptions",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Dental Clinic possède deux mécanismes de génération "
                        "documentaire distincts : le moteur historique des "
                        "ordonnances DOCX et le moteur de documents dynamiques. "
                        "Ils ne doivent pas être confondus."
                    ),
                },
                {
                    "type": "paragraph",
                    "text": (
                        "Pour un modèle destiné au moteur historique des "
                        "ordonnances, sélectionner l'option « Aucun type dynamique "
                        "(modèle historique) ». Ce moteur utilise notamment "
                        "les marqueurs {{ prescription_start }} et "
                        "{{ prescription_end }} pour répéter les lignes de médicaments."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Vérifier que le fichier est un DOCX valide.",
                        "Contrôler les variables et les marqueurs utilisés par le moteur visé.",
                        "Approuver le modèle après vérification.",
                        "Effectuer un essai de génération avant de le mettre en service.",
                        "Une modification du fichier source d'un modèle peut révoquer son approbation.",
                    ],
                },
                {
                    "type": "note",
                    "text": (
                        "Ne pas convertir un modèle historique en modèle dynamique "
                        "sans vérifier sa compatibilité. Les variables et les "
                        "mécanismes de répétition ne sont pas interchangeables."
                    ),
                },
            ],
        },
        {
            "id": "prescription-rules",
            "title": "6. Conditions de génération d'une ordonnance",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "La génération d'une ordonnance historique est soumise "
                        "à des contrôles métier. Le patient doit être rattaché "
                        "au dentiste, le rendez-vous doit être confirmé et "
                        "attribué à ce dentiste, et l'opération doit intervenir "
                        "dans la période autorisée du rendez-vous."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Un modèle DOCX actif et approuvé est nécessaire.",
                        "Au moins un médicament doit être renseigné.",
                        "La date de fin d'un traitement ne doit pas précéder sa date de début.",
                        "Les données utilisées sont rendues côté serveur et conservées avec le document généré.",
                    ],
                },
                {
                    "type": "note",
                    "text": (
                        "En cas de refus, lire le message retourné par l'application "
                        "et vérifier les préconditions du rendez-vous et du modèle. "
                        "Ne pas contourner les contrôles métier."
                    ),
                },
            ],
        },
        {
            "id": "prescription-billing",
            "title": "7. Facturation des prescriptions (PRESC)",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Le code de prestation PRESC est utilisé pour la facturation "
                        "d'une prescription dans le cas prévu par les règles métier : "
                        "aucun acte dentaire n'a été réalisé pendant le rendez-vous."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "La facturation intervient à la clôture du rendez-vous.",
                        "La quantité facturée est de 1.",
                        "La création est protégée contre les doublons.",
                        "Si le tarif PRESC est absent ou invalide, la clôture du rendez-vous peut aboutir tandis qu'une erreur de facturation est consignée.",
                    ],
                },
                {
                    "type": "note",
                    "text": (
                        "Vérifier l'existence et la validité du tarif PRESC avant "
                        "la mise en exploitation de cette règle."
                    ),
                },
            ],
        },
        {
            "id": "dynamic-documents",
            "title": "8. Documents dynamiques",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Le moteur de documents dynamiques utilise une configuration "
                        "de structure et un catalogue de données. Il est distinct "
                        "du moteur historique des ordonnances."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Vérifier le type de document et sa configuration.",
                        "Utiliser les champs et variables proposés par le catalogue correspondant.",
                        "Valider le document généré avec des données de test.",
                    ],
                },
                {
                    "type": "note",
                    "text": (
                        "Ne pas réutiliser les marqueurs du moteur historique "
                        "dans un modèle dynamique sans prise en charge explicite."
                    ),
                },
            ],
        },
        {
            "id": "inventory",
            "title": "9. Gestion et contrôle de l'inventaire",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Les mouvements d'inventaire doivent être enregistrés "
                        "et contrôlés avec attention. Une opération de destruction "
                        "créée n'entraîne pas à elle seule la déduction du stock."
                    ),
                },
                {
                    "type": "note",
                    "text": (
                        "L'application effective d'une destruction passe par "
                        "l'action dédiée « apply ». Vérifier son résultat avant "
                        "de considérer la quantité comme déduite."
                    ),
                },
                {
                    "type": "list",
                    "items": [
                        "Contrôler les quantités et les dates de péremption.",
                        "Vérifier les mouvements après chaque opération importante.",
                        "Conserver les justificatifs nécessaires aux contrôles internes.",
                    ],
                },
            ],
        },
        {
            "id": "periodic-controls",
            "title": "10. Contrôles périodiques",
            "blocks": [
                {
                    "type": "list",
                    "items": [
                        "Vérifier régulièrement les utilisateurs actifs et leurs rôles.",
                        "Contrôler les modèles documentaires actifs et approuvés.",
                        "Vérifier les catégories, prestations et tarifs utilisés.",
                        "Contrôler les opérations de facturation et les erreurs signalées.",
                        "Comparer périodiquement le stock physique aux quantités enregistrées.",
                        "Examiner les anomalies remontées par les utilisateurs.",
                    ],
                },
            ],
        },
        {
            "id": "troubleshooting",
            "title": "11. Diagnostic des problèmes courants",
            "blocks": [
                {
                    "type": "list",
                    "items": [
                        "Accès refusé : vérifier le rôle, l'état du compte et les droits associés à l'opération.",
                        "Ordonnance refusée : vérifier le rendez-vous, le rattachement du patient, le dentiste assigné et le modèle approuvé.",
                        "Document incorrect : vérifier le moteur utilisé, le modèle DOCX et ses variables.",
                        "Facturation PRESC absente : vérifier les conditions métier, le code de prestation et le tarif.",
                        "Stock non déduit : vérifier que l'opération de destruction a bien été appliquée.",
                    ],
                },
                {
                    "type": "note",
                    "text": (
                        "Pour transmettre un incident, conserver le message d'erreur, "
                        "la date et l'heure, le module concerné et les étapes "
                        "reproductibles. Ne pas transmettre de mot de passe ni "
                        "de données médicales inutiles."
                    ),
                },
            ],
        },
        {
            "id": "handover",
            "title": "12. Transmission et limites du guide",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "Ce guide décrit les règles et contrôles connus de "
                        "l'application. Il ne remplace ni les procédures internes "
                        "du cabinet, ni les consignes de sécurité, ni la vérification "
                        "des droits réellement disponibles dans l'interface."
                    ),
                },
                {
                    "type": "paragraph",
                    "text": (
                        "Lors d'une transmission à un autre administrateur, "
                        "communiquer les procédures applicables, les paramètres "
                        "à surveiller, les incidents connus et les points restant "
                        "à vérifier. Ne jamais transmettre des identifiants personnels."
                    ),
                },
            ],
        },
    ],
}
