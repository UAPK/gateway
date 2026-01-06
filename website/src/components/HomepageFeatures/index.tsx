import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
  link: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Policy Enforcement',
    icon: '🛡️',
    description: (
      <>
        <strong>ALLOW, DENY, or ESCALATE</strong> decisions based on manifests, budgets, and risk hooks.
        Non-bypassable enforcement at the action boundary.
      </>
    ),
    link: '/docs/concepts/decisions',
  },
  {
    title: 'Human Approvals',
    icon: '👤',
    description: (
      <>
        High-risk actions <strong>escalate to operators</strong> for review.
        Web UI + API with 5-minute SLA. Full audit trail of every decision.
      </>
    ),
    link: '/docs/concepts/approvals',
  },
  {
    title: 'Tamper-Evident Logs',
    icon: '📜',
    description: (
      <>
        <strong>Hash-chained, Ed25519-signed</strong> interaction records.
        Cryptographically verifiable audit logs for regulators and courts.
      </>
    ),
    link: '/docs/concepts/logs',
  },
];

function Feature({title, icon, description, link}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center" style={{fontSize: '4rem', marginBottom: '1rem'}}>
        {icon}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p style={{minHeight: '100px'}}>{description}</p>
        <Link to={link} style={{fontSize: '0.9rem'}}>Learn more →</Link>
      </div>
    </div>
  );
}

function Testimonials() {
  return (
    <div style={{marginTop: '4rem', padding: '3rem 0', backgroundColor: 'var(--ifm-color-emphasis-100)'}}>
      <div className="container">
        <Heading as="h3" style={{textAlign: 'center', marginBottom: '2rem'}}>
          What Customers Say
        </Heading>
        <div className="row">
          <div className="col col--4">
            <blockquote style={{borderLeft: '4px solid var(--ifm-color-primary)', paddingLeft: '1rem', fontStyle: 'italic'}}>
              "The pilot paid for itself in the first month."
              <footer style={{marginTop: '0.5rem', fontStyle: 'normal', fontSize: '0.9rem'}}>
                — <strong>Managing Partner</strong>, IP Litigation Boutique
              </footer>
            </blockquote>
          </div>
          <div className="col col--4">
            <blockquote style={{borderLeft: '4px solid var(--ifm-color-primary)', paddingLeft: '1rem', fontStyle: 'italic'}}>
              "Got to production in 3 weeks. The audit trail was exactly what regulators wanted."
              <footer style={{marginTop: '0.5rem', fontStyle: 'normal', fontSize: '0.9rem'}}>
                — <strong>CTO</strong>, Series B Fintech
              </footer>
            </blockquote>
          </div>
          <div className="col col--4">
            <blockquote style={{borderLeft: '4px solid var(--ifm-color-primary)', paddingLeft: '1rem', fontStyle: 'italic'}}>
              "We can finally say 'yes' to AI agents without sacrificing governance."
              <footer style={{marginTop: '0.5rem', fontStyle: 'normal', fontSize: '0.9rem'}}>
                — <strong>Director of Compliance</strong>, Regional Bank
              </footer>
            </blockquote>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <>
      <section className={styles.features} style={{padding: '4rem 0'}}>
        <div className="container">
          <Heading as="h2" style={{textAlign: 'center', marginBottom: '3rem'}}>
            What You Get
          </Heading>
          <div className="row">
            {FeatureList.map((props, idx) => (
              <Feature key={idx} {...props} />
            ))}
          </div>
        </div>
      </section>
      <Testimonials />
    </>
  );
}
