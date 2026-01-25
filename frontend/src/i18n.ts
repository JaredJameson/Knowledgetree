/**
 * KnowledgeTree - i18n Configuration
 * Polish (primary) and English (secondary) language support
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Import translation files
import translationEN from './locales/en/translation.json'
import translationPL from './locales/pl/translation.json'

// Translation resources
const resources = {
  en: {
    translation: translationEN,
  },
  pl: {
    translation: translationPL,
  },
}

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources,
    fallbackLng: 'pl', // Polish is primary language
    debug: import.meta.env.DEV, // Enable debug in development

    // Language detection settings
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'knowledgetree-language',
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Namespace configuration
    ns: ['translation'],
    defaultNS: 'translation',
  })

export default i18n
