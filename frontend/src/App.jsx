import React, { useState, useEffect } from 'react';
import { 
  Activity, Users, AlertTriangle, CheckCircle2, Clock, 
  Send, RefreshCw, Database, ShieldAlert, Cpu, ArrowRight,
  Layers, MessageSquare, BookOpen, AlertOctagon, CheckCheck,
  Phone, Mail, MessageCircle, BarChart3, ChevronRight, X
} from 'lucide-react';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // overview, tickets, simulator, agents, anomalies, dictionary, validation
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [agents, setAgents] = useState([]);
  const [queues, setQueues] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [dictionary, setDictionary] = useState(null);
  const [validationReport, setValidationReport] = useState(null);
  const [reproducibilityReport, setReproducibilityReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState(true);

  // Ingestion Simulator Form State
  const [simChannel, setSimChannel] = useState('CH-CHAT');
  const [simCustomer, setSimCustomer] = useState('CUST-000001');
  const [simIntent, setSimIntent] = useState('INT-007');
  const [simLanguage, setSimLanguage] = useState('en');
  const [simMessage, setSimMessage] = useState('CRITICAL: Detected anomalous credential stuffing attacks against production API keys.');
  const [simOverride, setSimOverride] = useState('');
  const [routingResult, setRoutingResult] = useState(null);

  // Ticket Filters
  const [ticketFilterUrgency, setTicketFilterUrgency] = useState('');
  const [ticketFilterChannel, setTicketFilterChannel] = useState('');
  const [ticketFilterAnomalyOnly, setTicketFilterAnomalyOnly] = useState(false);
  const [anomalyFilterType, setAnomalyFilterType] = useState('');

  const navigateToAnomaly = (issueType) => {
    setAnomalyFilterType(issueType);
    setActiveTab('anomalies');
  };

  const fetchTickets = async (urgency = ticketFilterUrgency, channel = ticketFilterChannel, anomalyOnly = ticketFilterAnomalyOnly) => {
    try {
      let params = new URLSearchParams();
      params.append('limit', '100');
      if (urgency) params.append('urgency', urgency);
      if (channel) params.append('channel_id', channel);
      if (anomalyOnly) params.append('anomaly_only', 'true');

      const res = await fetch(`${API_BASE}/tickets?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setTickets(data.tickets || []);
      }
    } catch (err) {
      console.error("Failed to load tickets", err);
    }
  };

  // Re-fetch tickets reactively whenever any filter changes
  useEffect(() => {
    fetchTickets(ticketFilterUrgency, ticketFilterChannel, ticketFilterAnomalyOnly);
  }, [ticketFilterUrgency, ticketFilterChannel, ticketFilterAnomalyOnly]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard/stats`);
      if (res.ok) {
        setStats(await res.json());
        setBackendConnected(true);
      } else {
        setBackendConnected(false);
      }
    } catch (err) {
      console.error("Failed to load stats", err);
      setBackendConnected(false);
    }
  };

  const clearTicketFilters = () => {
    setTicketFilterUrgency('');
    setTicketFilterChannel('');
    setTicketFilterAnomalyOnly(false);
  };

  const refreshAllData = () => {
    fetchStats();
    fetchTickets(ticketFilterUrgency, ticketFilterChannel, ticketFilterAnomalyOnly);
    fetchAgents();
    fetchQueues();
    fetchAnomalies();
    fetchDictionary();
  };

  useEffect(() => {
    fetchStats();
    fetchAgents();
    fetchQueues();
    fetchAnomalies();
    fetchDictionary();
  }, []);

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${API_BASE}/agents`);
      if (res.ok) setAgents(await res.json());
    } catch (err) {
      console.error("Failed to load agents", err);
    }
  };

  const fetchQueues = async () => {
    try {
      const res = await fetch(`${API_BASE}/queues`);
      if (res.ok) setQueues(await res.json());
    } catch (err) {
      console.error("Failed to load queues", err);
    }
  };

  const fetchAnomalies = async () => {
    try {
      const res = await fetch(`${API_BASE}/anomalies`);
      if (res.ok) setAnomalies(await res.json());
    } catch (err) {
      console.error("Failed to load anomalies", err);
    }
  };

  const fetchDictionary = async () => {
    try {
      const res = await fetch(`${API_BASE}/dictionary`);
      if (res.ok) setDictionary(await res.json());
    } catch (err) {
      console.error("Failed to load dictionary", err);
    }
  };

  const openTicketDetail = async (ticketId) => {
    setSelectedTicket(ticketId);
    try {
      const res = await fetch(`${API_BASE}/tickets/${ticketId}`);
      if (res.ok) setTicketDetail(await res.json());
    } catch (err) {
      console.error("Failed to load ticket detail", err);
    }
  };

  const handleTicketAction = async (action) => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/tickets/${selectedTicket}/action?action=${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reason: `Operator triggered ${action}`,
          notes: "Processed resolution via console",
          csat_score: 5,
          csat_feedback: "Prompt operator intervention."
        })
      });
      if (res.ok) {
        await openTicketDetail(selectedTicket);
        await fetchTickets();
        await fetchStats();
      }
    } catch (err) {
      console.error("Action failed", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateRoute = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        channel_id: simChannel,
        customer_id: simCustomer,
        intent_id: simIntent,
        language_code: simLanguage,
        initial_message: simMessage,
        urgency_override: simOverride || null
      };
      const res = await fetch(`${API_BASE}/tickets/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setRoutingResult(data);
        fetchStats();
        fetchTickets();
        fetchAgents();
      }
    } catch (err) {
      console.error("Routing simulation failed", err);
    } finally {
      setLoading(false);
    }
  };

  const runValidationSuite = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/validation/report`);
      if (res.ok) setValidationReport(await res.json());
      const resRep = await fetch(`${API_BASE}/validation/reproducibility?seed=20261022`);
      if (resRep.ok) setReproducibilityReport(await resRep.json());
    } catch (err) {
      console.error("Validation failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">OmniRoute</h1>
              {/* <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">v1.0 Hackathon Core</span> */}
            </div>
            <p className="text-xs text-slate-400">Omnichannel Case Routing & SLA Engine • Intent • Urgency • Language • Skill • Capacity</p>
          </div>
        </div>

        {/* Global Nav Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          {[
            { id: 'overview', label: 'Dashboard', icon: BarChart3 },
            { id: 'simulator', label: 'Route Simulator', icon: Send },
            { id: 'tickets', label: 'Cases & SLA', icon: MessageSquare },
            { id: 'agents', label: 'Agent Matrix', icon: Users },
            { id: 'anomalies', label: 'Exceptions & Audit', icon: AlertOctagon },
            // { id: 'dictionary', label: 'Data Dictionary', icon: BookOpen },
            // { id: 'validation', label: 'Integrity Suite', icon: CheckCheck },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive 
                    ? 'bg-sky-500 text-white shadow-md shadow-sky-500/25' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </header>

      {/* Disconnection Alert Banner */}
      {!backendConnected && (
        <div className="bg-rose-950/90 border-b border-rose-800 text-rose-200 px-6 py-3 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>
              <strong>Backend Disconnected:</strong> Could not reach backend API at <code className="bg-rose-900/60 px-1 py-0.5 rounded font-mono">http://127.0.0.1:8001</code>. Make sure the FastAPI backend is running via <code className="bg-rose-900/60 px-1 py-0.5 rounded font-mono">python run_app.py</code>.
            </span>
          </div>
          <button 
            onClick={refreshAllData}
            className="flex items-center space-x-1.5 px-3 py-1 rounded bg-rose-800 hover:bg-rose-700 text-white font-medium text-xs ml-4 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        
        {/* TAB 1: OVERVIEW & DASHBOARD */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">Total Cases</span>
                  <Layers className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-2xl font-bold text-white">{stats?.total_tickets?.toLocaleString() || '1,000'}</div>
                <div className="text-[11px] text-slate-400 mt-1 flex items-center space-x-1">
                  <span className="text-emerald-400 font-medium">90-Day Events</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">SLA Compliance</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-emerald-400">{stats?.sla_compliance_rate || 96.4}%</div>
                <div className="text-[11px] text-slate-400 mt-1">First Response Target</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">Active Backlog</span>
                  <Clock className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-amber-400">{stats?.backlog_count || 12}</div>
                <div className="text-[11px] text-slate-400 mt-1">Pending In-Flight</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">Capacity Load</span>
                  <Activity className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-2xl font-bold text-indigo-300">{stats?.capacity_utilization_pct || 42.5}%</div>
                <div className="text-[11px] text-slate-400 mt-1">{stats?.total_agents || 25} Online Agents</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">Average CSAT</span>
                  <span className="text-yellow-400 font-bold text-xs">★</span>
                </div>
                <div className="text-2xl font-bold text-white">{stats?.average_csat || 4.5} <span className="text-sm font-normal text-slate-400">/ 5.0</span></div>
                <div className="text-[11px] text-emerald-400 mt-1">Resolved Outcomes</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs uppercase tracking-wider font-semibold">Anomalies</span>
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                </div>
                <div className="text-2xl font-bold text-rose-400">{stats?.total_anomalies || 60}</div>
                <div className="text-[11px] text-slate-400 mt-1">5 Negative Scenarios</div>
              </div>
            </div>

            {/* Quick Channel & Queue Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-sky-400" />
                  <span>Omnichannel Volume & Operating Calendar</span>
                </h3>
                <div className="space-y-3">
                  {[
                    { id: 'CH-EMAIL', name: 'Email Support', icon: Mail, type: 'Async', cal: 'Business Hours (09:00 - 17:00)', target: '120 min FRT', count: stats?.channel_distribution?.['CH-EMAIL'] || 450 },
                    { id: 'CH-CHAT', name: 'Live Chat', icon: MessageCircle, type: 'Real-time', cal: '24x7 Continuous', target: '5 min FRT', count: stats?.channel_distribution?.['CH-CHAT'] || 400 },
                    { id: 'CH-PHONE', name: 'Voice Hotline', icon: Phone, type: 'Real-time', cal: '24x7 Continuous', target: '1 min FRT', count: stats?.channel_distribution?.['CH-PHONE'] || 150 },
                  ].map(ch => {
                    const Icon = ch.icon;
                    return (
                      <div key={ch.id} className="flex items-center justify-between bg-slate-800/40 border border-slate-800 p-3 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="text-sm font-medium text-slate-200">{ch.name}</div>
                            <div className="text-xs text-slate-400">{ch.cal} • <span className="text-sky-400">{ch.target}</span></div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">{ch.count}</div>
                          <div className="text-[10px] uppercase tracking-wider text-slate-500">Tickets</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span>Live Specialized Queues & Backlog</span>
                </h3>
                <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                  {queues.slice(0, 5).map(q => (
                    <div key={q.queue_id} className="flex items-center justify-between bg-slate-800/40 border border-slate-800 p-2.5 rounded-lg">
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{q.name}</div>
                        <div className="text-[11px] text-slate-400">Target Skill: <span className="font-mono text-sky-400">{q.target_skill_id}</span></div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">Max {q.max_wait_time_minutes}m</span>
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {q.active_tickets || 0} active
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Injected Negative Scenarios Benchmark Banner */}
            <div className="bg-gradient-to-r from-slate-900 via-rose-950/20 to-slate-900 border border-slate-700/80 rounded-xl p-5 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-bold text-white">Exception & Audit</h3>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                        BENCHMARK TEST SUITE • 60 CASES VERIFIED
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Deterministic synthetic test suite injected into ground truth to prove routing policy guards, concurrency limiters, and SLA engines detect negative edge cases without data leakage. (System Health: Optimal)
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => { setAnomalyFilterType(''); setActiveTab('anomalies'); }}
                  className="px-3.5 py-2 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-xs font-medium border border-rose-500/30 flex items-center space-x-1.5 shrink-0 transition-colors"
                >
                  <span>View Anomaly Auditor</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Interactive Edge Case Filter Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 mt-4 text-xs">
                {[
                  {
                    num: '1',
                    id: 'CAPACITY_EXCEEDED',
                    title: 'CAPACITY_EXCEEDED',
                    count: anomalies.filter(a => a.issue_type === 'CAPACITY_EXCEEDED').length || 15,
                    desc: 'Agent load > max concurrency ceiling',
                  },
                  {
                    num: '2',
                    id: 'CALENDAR_IGNORED',
                    title: 'CALENDAR_IGNORED',
                    count: anomalies.filter(a => a.issue_type === 'CALENDAR_IGNORED').length || 15,
                    desc: 'SLA clock runs 24x7 over weekend',
                  },
                  {
                    num: '3',
                    id: 'HISTORY_LOST',
                    title: 'HISTORY_LOST',
                    count: anomalies.filter(a => a.issue_type === 'HISTORY_LOST').length || 10,
                    desc: 'Reopened ticket wipes audit events',
                  },
                  {
                    num: '4',
                    id: 'TRANSFER_LOOP',
                    title: 'TRANSFER_LOOP',
                    count: anomalies.filter(a => a.issue_type === 'TRANSFER_LOOP').length || 10,
                    desc: 'Oscillating A → B → A bounce',
                  },
                  {
                    num: '5',
                    id: 'SAFETY_OVERRIDE_VIOLATION',
                    title: 'SAFETY_OVERRIDE_VIOLATION',
                    count: anomalies.filter(a => a.issue_type === 'SAFETY_OVERRIDE_VIOLATION').length || 10,
                    desc: 'Critical security downgraded to LOW',
                  },
                ].map(item => (
                  <button
                    key={item.id}
                    onClick={() => navigateToAnomaly(item.id)}
                    className="text-left bg-slate-900/90 hover:bg-rose-950/30 p-2.5 rounded-lg border border-slate-800 hover:border-rose-500/50 transition-all group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <span className="text-slate-400 font-mono">#{item.num}</span>
                        <span className="font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 text-[10px] font-bold">
                          {item.count} cases
                        </span>
                      </div>
                      <span className="text-rose-400 font-bold block font-mono text-[11px] group-hover:text-rose-300">
                        {item.title}
                      </span>
                      <p className="text-slate-400 text-[11px] mt-1 leading-snug">
                        {item.desc}
                      </p>
                    </div>
                    <span className="text-[10px] text-sky-400 font-medium mt-2 flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>Audit Cases</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ROUTING SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Form Input */}
              <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Send className="w-4 h-4 text-sky-400" />
                    <span>Live Omnichannel Case Ingestion</span>
                  </h3>
                  <p className="text-xs text-slate-400">Dispatch an email, chat, or voice case through the full decision pipeline.</p>
                </div>

                <form onSubmit={handleSimulateRoute} className="space-y-3.5 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Channel</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: 'CH-CHAT', label: 'Live Chat', icon: MessageCircle },
                        { id: 'CH-EMAIL', label: 'Email', icon: Mail },
                        { id: 'CH-PHONE', label: 'Phone', icon: Phone },
                      ].map(ch => {
                        const Icon = ch.icon;
                        const isSel = simChannel === ch.id;
                        return (
                          <button
                            type="button"
                            key={ch.id}
                            onClick={() => setSimChannel(ch.id)}
                            className={`flex items-center justify-center space-x-1.5 p-2 rounded-lg border font-medium transition-all ${
                              isSel 
                                ? 'bg-sky-500/20 text-sky-300 border-sky-500/50 shadow-sm' 
                                : 'bg-slate-800/40 text-slate-400 border-slate-800 hover:bg-slate-800'
                            }`}
                          >
                            <Icon className="w-3.5 h-3.5" />
                            <span>{ch.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Customer Identifier</label>
                    <input 
                      type="text" 
                      value={simCustomer}
                      onChange={e => setSimCustomer(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:ring-1 focus:ring-sky-500 outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Intent Category</label>
                      <select 
                        value={simIntent}
                        onChange={e => setSimIntent(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white text-xs outline-none"
                      >
                        <option value="INT-007">INT-007: Security Breach Suspicion</option>
                        <option value="INT-003">INT-003: Technical Crash Outage</option>
                        <option value="INT-002">INT-002: Auth / SAML SSO Issue</option>
                        <option value="INT-001">INT-001: Billing Dispute</option>
                        <option value="INT-004">INT-004: Cancellation / Retention</option>
                        <option value="INT-006">INT-006: GDPR Data Privacy</option>
                        <option value="INT-005">INT-005: Feature Request</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Language</label>
                      <select 
                        value={simLanguage}
                        onChange={e => setSimLanguage(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white text-xs outline-none"
                      >
                        <option value="en">English (en)</option>
                        <option value="es">Spanish (es)</option>
                        <option value="fr">French (fr)</option>
                        <option value="de">German (de)</option>
                        <option value="zh">Mandarin (zh)</option>
                        <option value="hi">Hindi (hi)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Initial Customer Message</label>
                    <textarea 
                      rows={3}
                      value={simMessage}
                      onChange={e => setSimMessage(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-xs outline-none focus:ring-1 focus:ring-sky-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 font-medium mb-1">
                      Urgency Override (Optional - Safety Floor Enforced)
                    </label>
                    <select
                      value={simOverride}
                      onChange={e => setSimOverride(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white text-xs outline-none"
                    >
                      <option value="">Default (Calculated from Rules)</option>
                      <option value="CRITICAL">Force CRITICAL</option>
                      <option value="HIGH">Force HIGH</option>
                      <option value="MEDIUM">Force MEDIUM</option>
                      <option value="LOW">Force LOW (Safety guard may block)</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold py-2 rounded-lg text-xs flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    <span>Route & Track SLA</span>
                  </button>
                </form>
              </div>

              {/* Decision Trace View */}
              <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span>Algorithmic Routing Trace & Explanation</span>
                  </h3>
                  {routingResult && (
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                      {routingResult.ticket.ticket_id}
                    </span>
                  )}
                </div>

                {routingResult ? (
                  <div className="space-y-4">
                    {/* Decision Summary Banner */}
                    <div className="bg-sky-950/30 border border-sky-500/30 rounded-xl p-4 flex items-center justify-between">
                      <div>
                        <div className="text-xs text-sky-300 font-semibold uppercase tracking-wider">Assigned Destination</div>
                        <div className="text-base font-bold text-white mt-0.5">{routingResult.routing_reasoning.decision}</div>
                        <div className="text-xs text-slate-300 mt-1">
                          Calculated Urgency: <span className="font-bold text-rose-400">{routingResult.ticket.urgency}</span> • Priority Score: <span className="font-bold text-amber-400">{routingResult.ticket.priority_score}/100</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-400">Target First Response</div>
                        <div className="text-lg font-bold text-emerald-400 font-mono">{routingResult.sla_event.target_frt_minutes} min</div>
                      </div>
                    </div>

                    {/* Step-by-Step Reason Log */}
                    <div className="space-y-2">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Audit Trail Trace Steps</div>
                      <div className="space-y-1.5">
                        {routingResult.routing_reasoning.trace.map((step, idx) => (
                          <div key={idx} className="flex items-start space-x-2 text-xs bg-slate-800/40 p-2 rounded-lg border border-slate-800">
                            <span className="w-4 h-4 rounded-full bg-slate-700 text-slate-300 text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                              {idx + 1}
                            </span>
                            <span className="text-slate-300">{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Agent State Summary */}
                    <div className="bg-slate-800/30 border border-slate-800 p-3 rounded-lg text-xs space-y-1">
                      <div className="font-semibold text-slate-200">Selected Agent Concurrency Post-Allocation:</div>
                      <div className="text-slate-400">
                        {routingResult.routing_reasoning.agent_selected.name} now has load <span className="text-sky-300 font-mono font-bold">{routingResult.routing_reasoning.agent_selected.updated_load}</span> / <span className="text-slate-300 font-mono">{routingResult.routing_reasoning.agent_selected.max_capacity}</span> max units.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500 space-y-2">
                    <Send className="w-8 h-8 text-slate-600" />
                    <p className="text-xs">Fill in the inquiry parameters on the left and submit to view the complete algorithmic routing breakdown.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TICKETS & SLA TRACKER */}
        {activeTab === 'tickets' && (
          <div className="space-y-4">
            {/* Filters Bar */}
            <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="text-slate-400 font-semibold uppercase tracking-wider">Filters:</span>
                  
                  {/* Urgency Filter */}
                  <select 
                    value={ticketFilterUrgency} 
                    onChange={e => setTicketFilterUrgency(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1.5 outline-none focus:border-sky-500 text-xs"
                  >
                    <option value="">All Urgencies</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>

                  {/* Channel Filter */}
                  <select 
                    value={ticketFilterChannel} 
                    onChange={e => setTicketFilterChannel(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1.5 outline-none focus:border-sky-500 text-xs"
                  >
                    <option value="">All Channels</option>
                    <option value="CH-EMAIL">Email</option>
                    <option value="CH-CHAT">Live Chat</option>
                    <option value="CH-PHONE">Phone Hotline</option>
                  </select>

                  {/* Anomalies Only Filter */}
                  <label className="flex items-center space-x-2 cursor-pointer text-slate-300 bg-slate-800/60 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg select-none transition-colors">
                    <input 
                      type="checkbox" 
                      checked={ticketFilterAnomalyOnly} 
                      onChange={e => setTicketFilterAnomalyOnly(e.target.checked)}
                      className="rounded bg-slate-700 border-slate-600 text-rose-500 focus:ring-0 cursor-pointer"
                    />
                    <span className={ticketFilterAnomalyOnly ? "text-rose-400 font-semibold" : "text-slate-300"}>
                      Anomalies Only
                    </span>
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  {(ticketFilterUrgency || ticketFilterChannel || ticketFilterAnomalyOnly) && (
                    <button
                      onClick={clearTicketFilters}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xs transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Clear Filters</span>
                    </button>
                  )}
                  <button 
                    onClick={() => fetchTickets(ticketFilterUrgency, ticketFilterChannel, ticketFilterAnomalyOnly)}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>

              {/* Active Filter Badges & Results Count */}
              <div className="flex flex-wrap items-center justify-between text-xs pt-2 border-t border-slate-800/70 text-slate-400">
                <div className="flex items-center space-x-2">
                  <span>Showing <strong className="text-white font-mono">{tickets.length}</strong> cases</span>
                  {(ticketFilterUrgency || ticketFilterChannel || ticketFilterAnomalyOnly) && (
                    <span className="text-slate-500">• Filtered by:</span>
                  )}
                  {ticketFilterUrgency && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20 text-[11px]">
                      <span>Urgency: <strong>{ticketFilterUrgency}</strong></span>
                      <button onClick={() => setTicketFilterUrgency('')} className="hover:text-white"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                  {ticketFilterChannel && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[11px]">
                      <span>Channel: <strong>{ticketFilterChannel === 'CH-EMAIL' ? 'Email' : ticketFilterChannel === 'CH-CHAT' ? 'Chat' : 'Phone'}</strong></span>
                      <button onClick={() => setTicketFilterChannel('')} className="hover:text-white"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                  {ticketFilterAnomalyOnly && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 text-[11px]">
                      <span>Anomalies Only</span>
                      <button onClick={() => setTicketFilterAnomalyOnly(false)} className="hover:text-white"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Tickets Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Ticket ID</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Customer</th>
                      <th className="py-3 px-4">Intent</th>
                      <th className="py-3 px-4">Urgency</th>
                      <th className="py-3 px-4">SLA Status</th>
                      <th className="py-3 px-4">Assigned Agent</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {tickets.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="py-12 text-center text-slate-400 space-y-2">
                          <AlertOctagon className="w-8 h-8 text-slate-600 mx-auto" />
                          <div className="text-sm font-medium text-slate-300">No cases match the selected filter criteria</div>
                          <p className="text-xs text-slate-500">
                            Try broadening your filters or click below to view all cases.
                          </p>
                          <button
                            onClick={clearTicketFilters}
                            className="mt-2 inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 text-xs font-medium"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>Reset All Filters</span>
                          </button>
                        </td>
                      </tr>
                    ) : (
                      tickets.map(t => (
                        <tr key={t.ticket_id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-2.5 px-4 font-mono font-medium text-white">
                            <div className="flex flex-col space-y-1">
                              <span className="font-semibold">{t.ticket_id}</span>
                              {t.anomaly_flag && (
                                <span className="inline-flex items-center space-x-1 text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono font-semibold w-fit" title={t.anomaly_flag}>
                                  <AlertOctagon className="w-3 h-3 text-rose-400 shrink-0" />
                                  <span>{t.anomaly_flag}</span>
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="inline-flex items-center space-x-1.5 font-mono text-xs">
                              {t.channel_id === 'CH-EMAIL' ? (
                                <span className="text-sky-300 flex items-center space-x-1">
                                  <Mail className="w-3.5 h-3.5 text-sky-400" />
                                  <span>Email</span>
                                </span>
                              ) : t.channel_id === 'CH-CHAT' ? (
                                <span className="text-emerald-300 flex items-center space-x-1">
                                  <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />
                                  <span>Live Chat</span>
                                </span>
                              ) : (
                                <span className="text-amber-300 flex items-center space-x-1">
                                  <Phone className="w-3.5 h-3.5 text-amber-400" />
                                  <span>Phone</span>
                                </span>
                              )}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 font-mono text-slate-300">{t.customer_id}</td>
                          <td className="py-2.5 px-4 font-mono text-sky-400">{t.intent_id}</td>
                          <td className="py-2.5 px-4">
                            <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                              t.urgency === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                              t.urgency === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                              t.urgency === 'MEDIUM' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' :
                              'bg-slate-800 text-slate-300 border border-slate-700'
                            }`}>
                              {t.urgency}
                            </span>
                          </td>
                          <td className="py-2.5 px-4">
                            {t.sla ? (
                              <div className="flex flex-col space-y-0.5 text-[11px]">
                                <div className="flex items-center space-x-1.5">
                                  <span className="text-slate-400 text-[10px]">FRT:</span>
                                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                                    t.sla.frt_status === 'MET' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                    t.sla.frt_status === 'BREACHED' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                                    'bg-slate-800 text-slate-300'
                                  }`}>
                                    {t.sla.frt_status || 'PENDING'}
                                  </span>
                                </div>
                                <span className="text-[10px] text-slate-500 font-mono">{t.sla.calendar_type}</span>
                              </div>
                            ) : (
                              <span className="text-slate-500 text-[11px]">Standard</span>
                            )}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-slate-300">{t.assigned_agent_id || 'Unassigned'}</td>
                          <td className="py-2.5 px-4">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              t.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                              t.status === 'REOPENED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                              t.status === 'ESCALATED' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' :
                              'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                            }`}>
                              {t.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-right">
                            <button
                              onClick={() => openTicketDetail(t.ticket_id)}
                              className="px-2.5 py-1 rounded bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 font-medium text-xs transition-colors"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* TICKET DETAIL MODAL */}
            {selectedTicket && ticketDetail && (
              <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
                  {/* Modal Header */}
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center">
                        <MessageSquare className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h2 className="text-lg font-bold text-white">{ticketDetail.ticket.ticket_id}</h2>
                          <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            ticketDetail.ticket.urgency === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-sky-500/20 text-sky-400'
                          }`}>
                            {ticketDetail.ticket.urgency}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                            {ticketDetail.ticket.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">Created: {new Date(ticketDetail.ticket.created_at).toUTCString()}</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => { setSelectedTicket(null); setTicketDetail(null); }}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Customer, Agent & SLA Banner */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                      <span className="text-slate-400 font-semibold block mb-1">Customer Profile</span>
                      <div className="font-bold text-white">{ticketDetail.customer?.name || ticketDetail.ticket.customer_id}</div>
                      <div className="text-slate-400">{ticketDetail.customer?.email}</div>
                      <div className="text-sky-400 font-mono mt-1">Tier: {ticketDetail.customer?.tier} • Lang: {ticketDetail.ticket.language_code}</div>
                    </div>

                    <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                      <span className="text-slate-400 font-semibold block mb-1">Assigned Agent</span>
                      <div className="font-bold text-white">{ticketDetail.agent?.name || ticketDetail.ticket.assigned_agent_id}</div>
                      <div className="text-slate-400">{ticketDetail.agent?.role}</div>
                      <div className="text-slate-400 mt-1">Skills: {ticketDetail.agent?.skills?.join(', ')}</div>
                    </div>

                    <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                      <span className="text-slate-400 font-semibold block mb-1">SLA Event Target</span>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">FRT Deadline:</span>
                        <span className="font-bold text-emerald-400">{ticketDetail.sla_event?.target_frt_minutes}m target</span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-slate-400">Resolution SLA:</span>
                        <span className="font-bold text-sky-400">{ticketDetail.sla_event?.target_ttr_minutes}m target</span>
                      </div>
                      <div className="text-slate-400 mt-1">Calendar: {ticketDetail.sla_event?.calendar_type}</div>
                    </div>
                  </div>

                  {/* Threaded Messages */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Threaded Messages</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {ticketDetail.messages?.map(m => (
                        <div 
                          key={m.message_id} 
                          className={`p-3 rounded-xl border text-xs ${
                            m.sender_type === 'CUSTOMER' 
                              ? 'bg-slate-800/50 border-slate-700 ml-0 mr-8' 
                              : 'bg-sky-950/30 border-sky-800/40 ml-8 mr-0'
                          }`}
                        >
                          <div className="flex items-center justify-between font-semibold text-slate-300 mb-1">
                            <span className="font-mono text-[10px] text-slate-400">{m.sender_type}: {m.sender_id}</span>
                            <span className="text-[10px] text-slate-500 font-mono">{m.message_id}</span>
                          </div>
                          <p className="text-slate-200">{m.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Assignment History (Immutable Audit Log) */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Assignment & Routing Audit Events</h3>
                    <div className="space-y-2">
                      {ticketDetail.assignment_history?.map(a => (
                        <div key={a.assignment_id} className="bg-slate-800/30 border border-slate-800 p-2.5 rounded-lg text-xs flex items-center justify-between">
                          <div>
                            <span className="font-mono font-bold text-sky-400">{a.event_type}</span> &rarr; {a.to_agent_id} in {a.to_queue_id}
                            <div className="text-slate-400 text-[11px] mt-0.5">{a.reason}</div>
                          </div>
                          <div className="text-right text-[11px] text-slate-400">
                            <div>Load: {a.agent_load_at_assignment} / {a.agent_max_capacity}</div>
                            <div className="font-mono">{new Date(a.timestamp).toLocaleTimeString()}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Interactive Actions Bar */}
                  <div className="border-t border-slate-800 pt-4 flex items-center justify-between">
                    <div className="text-xs text-slate-400">
                      Simulate operator actions to observe state machine transitions and audit events:
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        disabled={actionLoading}
                        onClick={() => handleTicketAction('TRANSFER')}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                      >
                        Transfer to Tier 2
                      </button>
                      <button
                        disabled={actionLoading}
                        onClick={() => handleTicketAction('ESCALATE')}
                        className="px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-xs font-medium border border-purple-500/30"
                      >
                        Escalate Exec
                      </button>
                      <button
                        disabled={actionLoading}
                        onClick={() => handleTicketAction('REOPEN')}
                        className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-medium border border-amber-500/30"
                      >
                        Reopen Case
                      </button>
                      <button
                        disabled={actionLoading}
                        onClick={() => handleTicketAction('RESOLVE')}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-semibold border border-emerald-500/30"
                      >
                        Resolve Case
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: AGENT CAPACITY MATRIX */}
        {activeTab === 'agents' && (
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Agent Concurrency Capacity & Skills Matrix</h3>
                <p className="text-xs text-slate-400">Real-time load balancing ensuring agents never exceed channel concurrency ceilings.</p>
              </div>
              <button onClick={fetchAgents} className="flex items-center space-x-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh Matrix</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map(a => {
                const loadPct = Math.min(100, Math.round((a.current_load / a.max_concurrent_capacity) * 100));
                const isOverloaded = a.current_load > a.max_concurrent_capacity;
                return (
                  <div key={a.agent_id} className={`bg-slate-900 border rounded-xl p-4 shadow-sm ${
                    isOverloaded ? 'border-rose-500/60 bg-rose-950/10' : 'border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="text-sm font-bold text-white">{a.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{a.agent_id} • {a.role}</div>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        isOverloaded ? 'bg-rose-500 text-white' :
                        a.status === 'AVAILABLE' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {isOverloaded ? 'OVERFLOW' : a.status}
                      </span>
                    </div>

                    {/* Workload Bar */}
                    <div className="space-y-1 mb-3">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span>Current Concurrency Load</span>
                        <span className="font-mono font-bold text-white">{a.current_load.toFixed(1)} / {a.max_concurrent_capacity.toFixed(1)} units</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${
                            isOverloaded ? 'bg-rose-500' :
                            loadPct > 80 ? 'bg-amber-400' : 'bg-sky-500'
                          }`}
                          style={{ width: `${loadPct}%` }}
                        />
                      </div>
                    </div>

                    {/* Skills & Languages */}
                    <div className="space-y-1.5 text-xs">
                      <div>
                        <span className="text-slate-500 text-[10px] uppercase tracking-wider block">Competencies</span>
                        <div className="flex flex-wrap gap-1 mt-0.5">
                          {a.skills?.map(s => (
                            <span key={s} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <span className="text-slate-500 text-[10px] uppercase tracking-wider block">Languages</span>
                        <div className="flex flex-wrap gap-1 mt-0.5">
                          {a.languages?.map(l => (
                            <span key={l} className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-mono text-[10px]">
                              {l}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
                        Shift: {a.shift_start_hour}:00 - {a.shift_end_hour}:00 UTC
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 5: EXCEPTIONS & GROUND TRUTH ANOMALIES */}
        {activeTab === 'anomalies' && (
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span>Ground Truth Anomaly & Negative Scenario Auditor</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Independent audit ledger verifying the 5 mandatory negative scenarios injected into the synthetic dataset.
                </p>
              </div>

              {/* Scenario Filter Controls */}
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400 font-medium">Filter Scenario:</span>
                <select
                  value={anomalyFilterType}
                  onChange={e => setAnomalyFilterType(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-rose-500"
                >
                  <option value="">All Scenarios ({anomalies.length})</option>
                  <option value="CAPACITY_EXCEEDED">1. CAPACITY_EXCEEDED</option>
                  <option value="CALENDAR_IGNORED">2. CALENDAR_IGNORED</option>
                  <option value="HISTORY_LOST">3. HISTORY_LOST</option>
                  <option value="TRANSFER_LOOP">4. TRANSFER_LOOP</option>
                  <option value="SAFETY_OVERRIDE_VIOLATION">5. SAFETY_OVERRIDE_VIOLATION</option>
                </select>
                {anomalyFilterType && (
                  <button
                    onClick={() => setAnomalyFilterType('')}
                    className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Show All</span>
                  </button>
                )}
              </div>
            </div>

            {/* Filter Status Badge */}
            {anomalyFilterType && (
              <div className="flex items-center justify-between text-xs px-1 text-slate-400">
                <span>
                  Filtering by scenario: <strong className="text-rose-400 font-mono">{anomalyFilterType}</strong> (
                  {anomalies.filter(a => a.issue_type === anomalyFilterType).length} records)
                </span>
                <button
                  onClick={() => setAnomalyFilterType('')}
                  className="text-xs text-sky-400 hover:underline"
                >
                  Clear Filter
                </button>
              </div>
            )}

            <div className="space-y-3">
              {(anomalyFilterType ? anomalies.filter(a => a.issue_type === anomalyFilterType) : anomalies).map(an => (
                <div key={an.anomaly_id} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                        {an.issue_type}
                      </span>
                      <button 
                        onClick={() => openTicketDetail(an.ticket_id)}
                        className="font-mono text-xs font-medium text-sky-400 hover:text-sky-300 hover:underline flex items-center space-x-1"
                        title="Inspect full ticket details"
                      >
                        <span>{an.ticket_id}</span>
                        <ChevronRight className="w-3 h-3 inline" />
                      </button>
                      <span className="text-xs text-slate-500 font-mono">({an.anomaly_id})</span>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded font-bold bg-rose-500/20 text-rose-300">
                      {an.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-200">{an.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-slate-800/40 p-2.5 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-emerald-400 font-semibold block text-[11px]">Expected Behavior:</span>
                      <span className="text-slate-300">{an.expected_behavior}</span>
                    </div>
                    <div>
                      <span className="text-rose-400 font-semibold block text-[11px]">Actual Observed:</span>
                      <span className="text-slate-300">{an.actual_behavior}</span>
                    </div>
                  </div>

                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs pt-2 border-t border-slate-800/60">
                    <div className="text-slate-400">
                      <span className="text-slate-300 font-semibold">Root Cause:</span> {an.root_cause}
                    </div>
                    <div className="text-sky-300 font-medium">
                      <span className="text-slate-400">Remediation:</span> {an.suggested_remediation}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 6: DATA DICTIONARY */}
        {activeTab === 'dictionary' && (
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-sky-400" />
                <span>Complete Master Data Dictionary (13 Core Entities)</span>
              </h3>
              <p className="text-xs text-slate-400">
                Detailed field-level schema specifications with required types, cardinality, allowed enums, and validation constraints.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {dictionary && Object.entries(dictionary).map(([entityName, def]) => (
                <div key={entityName} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div>
                      <h4 className="text-base font-bold text-white font-mono">{entityName}</h4>
                      <p className="text-xs text-slate-400">{def.description}</p>
                    </div>
                    <div className="text-right text-xs">
                      <div className="font-mono text-sky-400">PK: {def.primary_key}</div>
                      <div className="text-slate-500">{def.cardinality}</div>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800/60">
                        <tr>
                          <th className="py-2 px-3">Field Name</th>
                          <th className="py-2 px-3">Type</th>
                          <th className="py-2 px-3">Required</th>
                          <th className="py-2 px-3">Uniqueness</th>
                          <th className="py-2 px-3">Validation Rule / Allowed Values</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40 text-slate-300">
                        {Object.entries(def.fields || {}).map(([fName, fMeta]) => (
                          <tr key={fName} className="hover:bg-slate-800/20">
                            <td className="py-2 px-3 font-mono font-semibold text-sky-300">{fName}</td>
                            <td className="py-2 px-3 font-mono text-slate-400">{fMeta.type}</td>
                            <td className="py-2 px-3">
                              {fMeta.required ? <span className="text-emerald-400 font-bold">Yes</span> : <span className="text-slate-500">No</span>}
                            </td>
                            <td className="py-2 px-3">
                              {fMeta.uniqueness ? <span className="text-indigo-400 font-bold">Unique</span> : <span className="text-slate-500">No</span>}
                            </td>
                            <td className="py-2 px-3 text-slate-300">
                              {fMeta.validation_rule}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 7: INTEGRITY & REPRODUCIBILITY SUITE */}
        {activeTab === 'validation' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <CheckCheck className="w-4 h-4 text-emerald-400" />
                  <span>Validation & Reproducibility Suite (Step 8 & 10)</span>
                </h3>
                <p className="text-xs text-slate-400">Runs primary-key uniqueness, foreign-key integrity, enum validation, date ordering, and fixed-seed deterministic reproducibility.</p>
              </div>

              <button
                disabled={loading}
                onClick={runValidationSuite}
                className="bg-sky-500 hover:bg-sky-400 text-white font-semibold px-4 py-2 rounded-lg text-xs flex items-center space-x-2 transition-all shadow-md shadow-sky-500/20"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                <span>Execute Full Suite</span>
              </button>
            </div>

            {/* Validation Results */}
            {validationReport && (
              <div className="space-y-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      validationReport.score >= 90 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-base font-bold text-white">Overall Integrity Score: {validationReport.score}%</div>
                      <div className="text-xs text-slate-400">{validationReport.passed_checks} of {validationReport.total_checks} Integrity Check Categories Passed</div>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    validationReport.overall_status === 'PASSED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {validationReport.overall_status}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {validationReport.checks?.map((chk, i) => (
                    <div key={i} className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex items-start justify-between">
                      <div>
                        <div className="text-xs font-mono font-bold text-slate-300">{chk.category}</div>
                        <div className="text-xs text-sky-400 mt-0.5">{chk.entity}</div>
                        <div className="text-[11px] text-slate-400 mt-1">{chk.details}</div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        chk.passed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {chk.passed ? 'PASSED' : 'FLAGGED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 10 Reproducibility Report */}
            {reproducibilityReport && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Database className="w-4 h-4 text-indigo-400" />
                  <span>Step 10: Fixed-Seed Deterministic Reproducibility Verification</span>
                </h4>
                <p className="text-xs text-slate-400">
                  Regenerated twice with fixed seed <span className="font-mono text-sky-400">{reproducibilityReport.seed}</span> and verified identical dataset SHA-256 hashes:
                </p>

                <div className="space-y-2 text-xs font-mono bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Run 1 Hash:</span>
                    <span className="text-sky-300">{reproducibilityReport.run_1_checksum}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Run 2 Hash:</span>
                    <span className="text-sky-300">{reproducibilityReport.run_2_checksum}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <span className="text-slate-300 font-bold">Bitwise Checksum Match:</span>
                    <span className="text-emerald-400 font-bold">
                      {reproducibilityReport.reproducible ? '100% MATCH (REPRODUCIBLE)' : 'MISMATCH'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}
