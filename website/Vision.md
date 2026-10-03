# Website — Vision et notes d’architecture

## Objectif

L'application `website` doit regrouper la configuration permettant à chaque clinique de personnaliser et administrer son site et son fonctionnement sans modifier le code de l'application.

L'objectif est de rendre la clinique **configurable, dynamique et indépendante** au niveau de sa configuration.

## Configuration envisagée

### Identité de la clinique

* nom de la clinique ;
* logo ;
* coordonnées ;
* informations publiques ;
* autres informations d'identité.

### Horaires et disponibilité

* configuration des jours de travail ;
* configuration des plages horaires ;
* paramètres liés à la réservation ;
* les créneaux disponibles seront calculés à partir de cette configuration et des rendez-vous existants.

### Gestion du staff

* ajouter un membre du staff ;
* modifier sa configuration ;
* désactiver/supprimer selon les règles du domaine.

Le modèle `User` reste la responsabilité de `accounts`. `website` ne doit pas créer un deuxième système d'utilisateurs.

### Gestion des pages du site

* ajouter une page ;
* modifier une page ;
* publier/dépublier une page ;
* supprimer une page.

### Apparence

* mode clair ;
* mode sombre ;
* logo ;
* thème et autres paramètres visuels configurables.

### Autres paramètres

Les autres paramètres qui doivent être configurables par l'administrateur seront identifiés progressivement pendant l'audit des différentes applications.

## Principe d'architecture

`website` possède la **configuration**, mais ne doit pas devenir propriétaire des domaines métier des autres applications.

Exemples :

* `accounts` → utilisateurs et authentification ;
* `patients` → patients ;
* `appointments` → rendez-vous ;
* `billing` → facturation ;
* `website` → configuration du site et de la clinique.

## Horaires et créneaux

Aucun mécanisme de configuration des horaires ou de créneaux n'existe actuellement.

À prévoir lors du chantier `website` :

```text
Configuration des horaires
          ↓
créneaux théoriques
          ↓
rendez-vous existants
          ↓
créneaux disponibles
          ↓
GET /crenaux/
```

`Appointment.start_at`, `Appointment.end_at` et `Appointment.status` pourront être utilisés pour déterminer les périodes déjà occupées.

Ne pas modifier `appointments` maintenant pour implémenter cette fonctionnalité. Le sujet sera repris lors du chantier `website`.

## Décision actuelle

`website` sera traité plus tard comme une application de configuration globale.

Pendant l'audit des autres applications, les éléments actuellement codés en dur mais qui pourraient devenir configurables devront être identifiés et notés pour le futur chantier `website`.
