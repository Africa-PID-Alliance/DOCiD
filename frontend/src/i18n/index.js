'use client';

import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en';
import fr from './locales/fr';
import sw from './locales/sw';
import ar from './locales/ar';
import pt from './locales/pt';
import de from './locales/de';
import ms from './locales/ms';
import km from './locales/km';
import es from './locales/es';
import id from './locales/id';
import hi from './locales/hi';
import vi from './locales/vi';
import ko from './locales/ko';
import lo from './locales/lo';
import zh from './locales/zh';
import my from './locales/my';
import fil from './locales/fil';
import th from './locales/th';
import tet from './locales/tet';

const resources = {
  en: { common: en },
  fr: { common: fr },
  sw: { common: sw },
  ar: { common: ar },
  pt: { common: pt },
  de: { common: de },
  ms: { common: ms },
  km: { common: km },
  es: { common: es },
  id: { common: id },
  hi: { common: hi },
  vi: { common: vi },
  ko: { common: ko },
  lo: { common: lo },
  zh: { common: zh },
  my: { common: my },
  fil: { common: fil },
  th: { common: th },
  tet: { common: tet },
};

i18next
  .use(initReactI18next)
  .use(LanguageDetector)
  .init({
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    },
    debug: false,
    fallbackLng: 'en',
    defaultNS: 'common',
    supportedLngs: ['en', 'fr', 'sw', 'ar', 'pt', 'de', 'ms', 'km', 'es', 'id', 'hi', 'vi', 'ko', 'lo', 'zh', 'my', 'fil', 'th', 'tet'],
    interpolation: {
      escapeValue: false,
    },
    resources,
  });

export default i18next;
