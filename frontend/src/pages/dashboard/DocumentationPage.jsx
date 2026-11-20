import { useEffect, useState } from 'react'

import { apiDownload, apiGet } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'

const DOCUMENTS = {
  pdf: {
    endpoint: '/user-guide/pdf/',
    filename: 'guide-utilisateur-dental-clinic.pdf',
    label: 'PDF',
  },
  docx: {
    endpoint: '/user-guide/docx/',
    filename: 'guide-utilisateur-dental-clinic.docx',
    label: 'Word',
  },
}

const GUIDE_SECTIONS = [
  {
    id: 'demarrer',
    title: '1. Commencer avec Dental Clinic',
    blocks: [
      { type: 'p', text: 'Dental Clinic centralise le suivi des patients, les rendez-vous, les actes cliniques, les ordonnances, la facturation, les encaissements, les documents et le stock. Les modules proposés dans le tableau de bord dépendent du rôle du compte connecté.' },
      { type: 'p', text: 'Connectez-vous avec votre adresse e-mail et votre mot de passe. Ces identifiants vous sont communiqués lors de la création de votre compte par l’administration du cabinet. Les comptes inactifs ou supprimés ne peuvent pas accéder normalement à l’application. Utilisez toujours votre propre compte : les opérations sensibles doivent conserver leur véritable auteur.' },
      { type: 'callout', text: 'Une fonctionnalité visible dans le menu ne donne pas automatiquement tous les droits sur les données. Le backend vérifie les permissions à chaque opération.' },
      { type: 'h', text: 'Rôles principaux' },
      { type: 'table', headers: ['Rôle', 'Utilisation principale'], rows: [
        ['Super administrateur', 'Administration générale, utilisateurs, audit, paramètres et accès transversal selon les permissions.'],
        ['Administrateur', 'Comptes, catalogue et tarifs, paramètres, échéances des factures, référentiels et fonctions administratives.'],
        ['Dentiste', 'Patients rattachés, rendez-vous personnels, dossier clinique, actes, traitements et ordonnances.'],
        ['Réceptionniste', 'Dossiers administratifs, rendez-vous, confirmation des demandes et opérations de stock autorisées.'],
        ['Comptable', 'Paiements, méthodes de paiement, consultation des factures, avoirs et opérations de stock autorisées.'],
        ['Assistant dentaire', 'Accès limité aux ressources cliniques et documents des patients qui lui sont rattachés.'],
      ] },
      { type: 'p', text: 'La navigation principale contient le lien Documentation pour tout utilisateur connecté. La page et les fichiers téléchargeables sont réservés aux utilisateurs authentifiés.' },
    ],
  },
  {
    id: 'patients',
    title: '2. Créer et gérer un patient',
    blocks: [
      { type: 'steps', items: [
        'Ouvrir le module Patients.',
        'Rechercher le patient avant de créer une nouvelle fiche afin d’éviter les doublons.',
        'Pour une nouvelle fiche, renseigner les informations d’identité et de contact demandées. Le numéro de téléphone est requis dans le modèle patient.',
        'Enregistrer la fiche. Le serveur attribue automatiquement un code patient unique de la forme PAT-… ; ce code ne doit pas être saisi manuellement.',
        'Vérifier les coordonnées et les informations médicales avant toute consultation ou intervention.',
      ] },
      { type: 'p', text: 'Le dossier peut contenir les coordonnées, informations d’assurance, contact d’urgence, groupe sanguin, poids, taille, tabagisme, grossesse, résumé médical, allergies, antécédents, médicaments, notes, pièces jointes et consentements selon les écrans et droits activés.' },
      { type: 'h', text: 'Dossier clinique du dentiste' },
      { type: 'p', text: 'Le dentiste accède aux patients qui lui sont rattachés par un rendez-vous non supprimé ou un traitement non supprimé. Le dossier comporte les espaces Vue d’ensemble, Allergies, Antécédents, Consultations / actes et Ordonnances.' },
      { type: 'callout', text: 'Avant de créer un acte ou une ordonnance, confirmer l’identité du patient et le rendez-vous correspondant. Le serveur refuse une opération lorsque le patient ne correspond pas au patient du rendez-vous.' },
    ],
  },
  {
    id: 'rendez-vous',
    title: '3. Gérer les rendez-vous',
    blocks: [
      { type: 'h', text: 'Demande de rendez-vous' },
      { type: 'p', text: 'Une demande en ligne peut concerner un nouveau patient ou un patient existant. Pour un patient existant, le code patient est prioritaire. Sans code, l’application recherche une correspondance à partir des informations communiquées et refuse les cas ambigus. Une nouvelle demande crée un rendez-vous au statut pending. La date de début doit être future.' },
      { type: 'h', text: 'Confirmer une demande à l’accueil' },
      { type: 'steps', items: [
        'Ouvrir le module Rendez-vous avec un compte autorisé.',
        'Repérer le rendez-vous pending et vérifier le patient, le praticien, la date, l’heure et le motif.',
        'Cliquer sur Valider. L’action de confirmation dédiée est réservée à la réceptionniste.',
        'Vérifier que le statut devient confirmed. La date et l’utilisateur de confirmation sont enregistrés et une notification de confirmation est déclenchée.',
      ] },
      { type: 'p', text: 'Un rendez-vous dont l’heure de début est déjà passée ne peut pas être confirmé par cette action. Seuls les rendez-vous pending peuvent être validés.' },
      { type: 'h', text: 'Règles de planning et statuts' },
      { type: 'p', text: 'Le praticien doit être un compte ayant le rôle dentiste. L’heure de fin doit être postérieure à l’heure de début. Deux rendez-vous non supprimés ne peuvent pas se chevaucher pour le même praticien ni pour la même salle. La capacité d’une salle doit être au moins égale à un.' },
      { type: 'table', headers: ['Statut', 'Signification'], rows: [
        ['pending', 'Demande reçue, en attente de confirmation.'],
        ['confirmed', 'Rendez-vous confirmé et planifié.'],
        ['completed', 'Séance terminée.'],
        ['cancelled', 'Rendez-vous annulé.'],
        ['no_show', 'Patient absent.'],
      ] },
      { type: 'p', text: 'Les changements de statut sont contrôlés et inscrits dans l’historique AppointmentStatusLog. Un changement manuel exige un utilisateur identifié. Depuis la liste, Ouvrir le dossier conduit à la fiche du patient, et non à une fiche portant l’identifiant du rendez-vous.' },
      { type: 'h', text: 'Clôture automatique' },
      { type: 'p', text: 'À l’heure de fin du créneau, le mécanisme de clôture peut faire passer un rendez-vous confirmed à completed. Les rendez-vous futurs, annulés, déjà terminés ou supprimés sont ignorés. La transition automatique est journalisée sans attribuer l’action à un dentiste fictif.' },
    ],
  },
  {
    id: 'actes',
    title: '4. Enregistrer un soin ou un traitement',
    blocks: [
      { type: 'steps', items: [
        'Ouvrir le dossier du patient depuis Patients ou depuis un rendez-vous confirmé.',
        'Dans Consultations / actes, choisir le rendez-vous confirmé correspondant à la séance.',
        'Si plusieurs rendez-vous confirmés existent pour ce patient, sélectionner explicitement le bon rendez-vous ; l’application ne choisit pas arbitrairement le premier.',
        'Choisir une prestation active dans le catalogue et saisir la quantité demandée.',
        'Enregistrer l’acte puis vérifier sa présence dans le dossier et la mise à jour de la facturation.',
      ] },
      { type: 'p', text: 'La création d’un traitement est réservée au dentiste. Le rendez-vous doit appartenir au dentiste connecté, être au statut confirmed et l’heure actuelle doit être comprise dans l’intervalle [début, fin[. Une prestation inactive est refusée et la quantité doit être strictement positive.' },
      { type: 'p', text: 'Le traitement est rattaché au patient, au dentiste, au rendez-vous et à la prestation. Il peut également être lié à un plan de traitement. Le patient du traitement doit être le même que celui du rendez-vous.' },
      { type: 'callout', text: 'Enregistrer un acte ne clôture pas immédiatement le rendez-vous. Plusieurs prestations peuvent être enregistrées pendant une même séance.' },
    ],
  },
  {
    id: 'ordonnances',
    title: '5. Créer et générer une ordonnance',
    blocks: [
      { type: 'h', text: 'Conditions préalables' },
      { type: 'p', text: 'La génération depuis le dossier dentiste exige un patient rattaché au dentiste, un rendez-vous confirmé pour ce patient, un rendez-vous affecté au dentiste connecté et une heure actuelle comprise dans le créneau. Le modèle DOCX doit être actif et approuvé.' },
      { type: 'p', text: 'Si aucun modèle approuvé n’est disponible, contacter l’administrateur afin qu’il charge, valide et approuve un modèle Word. Le dentiste ne contourne pas cette exigence avec une création libre.' },
      { type: 'h', text: 'Procédure dans le dossier patient' },
      { type: 'steps', items: [
        'Ouvrir le dossier patient, puis l’espace Ordonnances.',
        'Sélectionner un modèle Word actif et approuvé.',
        'Choisir le rendez-vous de la séance. S’il y en a plusieurs, choisir celui qui correspond à la consultation.',
        'Ajouter au moins un médicament et renseigner Médicament, Dosage, Fréquence, Voie et Début. La date de fin est facultative, mais ne peut pas précéder la date de début.',
        'Ajouter les notes nécessaires et vérifier les médicaments existants proposés dans le dossier.',
        'Cliquer sur Générer et attendre le résultat confirmé par le backend.',
        'Ouvrir le véritable fichier Word généré par le serveur, puis le vérifier avant impression ou archivage.',
      ] },
      { type: 'p', text: 'Les médicaments sont enregistrés dans le dossier patient et liés au dentiste connecté. Le backend vérifie que chaque médicament transmis appartient au patient et a été prescrit par ce dentiste. Une ligne existante peut être réutilisée ; une ligne modifiée est mise à jour, et une nouvelle ligne est enregistrée avant la génération.' },
      { type: 'h', text: 'Document généré et contrôle du modèle' },
      { type: 'p', text: 'L’ordonnance est liée au patient, au dentiste, au rendez-vous et au modèle de document. Les données des médicaments sont conservées dans un instantané. Le DOCX est rendu côté backend ; il ne s’agit pas d’une reconstruction HTML du document médical.' },
      { type: 'p', text: 'Le fichier source du modèle est vérifié : le modèle doit être actif et approuvé, le fichier doit être disponible et son empreinte SHA-256 doit correspondre à celle enregistrée lors de l’approbation. Une modification du fichier source impose une nouvelle validation et approbation.' },
      { type: 'h', text: 'Règle de facturation de l’acte PRESC' },
      { type: 'p', text: 'La génération ne crée pas immédiatement une facture. Elle rattache l’acte technique PRESC à la séance lorsque celle-ci ne comporte pas déjà de prestation dentaire. Si un acte dentaire existe, aucun traitement PRESC supplémentaire n’est ajouté.' },
      { type: 'p', text: 'À la clôture du rendez-vous, PRESC est facturé uniquement si une ordonnance existe et qu’aucune prestation dentaire n’a été réalisée pendant cette séance. La quantité facturée est 1 et la création de la ligne est idempotente. Une séance comportant un acte dentaire ne reçoit pas de ligne PRESC additionnelle.' },
      { type: 'callout', text: 'Le moteur historique de génération d’ordonnance DOCX et le moteur générique de documents dynamiques sont deux circuits distincts. Leurs modèles et règles de validation ne sont pas interchangeables.' },
    ],
  },
  {
    id: 'factures',
    title: '6. Comprendre les factures',
    blocks: [
      { type: 'h', text: 'Création et regroupement automatique' },
      { type: 'p', text: 'L’API Factures n’expose pas de création ou suppression manuelle de facture. Lorsqu’une ligne de facture est créée à partir d’un traitement, le backend retrouve ou crée la facture appropriée. Tous les traitements liés au même rendez-vous doivent être regroupés sur une même facture : une facture par rendez-vous.' },
      { type: 'p', text: 'Une facture existante est réutilisée. Fournir une autre facture ne permet pas de contourner le regroupement. Si les traitements d’un rendez-vous sont déjà répartis sur plusieurs factures, l’ajout d’une nouvelle ligne est bloqué pour préserver la cohérence. Un traitement sans rendez-vous peut déclencher une facture distincte. Une facture archivée ne peut pas recevoir de nouvelle ligne.' },
      { type: 'h', text: 'Configurer le catalogue et les tarifs' },
      { type: 'steps', items: [
        'L’administrateur crée une catégorie de prestation.',
        'Il crée une prestation avec un code métier unique, un libellé et un état actif ou inactif.',
        'Il crée un tarif avec son montant, son taux de taxe et sa date d’entrée en vigueur.',
        'À la facturation, le backend sélectionne le tarif dont la date d’effet est la plus récente parmi celles qui ne dépassent pas la date du traitement.',
        'Le prix unitaire et le taux de taxe sont copiés dans la ligne de facture afin de conserver l’historique du prix facturé.',
      ] },
      { type: 'h', text: 'Calculs' },
      { type: 'table', headers: ['Élément', 'Calcul'], rows: [
        ['Sous-total d’une ligne', 'Quantité × prix unitaire.'],
        ['Taxe d’une ligne', 'Sous-total × taux de taxe ÷ 100.'],
        ['Total d’une ligne', 'Sous-total + taxe.'],
        ['Solde dû', 'Total facture − avoirs − paiements.'],
      ] },
      { type: 'p', text: 'Les montants sont arrondis à deux décimales. Les totaux sont recalculés à partir des lignes, paiements et avoirs, et non saisis directement dans la facture.' },
      { type: 'h', text: 'Référence, statut et consultation' },
      { type: 'p', text: 'La référence est générée automatiquement par année (par exemple A0001/2026). Un verrou PostgreSQL protège la génération concurrente des références. Les statuts possibles sont draft, issued et completed. Une facture non soldée reste généralement issued ; elle passe à completed lorsque son total est non nul et que son solde atteint zéro.' },
      { type: 'steps', items: [
        'Ouvrir Facturation puis Factures.',
        'Rechercher par référence, patient, statut ou montant.',
        'Sélectionner une facture pour afficher ses lignes, paiements et avoirs associés.',
        'Contrôler le total, le montant payé, le montant crédité et le solde dû.',
      ] },
      { type: 'p', text: 'Le rôle administrateur peut modifier la date d’échéance et les notes. Les autres rôles autorisés consultent la facture sans modifier ses montants. Les lignes sont consultables par plusieurs rôles ; leur création et modification API sont réservées au dentiste, et leur suppression est refusée par la permission dédiée.' },
    ],
  },
  {
    id: 'paiements',
    title: '7. Enregistrer un paiement',
    blocks: [
      { type: 'h', text: 'Méthodes de paiement' },
      { type: 'p', text: 'Les méthodes de paiement sont des références configurables (nom, fournisseur, détails, état actif/inactif). Elles sont gérées par les rôles comptable ou administrateur selon la permission API. Sélectionner une méthode reconnue par la clinique.' },
      { type: 'h', text: 'Procédure d’encaissement' },
      { type: 'steps', items: [
        'Ouvrir Facturation puis Paiements.',
        'Dans Enregistrer un paiement, sélectionner une facture dont le solde dû est positif.',
        'Contrôler le patient et le solde restant.',
        'Saisir un montant strictement positif, inférieur ou égal au solde.',
        'Choisir la méthode de paiement et saisir, si disponible, la référence de transaction ou de reçu.',
        'La date et l’heure sont facultatives ; sans valeur, le serveur utilise l’heure courante.',
        'Enregistrer le paiement, puis vérifier son apparition dans l’historique et la diminution du solde de la facture.',
      ] },
      { type: 'p', text: 'Le formulaire est disponible aux rôles super administrateur, administrateur et comptable. Le backend refuse un montant nul ou négatif, un montant supérieur au solde ou un patient différent de celui de la facture.' },
      { type: 'h', text: 'Paiement partiel et solde' },
      { type: 'p', text: 'Un paiement partiel est possible. Le solde diminue du montant encaissé et plusieurs paiements successifs peuvent solder la facture. Lorsque le solde atteint zéro, la facture passe à completed si son total est non nul. Le statut d’un paiement enregistré est completed.' },
      { type: 'p', text: 'Le backend verrouille la facture dans une transaction, enregistre le paiement puis recalcule les totaux. Un paiement ne peut pas être transféré vers une autre facture lors d’une modification.' },
      { type: 'h', text: 'Suppression d’un paiement' },
      { type: 'p', text: 'L’écran propose une suppression avec confirmation. La suppression recalcule la facture et peut réaugmenter son solde. Elle doit être réservée à la correction d’une erreur réelle et suivre les règles comptables de la clinique.' },
    ],
  },
  {
    id: 'avoirs-devis',
    title: '8. Avoirs et devis',
    blocks: [
      { type: 'h', text: 'Avoirs' },
      { type: 'p', text: 'Un avoir est rattaché à une facture, possède une date, un montant strictement positif, un motif obligatoire et un créateur. Son montant ne peut pas dépasser le montant encore disponible après prise en compte des avoirs précédents et des paiements. L’avoir diminue le solde dû.' },
      { type: 'p', text: 'La gestion des avoirs est réservée aux rôles comptable ou administrateur. Les avoirs associés peuvent être consultés dans le détail d’une facture.' },
      { type: 'h', text: 'Devis' },
      { type: 'p', text: 'Le modèle de devis contient un patient, un créateur, un validateur éventuel, une date de validité, un total, une taxe, une référence, des notes et un lien facultatif vers un plan de traitement. Les montants ne peuvent pas être négatifs et la taxe ne peut pas dépasser le total.' },
      { type: 'callout', text: 'L’API expose les devis, mais le tableau de bord examiné ne comporte pas encore d’écran React dédié à leur création et validation. Ne pas supposer qu’un parcours utilisateur complet est disponible.' },
    ],
  },
  {
    id: 'documents',
    title: '9. Documents et modèles Word',
    blocks: [
      { type: 'steps', items: [
        'Un administrateur ouvre Modèles de documents et téléverse un fichier DOCX.',
        'Renseigner le nom, la description et, lorsque nécessaire, la configuration du moteur dynamique.',
        'Lancer la validation du modèle. Le backend analyse les variables et les marqueurs autorisés.',
        'Approuver le modèle. L’application conserve l’utilisateur, la date et l’empreinte du fichier approuvé.',
        'Après toute modification du fichier ou de sa structure, refaire la validation et l’approbation avant utilisation.',
      ] },
      { type: 'p', text: 'Les dentistes ne voient que les modèles actifs et approuvés. Le parcours d’ordonnance utilise le moteur DOCX historique. Le générateur dynamique de documents est un moteur séparé, basé sur une configuration structure_config et un catalogue de données.' },
      { type: 'p', text: 'Le backend prévoit notamment des modèles dynamiques de facture, paiement et inventaire, avec des rôles autorisés selon le type. La disponibilité d’une action dépend du type et de la configuration du modèle.' },
    ],
  },
  {
    id: 'inventaire',
    title: '10. Gérer l’inventaire',
    blocks: [
      { type: 'h', text: 'Référentiels et articles' },
      { type: 'p', text: 'Le stock s’appuie sur les catégories MAT (matériel) et CON (consommable), familles, unités, fournisseurs et articles. Les catégories, familles, fournisseurs et unités sont administrés par les rôles administrateur et super administrateur. Les opérations de stock sont autorisées aux rôles administrateur, super administrateur, comptable et réceptionniste.' },
      { type: 'p', text: 'Chaque article doit appartenir à une famille active. Le SKU est généré par le serveur sous la forme DCL-<catégorie>-<famille>-<numéro>. Le SKU et la famille d’un article existant sont immuables. Un stock négatif est interdit.' },
      { type: 'h', text: 'Entrée et sortie' },
      { type: 'p', text: 'Une entrée enregistre l’article, la quantité, le coût unitaire et, si disponible, le fournisseur ainsi que les informations de lot et de péremption. Le serveur associe l’utilisateur qui réceptionne et met à jour le stock.' },
      { type: 'p', text: 'Une sortie enregistre la quantité utilisée. Les allocations aux lots conservent la traçabilité et empêchent une sortie supérieure à la quantité disponible.' },
      { type: 'h', text: 'Alertes et destructions' },
      { type: 'p', text: 'Les alertes couvrent notamment les seuils de réapprovisionnement et les dates de péremption. Le délai d’alerte avant péremption est paramétrable par article.' },
      { type: 'p', text: 'Une destruction se prépare comme un document avec ses lignes. Sa création ne déduit pas encore les quantités. Il faut exécuter l’action Appliquer : le système contrôle les lots et quantités, déduit les quantités des lots et du stock physique, passe le document à completed et synchronise les alertes.' },
      { type: 'callout', text: 'Ne pas confondre enregistrer une destruction et l’appliquer. La diminution effective du stock intervient uniquement lors de l’action dédiée.' },
    ],
  },
  {
    id: 'autres-modules',
    title: '11. Autres modules disponibles dans le backend',
    blocks: [
      { type: 'h', text: 'Plans de traitement' },
      { type: 'p', text: 'Le backend contient les plans de traitement, étapes, éléments, approbations, coûts estimés et versions. Les statuts du plan sont draft, active et approved. Le modèle conserve notamment les données d’approbation patient, les étapes séquencées, les coûts et les dates prévues. L’interface React examinée ne présente pas encore de parcours complet dédié.' },
      { type: 'h', text: 'Odontogramme' },
      { type: 'p', text: 'Le backend gère un odontogramme versionné par patient, les dents, leurs états, les états de surface, remarques, diagnostics, historiques et traitements associés. Aucun écran React complet n’a été identifié dans le tableau de bord examiné.' },
      { type: 'h', text: 'Imagerie, personnel, rapports et notifications' },
      { type: 'p', text: 'Les ressources d’imagerie médicale, de personnel, de rapports, de notifications et de modèles de notification sont exposées par l’API avec leurs permissions. Tous ces domaines ne disposent pas encore d’un parcours utilisateur complet intégré dans le tableau de bord.' },
    ],
  },
  {
    id: 'permissions',
    title: '12. Matrice rapide des permissions',
    blocks: [
      { type: 'table', headers: ['Opération', 'Rôles principalement autorisés'], rows: [
        ['Créer / modifier les patients administratifs', 'Réceptionniste, administrateur, super administrateur.'],
        ['Dossier clinique, allergies, antécédents et médicaments', 'Dentiste, pour les patients qui lui sont rattachés.'],
        ['Gérer les rendez-vous', 'Dentiste, réceptionniste, administrateur, super administrateur ; confirmation dédiée réservée à la réception.'],
        ['Créer un traitement ou générer une ordonnance', 'Dentiste.'],
        ['Consulter les factures', 'Comptable, réceptionniste, administrateur, super administrateur.'],
        ['Modifier échéance et notes d’une facture', 'Administrateur via l’API PATCH.'],
        ['Créer / modifier les lignes de facture', 'Dentiste via la permission API ; suppression refusée.'],
        ['Créer / supprimer un paiement', 'Comptable, administrateur, super administrateur.'],
        ['Gérer les méthodes de paiement et les avoirs', 'Comptable, administrateur, super administrateur.'],
        ['Gérer les catégories et tarifs de prestations', 'Administrateur, super administrateur.'],
        ['Gérer les référentiels de stock', 'Administrateur, super administrateur.'],
        ['Mouvements de stock', 'Administrateur, super administrateur, comptable, réceptionniste.'],
        ['Modèles de documents', 'Administrateur / super administrateur ; consultation limitée pour le dentiste.'],
        ['Journal d’audit', 'Super administrateur.'],
      ] },
      { type: 'p', text: 'Cette matrice résume les permissions vérifiées dans le code. Certaines vues ajoutent des restrictions par patient, rendez-vous, utilisateur ou action. La réponse du backend reste l’autorité finale.' },
    ],
  },
  {
    id: 'depannage',
    title: '13. Comprendre les erreurs courantes',
    blocks: [
      { type: 'table', headers: ['Message ou situation', 'Cause probable et action'], rows: [
        ['Aucun rendez-vous confirmé', 'Le patient n’a pas de séance confirmed disponible. Faire confirmer le rendez-vous et vérifier le créneau.'],
        ['Le rendez-vous n’appartient pas au dentiste connecté', 'Le rendez-vous est affecté à un autre praticien. Sélectionner la séance correcte.'],
        ['L’heure actuelle doit appartenir au créneau', 'La séance n’a pas commencé ou sa fin est atteinte. Les actes et ordonnances sont limités au créneau.'],
        ['Aucun modèle approuvé disponible', 'Un administrateur doit téléverser, valider et approuver un modèle DOCX actif.'],
        ['Aucun tarif applicable', 'Configurer un tarif dont la date d’effet est antérieure ou égale à la date du traitement.'],
        ['Facturation bloquée pour plusieurs factures sur une séance', 'Les traitements du rendez-vous sont déjà répartis sur plusieurs factures. Ne pas forcer le rattachement ; faire examiner l’historique.'],
        ['Paiement supérieur au solde', 'Réduire le montant ou sélectionner une facture ayant un solde suffisant.'],
        ['Patient du paiement différent du patient de la facture', 'Sélectionner la facture correspondant au patient.'],
        ['Destruction enregistrée mais stock inchangé', 'Le document de destruction n’a pas encore été appliqué.'],
      ] },
      { type: 'callout', text: 'En cas d’erreur, ne répétez pas aveuglément une opération clinique ou financière. Vérifiez d’abord si l’objet a été créé, puis contrôlez les références et l’historique.' },
    ],
  },
  {
    id: 'bonnes-pratiques',
    title: '14. Bonnes pratiques',
    blocks: [
      { type: 'steps', items: [
        'Vérifier l’identité du patient avant tout acte, ordonnance, facture ou paiement.',
        'Confirmer le rendez-vous et vérifier le dentiste, la date et le créneau avant la consultation.',
        'Renseigner les prestations et tarifs avec des dates d’effet cohérentes avant la première facturation.',
        'Ne pas modifier un tarif historique pour corriger une facture déjà émise ; examiner la procédure d’avoir ou de correction comptable.',
        'Enregistrer chaque paiement sur la bonne facture et conserver la référence de transaction lorsqu’elle existe.',
        'Vérifier le solde après chaque encaissement ou suppression de paiement.',
        'Ne pas modifier un modèle Word après approbation sans le revalider et le réapprouver.',
        'Pour une destruction de stock, contrôler les lots puis appliquer explicitement le document.',
        'Ne jamais partager les identifiants de connexion.',
      ] },
    ],
  },
  {
    id: 'perimetre',
    title: '15. Périmètre et mise à jour du guide',
    blocks: [
      { type: 'p', text: 'Ce guide décrit le dépôt GitHub CHAFAI802/dental_clinic, branche main, examiné le 20 novembre 2026. Il ne constitue pas une inspection en direct de la production, de sa base de données ou des comptes réels. Les catalogues, tarifs, méthodes de paiement, horaires, modèles approuvés et comptes actifs dépendent des paramètres de chaque installation.' },
      { type: 'p', text: 'Certaines fonctions sont présentes dans l’API mais leur écran utilisateur complet n’est pas encore intégré. Elles sont signalées dans les sections correspondantes afin de ne pas présenter une fonction backend comme une procédure disponible à tous les employés.' },
      { type: 'p', text: 'La documentation doit être revue lorsque les écrans, permissions ou règles métier évoluent. Avant diffusion officielle au personnel, effectuer une recette sur l’environnement de test avec les rôles et paramètres réellement utilisés par la clinique.' },
    ],
  },
]

function GuideBlock({ block }) {
  if (block.type === 'p') return <p>{block.text}</p>
  if (block.type === 'h') return <h3>{block.text}</h3>
  if (block.type === 'callout') return <div className="documentation-callout">{block.text}</div>

  if (block.type === 'steps') {
    return (
      <ol className="documentation-list">
        {block.items.map((item) => <li key={item}>{item}</li>)}
      </ol>
    )
  }

  if (block.type === 'table') {
    return (
      <div className="table-shell documentation-table-shell">
        <table className="documentation-table">
          <thead>
            <tr>{block.headers.map((header) => <th key={header}>{header}</th>)}</tr>
          </thead>
          <tbody>
            {block.rows.map((row) => (
              <tr key={row[0]}>
                {row.map((cell, index) => <td key={`${row[0]}-${index}`}>{cell}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return null
}


function AdminGuideBlock({ block }) {
  if (block.type === 'paragraph') {
    return <p>{block.text}</p>
  }

  if (block.type === 'note') {
    return (
      <div className="documentation-callout">
        {block.text}
      </div>
    )
  }

  if (block.type === 'list') {
    return (
      <ul className="documentation-list">
        {block.items.map((item, index) => (
          <li key={`${index}-${item}`}>{item}</li>
        ))}
      </ul>
    )
  }

  return null
}

function DocumentationPage() {
  const { user } = useAuth()

  const canViewAdminGuide = [
    'super_admin',
    'administrator',
  ].includes(user?.role)

  const [adminGuide, setAdminGuide] = useState(null)
  const [adminGuideLoading, setAdminGuideLoading] = useState(false)
  const [adminGuideError, setAdminGuideError] = useState('')

  const [isDownloading, setIsDownloading] = useState('')
  const [downloadError, setDownloadError] = useState('')


  useEffect(() => {
    if (!canViewAdminGuide) {
      setAdminGuide(null)
      setAdminGuideError('')
      setAdminGuideLoading(false)
      return
    }

    let cancelled = false

    const loadAdminGuide = async () => {
      setAdminGuideLoading(true)
      setAdminGuideError('')

      try {
        const data = await apiGet('/admin-guide/')

        if (!cancelled) {
          setAdminGuide(data)
        }
      } catch (error) {
        if (!cancelled) {
          setAdminGuideError(
            error?.message || 'Impossible de charger le guide administrateur.',
          )
        }
      } finally {
        if (!cancelled) {
          setAdminGuideLoading(false)
        }
      }
    }

    loadAdminGuide()

    return () => {
      cancelled = true
    }
  }, [canViewAdminGuide])

  const downloadDocument = async (format) => {
    const fileConfig = DOCUMENTS[format]
    if (!fileConfig) return

    setIsDownloading(format)
    setDownloadError('')

    try {
      const { blob, filename } = await apiDownload(fileConfig.endpoint)
      const objectUrl = URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = objectUrl
      link.download = filename || fileConfig.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
    } catch (error) {
      setDownloadError(error?.message || `Impossible de télécharger le document ${fileConfig.label}.`)
    } finally {
      setIsDownloading('')
    }
  }

  return (
    <section className="documentation-page">
      <div className="dashboard-page-header documentation-header">
        <div>
          <h2>Guide utilisateur Dental Clinic</h2>
          <p>
            Retrouvez les procédures et les règles métier de l’application.
            Le contenu est consultable directement dans le navigateur.
          </p>
        </div>
        <div className="documentation-actions">
          <button
            type="button"
            className="btn"
            onClick={() => downloadDocument('pdf')}
            disabled={Boolean(isDownloading)}
          >
            {isDownloading === 'pdf' ? 'Préparation…' : 'Télécharger le PDF'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => downloadDocument('docx')}
            disabled={Boolean(isDownloading)}
          >
            {isDownloading === 'docx' ? 'Préparation…' : 'Télécharger le Word'}
          </button>
        </div>
      </div>

      {downloadError && <p className="error-text" role="alert">{downloadError}</p>}

      <div className="documentation-layout">
        <aside className="documentation-toc" aria-label="Sommaire du guide">
          <h3>Sommaire</h3>
          <nav>
            {GUIDE_SECTIONS.map((section) => (
              <a key={section.id} href={`#${section.id}`}>{section.title}</a>
            ))}
          </nav>
        </aside>

        <article className="documentation-article">
          <div className="documentation-intro">
            <p className="documentation-eyebrow">MANUEL UTILISATEUR · VERSION 1.0</p>
            <h1>Utiliser Dental Clinic</h1>
            <p>
              Ce guide s’adresse aux membres de l’équipe de la clinique. Il décrit
              les parcours disponibles et précise les contrôles automatiques qui
              protègent les dossiers et les opérations financières.
            </p>
            <p className="documentation-meta">Référence du code : CHAFAI802/dental_clinic · 20 novembre 2026</p>
          </div>

          {GUIDE_SECTIONS.map((section) => (
            <section className="documentation-section" id={section.id} key={section.id}>
              <h2>{section.title}</h2>
              {section.blocks.map((block, index) => (
                <GuideBlock block={block} key={`${section.id}-${index}`} />
              ))}
            </section>
          ))}

          <div className="documentation-endnote">
            <strong>Fin du guide.</strong> Pour une opération refusée ou un résultat inattendu,
            relever le message affiché et contacter le responsable de la clinique ou le support.
          </div>
        </article>
      </div>

      {canViewAdminGuide && (
        <div className="documentation-admin">
          {adminGuideLoading && (
            <p role="status">Chargement du guide administrateur…</p>
          )}

          {adminGuideError && (
            <p className="error-text" role="alert">
              {adminGuideError}
            </p>
          )}

          {adminGuide && (
            <>
              <div className="dashboard-page-header">
                <div>
                  <h2>Guide administrateur</h2>
                  <p>
                    Documentation réservée aux administrateurs et
                    super administrateurs.
                  </p>
                </div>
              </div>

              <div className="documentation-layout">
                <aside
                  className="documentation-toc"
                  aria-label="Sommaire du guide administrateur"
                >
                  <h3>Sommaire administrateur</h3>

                  <nav>
                    {adminGuide.sections.map((section) => (
                      <a
                        key={section.id}
                        href={`#admin-${section.id}`}
                      >
                        {section.title}
                      </a>
                    ))}
                  </nav>
                </aside>

                <article className="documentation-article">
                  <div className="documentation-intro">
                    <p className="documentation-eyebrow">
                      MANUEL ADMINISTRATEUR · VERSION {adminGuide.version}
                    </p>

                    <h1>{adminGuide.title}</h1>

                    <p>
                      Ce guide décrit les responsabilités administratives,
                      les paramètres métier et les contrôles à effectuer
                      dans Dental Clinic.
                    </p>
                  </div>

                  {adminGuide.sections.map((section) => (
                    <section
                      className="documentation-section"
                      id={`admin-${section.id}`}
                      key={section.id}
                    >
                      <h2>{section.title}</h2>

                      {section.blocks.map((block, index) => (
                        <AdminGuideBlock
                          block={block}
                          key={`${section.id}-${index}`}
                        />
                      ))}
                    </section>
                  ))}

                  <div className="documentation-endnote">
                    <strong>Fin du guide administrateur.</strong>
                    Les droits effectifs restent déterminés par les
                    permissions vérifiées côté serveur.
                  </div>
                </article>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default DocumentationPage
