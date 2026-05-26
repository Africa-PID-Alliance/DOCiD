'use client';

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  Chip,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { useTranslation } from 'react-i18next';

const faqs = [
  {
    question: 'What is DOCiD™?',
    answer:
      'DOCiD™ (Digital Object Container Identifier) is a persistent identifier and Handle framework developed by the Africa PID Alliance under TCC Africa. It is designed to aggregate, connect, and manage multiple research-related identifiers and metadata within a single interoperable digital container.',
    category: 'General',
  },
  {
    question: 'What problem does DOCiD™ solve?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          DOCiD™ addresses major gaps in African and global scholarly infrastructure, including:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Fragmented research identifiers',
            'Poor visibility of African research outputs',
            'Lack of persistent identification for grey literature',
            'Weak provenance tracking',
            'Underrepresentation of Indigenous Knowledge and cultural heritage',
            'Limited interoperability between research systems',
            'Challenges in long-term stewardship of digital knowledge assets',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          It enables African-originated knowledge systems to become more discoverable, interoperable, and ethically governed.
        </Typography>
      </>
    ),
    category: 'General',
  },
  {
    question: 'What does "Digital Object Container Identifier" mean?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Unlike traditional identifiers that identify a single object (for example, one DOI for one article), DOCiD™ identifies a container that can aggregate:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Publications',
            'Datasets',
            'Software',
            'Audio/video files',
            'Images',
            'Patents',
            'Protocols',
            'Indigenous knowledge records',
            'Institutional records',
            'Metadata from multiple PID systems',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          This allows the full lifecycle of a research or knowledge object to be connected within one structured environment.
        </Typography>
      </>
    ),
    category: 'General',
  },
  {
    question: 'How is DOCiD™ different from a DOI?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          A DOI identifies a single digital object. DOCiD™ functions as a federated container that can integrate multiple identifiers and metadata layers together. DOCiD™ can connect:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'DOI', 'ORCID', 'ROR', 'RAiD', 'Handles', 'ARKs', 'RRIDs',
            'Crossref metadata', 'DataCite metadata', 'Institutional identifiers', 'Local identifiers',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          …into one machine-actionable research object.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Is DOCiD™ a DOI?',
    answer:
      'No. DOCiD™ is not simply another DOI. It is a broader federated PID framework and container architecture designed to interconnect multiple PID ecosystems. It can work alongside DOIs while supporting additional identifier layers and contextual metadata.',
    category: 'Technical',
  },
  {
    question: 'What does "multilinear" mean in DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          "Multilinear" refers to DOCiD's ability to support multiple persistent identifier pathways and infrastructures simultaneously rather than relying on a single PID workflow. For example, one DOCiD container may simultaneously connect:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'a DOI',
            'an ORCID researcher profile',
            'a Handle identifier',
            'a ROR institutional identifier',
            'a RAiD project identifier',
            'and associated datasets or patents',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          This creates a richer and more interconnected research object.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'What types of content can DOCiD™ identify?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ can support:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Journal articles', 'Grey literature', 'Policy papers', 'Technical reports',
            'Patents', 'Datasets', 'Indigenous knowledge records', 'Cultural heritage materials',
            'Audio and video files', 'Museum collections', 'Community knowledge records',
            'Research projects', 'Institutional repositories', 'Research workflows',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'General',
  },
  {
    question: 'What is grey literature and why does DOCiD™ matter for it?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Grey literature includes reports, working papers, policy documents, technical manuals, theses, government publications, and community-generated knowledge. Much of Africa's knowledge ecosystem exists as grey literature and often lacks persistent identifiers, making it difficult to discover, cite, preserve, and track. DOCiD™ helps make grey literature:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {['discoverable', 'citable', 'traceable', 'and interoperable within global scholarly systems'].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'How does DOCiD™ support Indigenous Knowledge and Cultural Heritage?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          DOCiD™ integrates both FAIR and CARE principles:
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 1.5 }}>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5 }}>FAIR</Typography>
            <Box component="ul" sx={{ pl: 3, m: 0 }}>
              {['Findable', 'Accessible', 'Interoperable', 'Reusable'].map((i) => (
                <Box component="li" key={i}><Typography variant="body2">{i}</Typography></Box>
              ))}
            </Box>
          </Box>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5 }}>CARE</Typography>
            <Box component="ul" sx={{ pl: 3, m: 0 }}>
              {['Collective Benefit', 'Authority to Control', 'Responsibility', 'Ethics'].map((i) => (
                <Box component="li" key={i}><Typography variant="body2">{i}</Typography></Box>
              ))}
            </Box>
          </Box>
        </Box>
        <Typography variant="body2">
          This means DOCiD™ not only improves discoverability but also supports ethical stewardship, community governance, provenance tracking, attribution, and culturally sensitive data management — which is particularly important for Indigenous Knowledge Systems and heritage collections.
        </Typography>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'What are FAIR Digital Objects (FDOs), and how does DOCiD™ relate to them?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          FAIR Digital Objects (FDOs) are machine-actionable digital entities that combine persistent identifiers, metadata, typing, and governance information. DOCiD™ aligns closely with the FDO approach because it:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'aggregates structured metadata',
            'interconnects PID systems',
            'supports interoperability',
            'and enables machine-actionable research objects',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          DOCiD™ is increasingly being positioned as an Africa-originated implementation of FAIR Digital Object principles.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Which identifier systems can DOCiD™ integrate with?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ is designed to interoperate with:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {['ORCID', 'ROR', 'Crossref', 'DataCite', 'Handles', 'RAiD', 'ARK', 'RRIDs', 'CSTR', 'Ringgold', 'ISNI', 'Institutional identifiers', 'Locally governed identifiers'].map((id) => (
            <Chip key={id} label={id} size="small" variant="outlined" />
          ))}
        </Box>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Who can use DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ is relevant for:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Researchers', 'Universities', 'Libraries', 'Museums', 'Cultural heritage institutions',
            'Patent offices', 'Government agencies', 'Indigenous communities', 'Publishers',
            'Research funders', 'Research institutes', 'Open science infrastructures',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'General',
  },
  {
    question: 'Why is DOCiD™ important for Africa?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ is designed to strengthen:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'African research visibility',
            'African data sovereignty',
            'Local ownership of scholarly infrastructure',
            'Representation of African knowledge systems',
            'Equitable participation in global Open Science',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          It addresses long-standing inequities where African research outputs are underrepresented in global scholarly infrastructures.
        </Typography>
      </>
    ),
    category: 'Africa & Sovereignty',
  },
  {
    question: 'What is meant by "African data sovereignty" in DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          African data sovereignty refers to ensuring that African institutions and communities maintain governance, stewardship, and control over their digital knowledge systems and metadata infrastructures. DOCiD™ promotes:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Regionally governed infrastructure',
            'African-led metadata systems',
            'Ethical governance frameworks for knowledge preservation and dissemination',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Africa & Sovereignty',
  },
  {
    question: 'Does DOCiD™ support patents and innovation tracking?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. DOCiD™ was partly developed to support patent metadata and innovation ecosystems by connecting:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {['Patents', 'Research outputs', 'Datasets', 'Inventors', 'Institutions', 'Supporting documentation within one research lifecycle container'].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'How does DOCiD™ improve research discoverability?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ improves discoverability through:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Metadata-rich containers',
            'Persistent identifiers',
            'Linked relationships between outputs',
            'Interoperability with global PID systems',
            'Machine-readable metadata structures',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          This enables research outputs to be more easily indexed, linked, cited, and reused.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Is DOCiD™ open infrastructure?',
    answer:
      'Yes. DOCiD™ is positioned as an African-led open infrastructure initiative focused on equitable, accessible, and interoperable scholarly communication systems.',
    category: 'General',
  },
  {
    question: 'Can DOCiD™ work with existing university systems?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. DOCiD™ is intended to integrate into:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Institutional repositories',
            'CRIS/RIMS systems',
            'Library systems',
            'Museum databases',
            'Research workflows',
            'Broader Open Science infrastructures',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'What role do librarians and curators play in DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Librarians and curators are central to:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Metadata quality',
            'Provenance management',
            'Ethical stewardship',
            'Governance workflows',
            'Interoperability standards',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          DOCiD™ recognizes these professionals as key stewards of trusted knowledge systems.
        </Typography>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'Is DOCiD™ already live?',
    answer:
      'Yes. DOCiD™ 1.0 is live and publicly accessible through the Africa PID Alliance platform.',
    category: 'General',
  },
  {
    question: 'What institutions are already engaging with DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          DOCiD™ has been piloted or discussed with universities, museums, cultural heritage institutions, research centers, and Indigenous Knowledge stakeholders across Africa. Examples referenced publicly include institutions in:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {['Kenya', 'Burkina Faso', 'South Africa', 'Nigeria'].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Africa & Sovereignty',
  },
  {
    question: 'How does DOCiD™ support interoperability?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ supports interoperability by:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Linking multiple PID systems',
            'Using structured metadata',
            'Supporting typed relationships',
            'Enabling machine-readable object connections across platforms',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          This allows distributed systems to exchange and understand research metadata more effectively.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Is DOCiD™ only for researchers?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          No. DOCiD™ is also designed for:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Communities',
            'Cultural heritage practitioners',
            'Innovation ecosystems',
            'Government agencies',
            'Museums',
            'Libraries',
            'Non-traditional knowledge holders',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'General',
  },
  {
    question: 'How does DOCiD™ support Open Science?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ supports Open Science by:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Improving accessibility',
            'Increasing discoverability',
            'Enabling interoperability',
            'Supporting reusable metadata',
            'Strengthening ethical governance of knowledge systems',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>
          It aligns strongly with the UNESCO Open Science Recommendation.
        </Typography>
      </>
    ),
    category: 'Use Cases',
  },
  {
    question: 'What infrastructure supports DOCiD™?',
    answer:
      'DOCiD™ is supported through partnerships and distributed infrastructure initiatives, including collaboration with the UbuntuNet Alliance to strengthen regional hosting and infrastructure resilience across Africa.',
    category: 'General',
  },
  {
    question: 'Where can someone access DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          You can explore DOCiD™ through:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'The DOCiD Platform (this site)',
            'Africa PID Alliance — africapidalliance.org',
            'The DOCiD About Page (available in the navigation above)',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'General',
  },
  {
    question: 'How can I verify and access a DOCiD record through the Handle System?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          You can verify DOCiD records directly through the Handle System Resolver. Simply append the DOCiD handle to the resolver URL to access the corresponding record through automatic redirection:
        </Typography>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', px: 1.5, py: 0.75, borderRadius: 1, mb: 0.5 }}>
          {'https://hdl.handle.net/{DOCiD}'}
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, mt: 1 }}>For example:</Typography>
        <Typography
          variant="body2"
          component="a"
          href="https://hdl.handle.net/20.500.14351/1ad229ce7aed487e2b4e"
          target="_blank"
          rel="noopener noreferrer"
          sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', px: 1.5, py: 0.75, borderRadius: 1, display: 'block', mb: 1.5, wordBreak: 'break-all' }}
        >
          https://hdl.handle.net/20.500.14351/1ad229ce7aed487e2b4e
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          If you would like to view the underlying Handle record metadata without being redirected, you can append <code>?noredirect</code> to the URL:
        </Typography>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', px: 1.5, py: 0.75, borderRadius: 1, mb: 0.5 }}>
          {'https://hdl.handle.net/{DOCiD}?noredirect'}
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, mt: 1 }}>For example:</Typography>
        <Typography
          variant="body2"
          component="a"
          href="https://hdl.handle.net/20.500.14351/1ad229ce7aed487e2b4e?noredirect"
          target="_blank"
          rel="noopener noreferrer"
          sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', px: 1.5, py: 0.75, borderRadius: 1, display: 'block', mb: 1.5, wordBreak: 'break-all' }}
        >
          https://hdl.handle.net/20.500.14351/1ad229ce7aed487e2b4e?noredirect
        </Typography>
        <Typography variant="body2">
          In most use cases, the automatic redirection option will be the most practical and user-friendly approach, particularly for resolving and accessing linked digital objects directly.
        </Typography>
      </>
    ),
    category: 'Technical',
  },
  {
    question: 'Where is DOCiD™ metadata stored?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          DOCiD™ metadata is designed to be stored within distributed, interoperable digital repository infrastructures that support persistent identifiers, machine-actionable metadata, and FAIR Digital Object principles.
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>The current DOCiD™ architecture supports:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'CORDRA-based metadata storage',
            'Distributed Handle infrastructure',
            'UbuntuNet Alliance–aligned regional data infrastructure',
            'JSON-based metadata objects',
            'RESTful APIs for metadata exchange and interoperability',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'What is CORDRA and why is it important for DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          CORDRA (Corporation for Digital Repository Advancement) is a digital object repository platform that supports:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Handle generation',
            'Object persistence',
            'Metadata management',
            'Distributed repositories',
            'Version control',
            'Machine-actionable digital objects',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ uses CORDRA because it enables:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Structured digital object storage',
            'Persistent identifier management',
            'Interoperable metadata handling',
            'FAIR Digital Object implementation',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2">
          CORDRA acts as one of the foundational metadata repository layers for DOCiD™ containers.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'What kind of metadata does CORDRA store for DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>CORDRA stores:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'JSON-based metadata objects',
            'Object relationships',
            'Handle identifiers',
            'Payload references',
            'Governance metadata',
            'Linked research object information',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2">
          The architecture allows metadata to be structured as interoperable machine-readable objects rather than static records.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Does DOCiD™ support JSON metadata?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. DOCiD™ metadata is designed to be accessible and exchangeable as structured JSON objects. This enables:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Machine readability',
            'API interoperability',
            'Metadata harvesting',
            'System integrations',
            'FAIR-compliant metadata exchange',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>JSON-based metadata structures also make it easier for:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {['Repositories', 'CRIS/RIMS platforms', 'Institutional repositories', 'Libraries', 'Museums', 'Software systems'].map((id) => (
            <Chip key={id} label={id} size="small" variant="outlined" />
          ))}
        </Box>
        <Typography variant="body2" sx={{ mt: 1 }}>to integrate with DOCiD™.</Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Can DOCiD™ metadata be accessed through APIs?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. DOCiD™ supports RESTful API integration and machine-accessible metadata exchange. The platform references:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'REST APIs',
            'Metadata query interfaces',
            'Identifier resolution services',
            'External service integrations',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>This allows institutions and developers to:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Retrieve metadata',
            'Push metadata',
            'Synchronize records',
            'Build interoperable applications around DOCiD™ infrastructure',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'What types of APIs does DOCiD™ support?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ supports APIs for:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Metadata retrieval',
            'Object creation',
            'Identifier resolution',
            'Metadata updates',
            'Repository synchronization',
            'External PID integrations',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>The ecosystem is designed to integrate with:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {['Crossref APIs', 'DataCite APIs', 'Handle APIs', 'ORCID integrations', 'Distributed repository infrastructures'].map((id) => (
            <Chip key={id} label={id} size="small" variant="outlined" />
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'How does UbuntuNet Alliance support DOCiD™ infrastructure?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          UbuntuNet Alliance plays an important role in strengthening African open infrastructure ecosystems through:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Regional network infrastructure',
            'Repository hosting',
            'Metadata aggregation',
            'Distributed scholarly communication systems',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ aligns with UbuntuNet Alliance's broader vision of:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'African-owned infrastructure',
            'Regional interoperability',
            'Distributed metadata stewardship',
            'Open Science infrastructure sustainability',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'What are UbuntuNet Alliance Data Centers in the context of DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          UbuntuNet Alliance Data Centers refer to regionally connected digital infrastructure environments that can support:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Metadata hosting',
            'Repository services',
            'Distributed digital preservation',
            'African-controlled scholarly infrastructure',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>Within the DOCiD™ ecosystem, UbuntuNet Alliance infrastructure can support:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Distributed metadata hosting',
            'Regional redundancy',
            'Low-latency African access',
            'Data sovereignty objectives',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2">
          This reduces overdependence on externally controlled infrastructure systems.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Why is distributed metadata storage important for DOCiD™?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>Distributed metadata storage improves:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Infrastructure resilience',
            'Long-term preservation',
            'Regional ownership',
            'Interoperability',
            'Disaster recovery',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>For African scholarly infrastructure, distributed storage also supports:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Digital sovereignty',
            'Local governance',
            'Reduced dependency on centralized Global North infrastructure systems',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Can institutions host their own DOCiD™ metadata infrastructure?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. The DOCiD™ architecture is designed to support federated and distributed implementation models. Institutions can potentially:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Host local metadata repositories',
            'Connect to regional infrastructure',
            'Synchronize metadata through APIs',
            'Maintain governance control over their digital objects',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2">
          This supports institutional autonomy while preserving interoperability.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Does DOCiD™ support machine-actionable metadata?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. DOCiD™ is designed around machine-actionable metadata principles aligned with FAIR Digital Object (FDO) approaches. This means:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Systems can automatically interpret metadata',
            'Relationships between objects are computable',
            'Identifiers are resolvable',
            'Metadata can be exchanged programmatically across infrastructures',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Can DOCiD™ integrate with institutional repositories and CRIS/RIMS systems?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>Yes. DOCiD™ is designed to integrate with:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.5 }}>
          {['Institutional repositories', 'CRIS systems', 'RIMS platforms', 'Digital libraries', 'Museum systems', 'Open Science infrastructures'].map((id) => (
            <Chip key={id} label={id} size="small" variant="outlined" />
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>Integration is enabled through:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'APIs',
            'Structured JSON metadata',
            'PID interoperability',
            'Repository synchronization workflows',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'How does DOCiD™ support interoperability across systems?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>DOCiD™ supports interoperability through:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.5 }}>
          {['JSON metadata standards', 'Persistent identifiers', 'REST APIs', 'Handle infrastructure', 'CORDRA repositories', 'Metadata exchange protocols'].map((id) => (
            <Chip key={id} label={id} size="small" variant="outlined" />
          ))}
        </Box>
        <Typography variant="body2">
          This allows multiple infrastructures to exchange and interpret metadata consistently.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Can developers build applications using DOCiD™ metadata?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Yes. Because DOCiD™ metadata is API-accessible and JSON-based, developers can build:
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Dashboards',
            'Discovery systems',
            'Analytics tools',
            'Repository integrations',
            'Institutional reporting systems',
            'AI-driven scholarly tools',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2">
          The architecture supports extensibility and integration into broader research ecosystems.
        </Typography>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Does DOCiD™ support metadata versioning?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>Yes. Through CORDRA integration, DOCiD™ supports:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Object versioning',
            'Lifecycle management',
            'Metadata updates',
            'Provenance tracking',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>This is important for:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Evolving research objects',
            'Cultural heritage records',
            'Datasets',
            'Long-term scholarly preservation',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
  {
    question: 'Why are APIs and JSON important for Open Science?',
    answer: (
      <>
        <Typography variant="body2" sx={{ mb: 1 }}>APIs and JSON support:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0, mb: 1.5 }}>
          {[
            'Automation',
            'Interoperability',
            'Scalability',
            'Metadata harvesting',
            'Machine readability',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
        <Typography variant="body2" sx={{ mb: 1 }}>This enables Open Science ecosystems to:</Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {[
            'Share metadata globally',
            'Integrate systems seamlessly',
            'Improve discoverability and reuse of research outputs',
          ].map((item) => (
            <Box component="li" key={item} sx={{ mb: 0.5 }}>
              <Typography variant="body2">{item}</Typography>
            </Box>
          ))}
        </Box>
      </>
    ),
    category: 'Infrastructure',
  },
];

const CATEGORIES = ['All', 'General', 'Technical', 'Use Cases', 'Africa & Sovereignty', 'Infrastructure'];

const categoryColors = {
  General: 'primary',
  Technical: 'secondary',
  'Use Cases': 'success',
  'Africa & Sovereignty': 'warning',
  Infrastructure: 'info',
};

const FaqPage = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const [activeCategory, setActiveCategory] = useState('All');

  const handleChange = (panel) => (_, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  const filteredFaqs =
    activeCategory === 'All' ? faqs : faqs.filter((f) => f.category === activeCategory);

  return (
    <Box sx={{ bgcolor: theme.palette.background.default, minHeight: '100vh' }}>
      {/* Hero */}
      <Box
        sx={{
          bgcolor: '#141a3b',
          color: 'white',
          py: { xs: 6, md: 8 },
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          '&:after': {
            content: '""',
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: 'linear-gradient(90deg, #1565c0 0%, #42a5f5 50%, #1565c0 100%)',
          },
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <HelpOutlineIcon sx={{ fontSize: 56, opacity: 0.85 }} />
          </Box>
          <Typography
            variant="h3"
            component="h1"
            sx={{ fontWeight: 800, mb: 2, fontSize: { xs: '2rem', md: '2.75rem' } }}
          >
            Frequently Asked Questions
          </Typography>
          <Typography
            variant="h6"
            sx={{ opacity: 0.85, fontWeight: 400, fontSize: { xs: '1rem', md: '1.15rem' } }}
          >
            Everything you need to know about DOCiD™ and the Africa PID Alliance
          </Typography>
        </Container>
      </Box>

      {/* Category filter */}
      <Box sx={{ bgcolor: theme.palette.background.paper, borderBottom: `1px solid ${theme.palette.divider}`, py: 2 }}>
        <Container maxWidth="md">
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: { xs: 'center', md: 'flex-start' } }}>
            {CATEGORIES.map((cat) => (
              <Chip
                key={cat}
                label={cat}
                onClick={() => setActiveCategory(cat)}
                color={activeCategory === cat ? 'primary' : 'default'}
                variant={activeCategory === cat ? 'filled' : 'outlined'}
                sx={{ cursor: 'pointer', fontWeight: activeCategory === cat ? 700 : 400 }}
              />
            ))}
          </Box>
        </Container>
      </Box>

      {/* FAQ list */}
      <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 } }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Showing {filteredFaqs.length} of {faqs.length} questions
        </Typography>

        {filteredFaqs.map((faq, index) => (
          <Accordion
            key={index}
            expanded={expanded === index}
            onChange={handleChange(index)}
            disableGutters
            elevation={0}
            sx={{
              mb: 1.5,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: '8px !important',
              overflow: 'hidden',
              '&:before': { display: 'none' },
              '&.Mui-expanded': {
                borderColor: theme.palette.primary.main,
                boxShadow: `0 0 0 1px ${theme.palette.primary.main}`,
              },
            }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              sx={{
                px: 3,
                py: 1,
                bgcolor: expanded === index
                  ? theme.palette.mode === 'dark'
                    ? 'rgba(25, 118, 210, 0.12)'
                    : 'rgba(21, 101, 192, 0.05)'
                  : theme.palette.background.paper,
                '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 1.5, flexWrap: 'wrap' },
              }}
            >
              <Typography
                variant="subtitle1"
                sx={{ fontWeight: 600, flex: 1, color: theme.palette.text.primary, lineHeight: 1.4 }}
              >
                {faq.question}
              </Typography>
              <Chip
                label={faq.category}
                size="small"
                color={categoryColors[faq.category] || 'default'}
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 22, display: { xs: 'none', sm: 'flex' } }}
              />
            </AccordionSummary>
            <Divider />
            <AccordionDetails sx={{ px: 3, py: 2.5, bgcolor: theme.palette.background.default }}>
              {typeof faq.answer === 'string' ? (
                <Typography variant="body2" sx={{ lineHeight: 1.8, color: theme.palette.text.primary }}>
                  {faq.answer}
                </Typography>
              ) : (
                <Box sx={{ color: theme.palette.text.primary, '& .MuiTypography-body2': { lineHeight: 1.8, color: theme.palette.text.primary } }}>
                  {faq.answer}
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Container>
    </Box>
  );
};

export default FaqPage;
