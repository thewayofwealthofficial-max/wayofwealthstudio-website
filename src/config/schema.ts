// JSON-LD (structured data) shared by the homepage, /about/ and /coaching/.
// Facts only: nothing here that isn't stated elsewhere on the site. No review or rating schema.
import { LINKS } from './links';

const SITE = LINKS.siteUrl;
export const INSTAGRAM = 'https://www.instagram.com/theway.ofwealth/';
export const ORG_ID = `${SITE}/#organization`;
export const PERSON_ID = `${SITE}/about/#joel`;

export const organization = {
  '@type': 'ProfessionalService',
  '@id': ORG_ID,
  name: 'Way of Wealth',
  legalName: 'Way of Wealth Ltd',
  url: `${SITE}/`,
  image: `${SITE}/cards/og-default.png`,
  description: 'Behavioural money coaching for small business owners and the self-employed: a steady wage, a tax pot that is never short, and calm about money. Coaching, not regulated financial advice.',
  email: 'joel@wayofwealthcoaching.com',
  address: { '@type': 'PostalAddress', addressLocality: 'London', addressCountry: 'GB' },
  areaServed: { '@type': 'Country', name: 'United Kingdom' },
  identifier: { '@type': 'PropertyValue', propertyID: 'Companies House company number', value: '17214427' },
  founder: { '@id': PERSON_ID },
  sameAs: [INSTAGRAM],
};

export const person = {
  '@type': 'Person',
  '@id': PERSON_ID,
  name: 'Joel Ezekiel',
  url: `${SITE}/about/`,
  image: `${SITE}/images/joel-headshot-web.jpg`,
  jobTitle: 'Behavioural money coach',
  description: 'Behavioural money coach and founder of Way of Wealth. Former financial planner at St James\'s Place. MSc Behavioural Economics, DipPFS.',
  worksFor: { '@id': ORG_ID },
  hasCredential: [
    { '@type': 'EducationalOccupationalCredential', name: 'MSc Behavioural Economics', credentialCategory: 'degree' },
    { '@type': 'EducationalOccupationalCredential', name: 'Diploma in Regulated Financial Planning (DipPFS)', credentialCategory: 'professional qualification' },
  ],
  knowsAbout: ['Behavioural economics', 'Money psychology', 'Cash flow for small business owners', 'Paying yourself when self-employed'],
  sameAs: [INSTAGRAM],
};

export const orgAndPerson = { '@context': 'https://schema.org', '@graph': [organization, person] };
