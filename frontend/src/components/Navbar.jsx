import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, AlertTriangle, GitMerge, Home, Globe, HeartPulse } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

function Navbar() {
  const location = useLocation();
  const { language, setLanguage, t } = useLanguage();

  const navItems = [
    { path: '/', label: t('dashboard'), icon: Home },
    { path: '/redistribution', label: t('redistribution'), icon: GitMerge },
    { path: '/alerts', label: t('alerts'), icon: AlertTriangle },
    { path: '/simulation', label: t('simulation'), icon: Activity },
  ];

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'hi' : language === 'hi' ? 'kn' : 'en');
  };

  return (
    <nav className="sticky top-0 z-50 bg-white/70 backdrop-blur-xl border-b border-white/60 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-violet-500 rounded-xl blur-md opacity-40"></div>
              <div className="relative bg-gradient-to-br from-primary-500 to-violet-600 p-2 rounded-xl">
                <HeartPulse className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-3">
              <h1 className="text-lg font-bold bg-gradient-to-r from-primary-600 to-violet-600 bg-clip-text text-transparent">
                Smart Health
              </h1>
              <p className="text-[10px] text-slate-500 font-medium tracking-wide">
                AI-Powered District Health Management
              </p>
            </div>
          </div>

          {/* Nav links */}
          <div className="flex items-center space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => {
              const active = location.pathname === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                    active
                      ? 'bg-gradient-to-r from-primary-500 to-violet-500 text-white shadow-lg shadow-primary-500/25'
                      : 'text-slate-600 hover:bg-white/80 hover:text-primary-600'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">{label}</span>
                </Link>
              );
            })}

            {/* Language toggle */}
            <button
              onClick={toggleLanguage}
              className="flex items-center px-3 py-2 rounded-xl text-sm font-medium bg-white/60 border border-slate-200 hover:border-primary-300 hover:bg-primary-50 text-slate-700 transition-all duration-200 ml-2"
              title="Switch Language"
            >
              <Globe className="h-4 w-4 mr-1.5 text-primary-500" />
              <span className="font-semibold">
                {language === 'en' ? 'EN' : language === 'hi' ? 'हिं' : 'ಕನ'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
