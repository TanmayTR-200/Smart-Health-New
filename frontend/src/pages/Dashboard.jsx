import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, Users, Pill, Bed, UserCheck, AlertTriangle,
  TrendingUp, TrendingDown, Minus, ArrowRight, ChevronRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadialBarChart, RadialBar
} from 'recharts';
import { getDashboardSummary, getAlerts, getPHCs } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

const COLORS = {
  good: '#10b981',
  warning: '#f59e0b',
  critical: '#ef4444',
  primary: '#6366f1',
  violet: '#8b5cf6',
  sky: '#0ea5e9',
};

const RADIAL_COLORS = ['#10b981', '#f59e0b', '#ef4444'];

function Dashboard() {
  const { t } = useLanguage();
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [phcs, setPhcs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, alertsRes, phcsRes] = await Promise.all([
        getDashboardSummary(),
        getAlerts(),
        getPHCs()
      ]);
      setSummary(summaryRes.data);
      setAlerts(alertsRes.data.slice(0, 5));
      setPhcs(phcsRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'bg-emerald-100 text-emerald-700 border border-emerald-200';
      case 'warning': return 'bg-amber-100 text-amber-700 border border-amber-200';
      case 'critical': return 'bg-rose-100 text-rose-700 border border-rose-200';
      default: return 'bg-slate-100 text-slate-700 border border-slate-200';
    }
  };

  const getStatusDot = (status) => {
    switch (status) {
      case 'good': return 'bg-emerald-500';
      case 'warning': return 'bg-amber-500';
      case 'critical': return 'bg-rose-500';
      default: return 'bg-slate-400';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      default: return 'bg-sky-50 text-sky-700 border-sky-200';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="h-4 w-4 text-emerald-500" />;
      case 'decreasing': return <TrendingDown className="h-4 w-4 text-rose-500" />;
      default: return <Minus className="h-4 w-4 text-slate-400" />;
    }
  };

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

  if (!summary) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-rose-600 font-medium">{t('error')}</div>
      </div>
    );
  }

  // Prepare chart data
  const healthScoreData = summary.phc_health_scores.map(score => ({
    name: score.phc_code,
    score: score.health_score,
    stock: score.stock_health,
    attendance: score.attendance_rate,
    beds: score.bed_occupancy_rate
  }));

  const statusDistribution = [
    { name: t('good'), value: summary.phc_health_scores.filter(s => s.status === 'good').length, fill: COLORS.good },
    { name: t('warning'), value: summary.phc_health_scores.filter(s => s.status === 'warning').length, fill: COLORS.warning },
    { name: t('critical'), value: summary.phc_health_scores.filter(s => s.status === 'critical').length, fill: COLORS.critical },
  ];

  const healthScorePct = Math.round(summary.avg_health_score || 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-100 text-primary-700 text-xs font-semibold border border-primary-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              LIVE
            </span>
            <span className="text-[10px] text-slate-400 ml-1">First load may take 30-60s (server cold start)</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight">
            <span className="gradient-text">{t('districtHealthDashboard')}</span>
          </h1>
          <p className="mt-2 text-slate-500">{t('realTimeOverview')}</p>
        </div>
        {summary.simulated_date && (
          <div className="glass-card rounded-2xl px-5 py-3 text-right">
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Simulated Date</p>
            <p className="text-lg font-bold text-slate-800">
              {new Date(summary.simulated_date).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}
            </p>
          </div>
        )}
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div className="stat-card-primary rounded-2xl p-5 card-hover animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('totalPHCs')}</p>
              <p className="text-4xl font-bold mt-1">{summary.total_phcs}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Activity className="h-7 w-7" />
            </div>
          </div>
        </div>

        <div className="stat-card-emerald rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.05s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('patientsToday')}</p>
              <p className="text-4xl font-bold mt-1">{summary.total_patients_today}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Users className="h-7 w-7" />
            </div>
          </div>
        </div>

        <div className="stat-card-rose rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.1s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('stockOutsToday')}</p>
              <p className="text-4xl font-bold mt-1">{summary.total_stockouts}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Pill className="h-7 w-7" />
            </div>
          </div>
        </div>

        <div className="stat-card-sky rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.15s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('avgAttendance')}</p>
              <p className="text-4xl font-bold mt-1">{summary.avg_attendance_rate.toFixed(1)}%</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <UserCheck className="h-7 w-7" />
            </div>
          </div>
        </div>
      </div>

      {/* Alerts and PHC Health Scores */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        {/* Alerts Panel */}
        <div className="lg:col-span-1 glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <div className="bg-amber-100 p-1.5 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
              </div>
              {t('activeAlerts')}
            </h2>
            <Link to="/alerts" className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1 group">
              {t('viewAll')}
              <ChevronRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-100 mb-2">
                  <UserCheck className="h-6 w-6 text-emerald-500" />
                </div>
                <p className="text-slate-400 text-sm">{t('noActiveAlerts')}</p>
              </div>
            ) : (
              alerts.map((alert, index) => (
                <div
                  key={`${alert.phc_id}-${index}`}
                  className={`p-3 rounded-xl border ${getSeverityColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{alert.phc_name}</p>
                      <p className="text-xs mt-1 opacity-80">{alert.description}</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/60 font-semibold uppercase">
                      {alert.severity}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* District Average Health Score */}
          <div className="mt-6 pt-6 border-t border-slate-200/60">
            <div className="bg-gradient-to-br from-primary-50 to-violet-50 rounded-2xl p-5 border border-primary-100">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">District Avg Health Score</p>
                {summary.simulated_date && (
                  <span className="text-[10px] text-slate-400">
                    as of {new Date(summary.simulated_date).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                  </span>
                )}
              </div>
              <div className="flex items-baseline gap-2">
                <p className="text-5xl font-extrabold gradient-text">
                  {typeof summary.avg_health_score === 'number' ? summary.avg_health_score.toFixed(1) : 'N/A'}
                </p>
                <span className="text-sm text-slate-400 font-medium">/ 100</span>
              </div>
              <div className="mt-4 h-2.5 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    healthScorePct >= 80 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' :
                    healthScorePct >= 60 ? 'bg-gradient-to-r from-amber-400 to-amber-500' :
                    'bg-gradient-to-r from-rose-400 to-rose-500'
                  }`}
                  style={{ width: `${healthScorePct}%` }}
                />
              </div>
              <div className="flex justify-between mt-1.5 text-[10px] text-slate-400 font-medium">
                <span>Critical (&lt;60)</span>
                <span>Warning (60-80)</span>
                <span>Good (80+)</span>
              </div>
            </div>
          </div>
        </div>

        {/* PHC Health Scores */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">{t('phcHealthScores')}</h2>
          <div className="space-y-3">
            {summary.phc_health_scores.map((phc, idx) => (
              <Link
                key={phc.phc_id}
                to={`/phc/${phc.phc_id}/${phc.phc_name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                className="block p-4 rounded-xl border border-slate-200/60 hover:border-primary-300 hover:bg-primary-50/30 transition-all duration-200 group"
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className={`w-2.5 h-2.5 rounded-full ${getStatusDot(phc.status)}`}></span>
                      <h3 className="font-semibold text-slate-800 group-hover:text-primary-600 transition-colors">{phc.phc_name}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${getStatusColor(phc.status)}`}>
                        {phc.status}
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center gap-1.5">
                        <Pill className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-slate-500 text-xs">Stock:</span>
                        <span className="font-semibold text-slate-700 text-xs">{phc.stock_health.toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <UserCheck className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-slate-500 text-xs">Doc Attendance:</span>
                        <span className="font-semibold text-slate-700 text-xs">{phc.attendance_rate.toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Bed className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-slate-500 text-xs">Bed Occupancy:</span>
                        <span className="font-semibold text-slate-700 text-xs">{phc.bed_occupancy_rate.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-3xl font-extrabold text-slate-800">{phc.health_score.toFixed(1)}</p>
                      <p className="text-[10px] text-slate-400 font-medium">Health Score</p>
                    </div>
                    {getTrendIcon(phc.footfall_trend)}
                    <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-primary-500 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* Health Score Comparison */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">{t('healthScoreComparison')}</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={healthScoreData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(255,255,255,0.95)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                  fontSize: '13px',
                }}
              />
              <Bar dataKey="score" fill={COLORS.primary} name="Overall Score" radius={[6, 6, 0, 0]} />
              <Bar dataKey="stock" fill={COLORS.good} name="Stock Health" radius={[6, 6, 0, 0]} />
              <Bar dataKey="attendance" fill={COLORS.warning} name="Attendance" radius={[6, 6, 0, 0]} />
              <Bar dataKey="beds" fill={COLORS.violet} name="Bed Occupancy" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">{t('phcStatusDistribution')}</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={90}
                innerRadius={50}
                paddingAngle={3}
                dataKey="value"
              >
                {statusDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={RADIAL_COLORS[index % RADIAL_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: 'rgba(255,255,255,0.95)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                  fontSize: '13px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="stat-card-amber rounded-2xl p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-white/90">{t('bedOccupancy')}</h3>
            <div className="bg-white/20 p-2 rounded-lg">
              <Bed className="h-5 w-5" />
            </div>
          </div>
          <p className="text-4xl font-bold">{summary.avg_bed_occupancy.toFixed(1)}%</p>
          <p className="text-sm text-white/70 mt-1">{t('averageAcrossAllPHCs')}</p>
        </div>

        <div className="stat-card-violet rounded-2xl p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-white/90">{t('criticalAlerts')}</h3>
            <div className="bg-white/20 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <p className="text-4xl font-bold">{summary.critical_alerts}</p>
          <p className="text-sm text-white/70 mt-1">
            {summary.warning_alerts} {t('warningAlerts').toLowerCase()}
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
