import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Play, AlertTriangle, CheckCircle, Clock,
  Activity, Pill, Users, Bed, UserX, Globe, Cpu, Zap, Calendar, UserCheck
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { advanceSimulationDay, triggerSimulationEvent, getPHCs, getSimulationStatus } from '../services/api';

function Simulation() {
  const { t } = useLanguage();
  const [phcs, setPhcs] = useState([]);
  const [selectedPHC, setSelectedPHC] = useState('');
  const [eventType, setEventType] = useState('disease_outbreak');
  const [duration, setDuration] = useState(3);
  const [severity, setSeverity] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(() => {
    try {
      const saved = sessionStorage.getItem('simulationResult');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });
  const [simulationMode, setSimulationMode] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState(null);
  const [phcsLoading, setPhcsLoading] = useState(true);
  const [phcsError, setPhcsError] = useState(null);

  useEffect(() => {
    loadPHCs();
    loadSimulationStatus();
  }, []);

  useEffect(() => {
    if (result) {
      sessionStorage.setItem('simulationResult', JSON.stringify(result));
    }
  }, [result]);

  const loadPHCs = async () => {
    setPhcsLoading(true);
    setPhcsError(null);
    try {
      const res = await getPHCs();
      setPhcs(res.data);
      if (res.data.length > 0) {
        setSelectedPHC(res.data[0].id.toString());
      }
    } catch (error) {
      console.error('Error loading PHCs:', error);
      setPhcsError('Failed to load PHCs. Please ensure the database is seeded.');
    } finally {
      setPhcsLoading(false);
    }
  };

  const loadSimulationStatus = async () => {
    try {
      const res = await getSimulationStatus();
      setSimulationStatus(res.data);
      setSimulationMode(res.data.is_active);
    } catch (error) {
      console.error('Error loading simulation status:', error);
    }
  };

  const handleAdvanceDay = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await advanceSimulationDay({ days: 1 });
      setResult(res.data);
      setSimulationMode(true);
      await loadSimulationStatus();
    } catch (error) {
      console.error('Error advancing simulation:', error);
      setResult({ success: false, message: 'Error advancing simulation' });
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerEvent = async () => {
    if (!selectedPHC) {
      alert('Please select a PHC');
      return;
    }

    setLoading(true);
    setResult(null);
    sessionStorage.removeItem('simulationResult');
    try {
      const res = await triggerSimulationEvent({
        event_type: eventType,
        phc_id: parseInt(selectedPHC),
        duration_days: duration,
        severity: severity
      });
      setResult(res.data);
      setSimulationMode(true);
      await loadSimulationStatus();
    } catch (error) {
      console.error('Error triggering event:', error);
      setResult({ success: false, message: 'Error triggering event' });
    } finally {
      setLoading(false);
    }
  };

  const handleClearResult = () => {
    setResult(null);
    sessionStorage.removeItem('simulationResult');
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'disease_outbreak': return <Activity className="h-5 w-5 text-rose-500" />;
      case 'delayed_resupply': return <Pill className="h-5 w-5 text-orange-500" />;
      case 'doctor_absence_spike': return <UserX className="h-5 w-5 text-amber-500" />;
      default: return <AlertTriangle className="h-5 w-5 text-slate-500" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <Link to="/" className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 font-medium group">
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          Back to Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight">
              <span className="gradient-text">{t('simulationControlPanel')}</span>
            </h1>
            <p className="mt-2 text-slate-500">{t('simulationDescription')}</p>
          </div>
          <div className="bg-gradient-to-br from-primary-500 to-violet-600 p-3 rounded-2xl shadow-lg shadow-primary-500/25">
            <Cpu className="h-7 w-7 text-white" />
          </div>
        </div>
      </div>

      {/* Simulation Mode Toggle */}
      <div className={`rounded-2xl p-5 mb-8 border transition-all ${
        simulationMode
          ? 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200'
          : 'bg-gradient-to-r from-slate-50 to-slate-100 border-slate-200'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${simulationMode ? 'bg-emerald-100' : 'bg-slate-200'}`}>
              {simulationMode
                ? <Zap className="h-6 w-6 text-emerald-600" />
                : <Clock className="h-6 w-6 text-slate-500" />
              }
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">{t('simulationMode')}</h3>
              <p className="text-sm text-slate-500 mt-0.5">
                {simulationMode
                  ? 'Simulation is active. Dashboard and alerts will reflect simulated changes.'
                  : 'Activate simulation mode to test live system reactions to events.'}
              </p>
              {simulationStatus && (
                <p className="text-xs text-slate-400 mt-1">{simulationStatus.message}</p>
              )}
            </div>
          </div>
          <div className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 ${
            simulationMode
              ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
              : 'bg-slate-100 text-slate-500 border border-slate-300'
          }`}>
            <span className={`w-2 h-2 rounded-full ${simulationMode ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
            {simulationMode ? 'ACTIVE' : 'INACTIVE'}
          </div>
        </div>
      </div>

      {/* Simulation Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* Advance Day */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-primary-100 p-2 rounded-lg">
              <Calendar className="h-5 w-5 text-primary-600" />
            </div>
            <h2 className="text-lg font-bold text-slate-800">{t('advanceOneDay')}</h2>
          </div>
          <p className="text-sm text-slate-500 mb-5">{t('advanceDayDescription')}</p>
          <button
            onClick={handleAdvanceDay}
            disabled={loading}
            className="w-full bg-gradient-to-r from-primary-500 to-violet-500 text-white px-4 py-3.5 rounded-xl font-semibold hover:from-primary-600 hover:to-violet-600 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-lg shadow-primary-500/20"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              <>
                <Play className="h-5 w-5 mr-2" />
                {t('advanceOneDay')}
              </>
            )}
          </button>
        </div>

        {/* Trigger Event */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-rose-100 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-rose-600" />
            </div>
            <h2 className="text-lg font-bold text-slate-800">{t('triggerEvent')}</h2>
          </div>
          <p className="text-sm text-slate-500 mb-4">{t('triggerEventDescription')}</p>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-1">{t('selectPHC')}</label>
              {phcsLoading ? (
                <div className="w-full px-3 py-2.5 border border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm">
                  Loading PHCs...
                </div>
              ) : phcsError ? (
                <div className="w-full px-3 py-2.5 border border-rose-200 rounded-xl bg-rose-50 text-rose-600 text-sm">
                  {phcsError}
                </div>
              ) : phcs.length === 0 ? (
                <div className="w-full px-3 py-2.5 border border-amber-200 rounded-xl bg-amber-50 text-amber-600 text-sm">
                  No PHCs found. Please seed the database first.
                </div>
              ) : (
                <select
                  value={selectedPHC}
                  onChange={(e) => setSelectedPHC(e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl bg-white/60 focus:ring-2 focus:ring-primary-400 focus:border-primary-400 text-sm font-medium text-slate-700 transition-all"
                >
                  {phcs.map(phc => (
                    <option key={phc.id} value={phc.id}>{phc.name}</option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-1">{t('eventType')}</label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-200 rounded-xl bg-white/60 focus:ring-2 focus:ring-primary-400 focus:border-primary-400 text-sm font-medium text-slate-700 transition-all"
              >
                <option value="disease_outbreak">{t('diseaseOutbreak')}</option>
                <option value="delayed_resupply">{t('delayedResupply')}</option>
                <option value="doctor_absence_spike">{t('doctorAbsenceSpike')}</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-slate-600 mb-1">{t('duration')}</label>
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  min="1"
                  max="14"
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl bg-white/60 focus:ring-2 focus:ring-primary-400 focus:border-primary-400 text-sm font-medium text-slate-700 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-600 mb-1">{t('severity')}</label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl bg-white/60 focus:ring-2 focus:ring-primary-400 focus:border-primary-400 text-sm font-medium text-slate-700 transition-all"
                >
                  <option value="low">{t('low')}</option>
                  <option value="medium">{t('medium')}</option>
                  <option value="high">{t('high')}</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleTriggerEvent}
              disabled={loading}
              className="w-full bg-gradient-to-r from-rose-500 to-rose-600 text-white px-4 py-3.5 rounded-xl font-semibold hover:from-rose-600 hover:to-rose-700 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-lg shadow-rose-500/20"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : result ? (
                <>
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  Trigger New Event
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5 mr-2" />
                  {t('triggerEvent')}
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Simulation Results */}
      {result && (
        <div className="glass-card rounded-2xl p-6 mb-8 animate-fade-in-up">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              {result.success ? (
                <div className="bg-emerald-100 p-1.5 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                </div>
              ) : (
                <div className="bg-rose-100 p-1.5 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-rose-600" />
                </div>
              )}
              {t('simulationResults')}
            </h2>
            <button
              onClick={handleClearResult}
              className="text-sm text-slate-400 hover:text-slate-600 px-3 py-1 rounded-lg hover:bg-slate-100 transition-colors"
            >
              ✕ Dismiss
            </button>
          </div>

          <div className="space-y-4">
            <div className={`p-4 rounded-xl border ${result.success ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'}`}>
              <p className="text-sm font-semibold text-slate-500">{t('message')}:</p>
              <p className="text-lg font-bold text-slate-800 mt-0.5">{result.message}</p>
            </div>

            {result.simulated_date && (
              <div className="p-4 bg-primary-50 border border-primary-200 rounded-xl">
                <p className="text-sm font-semibold text-slate-500">{t('simulatedDate')}:</p>
                <p className="text-lg font-bold text-primary-700 mt-0.5">{result.simulated_date}</p>
              </div>
            )}

            {result.changes && (
              <div className="p-4 bg-slate-50/80 border border-slate-200 rounded-xl">
                <p className="text-sm font-bold text-slate-600 mb-3">{t('changes')}:</p>

                {/* District Summary */}
                {result.changes.district_summary && (
                  <div className="mb-4 p-4 bg-gradient-to-r from-primary-50 to-violet-50 border border-primary-100 rounded-xl">
                    <p className="font-bold text-primary-700 mb-3 text-sm">District-Wide Impact:</p>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <Users className="h-3.5 w-3.5 text-primary-500" />
                        <span className="text-slate-600">PHCs Affected:</span>
                        <span className="font-bold text-slate-800">{result.changes.district_summary.total_phcs_affected}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="h-3.5 w-3.5 text-emerald-500" />
                        <span className="text-slate-600">Total Patients:</span>
                        <span className="font-bold text-slate-800">{result.changes.district_summary.total_patients}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
                        <span className="text-slate-600">Emergency:</span>
                        <span className="font-bold text-slate-800">{result.changes.district_summary.total_emergency}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <UserCheck className="h-3.5 w-3.5 text-amber-500" />
                        <span className="text-slate-600">Avg Attendance:</span>
                        <span className="font-bold text-slate-800">{result.changes.district_summary.avg_attendance}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Bed className="h-3.5 w-3.5 text-violet-500" />
                        <span className="text-slate-600">Avg Bed Occ:</span>
                        <span className="font-bold text-slate-800">{result.changes.district_summary.avg_bed_occupancy}%</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-1 text-sm text-slate-600 max-h-96 overflow-y-auto">
                  {result.changes.stock_changes && result.changes.stock_changes.length > 0 && (
                    <div>
                      <p className="font-bold mt-2 text-slate-700">• Stock Changes ({result.changes.stock_changes.length} total):</p>
                      <div className="ml-4 mt-1 space-y-1 max-h-40 overflow-y-auto">
                        {result.changes.stock_changes.slice(0, 10).map((change, idx) => (
                          <p key={idx} className="text-xs flex items-center gap-1">
                            <Pill className="h-3 w-3 text-slate-400" />
                            <span className="font-semibold">[{change.phc_name}]</span> {change.medicine_name}: {change.quantity} units
                            <span className={change.change > 0 ? 'text-emerald-600 font-medium' : 'text-rose-600 font-medium'}>
                              ({change.change > 0 ? '+' : ''}{change.change})
                            </span>
                            {change.restock_ordered && (
                              <span className="ml-1 text-orange-600 font-medium px-1.5 py-0.5 bg-orange-100 rounded-full text-[10px]">
                                ⏳ Arrives {change.restock_arrives_on}
                              </span>
                            )}
                            {change.restock_arrived && (
                              <span className="ml-1 text-emerald-600 font-medium px-1.5 py-0.5 bg-emerald-100 rounded-full text-[10px]">
                                ✓ Arrived
                              </span>
                            )}
                          </p>
                        ))}
                        {result.changes.stock_changes.length > 10 && (
                          <p className="text-xs text-slate-400">... and {result.changes.stock_changes.length - 10} more</p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.changes.footfall_changes && result.changes.footfall_changes.length > 0 && (
                    <div>
                      <p className="font-bold mt-2 text-slate-700">• Footfall Changes ({result.changes.footfall_changes.length} total):</p>
                      <div className="ml-4 mt-1 space-y-1 max-h-40 overflow-y-auto">
                        {result.changes.footfall_changes.slice(0, 5).map((change, idx) => (
                          <p key={idx} className="text-xs flex items-center gap-1">
                            <Users className="h-3 w-3 text-slate-400" />
                            <span className="font-semibold">[{change.phc_name}]</span> {change.total_patients} patients, {change.emergency_cases} emergency
                          </p>
                        ))}
                        {result.changes.footfall_changes.length > 5 && (
                          <p className="text-xs text-slate-400">... and {result.changes.footfall_changes.length - 5} more</p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.changes.bed_changes && result.changes.bed_changes.length > 0 && (
                    <div>
                      <p className="font-bold mt-2 text-slate-700">• Bed Occupancy Changes ({result.changes.bed_changes.length} total):</p>
                      <div className="ml-4 mt-1 space-y-1 max-h-40 overflow-y-auto">
                        {result.changes.bed_changes.slice(0, 5).map((change, idx) => (
                          <p key={idx} className="text-xs flex items-center gap-1">
                            <Bed className="h-3 w-3 text-slate-400" />
                            <span className="font-semibold">[{change.phc_name}]</span> {change.occupancy_rate}% occupancy, {change.available_beds} beds available
                          </p>
                        ))}
                        {result.changes.bed_changes.length > 5 && (
                          <p className="text-xs text-slate-400">... and {result.changes.bed_changes.length - 5} more</p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.changes.attendance_changes && result.changes.attendance_changes.length > 0 && (
                    <div>
                      <p className="font-bold mt-2 text-slate-700">• Attendance Changes ({result.changes.attendance_changes.length} total):</p>
                      <div className="ml-4 mt-1 space-y-1 max-h-40 overflow-y-auto">
                        {result.changes.attendance_changes.slice(0, 5).map((change, idx) => (
                          <p key={idx} className="text-xs flex items-center gap-1">
                            <UserCheck className="h-3 w-3 text-slate-400" />
                            <span className="font-semibold">[{change.phc_name}]</span> {change.attendance_rate}% attendance, {change.absent_doctors} absent
                          </p>
                        ))}
                        {result.changes.attendance_changes.length > 5 && (
                          <p className="text-xs text-slate-400">... and {result.changes.attendance_changes.length - 5} more</p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.changes.test_changes && result.changes.test_changes.length > 0 && (
                    <div>
                      <p className="font-bold mt-2 text-slate-700">• Test Availability Changes ({result.changes.test_changes.length} total):</p>
                      <div className="ml-4 mt-1 space-y-1 max-h-40 overflow-y-auto">
                        {result.changes.test_changes.slice(0, 5).map((change, idx) => (
                          <p key={idx} className="text-xs flex items-center gap-1">
                            <Activity className="h-3 w-3 text-slate-400" />
                            <span className="font-semibold">[{change.phc_name}]</span> {change.test_name}: {change.is_available ? 'Available' : 'Unavailable'}
                          </p>
                        ))}
                        {result.changes.test_changes.length > 5 && (
                          <p className="text-xs text-slate-400">... and {result.changes.test_changes.length - 5} more</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Simulation Guide */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="bg-amber-100 p-2 rounded-lg">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-800">Simulation Guide</h3>
        </div>
        <ul className="space-y-3 text-sm text-slate-600">
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-600 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">1</span>
            <span><strong className="text-slate-800">Advance 1 Day:</strong> Click this to move the simulation forward by one day. Watch the dashboard metrics update in real-time.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">2</span>
            <span><strong className="text-slate-800">Disease Outbreak:</strong> Simulates a disease outbreak at the selected PHC, causing a spike in patient footfall and accelerated medicine consumption.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">3</span>
            <span><strong className="text-slate-800">Delayed Resupply:</strong> Simulates a delayed medicine delivery, causing stock levels to deplete faster and triggering stock-out alerts.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-600 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">4</span>
            <span><strong className="text-slate-800">Doctor Absence Spike:</strong> Simulates a sudden increase in doctor absences, affecting the attendance metric and health score.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">5</span>
            <span><strong className="text-slate-800">Live System Flow:</strong> After triggering an event, navigate to Dashboard, Alerts, and Recommendations pages to see how the entire system reacts in real-time.</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default Simulation;
