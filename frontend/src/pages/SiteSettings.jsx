import { useState } from 'react'
import { Link } from 'react-router-dom'

import Icon from '../components/common/Icon.jsx'
import { useSiteConfig } from '../context/SiteConfigContext.jsx'
import { SECTION_LABELS, MEDIA_SECTIONS } from '../config/siteConfig.js'

const PANELS = [
  { id: 'identity', label: 'Identité & thème' },
  { id: 'hero', label: 'Bandeau Hero' },
  { id: 'navigation', label: 'Navigation' },
  { id: 'sections', label: 'Sections de l’accueil' },
  { id: 'content', label: 'Contenus textuels' },
  { id: 'images', label: 'Images' },
  { id: 'contact', label: 'Contact & pied de page' },
]

const THEME_COLORS = [
  ['primary', 'Couleur principale'],
  ['primaryHover', 'Principale (survol)'],
  ['secondary', 'Couleur secondaire'],
  ['accent', 'Couleur d’accent'],
  ['background', 'Fond du site'],
  ['surface', 'Surface / cartes'],
  ['text', 'Texte'],
  ['textMuted', 'Texte secondaire'],
  ['border', 'Bordures'],
]

function Field({ label, value, onChange, type = 'text', placeholder = '' }) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <input
        type={type}
        value={value ?? ''}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}

function TextAreaField({ label, value, onChange, rows = 4 }) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <textarea rows={rows} value={value ?? ''} onChange={(event) => onChange(event.target.value)} />
    </div>
  )
}

function ColorField({ label, value, onChange }) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <div className="settings-color">
        <input type="color" value={value || '#000000'} onChange={(event) => onChange(event.target.value)} />
        <code>{value}</code>
      </div>
    </div>
  )
}

/**
 * Éditeur de liste générique (navigation, points du hero, horaires…).
 * `columns` décrit les champs de chaque élément.
 */
function ListEditor({ items = [], columns, onChange, addLabel = '+ Ajouter un élément' }) {
  const updateAt = (index, key, value) => {
    onChange(items.map((item, i) => (i === index ? { ...item, [key]: value } : item)))
  }

  const add = () => {
    const blank = Object.fromEntries(columns.map((column) => [column.key, '']))
    onChange([...items, blank])
  }

  const remove = (index) => {
    onChange(items.filter((_, i) => i !== index))
  }

  return (
    <div className="settings-list-editor">
      {items.map((item, index) => (
        <div className="settings-list-item" key={`${columns[0].key}-${index}`}>
          <div className="settings-fields">
            {columns.map((column) => (
              <Field
                key={column.key}
                label={column.label}
                value={item[column.key]}
                onChange={(value) => updateAt(index, column.key, value)}
              />
            ))}
          </div>

          <button
            type="button"
            className="settings-icon-btn"
            onClick={() => remove(index)}
            aria-label="Supprimer"
            title="Supprimer"
          >
            <Icon name="close" />
          </button>
        </div>
      ))}

      <div>
        <button type="button" className="btn btn-outline btn-sm" onClick={add}>
          {addLabel}
        </button>
      </div>
    </div>
  )
}

/**
 * Zone de paramétrage du site (/settings/site).
 *
 * Frontend uniquement : les modifications sont appliquées en direct puis
 * stockées dans le navigateur. Quand une API d'administration du site
 * existera, `saveConfig`/`loadSiteConfig` basculeront sur cette API sans
 * toucher aux composants ni au backend actuel.
 */
function SiteSettings() {
  const { config, updateConfig, saveConfig, resetConfig } = useSiteConfig()
  const [activePanel, setActivePanel] = useState(PANELS[0].id)
  const [savedMessage, setSavedMessage] = useState('')

  const handleSave = () => {
    saveConfig(config)
    setSavedMessage('Configuration enregistrée dans ce navigateur.')
    window.setTimeout(() => setSavedMessage(''), 3000)
  }

  const handleReset = () => {
    if (window.confirm('Rétablir la configuration par défaut du site ?')) {
      resetConfig()
      setSavedMessage('Configuration par défaut restaurée.')
      window.setTimeout(() => setSavedMessage(''), 3000)
    }
  }

  const moveSection = (index, direction) => {
    const sections = [...(config.home?.sections || [])]
    const target = index + direction
    if (target < 0 || target >= sections.length) return
    ;[sections[index], sections[target]] = [sections[target], sections[index]]
    updateConfig({ home: { sections } })
  }

  const renderIdentity = () => (
    <>
      <div className="settings-card">
        <h2>Identité du cabinet</h2>
        <p>Nom, coordonnées et éléments de marque affichés dans la navbar et le footer.</p>

        <div className="settings-fields">
          <Field
            label="Nom du cabinet"
            value={config.branding.cabinetName}
            onChange={(v) => updateConfig({ branding: { cabinetName: v } })}
          />
          <Field
            label="Nom court (monogramme)"
            value={config.branding.shortName}
            onChange={(v) => updateConfig({ branding: { shortName: v } })}
          />
          <Field
            label="Slogan"
            value={config.branding.tagline}
            onChange={(v) => updateConfig({ branding: { tagline: v } })}
          />
          <Field
            label="Téléphone"
            value={config.branding.phone}
            onChange={(v) => updateConfig({ branding: { phone: v } })}
          />
          <Field
            label="Email"
            type="email"
            value={config.branding.email}
            onChange={(v) => updateConfig({ branding: { email: v } })}
          />
          <Field
            label="Adresse"
            value={config.branding.address}
            onChange={(v) => updateConfig({ branding: { address: v } })}
          />
        </div>
      </div>

      <div className="settings-card">
        <h2>Thème du site</h2>
        <p>
          Ces couleurs sont injectées dans les variables CSS : tout le site (navbar, boutons,
          cartes, footer) se met à jour instantanément.
        </p>

        <div className="settings-preview">
          <span>Exemple</span>
          <button type="button" className="btn btn-accent btn-sm">
            Bouton accent
          </button>
          <button type="button" className="btn btn-light btn-sm">
            Bouton clair
          </button>
        </div>

        <div className="settings-fields">
          {THEME_COLORS.map(([key, label]) => (
            <ColorField
              key={key}
              label={label}
              value={config.branding.theme[key]}
              onChange={(v) => updateConfig({ branding: { theme: { [key]: v } } })}
            />
          ))}
        </div>
      </div>

      <div className="settings-card">
        <h2>Réseaux sociaux</h2>
        <p>Liens affichés dans le footer.</p>
        <ListEditor
          items={config.branding.socials}
          columns={[
            { key: 'label', label: 'Réseau' },
            { key: 'url', label: 'Lien' },
          ]}
          onChange={(socials) => updateConfig({ branding: { socials } })}
        />
      </div>
    </>
  )

  const renderHero = () => (
    <div className="settings-card">
      <h2>Bandeau Hero (accueil)</h2>
      <p>Premier écran de la page d’accueil : accroche, texte et boutons.</p>

      <div className="settings-fields">
        <Field
          label="Sur-titre"
          value={config.hero.eyebrow}
          onChange={(v) => updateConfig({ hero: { eyebrow: v } })}
        />
        <Field
          label="Sous-titre"
          value={config.hero.subtitle}
          onChange={(v) => updateConfig({ hero: { subtitle: v } })}
        />
      </div>

      <div className="settings-fields single">
        <Field
          label="Titre principal"
          value={config.hero.title}
          onChange={(v) => updateConfig({ hero: { title: v } })}
        />
        <TextAreaField
          label="Description"
          value={config.hero.description}
          onChange={(v) => updateConfig({ hero: { description: v } })}
        />
      </div>

      <div className="settings-fields">
        <Field
          label="Bouton principal — texte"
          value={config.hero.primaryButton?.label}
          onChange={(v) => updateConfig({ hero: { primaryButton: { label: v } } })}
        />
        <Field
          label="Bouton principal — lien"
          value={config.hero.primaryButton?.to}
          onChange={(v) => updateConfig({ hero: { primaryButton: { to: v } } })}
        />
        <Field
          label="Bouton secondaire — texte"
          value={config.hero.secondaryButton?.label}
          onChange={(v) => updateConfig({ hero: { secondaryButton: { label: v } } })}
        />
        <Field
          label="Bouton secondaire — lien"
          value={config.hero.secondaryButton?.to}
          onChange={(v) => updateConfig({ hero: { secondaryButton: { to: v } } })}
        />
        <Field
          label="Badge — titre"
          value={config.hero.badge?.title}
          onChange={(v) => updateConfig({ hero: { badge: { title: v } } })}
        />
        <Field
          label="Badge — texte"
          value={config.hero.badge?.text}
          onChange={(v) => updateConfig({ hero: { badge: { text: v } } })}
        />
      </div>

      <div className="settings-fields single">
        <div className="settings-field">
          <label>Points mis en avant (un par ligne)</label>
          <textarea
            rows={3}
            value={(config.hero.points || []).join('\n')}
            onChange={(event) =>
              updateConfig({ hero: { points: event.target.value.split('\n') } })
            }
          />
        </div>
      </div>
    </div>
  )

  const renderNavigation = () => (
    <div className="settings-card">
      <h2>Navigation (navbar)</h2>
      <p>Liens du menu et bouton de prise de rendez-vous.</p>

      <ListEditor
        items={config.nav.links}
        columns={[
          { key: 'label', label: 'Libellé' },
          { key: 'to', label: 'Route (ex. /services)' },
        ]}
        onChange={(links) => updateConfig({ nav: { links } })}
        addLabel="+ Ajouter un lien"
      />

      <div className="settings-fields">
        <Field
          label="Bouton RDV — texte"
          value={config.nav.cta?.label}
          onChange={(v) => updateConfig({ nav: { cta: { label: v } } })}
        />
        <Field
          label="Bouton RDV — lien"
          value={config.nav.cta?.to}
          onChange={(v) => updateConfig({ nav: { cta: { to: v } } })}
        />
      </div>
    </div>
  )

  const renderSections = () => (
    <div className="settings-card">
      <h2>Sections de l’accueil</h2>
      <p>
        Activez, désactivez, réordonnez les sections et changez la disposition des blocs
        image/texte (« image gauche » ou « image droite »).
      </p>

      <div>
        {(config.home?.sections || []).map((section, index) => (
          <div className="settings-section-row" key={section.key}>
            <span className="settings-section-name">
              {SECTION_LABELS[section.key] || section.key}
              <span className="settings-section-meta">#{index + 1}</span>
            </span>

            {MEDIA_SECTIONS.includes(section.key) && (
              <select
                value={section.layout || 'image-left'}
                onChange={(event) =>
                  updateConfig({
                    home: {
                      sections: config.home.sections.map((item, i) =>
                        i === index ? { ...item, layout: event.target.value } : item,
                      ),
                    },
                  })
                }
                aria-label={`Disposition de ${SECTION_LABELS[section.key] || section.key}`}
              >
                <option value="image-left">Image à gauche</option>
                <option value="image-right">Image à droite</option>
              </select>
            )}

            <label className="settings-switch">
              <input
                type="checkbox"
                checked={section.enabled !== false}
                onChange={(event) =>
                  updateConfig({
                    home: {
                      sections: config.home.sections.map((item, i) =>
                        i === index ? { ...item, enabled: event.target.checked } : item,
                      ),
                    },
                  })
                }
              />
              Visible
            </label>

            <button
              type="button"
              className="settings-icon-btn"
              onClick={() => moveSection(index, -1)}
              disabled={index === 0}
              aria-label="Monter la section"
              title="Monter"
            >
              ↑
            </button>
            <button
              type="button"
              className="settings-icon-btn"
              onClick={() => moveSection(index, 1)}
              disabled={index === config.home.sections.length - 1}
              aria-label="Descendre la section"
              title="Descendre"
            >
              ↓
            </button>
          </div>
        ))}
      </div>
    </div>
  )

  const renderContent = () => (
    <>
      <div className="settings-card">
        <h2>Présentation du cabinet</h2>
        <div className="settings-fields">
          <Field
            label="Sur-titre"
            value={config.about.eyebrow}
            onChange={(v) => updateConfig({ about: { eyebrow: v } })}
          />
          <Field
            label="Titre"
            value={config.about.title}
            onChange={(v) => updateConfig({ about: { title: v } })}
          />
        </div>
        <div className="settings-fields single">
          <TextAreaField
            label="Paragraphes (un par ligne)"
            value={(config.about.paragraphs || []).join('\n')}
            onChange={(v) => updateConfig({ about: { paragraphs: v.split('\n') } })}
            rows={5}
          />
        </div>
      </div>

      <div className="settings-card">
        <h2>Sections éditoriales</h2>
        <p>Titres et textes d’introduction de chaque section.</p>

        {[
          ['services', 'Services'],
          ['team', 'Équipe'],
          ['technology', 'Technologies'],
          ['steps', 'Parcours patient'],
          ['testimonials', 'Témoignages'],
          ['info', 'Informations pratiques'],
        ].map(([key, label]) => (
          <div className="settings-fields" key={key}>
            <Field
              label={`${label} — titre`}
              value={config[key]?.title}
              onChange={(v) => updateConfig({ [key]: { title: v } })}
            />
            <Field
              label={`${label} — introduction`}
              value={config[key]?.intro}
              onChange={(v) => updateConfig({ [key]: { intro: v } })}
            />
          </div>
        ))}

        <div className="settings-fields">
          <Field
            label="CTA — titre"
            value={config.cta.title}
            onChange={(v) => updateConfig({ cta: { title: v } })}
          />
          <Field
            label="CTA — texte"
            value={config.cta.text}
            onChange={(v) => updateConfig({ cta: { text: v } })}
          />
        </div>
      </div>

      <div className="settings-card">
        <h2>Services proposés</h2>
        <ListEditor
          items={config.services.items}
          columns={[
            { key: 'title', label: 'Service' },
            { key: 'description', label: 'Description' },
          ]}
          onChange={(items) => updateConfig({ services: { items } })}
          addLabel="+ Ajouter un service"
        />
      </div>

      <div className="settings-card">
        <h2>Équipe</h2>
        <ListEditor
          items={config.team.members}
          columns={[
            { key: 'name', label: 'Nom' },
            { key: 'role', label: 'Fonction' },
            { key: 'description', label: 'Description' },
            { key: 'photo', label: 'Photo (URL ou /images/…)' },
          ]}
          onChange={(members) => updateConfig({ team: { members } })}
          addLabel="+ Ajouter un praticien"
        />
      </div>

      <div className="settings-card">
        <h2>Parcours patient</h2>
        <ListEditor
          items={config.steps.items}
          columns={[
            { key: 'title', label: 'Étape' },
            { key: 'description', label: 'Description' },
          ]}
          onChange={(items) => updateConfig({ steps: { items } })}
          addLabel="+ Ajouter une étape"
        />
      </div>

      <div className="settings-card">
        <h2>Témoignages</h2>
        <ListEditor
          items={config.testimonials.items}
          columns={[
            { key: 'author', label: 'Auteur' },
            { key: 'role', label: 'Lien au cabinet' },
            { key: 'quote', label: 'Témoignage' },
          ]}
          onChange={(items) => updateConfig({ testimonials: { items } })}
          addLabel="+ Ajouter un témoignage"
        />
      </div>
    </>
  )

  const renderImages = () => (
    <div className="settings-card">
      <h2>Images du site</h2>
      <p>
        Collez une URL d’image (PNG/JPG/WEBP) ou un chemin du type
        <code> /images/mon-image.jpg</code> (fichier déposé dans
        <code> frontend/public/images/</code>). Laissez vide pour revenir à l’illustration
        intégrée aux couleurs du thème.
      </p>

      <div className="settings-fields">
        <Field
          label="Logo (navbar / footer)"
          value={config.branding.logo}
          onChange={(v) => updateConfig({ branding: { logo: v || null } })}
          placeholder="https://…/logo.png"
        />
        <Field
          label="Image du Hero"
          value={config.hero.image}
          onChange={(v) => updateConfig({ hero: { image: v || null } })}
          placeholder="https://…/hero.jpg"
        />
        <Field
          label="Image — présentation"
          value={config.about.image}
          onChange={(v) => updateConfig({ about: { image: v || null } })}
          placeholder="https://…/cabinet.jpg"
        />
        <Field
          label="Image — technologies"
          value={config.technology.image}
          onChange={(v) => updateConfig({ technology: { image: v || null } })}
          placeholder="https://…/equipement.jpg"
        />
      </div>

      <div className="settings-fields single">
        <Field
          label="Texte alternatif de l’image du Hero (accessibilité)"
          value={config.hero.imageAlt}
          onChange={(v) => updateConfig({ hero: { imageAlt: v } })}
        />
      </div>
    </div>
  )

  const renderContact = () => (
    <>
      <div className="settings-card">
        <h2>Coordonnées de contact</h2>
        <div className="settings-fields">
          <Field
            label="Titre de la page contact"
            value={config.contact.title}
            onChange={(v) => updateConfig({ contact: { title: v } })}
          />
          <Field
            label="Objet des messages"
            value={config.contact.subject}
            onChange={(v) => updateConfig({ contact: { subject: v } })}
          />
        </div>
        <div className="settings-fields single">
          <TextAreaField
            label="Introduction"
            value={config.contact.intro}
            onChange={(v) => updateConfig({ contact: { intro: v } })}
            rows={3}
          />
          <Field
            label="Message d’urgence"
            value={config.contact.emergency}
            onChange={(v) => updateConfig({ contact: { emergency: v } })}
          />
        </div>

        <ListEditor
          items={config.contact.hours}
          columns={[
            { key: 'label', label: 'Jours' },
            { key: 'value', label: 'Horaires' },
          ]}
          onChange={(hours) => updateConfig({ contact: { hours } })}
          addLabel="+ Ajouter une ligne d’horaires"
        />
      </div>

      <div className="settings-card">
        <h2>Pied de page</h2>
        <div className="settings-fields single">
          <TextAreaField
            label="Description"
            value={config.footer.description}
            onChange={(v) => updateConfig({ footer: { description: v } })}
            rows={3}
          />
          <Field
            label="Mention de copyright"
            value={config.footer.copyright}
            onChange={(v) => updateConfig({ footer: { copyright: v } })}
          />
          <Field
            label="Mention légale"
            value={config.footer.legal}
            onChange={(v) => updateConfig({ footer: { legal: v } })}
          />
        </div>
      </div>
    </>
  )

  const panels = {
    identity: renderIdentity,
    hero: renderHero,
    navigation: renderNavigation,
    sections: renderSections,
    content: renderContent,
    images: renderImages,
    contact: renderContact,
  }

  return (
    <div className="settings-page container">
      <header className="settings-header">
        <p className="eyebrow">Administration du site</p>
        <h1>Paramétrage du site public</h1>
        <p>
          Modifiez l’identité, le hero, les sections et les textes du site. Les changements
          s’appliquent en direct ; « Enregistrer » les conserve dans ce navigateur.
        </p>
      </header>

      <div className="settings-notice">
        <Icon name="bell" />
        <span>
          <strong>Stockage local en attendant l’API.</strong> Aucun endpoint d’administration
          n’existe côté backend : cette zone utilisera l’API de configuration du site dès qu’elle
          sera disponible, avec les permissions existantes. Aucune modification backend n’a été
          effectuée.
        </span>
      </div>

      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Sections du paramétrage">
          {PANELS.map((panel) => (
            <button
              key={panel.id}
              type="button"
              className={activePanel === panel.id ? 'active' : ''}
              onClick={() => setActivePanel(panel.id)}
            >
              {panel.label}
            </button>
          ))}
        </nav>

        <div className="settings-panel">{panels[activePanel]()}</div>
      </div>

      <div className="settings-actions">
        <button type="button" className="btn btn-primary" onClick={handleSave}>
          Enregistrer
        </button>
        <Link className="btn btn-outline" to="/">
          Voir le site
        </Link>
        <span className="spacer" />
        {savedMessage && <span className="success-text">{savedMessage}</span>}
        <button type="button" className="btn btn-outline" onClick={handleReset}>
          Rétablir les valeurs par défaut
        </button>
      </div>
    </div>
  )
}

export default SiteSettings
