# Plan directeur du moteur documentaire

## État

**Statut : préparation en cours.** L’intégration Django reste bloquée jusqu’à validation complète du prototype DOCX et approbation explicite de la conception.

Ce document constitue la référence de planification documentaire pour le projet Dental Clinic. Il est un document de planification uniquement : aucune modification de code applicatif ni de migration n’est prévue dans cette phase.

Les principes de direction sont les suivants :

- le moteur documentaire reste générique et ne dépend pas d’un seul flux métier ;
- les données métier restent dans leurs modules de responsabilité (patient, prescription, billing, etc.) ;
- le backend documentaire demeure concentré dans `documents/` ;
- une seule configuration est la source de vérité pour le rendu documentaire ;
- le moteur doit résoudre les données nécessaires au moment du rendu, sans dupliquer les informations de base ;
- `docxtpl` reste le moteur candidat : ses fonctions de base sont validées dans le prototype isolé, mais la validation visuelle et l’écart d’environnement local/Docker restent à traiter.

---

## Phase 01 — Périmètre et contraintes

### Objectif
Définir clairement les limites du moteur documentaire et protéger le reste du système des dépendances de rendu.

### Contraintes validées

1. Le moteur documentaire ne doit pas stocker ou dupliquer les données historiques métier déjà gérées ailleurs.
2. Les objets métier restent propriétaires de leurs données.
3. Les documents doivent référencer des contextes de rendu calculés à partir des objets métier, pas des copies locales.
4. Les modèles de `documents/` ne doivent pas être utilisés pour gérer de la logique médicale ou financière qui appartient à d’autres modules.
5. Les fichiers de génération doivent être traités comme des artefacts de document, pas comme des bases de données de vérité.

### Règles d’alignement

- `documents/` : modèles, templates, contexte de génération, validation, stockage privé des artefacts DOCX et métadonnées documentaires ; l’export PDF est une évolution ultérieure.
- `prescriptions/` : données métier de prescription, règles médicales, historiques et validations fonctionnelles.
- `patients/` : données du patient, identités, contacts, contextes de dossiers.
- `accounts/` : comptes, rôles, contexte utilisateur.
- `billing/` : facturation, devis, paiements, montants.

---

## Phase 02 — Décisions d’architecture arrêtées

### Décision 1 — séparation des responsabilités
Le moteur documentaire n’est pas un système de données métier supplémentaire. Il est un mécanisme de sérialisation et de rendu à partir d’un contexte de génération.

### Décision 2 — moteur de rendu générique
Le moteur doit accepter un template, un contexte, et des règles de validation de variables. Il ne doit pas incorporer de logique métier spécifique à une spécialité ou à un type de document.

### Décision 3 — validation des variables au moment du rendu
Les champs requis doivent être évalués avant génération. Les valeurs manquantes doivent provoquer une erreur explicite et ne doivent pas produire un document partiellement vide.

### Décision 4 — document non redondant
Le document final peut être stocké sous forme de fichier généré, mais le contenu technique du document ne doit pas être traité comme une duplication de la source métier.

### Décision 5 — migration existante conservée
La migration `0003` liée aux modèles documentaires est déjà appliquée. Il ne faut pas la réécrire ni la remodeler tant que le contrat fonctionnel n’est pas stabilisé.

---

## Phase 03 — Modèle de données cible

### 3.1. Objectif
Transformer les décisions de Phase 02 en spécification de travail du modèle de données cible pour les documents. La spécification ne devient définitive qu’après les vérifications techniques et une validation explicite.

### 3.2. Modèles fonctionnels retenus à ce stade

Cette cible est une spécification de travail, pas un schéma Django approuvé. Elle ne préjuge pas des noms de champs, des migrations ni de l’organisation physique du stockage.

#### DocumentType
Représente la catégorie documentaire ou la famille de document.

Attributs attendus :

- `code`: identifiant technique unique, type slug ;
- `name`: libellé lisible ;
- `description`: description métier ;
- `is_active`: activation de la catégorie.

Rôle :

- classe de document (prescription, certificat, compte rendu, lettre, etc.) ;
- point d’entrée pour les règles de type et les templates associés.

#### DocumentTemplate
Représente le template générique utilisé pour produire un document d’un type donné. Une configuration unique du template est la source de vérité : elle référence le fichier DOCX et définit le contrat des variables, leur caractère requis ou facultatif, leurs types et les règles propres aux listes. Le DOCX porte la mise en page, le texte et les occurrences de placeholders ; ces occurrences ne constituent pas un second catalogue de variables.

Attributs attendus :

- `code`: identifiant unique du template ;
- `document_type`: lien vers le type de document ;
- `name`: nom affiché ;
- `description`: description fonctionnelle ;
- une configuration unique comprenant la référence vers le fichier DOCX et le contrat des variables ;
- `is_active`: activation du template ;
- `created_by`: créateur ou responsable du template.

Rôle :

- définir le modèle de document technique ;
- être l’unique point d’administration du template et de son contrat de génération ;
- éviter de recopier dans des modèles séparés les placeholders déjà présents dans le DOCX.

#### DocumentTemplateVersion — existant et transition, hors cible
La décision fonctionnelle cible est de ne pas conserver le versionnement applicatif des templates. `DocumentTemplateVersion` n’est donc pas un modèle cible retenu.

État existant : le modèle et sa table ont été introduits par la migration `0003`, déjà appliquée. L’historique de migration doit rester intact.

Transition technique : le retrait éventuel du modèle, de sa table et des références associées doit faire l’objet d’un chantier distinct. Il nécessite d’abord l’inventaire des références dans le code, les données, les API et les usages opérationnels, puis une stratégie de transition et des migrations nouvelles si nécessaire. Aucune suppression ni réécriture n’est autorisée dans cette phase.

#### Document
Représente une instance documentaire produite à partir d’un template et d’un contexte métier résolu.

Contrat fonctionnel attendu :

- référence au patient concerné et à l’utilisateur créateur, lorsque ces liens sont applicables ;
- référence au type et au template utilisés ;
- titre et état documentaire ;
- référence aux fichiers générés, conservés comme artefacts ;
- traçabilité du rendu suffisante pour les besoins validés, sans recopier les données métier.

Le format de référence de la première phase est DOCX. La conception fonctionnelle doit permettre d’ajouter ultérieurement un export PDF, sans ajouter dès maintenant de champs ou de dépendances non justifiés. Le DOCX généré est l’artefact principal de cette première phase ; un éventuel PDF sera un export dérivé.

Le contrat ne retient pas de champ générique `content` : il pourrait désigner une définition de template, un contexte, un texte métier ou du texte extrait, qui sont des notions distinctes. La définition technique appartient au template, le contexte est résolu à la génération, et les données métier restent dans leurs modules propriétaires. Le texte extrait n’est pas requis dans le premier périmètre.

Le premier périmètre distingue uniquement un document en brouillon d’un document finalisé. Il ne définit ni signature électronique, ni validation juridique, ni valeur juridique ; une date ou un état ne constitue pas une preuve de signature.

#### Traçabilité et conservation du rendu
Décision de conception proposée pour le premier périmètre : conserver comme métadonnées le type documentaire, la référence stable du template utilisé, la date/heure UTC de génération, le créateur, le patient lié et l’état du document. Une empreinte cryptographique du fichier DOCX source peut être conservée pour vérifier son identité sans introduire de versionnement applicatif.

Le DOCX généré est l’artefact qui préserve exactement le rendu produit. Ne pas persister de copie complète du contexte : elle dupliquerait des données personnelles et médicales. Aucun instantané métier additionnel n’est prévu dans le premier périmètre ; une exigence d’audit ou de reproductibilité devra justifier explicitement tout champ figé supplémentaire, sa finalité, sa conservation et ses permissions d’accès.

#### DocumentSection et DocumentVariable — non retenus comme modèles cibles à ce stade
`docxtpl` permet de porter la composition et les placeholders dans le fichier DOCX. Aucune nécessité fonctionnelle n’a été établie pour maintenir des modèles `DocumentSection` ou `DocumentVariable` en parallèle.

- `DocumentSection` ne sera réintroduit que si une composition dynamique de documents depuis l’interface devient un besoin explicite ; sinon, la composition reste dans le DOCX.
- `DocumentVariable` ne sera réintroduit que si l’administration indépendante des variables et de leurs contraintes est requise ; sinon, le contrat est tenu dans une seule configuration associée au template.
- Les placeholders du DOCX et le contrat ne doivent pas devenir deux catalogues maintenus manuellement. Le contrôle de cohérence doit signaler toute variable présente dans le DOCX mais inconnue du contrat.

#### DocumentAttachment
Représente un fichier joint associé à un document ou à un dossier patient.

Attributs attendus :

- `patient`: patient associé ;
- `document`: document associé si applicable ;
- `uploaded_by`: utilisateur ayant téléversé le fichier ;
- `file`: fichier physique ;
- `file_type`: type MIME ou catégorie de fichier ;
- `description`: description ;
- `is_confidential`: sensibilité.

Rôle :

- gérer les pièces jointes documentaires ;
- conserver les annexes associées au dossier patient ;
- ne pas être confondu avec le contenu du document final.

### 3.3. Règles de contexte de génération
Le moteur doit résoudre les valeurs au moment du rendu depuis les objets métier et les contextes du dossier patient.

Contexte attendu :

- données patient ;
- données praticien ;
- données de cabinet ou de structure ;
- liste de médicaments ou de lignes de prescription ;
- date de génération et état documentaire (brouillon ou finalisé).

Règle de sécurité : il ne faut pas dupliquer les mêmes données en base dans plusieurs modules. Le moteur reçoit un contexte de génération calculé à partir des objets sources.

Avant toute intégration, établir une matrice par type de document précisant les données nécessaires et leur source propriétaire. Pour chaque champ ou collection, la matrice doit indiquer : source métier, chemin ou règle de résolution, caractère requis ou facultatif, type attendu et règle de validation. Par exemple, une ordonnance peut nécessiter les informations d’identité du patient et du praticien ainsi que les lignes et posologies de la prescription ; ces données restent la propriété de `patients/`, `staff/` ou `accounts/`, et `prescriptions/`. Les valeurs exactes requises sont à confirmer avec les règles métier de chaque document.

### 3.4. Permissions et accès aux fichiers
Les règles d’accès doivent être définies avant l’approbation du contrat, au minimum pour la génération, la consultation et le téléchargement. Une matrice par action et type de document doit préciser les rôles autorisés, les contraintes liées au patient et la séparation entre les permissions d’édition des templates et celles d’accès aux documents générés.

Les fichiers générés contiennent des données sensibles. Le stockage doit être privé, non accessible par URL publique ou chemin devinable. Chaque téléchargement doit passer par un contrôle d’autorisation côté serveur portant sur l’utilisateur et le document concerné. La spécification doit également définir la politique de rétention, de suppression, de sauvegarde et, selon les capacités de l’environnement, de chiffrement au repos. Ces exigences ne déterminent pas encore un fournisseur ou un champ Django particulier.

### 3.5. Cibles de responsabilité métier

- `documents/` : templates DOCX, contrat unique des variables, validation, rendu et stockage des artefacts.
- `prescriptions/` : produit la commande médicale, les lignes de traitement et la donnée de prescription.
- `patients/` : source fiable des informations du patient.
- `staff/` ou `accounts/` : source fiable des informations du praticien et des rôles.

---

## Phase 04 — Contrat technique du moteur et validation DOCX

### 4.1. Moteur candidat retenu
Le moteur candidat retenu est `docxtpl`.

### 4.2. Critères techniques validés
Le prototype hors projet a validé les points suivants :

- remplacement correct des variables simples ;
- génération de listes répétées dans un bloc ;
- support des caractères français et arabes ;
- rendu cohérent de contenu avec accents ;
- validation explicite des champs absents ;
- génération d’un fichier DOCX dans le prototype isolé.

La pagination et les dimensions ne sont pas validées : l’inspection LibreOffice décrite ci-dessous a révélé un défaut bloquant. La génération fonctionnelle rapportée ne doit pas être présentée comme une validation complète du moteur.

### 4.3. Contrat fonctionnel à formaliser avant intégration Django

#### Entrées
- template DOCX ;
- contexte de génération, sous forme de dictionnaire ou d’objet sérialisable ;
- règles de validation de variables ;
- chemin de sortie attendu.

#### Sorties
- document DOCX généré ;
- validation réussie ou échec explicite ;
- logs d’erreurs de contexte manquant ;
- pas d’export PDF dans le premier périmètre ; un export PDF dérivé pourra être défini ultérieurement sans changer le DOCX de référence.

#### Règles de validation
Le contrat du template est la source unique des contraintes fonctionnelles. Le moteur générique applique ces contraintes sans imposer les mêmes règles à tous les types documentaires.

- Variable requise absente du contexte : erreur explicite, génération bloquée.
- Variable présente dans le DOCX mais inconnue du contrat : erreur explicite, génération bloquée jusqu’à clarification du template ou de son contrat.
- Variable facultative non renseignée : appliquer le comportement déclaré dans le contrat ; le comportement par défaut doit être explicite, par exemple chaîne vide, valeur par défaut ou omission d’un bloc conditionnel. Ne jamais la confondre avec une variable inconnue.
- Liste répétable vide : autorisée ou refusée selon la règle définie pour le type de document. Le moteur générique ne la rejette pas systématiquement.
- Valeur ou structure incompatible avec le type déclaré : erreur explicite avant le rendu.

Le prototype a démontré le remplacement de variables, le rendu d’une liste et le signalement d’un champ manquant. Il ne démontre pas encore l’ensemble de ces distinctions ; elles constituent le contrat à spécifier et tester avant l’intégration.

### 4.4. Contrat de cohérence générique
Le moteur documentaire doit respecter les principes suivants :

1. variable = donnée résolue dans le contexte et déclarée dans le contrat unique du template ;
2. structure et mise en page = portées par le fichier DOCX ;
3. template = configuration unique, source de vérité, qui référence le DOCX et contient le contrat ;
4. document = instance produite à partir du template et du contexte ;
5. données métier = source de vérité ;
6. contexte = résolution dynamique, jamais copie persistante de toutes les données sources.

### 4.5. Vérification visuelle requise
Avant intégration dans le backend Django, le document doit être ouvert dans un logiciel compatible (Microsoft Word ou LibreOffice) et vérifié sur :

- sens de lecture et alignement arabe ;
- retours à la ligne ;
- pagination ;
- gestion des blocs de médicaments ;
- aperçu avant impression ;
- absence de débordement ou de colonnes cassées.

La première conversion a révélé que le prototype utilisait des twips comme valeurs EMU ; après correction du seul prototype temporaire, LibreOffice produit une page A4 (`595.304 x 841.89 pt`). Les accents et les deux lignes de médicaments sont visibles, sans débordement, et les caractères arabes s’affichent. Toutefois, le paragraphe arabe reste visuellement aligné à gauche malgré les propriétés OOXML RTL et alignement droit présentes ; le sens de lecture/alignement n’est donc que partiellement validé. Le contrôle Word ou LibreOffice devra confirmer ce point et les résultats devront être consignés. Le DOCX tient sur une page et son aperçu avant impression est exploitable.

### 4.6. Contrôle préalable des templates DOCX
Avant qu’un template soit activé ou utilisé, un contrôle technique doit confirmer :

- que le fichier est un DOCX lisible et structurellement valide ;
- que les variables détectées dans le document correspondent au contrat unique : variables inconnues rejetées, variables requises déclarées, facultatives et types cohérents ;
- que les structures répétables sont syntaxiquement valides et que leurs collections et champs sont couverts par le contrat ;
- que les erreurs de parsing, variables ou structures incompatibles sont signalées avant génération, sans laisser un fichier de sortie partiel.

Le contrôle doit tenir compte de la structure XML Word et des placeholders susceptibles d’être répartis entre plusieurs runs. La méthode technique de détection reste à choisir et à tester avec les modèles de référence. Ce précontrôle du fichier est distinct des permissions d’accès ou de téléchargement, qui sont définies en Phase 03.

### 4.7. Diagnostic des environnements Python et migrations
Les versions relevées en lecture seule sont :

- environnement du projet : Python `3.12.3`, Django `6.0.6` ;
- conteneur `web` : Python `3.12.13`, Django `6.1.2`.

La divergence du graphe est confirmée. Le répertoire `django/contrib/auth/migrations` du venv local ne contient que `0001_initial.py`, alors que la migration `accounts.0001_initial` dépend de `auth.0012_alter_user_first_name_max_length`. Le chargement local via `MigrationLoader(None)` échoue donc avec `NodeNotFoundError` pour ce parent absent. Dans Docker, le graphe se charge ; les migrations `auth.0001` à `auth.0012` sont présentes, et `showmigrations --plan` rapporte `documents.0003` comme appliquée.

À distinguer de cette incohérence : `showmigrations --plan` lancé depuis l’hôte local ne peut pas résoudre le nom réseau Docker `db`. Cette erreur de connectivité ne constitue pas l’origine du `NodeNotFoundError` local. Aucune dépendance, migration ou donnée n’a été modifiée pendant ce diagnostic ; la remise en cohérence de l’environnement local reste hors de cette phase.

---

## Phase 05 — Plan de mise en œuvre Django (après validation explicite)

### Objectif
L’intégration Django ne démarrera qu’après validation explicite de la spécification consolidée. Les variables, la liste répétable et le signalement d’un champ manquant ont été validés dans le prototype. Le document tient maintenant sur une page A4, mais la validation visuelle de l’alignement RTL reste partielle. L’écart d’environnement est diagnostiqué mais non corrigé. Aucune étape ci-dessous n’autorise à elle seule une modification du dépôt.

### Étapes prévues

1. Confirmer dans Word ou LibreOffice le sens de lecture et l’alignement RTL du DOCX A4 généré ; consigner le résultat. Les dimensions sont corrigées dans le prototype isolé et ne doivent pas être confondues avec une validation de l’alignement.
2. Diagnostic effectué : Python/Django local `3.12.3/6.0.6`, Docker `3.12.13/6.1.2` ; l’installation locale ne possède pas `auth.0012`, nécessaire à `accounts.0001`, alors que le graphe Docker est cohérent. Documenter une configuration reproductible sans changer les dépendances ni les migrations pendant cette phase.
3. Finaliser la spécification des modèles cibles, de la source de vérité du template, des métadonnées de traçabilité et du stockage sécurisé des fichiers.
4. Formaliser, pour chaque type de document, les données requises, leur source, les règles de génération et de validation, ainsi que les permissions de génération et de téléchargement.
5. Définir les contrôles préalables d’intégrité et de cohérence des templates DOCX.
6. Auditer les références et dépendances au versionnement existant, puis préparer séparément sa transition sans réécrire `0003`.
7. Effectuer une revue finale du plan après les vérifications techniques et intégrer les constats.
8. Soumettre explicitement la spécification consolidée à validation ; l’approbation doit précéder tout changement applicatif.
9. Après approbation seulement, implémenter progressivement le service de rendu et ses tests dans `documents/`.

### Règles de sécurité de mise en œuvre

- aucune réécriture de migration déjà appliquée ;
- aucune modification des dépendances du projet sans validation explicite ;
- aucune duplication des tables métier dans `documents/` ;
- aucune génération sans contexte résolu ;
- aucune logique médicale dans le moteur documentaire ;
- aucun accès public direct aux fichiers générés ;
- aucun téléchargement sans contrôle d’autorisation côté serveur ;
- aucune modification applicative avant validation explicite de la spécification.

---

## Phase 06 — Validation de sortie et critères d’acceptation

### Critères d’acceptation

- le moteur documentaire est générique ;
- le rendu dépend du contexte, pas d’une base interne de données redondantes ;
- les fonctions de base du prototype sont validées et la mise en page est vérifiée séparément avant intégration ;
- le rendu, y compris l’alignement RTL, est validé visuellement par Word ou LibreOffice ;
- l’environnement Python est stabilisé avant intégration ;
- la migration existante est préservée ;
- le backend documentaire reste conforme au périmètre `documents/` ;
- `DocumentTemplateVersion`, `DocumentSection` et `DocumentVariable` ne sont pas présentés comme des modèles cibles retenus ;
- le document n’implique pas la gestion d’une signature électronique ou d’une valeur juridique ;
- les données et leurs sources sont spécifiées par type de document ;
- les permissions de génération et de téléchargement sont définies ;
- le stockage des fichiers est privé et sa politique de cycle de vie est documentée ;
- les métadonnées de traçabilité et la politique de conservation du rendu sont définies ;
- les templates DOCX passent un contrôle préalable d’intégrité et de cohérence avec leur contrat.

### Sortie attendue
Le projet passe en phase d’intégration Django uniquement après vérification de :

- environnement Python ;
- validation visuelle du document ;
- diagnostic comparatif des environnements Python et analyse de la divergence de migrations ;
- contrat de contexte de génération ;
- matrice des permissions et contrat de stockage sécurisé ;
- séparation claire des responsabilités métiers et documentaire.

---

## Décision de suivi immédiate

### Recommandation retenue
Les fonctions DOCX de base sont validées et le prototype produit maintenant une page A4, mais le contrôle RTL reste à confirmer. `docxtpl` reste le moteur candidat, sans validation visuelle complète. L’écart local/Docker est diagnostiqué sans correction. Le plan reste un document de travail jusqu’à la revue finale et l’approbation explicite de la conception.

### Prochaines étapes, dans l’ordre

#### Étape A — Confirmer le rendu visuel du prototype
Le prototype isolé a été corrigé : la conversion LibreOffice produit maintenant une page A4. Le premier rendu RTL affiche les glyphes arabes, mais le paragraphe apparaît aligné à gauche malgré les propriétés RTL et alignement droit du DOCX. Confirmer ce résultat dans Word ou LibreOffice et consigner explicitement si l’alignement est acceptable ou s’il reste un défaut :

- l’affichage des caractères arabes et leur sens de lecture ;
- les retours à la ligne et la pagination ;
- l’absence de débordement dans la liste des médicaments ;
- le rendu à l’impression ou en aperçu avant impression.

Les accents, les retours à la ligne, les deux médicaments et la pagination A4 ont été vérifiés dans l’aperçu PDF ; aucun débordement n’est visible. Le diagnostic local/Docker est également effectué et consigné en Phase 04.7. Aucun changement Django n’est autorisé pour résoudre ou contourner le problème RTL.

#### Étape B — Stabiliser la décision d’environnement
Le diagnostic est consigné en Phase 04.7. La divergence provient de l’installation locale incomplète de Django, distincte de l’impossibilité de résoudre `db` depuis l’hôte. Une configuration reproductible reste à établir séparément ; aucune correction de dépendance ou migration n’est autorisée à ce stade.

#### Étape C — Clarifier les modèles cibles et la source de vérité
Confirmer que le versionnement applicatif, `DocumentSection` et `DocumentVariable` sont hors cible initiale, et préciser la définition unique du template et de ses variables. Définir le stockage du DOCX généré et l’extension éventuelle aux exports PDF sans ajouter prématurément de champs ou de dépendances.

#### Étape D — Formaliser les contrats métier et d’accès
Pour chaque type de document, définir les données attendues, leurs sources et leurs règles de validation. Distinguer les variables requises, inconnues et facultatives, préciser le comportement des champs facultatifs et fixer la règle de liste vide. Définir également les rôles autorisés à générer et télécharger chaque document et les contrôles d’accès par patient. Maintenir les responsabilités suivantes :

- `documents/`: configuration du template, modèles DOCX, validation, génération et stockage des fichiers ;
- `prescriptions/`: données métier de l’ordonnance et règles médicales ;
- `contexte de génération`: informations du patient, du praticien, des médicaments et des posologies, résolues depuis leurs sources sans duplication persistante.

Documenter les contrôles d’accès au stockage, la politique de rétention et de suppression, les sauvegardes et les mesures de protection au repos applicables. Les fichiers ne doivent pas être accessibles publiquement et tout téléchargement doit être autorisé côté serveur.

#### Étape E — Auditer la transition du versionnement existant
Inventorier les références et dépendances de `DocumentTemplateVersion`, puis préparer une stratégie de retrait distincte. Préserver l’historique de migration et ne pas réécrire la migration `0003` déjà appliquée.

#### Étape F — Revoir le plan après les vérifications
Après la vérification visuelle du DOCX et le diagnostic Python/Docker, réexaminer le plan, intégrer les constats et vérifier la cohérence de l’ensemble, notamment les données par type, permissions, stockage, métadonnées de traçabilité, précontrôle des templates et transition de `DocumentTemplateVersion`.

#### Étape G — Soumettre la spécification à validation
Le plan demeure un document de travail jusqu’à approbation explicite. Aucune implémentation backend ne commence avant cette approbation.

#### Étape H — Implémenter progressivement le backend
Cette étape est conditionnelle à la validation explicite. Elle devra rester concentrée dans `documents/` pour le moteur documentaire et respecter la propriété des données métier par leurs applications.

### Conclusion
Les fonctions DOCX de base sont validées et les dimensions corrigées du prototype donnent une page A4 avec accents et liste de médicaments visibles sans débordement. Le sens de lecture et l’alignement RTL restent à confirmer. L’écart Python/Django et l’absence locale de `auth.0012` sont diagnostiqués, sans modification d’environnement ou de migration. La revue finale du plan doit intégrer la décision RTL et les choix de traçabilité, conservation, prévalidation et stockage privé avant de demander l’approbation explicite. L’intégration Django demeure bloquée jusque-là.

Le dépôt Django reste intact jusqu’à ce que ces vérifications et le contrat fonctionnel soient établis.
