import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  GitMerge, ArrowLeft, AlertTriangle, CheckCircle, Clock,
  Pill, Building2, MapPin, TrendingUp, RefreshCw, ArrowRight, Info
} from 'lucide-react';
import { getRedistributionRecommendations, getLowStock, translateText } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { RecommendationsSkeleton } from '../components/Skeleton';

function Recommendations() {
  const { t, language } = useLanguage();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [districtShortage, setDistrictShortage] = useState(false);
  const [stockoutCount, setStockoutCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const translateRecommendations = async (recs) => {
    if (language === 'en') return recs;
    const translated = await Promise.all(
      recs.map(async (rec) => {
        const [reasonTr, impactTr] = await Promise.all([
          translateText(rec.reason, language),
          translateText(rec.impact, language),
        ]);
        return { ...rec, reason: reasonTr.data.translated_text, impact: impactTr.data.translated_text };
      })
    );
    return translated;
  };

  const loadRecommendations = async () => {
    try {
      const res = await getRedistributionRecommendations();
      let recs = res.data;
      recs = await translateRecommendations(recs);
      setRecommendations(recs);

      if (recs.length === 0) {
        try {
          const lowStockRes = await getLowStock();
          const lowStockItems = lowStockRes.data;
          setStockoutCount(lowStockItems.length);
          setDistrictShortage(lowStockItems.length > 0);
        } catch (err) {
          setDistrictShortage(false);
        }
      } else {
        setDistrictShortage(false);
      }
    } catch (error) {
      console.error('Error loading recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadRecommendations();
    } finally {
      setRefreshing(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      default: return 'bg-sky-50 text-sky-700 border-sky-200';
    }
  };

  const getPriorityBorder = (priority) => {
    switch (priority) {
      case 'critical': return 'border-l-rose-500';
      case 'high': return 'border-l-orange-500';
      case 'medium': return 'border-l-amber-500';
      default: return 'border-l-sky-500';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical': return <AlertTriangle className="h-5 w-5 text-rose-500" />;
      case 'high': return <Clock className="h-5 w-5 text-orange-500" />;
      default: return <CheckCircle className="h-5 w-5 text-sky-500" />;
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [language]);

  if (loading) {
    return <RecommendationsSkeleton />;
  }

  const criticalCount = recommendations.filter(r => r.urgency === 'critical').length;
  const highCount = recommendations.filter(r => r.urgency === 'high').length;
  const totalQuantity = recommendations.reduce((sum, r) => sum + r.quantity, 0);

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
              <span className="gradient-text">{t('resourceRedistribution')}</span>
            </h1>
            <p className="mt-2 text-slate-500">{t('aiPoweredRecommendations')}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium border border-slate-200 bg-white/70 backdrop-blur text-slate-700 hover:border-primary-300 hover:bg-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''} text-primary-500`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
            <div className="bg-gradient-to-br from-primary-500 to-violet-600 p-3 rounded-2xl shadow-lg shadow-primary-500/25">
              <GitMerge className="h-7 w-7 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {recommendations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          <div className="stat-card-rose rounded-2xl p-5 card-hover animate-fade-in-up">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">{t('criticalActions')}</p>
                <p className="text-4xl font-bold mt-1">{criticalCount}</p>
                <p className="text-xs text-white/60 mt-1">{t('requireImmediateAttention')}</p>
              </div>
              <div className="bg-white/20 p-2.5 rounded-xl">
                <AlertTriangle className="h-6 w-6" />
              </div>
            </div>
          </div>

          <div className="stat-card-amber rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.05s'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">{t('highPriority')}</p>
                <p className="text-4xl font-bold mt-1">{highCount}</p>
                <p className="text-xs text-white/60 mt-1">{t('planWithin24Hours')}</p>
              </div>
              <div className="bg-white/20 p-2.5 rounded-xl">
                <Clock className="h-6 w-6" />
              </div>
            </div>
          </div>

          <div className="stat-card-primary rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.1s'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">{t('totalUnitsToRedistribute')}</p>
                <p className="text-4xl font-bold mt-1">{totalQuantity}</p>
                <p className="text-xs text-white/60 mt-1">
                  {t('acrossRecommendations').replace('{count}', recommendations.length)}
                </p>
              </div>
              <div className="bg-white/20 p-2.5 rounded-xl">
                <TrendingUp className="h-6 w-6" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations List */}
      {recommendations.length === 0 ? (
        districtShortage ? (
          <div className="glass-card rounded-2xl p-12 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-orange-100 mb-4">
              <AlertTriangle className="h-10 w-10 text-orange-500" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">District-Wide Shortage Detected</h3>
            <p className="text-slate-500 mb-4 max-w-md mx-auto">
              {stockoutCount} stock item(s) are below minimum threshold across the district,
              but <strong className="text-slate-700">no PHC has surplus stock</strong> available to redistribute.
            </p>
            <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 max-w-lg mx-auto">
              <p className="text-sm text-orange-800 text-left">
                <strong>What this means:</strong> All PHCs are experiencing shortage simultaneously.
                External resupply orders have been placed automatically and will arrive within 3-5 days.
                No redistribution is possible until at least one PHC receives a restock delivery.
              </p>
            </div>
          </div>
        ) : (
          <div className="glass-card rounded-2xl p-12 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 mb-4">
              <CheckCircle className="h-10 w-10 text-emerald-500" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">{t('allGood')}</h3>
            <p className="text-slate-500">{t('noRecommendations')}</p>
          </div>
        )
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className={`glass-card rounded-2xl border-l-4 ${getPriorityBorder(rec.urgency)} p-6 animate-fade-in-up`}
              style={{animationDelay: `${index * 0.05}s`}}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="bg-slate-100 p-2 rounded-lg">
                      {getPriorityIcon(rec.urgency)}
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">
                      {t('transfer')} <span className="text-primary-600">{rec.quantity}</span> {t('unitsOf')} {rec.medicine_name}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${getPriorityColor(rec.urgency)}`}>
                      {rec.urgency}
                    </span>
                    {rec.method && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-violet-50 text-violet-600 border border-violet-100">
                        {rec.method.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* From PHC */}
                    <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-100">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="bg-emerald-100 p-1.5 rounded-lg">
                          <Building2 className="h-3.5 w-3.5 text-emerald-600" />
                        </div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">{t('fromSource')}</p>
                      </div>
                      <Link
                        to={`/phc/${rec.from_phc_id}/${rec.from_phc_name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                        className="text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1 group"
                      >
                        {rec.from_phc_name}
                        <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                      <p className="text-xs text-slate-500 mt-1">Excess {rec.medicine_name} ({rec.quantity}+ units above reserve)</p>
                    </div>

                    {/* To PHC */}
                    <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-100">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="bg-rose-100 p-1.5 rounded-lg">
                          <MapPin className="h-3.5 w-3.5 text-rose-600" />
                        </div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">{t('toDestination')}</p>
                      </div>
                      <Link
                        to={`/phc/${rec.to_phc_id}/${rec.to_phc_name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                        className="text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1 group"
                      >
                        {rec.to_phc_name}
                        <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                      <p className="text-xs text-slate-500 mt-1">Short on {rec.medicine_name} (below threshold)</p>
                    </div>
                  </div>

                  {/* Reason and Impact */}
                  <div className="bg-gradient-to-r from-primary-50 to-violet-50 border border-primary-100 rounded-xl p-4">
                    <p className="text-sm text-slate-700">
                      <span className="font-bold text-primary-700">{t('reason')}:</span> {rec.reason}
                    </p>
                    <p className="text-sm text-slate-700 mt-1.5">
                      <span className="font-bold text-primary-700">{t('impact')}:</span> {rec.impact}
                    </p>
                  </div>
                </div>

                {/* Medicine Icon */}
                <div className="ml-4">
                  <div className="bg-gradient-to-br from-primary-500 to-violet-600 p-3 rounded-2xl shadow-lg shadow-primary-500/20">
                    <Pill className="h-8 w-8 text-white" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 glass-card rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="bg-primary-100 p-2 rounded-lg">
            <Info className="h-5 w-5 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-800">{t('howRedistributionWorks')}</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-50/60 rounded-xl p-4 border border-slate-100">
            <p className="font-bold text-slate-700 text-sm mb-1">{t('excessDetection')}</p>
            <p className="text-sm text-slate-500">{t('excessDescription')}</p>
          </div>
          <div className="bg-slate-50/60 rounded-xl p-4 border border-slate-100">
            <p className="font-bold text-slate-700 text-sm mb-1">{t('criticalNeedDetection')}</p>
            <p className="text-sm text-slate-500">{t('criticalNeedDescription')}</p>
          </div>
          <div className="bg-slate-50/60 rounded-xl p-4 border border-slate-100">
            <p className="font-bold text-slate-700 text-sm mb-1">{t('optimalTransfer')}</p>
            <p className="text-sm text-slate-500">{t('optimalTransferDescription')}</p>
          </div>
          <div className="bg-slate-50/60 rounded-xl p-4 border border-slate-100">
            <p className="font-bold text-slate-700 text-sm mb-1">{t('priorityRanking')}</p>
            <p className="text-sm text-slate-500">{t('priorityRankingDescription')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
