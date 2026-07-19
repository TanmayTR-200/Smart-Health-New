import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Pill, Users, Bed, UserCheck, AlertTriangle,
  TrendingUp, TrendingDown, Minus, ChevronRight
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Area, AreaChart
} from 'recharts';
import { getPHC, getStock, getFootfall, getBedOccupancy, getAttendance } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

const CHART_COLORS = {
  primary: '#6366f1',
  emergency: '#ef4444',
  occupied: '#f59e0b',
  available: '#10b981',
  present: '#10b981',
  absent: '#ef4444',
};

function PHCDetail() {
  const { id } = useParams();
  const { t } = useLanguage();
  const [phc, setPhc] = useState(null);
  const [stock, setStock] = useState([]);
  const [footfall, setFootfall] = useState([]);
  const [beds, setBeds] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [phcRes, stockRes, footfallRes, bedsRes, attendanceRes, stockoutRes, demandRes] = await Promise.all([
        getPHC(id),
        getStock({ phc_id: id, days: 15 }),
        getFootfall({ phc_id: id, days: 15 }),
        getBedOccupancy({ phc_id: id, days: 15 }),
        getAttendance({ phc_id: id, days: 15 }),
      ]);
      setPhc(phcRes.data);
      setStock(stockRes.data);
      setFootfall(footfallRes.data);
      setBeds(bedsRes.data);
      setAttendance(attendanceRes.data);
    } catch (error) {
      console.error('Error loading PHC data:', error);
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

  if (!phc) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-rose-600 font-medium">PHC not found</div>
      </div>
    );
  }

  // Prepare chart data
  const getContiguous = (arr, maxDays) => {
    if (!arr || arr.length === 0) return [];
    const sorted = [...arr].sort((a, b) => new Date(b.date) - new Date(a.date));
    const result = [sorted[0]];
    for (let i = 1; i < sorted.length && result.length < maxDays; i++) {
      const prev = new Date(result[result.length - 1].date);
      const curr = new Date(sorted[i].date);
      const diff = Math.round((prev - curr) / (1000 * 60 * 60 * 24));
      if (diff > 1) break;
      result.push(sorted[i]);
    }
    return result.reverse();
  };

  const footfallChartData = getContiguous(footfall, 15).map(f => ({
    date: new Date(f.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    patients: f.total_patients,
    emergency: f.emergency_cases
  }));

  const bedChartData = getContiguous(beds, 15).map(b => ({
    date: new Date(b.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    occupied: b.occupied_beds,
    available: b.available_beds
  }));

  const attendanceChartData = getContiguous(attendance, 15).map(a => ({
    date: new Date(a.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    present: a.present_doctors,
    absent: a.absent_doctors,
    patient_load: a.patient_load_per_doctor
  }));

  const avgFootfall = footfall.length > 0
    ? Math.round(footfall.reduce((sum, f) => sum + f.total_patients, 0) / footfall.length)
    : 0;
  const latestOccupancy = beds.length > 0
    ? beds[0].occupancy_rate.toFixed(1)
    : 0;
  const displayAvgAttendance = attendance.length > 0
    ? attendance[0].attendance_rate.toFixed(1)
    : 0;

  const lowStockItems = stock.filter(s => s.quantity < s.min_required);

  const tooltipStyle = {
    background: 'rgba(255,255,255,0.95)',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
    fontSize: '13px',
  };

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
            <div className="flex items-center gap-3 mb-2">
              <span className={`w-3 h-3 rounded-full ${getStatusDot(phc.status || 'warning')} animate-pulse`}></span>
              <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">{phc.name}</h1>
            </div>
            <p className="text-slate-500 flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs font-mono font-semibold">{phc.code}</span>
              <span>•</span>
              <span>{phc.type}</span>
              <span>•</span>
              <span>{phc.district}</span>
            </p>
          </div>
          <span className={`px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wide ${getStatusColor(phc.status || 'warning')}`}>
            {phc.status || 'warning'}
          </span>
        </div>
      </div>

      {/* PHC Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
        <div className="stat-card-sky rounded-2xl p-5 card-hover animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('totalBeds')}</p>
              <p className="text-3xl font-bold mt-1">{phc.total_beds}</p>
            </div>
            <div className="bg-white/20 p-2.5 rounded-xl">
              <Bed className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="stat-card-primary rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.05s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('expectedDoctors')}</p>
              <p className="text-3xl font-bold mt-1">{phc.expected_doctors}</p>
            </div>
            <div className="bg-white/20 p-2.5 rounded-xl">
              <UserCheck className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="stat-card-emerald rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.1s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('avgDailyFootfall')}</p>
              <p className="text-3xl font-bold mt-1">{avgFootfall}</p>
            </div>
            <div className="bg-white/20 p-2.5 rounded-xl">
              <Users className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="stat-card-violet rounded-2xl p-5 card-hover animate-fade-in-up" style={{animationDelay: '0.15s'}}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">{t('healthScore')}</p>
              <p className="text-3xl font-bold mt-1">{phc.health_score?.toFixed(1) || 'N/A'}</p>
            </div>
            <div className="bg-white/20 p-2.5 rounded-xl">
              {getTrendIcon(phc.footfall_trend || 'stable')}
            </div>
          </div>
        </div>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <div className="bg-gradient-to-r from-rose-50 to-orange-50 border border-rose-200 rounded-2xl p-5 mb-8 animate-fade-in-up">
          <div className="flex items-start">
            <div className="bg-rose-100 p-2 rounded-xl mr-4">
              <AlertTriangle className="h-5 w-5 text-rose-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-rose-800 mb-2">{t('lowStockAlert')}</h3>
              <div className="space-y-1">
                {lowStockItems.slice(0, 5).map(item => (
                  <p key={item.id} className="text-sm text-rose-700 flex items-center gap-2">
                    <span className="font-semibold">{item.medicine_name}:</span>
                    <span className="font-mono bg-rose-100 px-1.5 py-0.5 rounded text-xs">{item.quantity} / {item.min_required}</span>
                    {item.restock_arrives_on && (
                      <span className="ml-1 text-orange-600 font-medium text-xs px-2 py-0.5 bg-orange-100 rounded-full">
                        ⏳ Restock arriving {item.restock_arrives_on}
                      </span>
                    )}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 gap-5 mb-8">
        {/* Footfall Trend */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-5">
            <h2 className="text-lg font-bold text-slate-800">{t('patientFootfall')}</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={footfallChartData}>
              <defs>
                <linearGradient id="colorPatients" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorEmergency" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.emergency} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CHART_COLORS.emergency} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="patients" stroke={CHART_COLORS.primary} strokeWidth={2.5} fill="url(#colorPatients)" name="Total Patients" />
              <Area type="monotone" dataKey="emergency" stroke={CHART_COLORS.emergency} strokeWidth={2.5} fill="url(#colorEmergency)" name="Emergency" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Bed Occupancy */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">{t('bedOccupancyLast30Days')}</h2>

          {beds.length > 0 && (
            <div className="mb-4 p-4 bg-slate-50/80 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-700">{beds[0].occupied_beds} beds occupied</span>
                  <span className="text-slate-400">of {beds[0].total_beds} total</span>
                  <span className={`ml-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    latestOccupancy >= 90 ? 'bg-rose-100 text-rose-700' :
                    latestOccupancy >= 70 ? 'bg-orange-100 text-orange-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    {latestOccupancy}%
                  </span>
                </div>
                <div className="text-slate-400 text-xs">
                  {beds[0].available_beds} available • {beds[0].reserved_beds} reserved
                </div>
              </div>
            </div>
          )}

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bedChartData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="occupied" fill={CHART_COLORS.occupied} name="Occupied" radius={[4, 4, 0, 0]} />
              <Bar dataKey="available" fill={CHART_COLORS.available} name="Available" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Doctor Attendance with Patient Load */}
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-5">{t('doctorAttendanceLast30Days')}</h2>

          {attendance.length > 0 && (
            <div className="mb-4 p-4 bg-slate-50/80 rounded-xl border border-slate-100">
              {(() => {
                const latest = attendance[0];
                const normalLoad = 35;
                const loadDisplay = latest.patient_load_per_doctor;
                return (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-700">{latest.present_doctors} doctors present</span>
                      <span className="text-slate-400">of {latest.expected_doctors} expected</span>
                      <span className={`ml-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        latest.attendance_rate >= 80 ? 'bg-emerald-100 text-emerald-700' :
                        latest.attendance_rate >= 60 ? 'bg-amber-100 text-amber-700' :
                        'bg-rose-100 text-rose-700'
                      }`}>
                        {latest.attendance_rate.toFixed(0)}%
                      </span>
                    </div>
                    {loadDisplay && (
                      <div className={`font-semibold text-xs ${
                        loadDisplay > normalLoad * 1.5 ? 'text-rose-600' :
                        loadDisplay > normalLoad ? 'text-orange-600' :
                        'text-emerald-600'
                      }`}>
                        {loadDisplay.toFixed(0)} patients/doctor
                        <span className="text-slate-400 font-normal ml-1">(normal: {normalLoad})</span>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={attendanceChartData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value, name) => {
                  if (name === 'patient_load') return [`${value} patients/doctor`, 'Patient Load'];
                  return [value, name === 'present' ? 'Present' : 'Absent'];
                }}
              />
              <Bar dataKey="present" fill={CHART_COLORS.present} name="Present" radius={[4, 4, 0, 0]} />
              <Bar dataKey="absent" fill={CHART_COLORS.absent} name="Absent" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stock Details */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <h2 className="text-lg font-bold text-slate-800">{t('currentStockLevels')}</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{t('medicine')}</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{t('currentStock')}</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{t('minRequired')}</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{t('status')}</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{t('lastRestocked')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stock.slice(0, 10).map(item => {
                const ratio = item.min_required > 0 ? item.quantity / item.min_required : 0;
                const isLow = item.quantity < item.min_required;
                const isWarning = !isLow && ratio < 1.5;
                return (
                <tr key={item.id} className={`transition-colors hover:bg-slate-50/50 ${isLow ? 'bg-rose-50/40' : isWarning ? 'bg-amber-50/40' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-800">
                    {item.medicine_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="font-mono font-semibold text-slate-700">{item.quantity}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="font-mono text-slate-500">{item.min_required}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {isLow ? (
                      <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-rose-100 text-rose-700">
                        {t('lowStock')}
                      </span>
                    ) : isWarning ? (
                      <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-amber-100 text-amber-700">
                        Warning
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-100 text-emerald-700">
                        {t('ok')}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {new Date(item.last_restocked).toLocaleDateString()}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default PHCDetail;
