import { Link } from 'react-router-dom'

import PageHero from '../components/common/PageHero.jsx'

function NotFound() {
  return (
    <>
      <PageHero
        eyebrow="Erreur 404"
        title="Page introuvable"
        description="La page demandée n’existe pas ou a été déplacée."
        actions={[{ label: 'Retour à l’accueil', to: '/', variant: 'btn-accent' }]}
      />

      <section className="page-shell">
        <p className="muted">
          Vous pouvez reprendre la navigation depuis l’accueil ou{' '}
          <Link to="/contact">nous contacter</Link> si le problème persiste.
        </p>
      </section>
    </>
  )
}

export default NotFound
