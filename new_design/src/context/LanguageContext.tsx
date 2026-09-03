import React, { createContext, useContext, useState } from 'react';
import { translations } from '@/data/translations';
import type { Language } from '@/data/translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: (key: keyof typeof translations.fr) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('pulse-lang');
    return (saved === 'en' || saved === 'fr') ? saved : 'fr';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('pulse-lang', lang);
  };

  const toggleLanguage = () => {
    const nextLang = language === 'fr' ? 'en' : 'fr';
    setLanguage(nextLang);
  };

  const t = (key: keyof typeof translations.fr): string => {
    const dict = translations[language] || translations.fr;
    // Compared against undefined, not truthiness: several entries are
    // deliberately empty (kickers and taglines the review asked to drop), and
    // an `||` chain treated "" as missing and rendered the key name itself --
    // which is how "heroTitleHighlight" ended up in the hero headline.
    const value = dict[key] ?? translations.fr[key];
    return value === undefined ? key : value;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
