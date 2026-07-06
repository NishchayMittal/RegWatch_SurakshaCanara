"use client";

import React, { useState, useEffect } from "react";
import { 
  Shield, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Search, 
  ArrowRight, 
  Upload, 
  History, 
  Activity, 
  RefreshCw, 
  Users, 
  Layers, 
  PlusCircle, 
  Check, 
  Send,
  Eye,
  Trash2
} from "lucide-react";
import InteractiveCanvas from "@/components/InteractiveCanvas";

// Interfaces
interface Circular {
  id: number;
  url: string;
  title: string;
  status: string;
  raw_text?: string;
}

interface MAPItem {
  id: number;
  action: string;
  assigned_department: string;
  status: string;
  confidence: number;
  circular_id?: number;
  sla_days?: number;
}

interface Evidence {
  id: number;
  description: string;
  status: string;
  missing_items: string | null;
  submitted_by: string;
  created_at: string;
}

interface AuditLog {
  id: number;
  event: string;
  details: string;
  created_at: string;
}

interface ReviewItem {
  id: number;
  circular_id: number;
  raw_extraction: string;
  confidence: number;
}

interface Department {
  id: number;
  name: string;
}

interface Stats {
  total_circulars: number;
  pending_maps: number;
  complete_maps: number;
  needs_review: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

const getCleanRawExtraction = (rawText: string) => {
  try {
    const parsed = JSON.parse(rawText);
    if (parsed && Array.isArray(parsed.maps)) {
      return parsed.maps.map((m: any) => m.action).join("\n");
    }
  } catch (e) {
    // Fail-safe: if already plain text or invalid JSON
  }
  return rawText;
};

export default function Home() {
  const [consoleLaunched, setConsoleLaunched] = useState(false);
  const [activeTab, setActiveTab] = useState<"action_points" | "human_review" | "circulars" | "search_maps">("action_points");
  
  // Data States
  const [stats, setStats] = useState<Stats>({ total_circulars: 0, pending_maps: 0, complete_maps: 0, needs_review: 0 });
  const [circulars, setCirculars] = useState<Circular[]>([]);
  const [allMaps, setAllMaps] = useState<MAPItem[]>([]);
  const [selectedMap, setSelectedMap] = useState<MAPItem | null>(null);
  const [evidenceHistory, setEvidenceHistory] = useState<Evidence[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [selectedReviewItem, setSelectedReviewItem] = useState<ReviewItem | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [viewingCircular, setViewingCircular] = useState<Circular | null>(null);

  // Filtering states
  const [selectedDept, setSelectedDept] = useState("All Departments");
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [minConfidence, setMinConfidence] = useState(0.00);
  const [quickFilter, setQuickFilter] = useState("");
  const [ingestionUrl, setIngestionUrl] = useState("");

  // Loading States
  const [loading, setLoading] = useState(true);
  const [backendError, setBackendError] = useState(false);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [submittingEvidence, setSubmittingEvidence] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [deletingMap, setDeletingMap] = useState(false);

  // Evidence Form Inputs
  const [evidenceDesc, setEvidenceDesc] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [evidenceSubmitter, setEvidenceSubmitter] = useState("");

  // Review Dispatch Inputs
  const [reviewAction, setReviewAction] = useState("");
  const [reviewDept, setReviewDept] = useState("");
  const [reviewSla, setReviewSla] = useState(7);

  // Sync baseline data
  const loadData = async () => {
    try {
      setBackendError(false);
      
      const statsRes = await fetch(`${API_BASE}/stats`);
      if (!statsRes.ok) throw new Error();
      const statsData = await statsRes.json();
      setStats(statsData);

      const circsRes = await fetch(`${API_BASE}/circulars`);
      const circsData = await circsRes.json();
      setCirculars(circsData);

      // Fetch ALL maps to list inside dashboard console
      const allMapsList: MAPItem[] = [];
      for (const c of circsData) {
        const mapsRes = await fetch(`${API_BASE}/circulars/${c.id}/maps`);
        const mapsData = await mapsRes.json();
        // inject circular_id
        mapsData.forEach((m: any) => {
          m.circular_id = c.id;
          m.assigned_department = m.department; // match API property mapping
          allMapsList.push(m);
        });
      }
      setAllMaps(allMapsList);

      const reviewRes = await fetch(`${API_BASE}/review/maps`);
      const reviewData = await reviewRes.json();
      setReviewItems(reviewRes.ok ? reviewData : []);
      if (reviewData.length > 0 && !selectedReviewItem) {
        setSelectedReviewItem(reviewData[0]);
        setReviewAction(getCleanRawExtraction(reviewData[0].raw_extraction));
      }

      const deptsRes = await fetch(`${API_BASE}/departments`);
      const deptsData = await deptsRes.json();
      setDepartments(deptsData);
      if (deptsData.length > 0 && !reviewDept) {
        setReviewDept(deptsData[0].name);
      }

      const logsRes = await fetch(`${API_BASE}/audit-logs`);
      const logsData = await logsRes.json();
      setAuditLogs(logsData);

      setLoading(false);
    } catch (err) {
      console.error(err);
      setBackendError(true);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Fetch history when selected MAP changes
  useEffect(() => {
    if (selectedMap) {
      fetch(`${API_BASE}/maps/${selectedMap.id}/evidence`)
        .then(res => res.json())
        .then(data => setEvidenceHistory(data))
        .catch(() => setEvidenceHistory([]));
    } else {
      setEvidenceHistory([]);
    }
  }, [selectedMap]);

  // Handle manual deletion of a MAPItem
  const deleteSelectedMap = async () => {
    if (!selectedMap) return;
    const confirmDelete = window.confirm("Are you sure you want to delete this compliance obligation? This will also remove all related verification tasks and evidence records.");
    if (!confirmDelete) return;

    setDeletingMap(true);
    try {
      const res = await fetch(`${API_BASE}/maps/${selectedMap.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setSelectedMap(null);
        loadData();
      } else {
        alert("Failed to delete obligation.");
      }
    } catch (err) {
      console.error(err);
      alert("Error deleting obligation.");
    } finally {
      setDeletingMap(false);
    }
  };

  // Handle pipeline ingestion trigger
  const runPipelineIngestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingestionUrl.trim()) return;
    setPipelineLoading(true);
    try {
      const res = await fetch(`${API_BASE}/pipeline/run?url=${encodeURIComponent(ingestionUrl)}`, {
        method: "POST"
      });
      if (res.ok) {
        setIngestionUrl("");
        loadData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setPipelineLoading(false);
    }
  };

  // Handle evidence submission
  const submitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMap || !evidenceDesc.trim()) return;

    setSubmittingEvidence(true);
    try {
      const params = new URLSearchParams({
        description: evidenceDesc,
        submitted_by: evidenceSubmitter || "Operations Dept"
      });
      if (evidenceUrl) params.append("file_url", evidenceUrl);

      const res = await fetch(`${API_BASE}/maps/${selectedMap.id}/evidence?${params.toString()}`, {
        method: "POST"
      });
      if (res.ok) {
        setEvidenceDesc("");
        setEvidenceUrl("");
        // Reload everything
        loadData();
        // Refresh selected map state
        const updatedRes = await fetch(`${API_BASE}/maps/${selectedMap.id}/status`);
        if (updatedRes.ok) {
          const updated = await updatedRes.json();
          setSelectedMap(updated);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingEvidence(false);
    }
  };

  // Route a human reviewed task
  const submitHumanRouting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReviewItem || !reviewAction.trim()) return;

    setSubmittingReview(true);
    try {
      const res = await fetch(`${API_BASE}/tasks/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: selectedReviewItem.id,
          action_text: reviewAction,
          department_name: reviewDept,
          sla_days: Number(reviewSla)
        })
      });
      if (res.ok) {
        const remaining = reviewItems.filter(item => item.id !== selectedReviewItem.id);
        setReviewItems(remaining);
        if (remaining.length > 0) {
          setSelectedReviewItem(remaining[0]);
          setReviewAction(getCleanRawExtraction(remaining[0].raw_extraction));
        } else {
          setSelectedReviewItem(null);
          setReviewAction("");
        }
        loadData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingReview(false);
    }
  };

  // Filter items
  const filteredMaps = allMaps.filter(m => {
    const matchesDept = selectedDept === "All Departments" || m.assigned_department === selectedDept;
    
    let matchesStatus = true;
    if (selectedStatus === "Pending") matchesStatus = m.status === "pending" || m.status === "assigned";
    else if (selectedStatus === "Complete") matchesStatus = m.status === "complete" || m.status === "accepted";
    else if (selectedStatus === "Evidence Incomplete") matchesStatus = m.status === "evidence_incomplete" || m.status === "incomplete";
    
    const matchesConfidence = (m.confidence ?? 1.0) >= minConfidence;
    
    const matchesSearch = quickFilter.trim() === "" || 
                          m.action.toLowerCase().includes(quickFilter.toLowerCase()) || 
                          m.assigned_department.toLowerCase().includes(quickFilter.toLowerCase());

    return matchesDept && matchesStatus && matchesConfidence && matchesSearch;
  });

  return (
    <div className="relative min-h-screen w-full flex flex-col justify-start items-center">
      {/* Canvas Backdrop */}
      <InteractiveCanvas isLoading={!consoleLaunched} />

      {/* Welcome Screen Flow (Image 2) */}
      {!consoleLaunched ? (
        <div className="flex-grow flex flex-col items-center justify-center max-w-2xl px-6 text-center z-10 select-none">
          <span className="font-extrabold text-[10px] tracking-[0.2em] uppercase bg-white border-2 border-black px-4 py-1 neo-shadow-sm rounded-full mb-6 inline-block">
            The Compliance Layer for Banco
          </span>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-neo-dark mb-6 leading-tight">
            Your compliance isn't up to date.{" "}
            <span className="bg-neo-accent px-3 py-1 border-2 border-black inline-block rotate-[-1deg] neo-shadow-sm rounded-[10px]">
              RegWatch
            </span>{" "}
            fixes that.
          </h1>
          <p className="text-sm font-semibold text-gray-700 max-w-xl leading-relaxed mb-8">
            RegWatch builds living regulatory knowledge, routed and validated personally across bank departments. No missed deadlines, 100% offline security.
          </p>
          <button 
            onClick={() => setConsoleLaunched(true)}
            className="px-8 py-3.5 bg-white text-base font-extrabold neo-button rounded-[12px] flex items-center gap-2"
          >
            Launch Compliance Console
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      ) : (
        /* Console Card Layout Flow (Image 3) */
        <div className="w-full max-w-7xl mx-auto my-8 bg-white neo-border neo-shadow-lg p-6 rounded-[20px] z-10 flex flex-col gap-6">
          
          {/* Card Top Nav header */}
          <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4 border-b border-black/10 pb-4">
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setConsoleLaunched(false)}
                className="bg-neo-accent font-extrabold text-sm px-3 py-1 border-2 border-black rounded-[6px] neo-shadow-sm cursor-pointer hover:translate-x-[-1px] hover:translate-y-[-1px] hover:neo-shadow active:translate-x-[1px] active:translate-y-[1px] active:neo-shadow-sm transition-all"
              >
                RegWatch
              </button>
            </div>

            {/* Nav tabs */}
            <div className="flex flex-wrap gap-2">
              <button 
                onClick={() => setActiveTab("action_points")}
                className={`px-5 py-2 font-extrabold text-xs rounded-full neo-button border-2 border-black ${activeTab === "action_points" ? "bg-neo-accent" : "bg-white"}`}
              >
                Action Points
              </button>
              <button 
                onClick={() => setActiveTab("human_review")}
                className={`px-5 py-2 font-extrabold text-xs rounded-full neo-button border-2 border-black ${activeTab === "human_review" ? "bg-neo-accent" : "bg-white"}`}
              >
                Human Review {reviewItems.length > 0 && `(${reviewItems.length})`}
              </button>
              <button 
                onClick={() => setActiveTab("circulars")}
                className={`px-5 py-2 font-extrabold text-xs rounded-full neo-button border-2 border-black ${activeTab === "circulars" ? "bg-neo-accent" : "bg-white"}`}
              >
                Circulars List
              </button>
              <button 
                onClick={() => setActiveTab("search_maps")}
                className={`px-5 py-2 font-extrabold text-xs rounded-full neo-button border-2 border-black ${activeTab === "search_maps" ? "bg-neo-accent" : "bg-white"}`}
              >
                Search MAPs
              </button>
            </div>
          </div>

          {/* Subheader Title Blue Banner */}
          <div className="bg-[#b7eaf6] border-3 border-black p-4 neo-shadow rounded-[12px]">
            <h2 className="font-extrabold text-xl text-neo-dark tracking-tight">
              {activeTab === "action_points" && "Mandatory Action Points Console"}
              {activeTab === "human_review" && "Awaiting Human Review Queue"}
              {activeTab === "circulars" && "Ingested Circulars Database"}
              {activeTab === "search_maps" && "Search compliance obligations"}
            </h2>
            <p className="text-xs font-semibold text-gray-700 mt-1">
              {activeTab === "action_points" && "Operational compliance items extracted from circulars, routed to departments."}
              {activeTab === "human_review" && "Edit raw extractions, target routing channels, and assign compliance tasks."}
              {activeTab === "circulars" && "Review ingested regulatory updates, download sources, and parse new circulars."}
              {activeTab === "search_maps" && "Scan, locate, and filter through all extracted compliance checkpoints."}
            </p>
          </div>

          {/* Core Content Body depending on tab */}
          {activeTab === "action_points" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              
              {/* Column 1: Filter and Configure (3 cols) */}
              <div className="lg:col-span-3 flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-extrabold text-neo-dark uppercase tracking-wider">Department</label>
                  <select 
                    value={selectedDept}
                    onChange={(e) => setSelectedDept(e.target.value)}
                    className="w-full px-3 py-2 border-2.5 border-black font-extrabold text-xs focus:outline-none bg-stone-50"
                  >
                    <option value="All Departments">All Departments</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.name}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-extrabold text-neo-dark uppercase tracking-wider">MAP Status</label>
                  <select 
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="w-full px-3 py-2 border-2.5 border-black font-extrabold text-xs focus:outline-none bg-stone-50"
                  >
                    <option value="All">All</option>
                    <option value="Pending">Pending</option>
                    <option value="Complete">Complete</option>
                    <option value="Evidence Incomplete">Incomplete</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-xs font-extrabold text-neo-dark uppercase tracking-wider">
                    <span>Min Confidence Score</span>
                    <span className="font-mono text-red-500">{minConfidence.toFixed(2)}</span>
                  </div>
                  <input 
                    type="range"
                    min={0.00}
                    max={1.00}
                    step={0.05}
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                    className="w-full accent-black h-1.5 bg-gray-200 border border-black cursor-pointer"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-extrabold text-neo-dark uppercase tracking-wider">Quick Filter</label>
                  <input 
                    type="text" 
                    placeholder="Type to narrow down list..." 
                    value={quickFilter}
                    onChange={(e) => setQuickFilter(e.target.value)}
                    className="w-full px-3 py-2 border-2.5 border-black font-bold text-xs focus:outline-none bg-stone-50"
                  />
                </div>

                {/* Micro Counters Panel */}
                <div className="mt-4 border-t border-black/10 pt-4 flex flex-col gap-2">
                  <span className="text-xs font-extrabold uppercase text-gray-500">Compliance Metrics</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-neo-lilac p-2 border-2 border-black flex flex-col justify-center">
                      <span className="text-[9px] font-extrabold uppercase font-mono">Ingested</span>
                      <span className="text-xl font-extrabold font-mono">{stats.total_circulars}</span>
                    </div>
                    <div className="bg-neo-butter p-2 border-2 border-black flex flex-col justify-center">
                      <span className="text-[9px] font-extrabold uppercase font-mono">Pending</span>
                      <span className="text-xl font-extrabold font-mono">{stats.pending_maps}</span>
                    </div>
                    <div className="bg-neo-mint p-2 border-2 border-black flex flex-col justify-center">
                      <span className="text-[9px] font-extrabold uppercase font-mono">Complete</span>
                      <span className="text-xl font-extrabold font-mono">{stats.complete_maps}</span>
                    </div>
                    <div className="bg-neo-sky p-2 border-2 border-black flex flex-col justify-center">
                      <span className="text-[9px] font-extrabold uppercase font-mono">Review</span>
                      <span className="text-xl font-extrabold font-mono">{stats.needs_review}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Column 2: Obligations List (5 cols) */}
              <div className="lg:col-span-5 flex flex-col gap-4 border-l border-r border-black/10 px-4 max-h-[580px] overflow-y-auto">
                <div className="flex justify-between items-center pb-2 border-b border-black/10">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-neo-dark">Obligations List</h3>
                  <span className="font-mono text-xs font-bold text-gray-500">Filtered: {filteredMaps.length}</span>
                </div>
                
                {filteredMaps.length === 0 ? (
                  <p className="text-xs font-mono text-gray-500 text-center py-12 border border-dashed border-gray-300">
                    No active MAP items match filters.
                  </p>
                ) : (
                  filteredMaps.map(m => (
                    <div key={m.id} className="p-4 border-2.5 border-black bg-white neo-shadow-sm flex flex-col gap-3">
                      <div className="flex justify-between items-center text-[10px] font-extrabold">
                        <span className="bg-neo-dark text-white px-2 py-0.5 border border-black">MAP {m.id}</span>
                        <span className="text-gray-500 uppercase">{m.assigned_department}</span>
                      </div>
                      <p className="font-bold text-sm text-neo-dark leading-snug">{m.action}</p>
                      
                      <div className="flex justify-between items-center">
                        <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 border border-black ${m.status === "complete" || m.status === "accepted" ? "bg-neo-mint" : m.status === "submitted" ? "bg-neo-sky" : m.status === "evidence_incomplete" || m.status === "incomplete" ? "bg-red-400" : "bg-neo-butter"}`}>
                          {m.status.toUpperCase()}
                        </span>
                        <button 
                          onClick={() => setSelectedMap(m)}
                          className="px-3 py-1 bg-white text-[10px] font-extrabold neo-button flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Details and Evidence
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Column 3: Compliance Review / Evidence details (4 cols) */}
              <div className="lg:col-span-4 flex flex-col gap-4">
                <div className="pb-2 border-b border-black/10">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-neo-dark">Compliance Review</h3>
                </div>

                {!selectedMap ? (
                  <div className="p-8 border border-dashed border-gray-300 bg-[#fafaf9] text-center flex flex-col items-center justify-center flex-grow">
                    <Shield className="w-8 h-8 text-gray-400 mb-2" />
                    <p className="text-xs font-extrabold text-neo-dark">No Selection</p>
                    <p className="text-[10px] text-gray-500 mt-1 max-w-[200px]">
                      Select a compliance card from the list to view stats, submit logs, and audit files.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    {/* Action obligations info */}
                    <div className="p-3 border-2 border-black bg-stone-50">
                      <span className="text-[10px] font-mono font-bold text-gray-500 block">SELECTED MAP {selectedMap.id} OBLIGATION:</span>
                      <p className="font-extrabold text-xs mt-1.5 text-neo-dark">{selectedMap.action}</p>
                    </div>

                    {(() => {
                      const relatedCircular = circulars.find(c => c.id === selectedMap.circular_id);
                      return relatedCircular && relatedCircular.url && relatedCircular.url.startsWith("http") ? (
                        <div className="p-3 border-2 border-black bg-neo-sky/20 flex flex-col gap-1">
                          <span className="text-[10px] font-mono font-bold text-gray-500 block">SOURCE CIRCULAR:</span>
                          <span className="font-bold text-xs text-neo-dark block line-clamp-1">{relatedCircular.title}</span>
                          <button 
                            onClick={(e) => {
                              e.preventDefault();
                              setViewingCircular(relatedCircular);
                            }}
                            className="text-[10px] font-extrabold text-blue-600 underline flex items-center gap-1 hover:text-blue-800 mt-0.5 cursor-pointer bg-transparent border-none p-0 align-baseline text-left"
                          >
                            <FileText className="w-3.5 h-3.5" />
                            View Circular Text
                          </button>
                        </div>
                      ) : null;
                    })()}

                    {/* Evidence History lists */}
                    {evidenceHistory.length > 0 && (
                      <div className="flex flex-col gap-2">
                        <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">History Records</span>
                        <div className="max-h-28 overflow-y-auto flex flex-col gap-2 border border-black/10 p-2 bg-stone-50">
                          {evidenceHistory.map(ev => (
                            <div key={ev.id} className="p-2 border border-black bg-white text-[11px] flex flex-col gap-1">
                              <div className="flex justify-between items-center font-bold">
                                <span>{ev.submitted_by}</span>
                                <span className={`text-[8px] uppercase px-1 border border-black ${ev.status === "accepted" ? "bg-neo-mint" : "bg-red-300"}`}>
                                  {ev.status}
                                </span>
                              </div>
                              <p className="text-gray-600 line-clamp-1">{ev.description}</p>
                              {ev.missing_items && (
                                <p className="text-red-500 font-mono text-[9px] font-bold">Missing: {ev.missing_items}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Submissions form */}
                    {selectedMap.status !== "complete" && selectedMap.status !== "accepted" ? (
                      <form onSubmit={submitEvidence} className="flex flex-col gap-3 border-2 border-black p-4 bg-stone-50">
                        <span className="text-xs font-extrabold uppercase border-b border-black/10 pb-1 text-neo-dark">Submit Verification Data</span>
                        
                        <div className="flex flex-col gap-1">
                          <label className="text-[10px] font-bold text-gray-700">Actions Executed *</label>
                          <textarea 
                            value={evidenceDesc}
                            onChange={(e) => setEvidenceDesc(e.target.value)}
                            required
                            rows={3}
                            placeholder="Detail actions taken..."
                            className="w-full px-2 py-1.5 border-2 border-black text-xs font-semibold focus:outline-none bg-white"
                          />
                        </div>

                        <div className="flex flex-col gap-1">
                          <label className="text-[10px] font-bold text-gray-700">Document URL</label>
                          <input 
                            type="text"
                            value={evidenceUrl}
                            onChange={(e) => setEvidenceUrl(e.target.value)}
                            placeholder="e.g. C:/shares/letter.pdf"
                            className="w-full px-2 py-1 border-2 border-black text-xs font-semibold focus:outline-none bg-white"
                          />
                        </div>

                        <div className="flex flex-col gap-1">
                          <label className="text-[10px] font-bold text-gray-700">Submitter Name *</label>
                          <input 
                            type="text"
                            value={evidenceSubmitter}
                            onChange={(e) => setEvidenceSubmitter(e.target.value)}
                            required
                            placeholder="Your Name / Dept"
                            className="w-full px-2 py-1 border-2 border-black text-xs font-semibold focus:outline-none bg-white"
                          />
                        </div>

                        <button 
                          type="submit"
                          disabled={submittingEvidence}
                          className="py-2 bg-neo-accent text-xs font-extrabold neo-button mt-1 flex justify-center items-center gap-1.5"
                        >
                          {submittingEvidence ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Send className="w-3.5 h-3.5" />
                          )}
                          Validate Submission
                        </button>
                      </form>
                    ) : (
                      <div className="bg-neo-mint border-2 border-black p-3 text-center">
                        <p className="font-extrabold text-xs text-neo-dark">Obligation checklist fully complete.</p>
                      </div>
                    )}

                    <div className="mt-4 border-t border-black/10 pt-4">
                      <button
                        onClick={deleteSelectedMap}
                        disabled={deletingMap}
                        className="w-full py-2 bg-red-400 text-xs font-extrabold neo-button flex justify-center items-center gap-1.5 border-2 border-black cursor-pointer hover:translate-x-[-1px] hover:translate-y-[-1px] hover:neo-shadow active:translate-x-[1px] active:translate-y-[1px] transition-all"
                      >
                        {deletingMap ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                        Delete Compliance Obligation
                      </button>
                    </div>

                  </div>
                )}
              </div>

            </div>
          )}

          {/* T2: Human Review Queue */}
          {activeTab === "human_review" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {reviewItems.length === 0 ? (
                <div className="lg:col-span-12 p-12 text-center flex flex-col items-center justify-center border border-dashed border-gray-300">
                  <CheckCircle className="w-12 h-12 text-neo-mint mb-3" />
                  <h3 className="font-extrabold text-lg text-neo-dark">Review Queue is Clear!</h3>
                  <p className="text-xs text-gray-500 mt-1">AI pipelines resolved all regulatory extractions with high confidence. No manual verification required.</p>
                </div>
              ) : (
                <>
                  {/* Left List */}
                  <div className="lg:col-span-4 border-2 border-black p-3 bg-stone-50 flex flex-col gap-3 max-h-[460px] overflow-y-auto">
                    {reviewItems.map(item => (
                      <div 
                        key={item.id}
                        onClick={() => {
                          setSelectedReviewItem(item);
                          setReviewAction(getCleanRawExtraction(item.raw_extraction));
                        }}
                        className={`p-3 border border-black cursor-pointer transition-all ${selectedReviewItem?.id === item.id ? "bg-neo-sky" : "bg-white hover:bg-stone-50"}`}
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-mono text-xs font-bold text-gray-500">ID: {item.id}</span>
                          <span className="text-[9px] bg-red-400 text-neo-dark font-extrabold px-1 border border-black">
                            Conf: {Math.round(item.confidence * 100)}%
                          </span>
                        </div>
                        <p className="font-extrabold text-xs text-neo-dark line-clamp-2">{getCleanRawExtraction(item.raw_extraction)}</p>
                      </div>
                    ))}
                  </div>

                  {/* Right Form Editor */}
                  <div className="lg:col-span-8">
                    {selectedReviewItem ? (
                      <form onSubmit={submitHumanRouting} className="border-2 border-black p-5 bg-white flex flex-col gap-4">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-black pb-2 gap-2">
                          <h3 className="font-extrabold text-md">Resolve Extraction Route</h3>
                          {(() => {
                            const relatedCircular = circulars.find(c => c.id === selectedReviewItem.circular_id);
                            return relatedCircular ? (
                              <button 
                                type="button"
                                onClick={() => setViewingCircular(relatedCircular)}
                                className="px-3 py-1 bg-[#b7eaf6] hover:bg-neo-sky text-[10px] font-extrabold border-2 border-black rounded-[6px] neo-shadow-sm flex items-center gap-1 cursor-pointer transition-all hover:translate-x-[-1px] hover:translate-y-[-1px] hover:neo-shadow active:translate-x-[1px] active:translate-y-[1px] active:neo-shadow-sm"
                              >
                                <FileText className="w-3.5 h-3.5" />
                                View Circular Text
                              </button>
                            ) : null;
                          })()}
                        </div>
                        
                        <div className="flex flex-col gap-1">
                          <label className="text-xs font-bold text-gray-700">Raw Extraction Text (Edit & Refine) *</label>
                          <textarea 
                            value={reviewAction}
                            onChange={(e) => setReviewAction(e.target.value)}
                            required
                            rows={4}
                            className="w-full px-3 py-2 border-2 border-black font-semibold text-sm focus:outline-none bg-stone-50"
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-1">
                            <label className="text-xs font-bold text-gray-700">Assigned Department *</label>
                            <select 
                              value={reviewDept}
                              onChange={(e) => setReviewDept(e.target.value)}
                              className="w-full px-3 py-2 border-2 border-black font-semibold text-sm focus:outline-none bg-stone-50"
                            >
                              {departments.map(d => (
                                <option key={d.id} value={d.name}>{d.name}</option>
                              ))}
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-xs font-bold text-gray-700">SLA Due Days *</label>
                            <input 
                              type="number" 
                              min={1}
                              max={90}
                              value={reviewSla}
                              onChange={(e) => setReviewSla(Number(e.target.value))}
                              className="w-full px-3 py-1.5 border-2 border-black font-semibold text-sm focus:outline-none bg-stone-50"
                            />
                          </div>
                        </div>

                        <button 
                          type="submit"
                          disabled={submittingReview}
                          className="py-2.5 bg-neo-sky text-sm font-extrabold neo-button mt-4 flex items-center justify-center gap-2"
                        >
                          {submittingReview ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Check className="w-4 h-4" />
                          )}
                          Approve Action Point & Route Task
                        </button>
                      </form>
                    ) : (
                      <div className="h-full flex items-center justify-center p-8 bg-neo-gray border border-dashed border-gray-300">
                        <p className="font-extrabold text-sm text-gray-500">Select an item from the review queue.</p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* T3: Circulars List */}
          {activeTab === "circulars" && (
            <div className="flex flex-col gap-6">
              
              {/* Ingest Form */}
              <form onSubmit={runPipelineIngestion} className="p-4 border-2 border-black bg-stone-50 flex flex-col md:flex-row gap-3 items-end">
                <div className="flex-grow flex flex-col gap-1">
                  <label className="text-xs font-extrabold uppercase text-neo-dark">Ingest New Regulatory Circular URL</label>
                  <input 
                    type="url"
                    value={ingestionUrl}
                    onChange={(e) => setIngestionUrl(e.target.value)}
                    required
                    placeholder="https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?id=12739"
                    className="w-full px-3 py-2 border-2.5 border-black font-semibold text-sm focus:outline-none bg-white"
                  />
                </div>
                <button 
                  type="submit"
                  disabled={pipelineLoading}
                  className="px-6 py-2.5 bg-neo-accent text-sm font-extrabold neo-button whitespace-nowrap"
                >
                  {pipelineLoading ? "Ingesting..." : "Run Ingestion Pipeline"}
                </button>
              </form>

              {/* Circulars List */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[460px] overflow-y-auto">
                {circulars.map(c => (
                  <div key={c.id} className="p-4 border-2 border-black bg-white neo-shadow-sm flex flex-col justify-between gap-3">
                    <div>
                      <div className="flex justify-between items-center text-[10px] font-extrabold font-mono text-gray-500">
                        <span>ID: {c.id}</span>
                        <span className={`px-1.5 py-0.5 border border-black uppercase ${c.status === "done" ? "bg-neo-mint" : "bg-neo-butter"}`}>{c.status}</span>
                      </div>
                      <h4 className="font-extrabold text-sm text-neo-dark mt-2 leading-snug">{c.title}</h4>
                    </div>
                    <div className="border-t border-black/10 pt-2 flex justify-end">
                      <button 
                        onClick={() => setViewingCircular(c)}
                        className="text-[10px] font-extrabold text-blue-600 underline hover:text-blue-800 flex items-center gap-1 cursor-pointer bg-transparent border-none p-0 align-baseline"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        View Database Circular Text
                      </button>
                    </div>
                  </div>
                ))}
              </div>

            </div>
          )}

          {/* T4: Search MAPs */}
          {activeTab === "search_maps" && (
            <div className="flex flex-col gap-4">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Filter and search all MAPs by details..." 
                  value={quickFilter}
                  onChange={(e) => setQuickFilter(e.target.value)}
                  className="w-full px-4 py-3 pl-11 border-3 border-black neo-shadow-sm font-bold text-sm focus:outline-none bg-stone-50"
                />
                <Search className="w-5 h-5 absolute left-4 top-3.5 text-gray-500" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[450px] overflow-y-auto">
                {filteredMaps.map(m => (
                  <div key={m.id} className="p-4 border-2 border-black bg-white neo-shadow-sm flex flex-col justify-between gap-3">
                    <div>
                      <div className="flex justify-between items-center text-[10px] font-extrabold">
                        <span className="bg-neo-dark text-white px-1.5 py-0.5 border border-black">MAP {m.id}</span>
                        <span className="text-gray-500 uppercase">{m.assigned_department}</span>
                      </div>
                      <p className="font-bold text-xs text-neo-dark mt-2 leading-normal">{m.action}</p>
                    </div>
                    <div className="flex justify-between items-center border-t border-black/10 pt-2.5">
                      <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 border border-black ${m.status === "complete" || m.status === "accepted" ? "bg-neo-mint" : "bg-neo-butter"}`}>
                        {m.status.toUpperCase()}
                      </span>
                      <button 
                        onClick={() => {
                          setActiveTab("action_points");
                          setSelectedMap(m);
                        }}
                        className="px-3 py-1 bg-white text-[9px] font-extrabold neo-button"
                      >
                        Inspect in Console
                      </button>
                    </div>
                  </div>
                ))}
              </div>

            </div>
          )}

          {/* Bottom Audit Trails Scrolling Timeline widget */}
          <div className="border-t border-black/10 pt-4 flex flex-col gap-3">
            <span className="text-xs font-extrabold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-neo-dark" />
              Audit Log Feed
            </span>
            <div className="flex gap-4 overflow-x-auto pb-2 pr-2 scrollbar-thin">
              {auditLogs.slice(0, 10).map((log) => (
                <div key={log.id} className="p-2 border-2 border-black bg-stone-50 text-[10px] flex-shrink-0 w-64">
                  <div className="flex justify-between items-center">
                    <span className="font-mono font-bold bg-neo-lilac px-1.5 border border-black text-[9px]">
                      {log.event}
                    </span>
                    <span className="text-[8px] text-gray-400 font-mono">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="font-semibold text-gray-700 mt-1 line-clamp-1">{log.details}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* Modal overlay to view circular raw text */}
      {viewingCircular && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white border-3 border-black neo-shadow-lg w-full max-w-3xl max-h-[85vh] flex flex-col rounded-[16px] overflow-hidden select-text">
            {/* Modal Header */}
            <div className="bg-[#b7eaf6] border-b-3 border-black p-4 flex justify-between items-center">
              <div>
                <span className="text-[10px] font-mono font-extrabold bg-black text-white px-2 py-0.5 border border-black rounded-sm">
                  CIRCULAR ID: {viewingCircular.id}
                </span>
                <h3 className="font-extrabold text-sm text-neo-dark mt-1 line-clamp-1">
                  {viewingCircular.title}
                </h3>
              </div>
              <button 
                onClick={() => setViewingCircular(null)}
                className="bg-white border-2 border-black font-extrabold text-xs px-3 py-1.5 rounded-[6px] neo-shadow-sm hover:translate-x-[-1px] hover:translate-y-[-1px] hover:neo-shadow active:translate-x-[1px] active:translate-y-[1px] active:neo-shadow-sm cursor-pointer"
              >
                Close
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto bg-stone-50 flex-grow font-mono text-xs text-gray-800 whitespace-pre-wrap leading-relaxed max-h-[60vh]">
              {viewingCircular.raw_text || "No text content available in the database for this circular."}
            </div>
            
            {/* Modal Footer */}
            {viewingCircular.url && viewingCircular.url.startsWith("http") && (
              <div className="border-t-3 border-black p-4 bg-white flex justify-between items-center">
                <span className="text-[10px] text-gray-500 font-bold truncate max-w-md">Source: {viewingCircular.url}</span>
                <a 
                  href={viewingCircular.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-white text-xs font-extrabold border-2 border-black rounded-[8px] neo-shadow-sm flex items-center gap-1 hover:translate-x-[-1px] hover:translate-y-[-1px] hover:neo-shadow active:translate-x-[1px] active:translate-y-[1px] active:neo-shadow-sm cursor-pointer"
                >
                  <FileText className="w-4 h-4" />
                  Open Source Link
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
