import React, { createContext, useContext, useState, useEffect } from "react";
import { translations } from "@/constants/translations";

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  // Default to English ('en'), or fallback to saved preference
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem("agriketha_language") || "en";
  });

  const setLanguage = (lang) => {
    setLanguageState(lang);
    localStorage.setItem("agriketha_language", lang);
  };

  const toggleLanguage = () => {
    const nextLang = language === "si" ? "en" : "si";
    setLanguage(nextLang);
  };

  // Translation helper function
  const t = (key, fallback = "") => {
    const langDict = translations[language] || translations.en;
    if (langDict && langDict[key] !== undefined) {
      return langDict[key];
    }
    // Fallback to English dictionary
    if (translations.en && translations.en[key] !== undefined) {
      return translations.en[key];
    }
    return fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
