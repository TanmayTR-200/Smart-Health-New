import React, { createContext, useContext, useState, useEffect } from 'react';
import { getTranslation } from '../utils/translations';

// Create context
const LanguageContext = createContext();

// Language provider component
export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState('en');
  const [translations, setTranslations] = useState({});

  useEffect(() => {
    // Load all translations for current language
    import('../utils/translations').then(module => {
      setTranslations(module.default);
    });
  }, [language]);

  const t = (key, params = {}) => {
    return getTranslation(key, language, params);
  };

  const value = {
    language,
    setLanguage,
    t,
    translations
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

// Custom hook for using language context
export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageContext;