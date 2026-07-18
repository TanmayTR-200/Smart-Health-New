import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, AlertTriangle, CheckCircle, Clock, Filter,
  Building2, Pill, UserX, Bed
} from 'lucide-react';
import { getAlerts, translateText } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

function Alerts() {
  const { t, language } = useLanguage();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const translateAlerts = async (alertList) => {
    if (language === 'en') return alertList;
    const translated = await Promise.all(
      alertList.map(async (alert) => {
        const descTr = await translateText(alert.description, language);
        return { ...alert, description: descTr.data.translated_text };
      })
    );
    return translated;
  };

  const loadAlerts = async () => {
    try {
      const res = await getAlerts();
      let alertList = res.data;
      alertList = await translateAlerts(alertList);
      setAlerts(alertList);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [language]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      default: return 'bg-sky-50 text-sky-700 border-sky-200';
    }
  };

  const getSeverityBorder = (severity) => {
    switch (severity) {
      case 'critical': return 'border-l-rose-500';
      case 'high': return 'border-l-orange-500';
      case 'medium': return 'border-l-amber-500';
      default: return 'border-l-sky-500';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-5 w-5 text-rose-500" />;
      case 'high': return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'medium': return <Clock className="h-5 w-5 text-amber-500" />;
      default: return <CheckCircle className="h-5 w-5 text-sky-500" />;
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'stockout': return <Pill className="h-4 w-4" />;
      case 'underperforming': return <Building2 className="h-4 w-4" />;
      case 'attendance': return <UserX className="h-4 w-4" />;
      case 'bed_shortage': return <Bed className="h-4 w-4" />;
      default: return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(alert => alert.severity === filter);

  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const highCount = alerts.filter(a => a.severity === 'high').length;
  const mediumCount = alerts.filter(a => a.severity === 'medium').length;
  const lowCount = alerts.filter(a => a.severity === 'low').length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-slate-200"></div>
          <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"></div>
        </div>
        <div className="text-slate-500 font-medium">{t('loading')}</div>
      </div>
    );
  }

  const filterButtons = [
    { key: 'all', label: 'All', count: alerts.length, activeClass: 'bg-gradient-to-r from-primary-500 to-violet-500 text-white', inactiveClass: 'bg-slate-100 text-slate-600 hover:bg-slate-200' },
    { key: 'critical', label: 'Critical', count: criticalCount, activeClass: 'bg-gradient-to-r from-rose-500 to-rose-600 text-white', inactiveClass: 'bg-rose-100 text-rose-700 hover:bg-rose-200' },
    { key: 'high', label: 'High', count: highCount, activeClass: 'bg-gradient-to-r from-orange-500 to-orange-600 text-white', inactiveClass: 'bg-orange-100 text-orange-700 hover:bg-orange-200' },
    { key: 'medium', label: 'Medium', count: mediumCount, activeClass: 'bg-gradient-to-r from-amber-500 to-amber-600 text-white', inactiveClass: 'bg-amber-100 text-amber-700 hover:bg-amber-200' },
    { key: 'low', label: 'Low', count: lowCount, activeClass: 'bg-gradient-to-r from-sky-500 to-sky-600 text-white', inactiveClass: 'bg-sky-100 text-sky-700 hover:bg-sky-200' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <Link to="/" className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 font-medium group">
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          {t('backToDashboard')}
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight">
              <span className="gradient-text">{t('activeAlertsTitle')}</span>
            </h1>
            <p className="mt-2 text-slate-500">{t('realTimeAlerts')}</p>
          </div>
          <div className="bg-gradient-to-br from-amber-400 to-orange-500 p-3 rounded-2xl shadow-lg shadow-amber-500/25">
            <AlertTriangle className="h-7 w-7 text-white" />
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="glass-card rounded-2xl p-5 card-hover animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{t('totalAlerts')}</p>
              <p className="text-3xl font-bold text-slate-800 mt-1">{alerts.length}</p>
            </div>
            <div className="bg-slate-100 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-slate-500" />
            </div>
          </div>
        </div>

        <div className="stat-card-rose rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.05s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-white/80 uppercase tracking-wide">{t('critical')}</p>
              <p className="text-3xl font-bold mt-1">{criticalCount}</p>
            </div>
            <div className="bg-white/20 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
        </div>

        <div className="stat-card-amber rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.1s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-white/80 uppercase tracking-wide">{t('high')}</p>
              <p className="text-3xl font-bold mt-1">{highCount}</p>
            </div>
            <div className="bg-white/20 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.15s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{t('medium')}</p>
              <p className="text-3xl font-bold text-amber-600 mt-1">{mediumCount}</p>
            </div>
            <div className="bg-amber-100 p-2 rounded-lg">
              <Clock className="h-5 w-5 text-amber-500" />
            </div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.2s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Low</p>
              <p className="text-3xl font-bold text-sky-600 mt-1">{lowCount}</p>
            </div>
            <div className="bg-sky-100 p-2 rounded-lg">
              <CheckCircle className="h-5 w-5 text-sky-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="glass-card rounded-2xl p-4 mb-6">
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="h-5 w-5 text-slate-400" />
          <span className="text-sm font-semibold text-slate-600 mr-2">{t('filterBySeverity')}</span>
          <div className="flex gap-2 flex-wrap">
            {filterButtons.map(btn => (
              <button
                key={btn.key}
                onClick={() => setFilter(btn.key)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${filter === btn.key ? btn.activeClass : btn.inactiveClass}`}
              >
                {btn.label} ({btn.count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 mb-4">
            <CheckCircle className="h-10 w-10 text-emerald-500" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">{t('noAlerts')}</h3>
          <p className="text-slate-500">
            {filter === 'all'
              ? t('allSystemsRunning')
              : t('noSeverityAlerts').replace('{severity}', filter)}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert, index) => (
            <div
              key={`${alert.phc_id}-${index}`}
              className={`glass-card rounded-2xl border-l-4 ${getSeverityBorder(alert.severity)} p-5 animate-fade-in-up`}
              style={{animationDelay: `${index * 0.04}s`}}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className="bg-slate-100 p-2 rounded-lg mt-0.5">
                    {getSeverityIcon(alert.severity)}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="bg-slate-100 p-1 rounded text-slate-500">
                        {getTypeIcon(alert.type)}
                      </div>
                      <h3 className="text-base font-bold text-slate-800">
                        {alert.type.replace('_', ' ').toUpperCase()}
                      </h3>
                      <span className={`px-3 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      {alert.method && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-violet-50 text-violet-600 border border-violet-100">
                          {alert.method.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mb-3">
                      <Building2 className="h-4 w-4 text-slate-400" />
                      <Link
                        to={`/phc/${alert.phc_id}/${alert.phc_name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                        className="text-primary-600 hover:text-primary-700 font-semibold text-sm"
                      >
                        {alert.phc_name}
                      </Link>
                    </div>

                    <p className="text-sm text-slate-600 mb-2">{alert.description}</p>

                    <p className="text-xs text-slate-400">
                      Created: {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Alert Types Legend */}
      <div className="mt-8 glass-card rounded-2xl p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">{t('alertTypes')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3 bg-rose-50/50 rounded-xl p-4 border border-rose-100">
            <div className="bg-rose-100 p-2 rounded-lg">
              <Pill className="h-4 w-4 text-rose-600" />
            </div>
            <div>
              <p className="font-bold text-slate-800 text-sm">{t('stockout')}</p>
              <p className="text-sm text-slate-500">{t('stockoutDescription')}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 bg-orange-50/50 rounded-xl p-4 border border-orange-100">
            <div className="bg-orange-100 p-2 rounded-lg">
              <Building2 className="h-4 w-4 text-orange-600" />
            </div>
            <div>
              <p className="font-bold text-slate-800 text-sm">{t('underperforming')}</p>
              <p className="text-sm text-slate-500">{t('underperformingDescription')}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 bg-amber-50/50 rounded-xl p-4 border border-amber-100">
            <div className="bg-amber-100 p-2 rounded-lg">
              <UserX className="h-4 w-4 text-amber-600" />
            </div>
            <div>
              <p className="font-bold text-slate-800 text-sm">{t('attendance')}</p>
              <p className="text-sm text-slate-500">{t('attendanceDescription')}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 bg-violet-50/50 rounded-xl p-4 border border-violet-100">
            <div className="bg-violet-100 p-2 rounded-lg">
              <Bed className="h-4 w-4 text-violet-600" />
            </div>
            <div>
              <p className="font-bold text-slate-800 text-sm">{t('bedShortage')}</p>
              <p className="text-sm text-slate-500">{t('bedShortageDescription')}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Alerts;
