import React, { useState, useEffect, useCallback } from 'react';
import {
  Code2,
  Tag,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Edit2,
  Trash2,
  Check,
  X,
  Layers,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
  Info,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  extractSkills,
  getSkills,
  reprocessSkills,
  confirmSkillMapping,
  rejectSkillMapping,
  updateSkillEntry,
  deleteSkillEntry,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

const CATEGORIES = [
  'All',
  'Programming Languages',
  'Frameworks & Libraries',
  'Databases',
  'Cloud & DevOps',
  'Machine Learning & AI',
  'Tools',
  'Soft Skills',
  'Other',
];

export function SkillsSection({ resumeId, className }) {
  const [skills, setSkills] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [expandedEvidence, setExpandedEvidence] = useState({});

  // Edit Modal State
  const [editingSkill, setEditingSkill] = useState(null);
  const [editForm, setEditForm] = useState({ canonical_name: '', category: '', skill_type: 'technical' });

  const loadSkills = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      let res = await getSkills(resumeId);
      if (!res.data || res.data.length === 0) {
        res = await extractSkills(resumeId);
      }
      setSkills(res.data || []);
      setSummary(res.summary || null);
    } catch (err) {
      setError(err.message || 'Failed to load skills.');
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  const handleReprocess = async (forceOverwrite = false) => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await reprocessSkills(resumeId, forceOverwrite);
      setSkills(res.data || []);
      setSummary(res.summary || null);
      setSuccessMessage('Skills reprocessed successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to reprocess skills.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirm = async (skillId, overrideName = null) => {
    try {
      await confirmSkillMapping(resumeId, skillId, overrideName);
      setSkills((prev) =>
        prev.map((s) =>
          s.id === skillId || s.canonical_name === skillId
            ? { ...s, normalization_status: 'confirmed', is_manually_edited: true }
            : s
        )
      );
    } catch (err) {
      setError(err.message || 'Failed to confirm skill mapping.');
    }
  };

  const handleReject = async (skillId) => {
    try {
      await rejectSkillMapping(resumeId, skillId);
      setSkills((prev) =>
        prev.map((s) =>
          s.id === skillId || s.canonical_name === skillId
            ? { ...s, canonical_name: s.original_name, normalization_status: 'rejected', is_manually_edited: true }
            : s
        )
      );
    } catch (err) {
      setError(err.message || 'Failed to reject skill mapping.');
    }
  };

  const handleDelete = async (skillId) => {
    if (!window.confirm('Delete this skill from candidate profile?')) return;
    try {
      await deleteSkillEntry(resumeId, skillId);
      setSkills((prev) => prev.filter((s) => s.id !== skillId && s.canonical_name !== skillId));
    } catch (err) {
      setError(err.message || 'Failed to delete skill.');
    }
  };

  const handleOpenEdit = (skill) => {
    setEditingSkill(skill);
    setEditForm({
      canonical_name: skill.canonical_name,
      category: skill.category,
      skill_type: skill.skill_type || 'technical',
    });
  };

  const handleSaveEdit = async () => {
    if (!editingSkill) return;
    try {
      const res = await updateSkillEntry(resumeId, editingSkill.id || editingSkill.canonical_name, editForm);
      if (res.data) {
        setSkills((prev) =>
          prev.map((s) => (s.id === editingSkill.id || s.canonical_name === editingSkill.canonical_name ? res.data : s))
        );
      }
      setEditingSkill(null);
    } catch (err) {
      setError(err.message || 'Failed to update skill.');
    }
  };

  const toggleEvidence = (skillKey) => {
    setExpandedEvidence((prev) => ({ ...prev, [skillKey]: !prev[skillKey] }));
  };

  // Filter skills by selected category
  const filteredSkills = skills.filter((s) => {
    if (selectedCategory === 'All') return true;
    return s.category === selectedCategory;
  });

  const pendingReviews = skills.filter((s) => s.normalization_status === 'pending_review');

  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-3 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="md" className="text-teal-600 mx-auto" />
        <h4 className="text-sm font-bold text-slate-800">Normalizing Skills...</h4>
        <p className="text-xs text-slate-500">Mapping aliases, resolving abbreviations, and consolidating duplicates.</p>
      </Card>
    );
  }

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-slate-900">
                  Normalized Skills Profile
                </CardTitle>
                <Badge variant="outline" className="border-teal-200 bg-teal-50 text-teal-800 text-[10px] font-bold">
                  Phase 3 • Feature 17
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                Standardized skills with alias resolution, false-merge guards, and section evidence.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleReprocess(false)}
              disabled={isProcessing}
              className="text-xs h-8 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:bg-slate-50"
              title="Reprocess skill extraction and normalization"
            >
              <RotateCw className={cn('w-3.5 h-3.5', isProcessing && 'animate-spin')} />
              <span>{isProcessing ? 'Normalizing...' : 'Reprocess'}</span>
            </Button>
          </div>
        </div>

        {/* Aggregate Summary Metrics */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-3 mt-3 border-t border-slate-200/60 text-center">
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">Extracted</span>
              <span className="text-sm font-bold text-slate-800 font-mono">{summary.total_original_skills}</span>
            </div>
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">Normalized</span>
              <span className="text-sm font-bold text-teal-700 font-mono">{summary.total_normalized_skills}</span>
            </div>
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">Consolidated</span>
              <span className="text-sm font-bold text-indigo-700 font-mono">{summary.duplicates_consolidated}</span>
            </div>
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">Aliases Matched</span>
              <span className="text-sm font-bold text-blue-700 font-mono">{summary.aliases_matched}</span>
            </div>
            <div className="bg-white p-2 rounded border border-slate-200 col-span-2 sm:col-span-1">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">Pending Reviews</span>
              <span className={cn('text-sm font-bold font-mono', summary.pending_reviews > 0 ? 'text-amber-600' : 'text-slate-500')}>
                {summary.pending_reviews}
              </span>
            </div>
          </div>
        )}

        {/* Feedback Alerts */}
        {error && (
          <Alert variant="destructive" className="mt-3 text-left">
            <p className="text-xs">{error}</p>
          </Alert>
        )}
        {successMessage && (
          <div className="mt-3 p-2.5 rounded bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Pending Reviews Banner */}
        {pendingReviews.length > 0 && (
          <div className="mt-3 p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>{pendingReviews.length} Uncertain Mapping{pendingReviews.length > 1 ? 's' : ''} Need Confirmation</span>
            </div>
            <p className="text-[11px] text-amber-700 leading-relaxed">
              These skill names were ambiguous or matched via semantic heuristics. Please confirm or reject below to prevent incorrect merging.
            </p>
            <div className="divide-y divide-amber-200/60 bg-white rounded border border-amber-200 text-xs">
              {pendingReviews.map((item) => (
                <div key={item.id || item.canonical_name} className="p-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="min-w-0">
                    <span className="font-semibold text-slate-800">{item.original_name}</span>
                    <span className="text-slate-400 mx-1.5">→</span>
                    <span className="font-bold text-teal-700">{item.canonical_name}</span>
                    <span className="text-[10px] text-slate-500 ml-2">({item.category})</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleConfirm(item.id || item.canonical_name)}
                      className="h-7 text-[11px] border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                    >
                      <Check className="w-3 h-3 mr-1" /> Confirm
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReject(item.id || item.canonical_name)}
                      className="h-7 text-[11px] border-red-300 text-red-700 hover:bg-red-50"
                    >
                      <X className="w-3 h-3 mr-1" /> Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Category Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-3 pb-1 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                'px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors',
                selectedCategory === cat
                  ? 'bg-teal-700 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </CardHeader>

      {/* Skills Grid */}
      <div className="p-4 sm:p-6">
        {filteredSkills.length === 0 ? (
          <div className="text-center py-8 text-slate-500 space-y-2">
            <Code2 className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-xs">No skills found for this category.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredSkills.map((skill) => {
              const skillKey = skill.id || skill.canonical_name;
              const hasEvidence = skill.source_evidence && skill.source_evidence.length > 0;
              const isExpanded = !!expandedEvidence[skillKey];

              return (
                <div
                  key={skillKey}
                  className={cn(
                    'p-3.5 rounded-lg border bg-white flex flex-col justify-between space-y-2.5 transition-shadow hover:shadow-xs',
                    skill.normalization_status === 'pending_review'
                      ? 'border-amber-300 bg-amber-50/30'
                      : 'border-slate-200'
                  )}
                >
                  <div className="space-y-1.5">
                    {/* Header Row: Canonical Name & Category */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-slate-900 truncate" title={skill.canonical_name}>
                          {skill.canonical_name}
                        </h4>
                        <span className="text-[10px] font-semibold text-slate-500 block truncate">
                          {skill.category}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleOpenEdit(skill)}
                          className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded"
                          title="Edit skill details"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(skill.id || skill.canonical_name)}
                          className="p-1 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded"
                          title="Delete skill"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Method & Confidence Pill */}
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-[9px] uppercase font-bold py-0 px-1.5',
                          skill.normalization_method === 'exact_match'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            : skill.normalization_method === 'alias_match'
                            ? 'border-blue-200 bg-blue-50 text-blue-800'
                            : skill.normalization_method === 'contextual_match'
                            ? 'border-purple-200 bg-purple-50 text-purple-800'
                            : 'border-slate-200 bg-slate-50 text-slate-700'
                        )}
                      >
                        {skill.normalization_method.replace('_', ' ')}
                      </Badge>

                      {skill.occurrence_count > 1 && (
                        <Badge variant="outline" className="text-[9px] border-indigo-200 bg-indigo-50 text-indigo-800 font-semibold py-0 px-1.5">
                          {skill.occurrence_count} mentions
                        </Badge>
                      )}

                      {skill.is_manually_edited && (
                        <Badge variant="outline" className="text-[9px] border-teal-200 bg-teal-50 text-teal-800 font-semibold py-0 px-1.5">
                          User Edited
                        </Badge>
                      )}
                    </div>

                    {/* Aliases Detected */}
                    {skill.aliases_detected && skill.aliases_detected.length > 0 && (
                      <div className="text-[11px] text-slate-600 flex flex-wrap items-center gap-1 pt-1">
                        <span className="text-slate-400 text-[10px]">Aliases:</span>
                        {skill.aliases_detected.map((al, idx) => (
                          <span key={idx} className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-mono">
                            {al}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Source Sections */}
                    {skill.source_sections && skill.source_sections.length > 0 && (
                      <div className="text-[10px] text-slate-400 flex items-center gap-1">
                        <span>Sections:</span>
                        <span className="text-slate-600 font-medium">
                          {skill.source_sections.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Evidence Drawer */}
                  {hasEvidence && (
                    <div className="pt-2 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => toggleEvidence(skillKey)}
                        className="text-[10px] text-slate-500 hover:text-slate-800 font-semibold flex items-center justify-between w-full"
                      >
                        <span>Evidence ({skill.source_evidence.length})</span>
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>
                      {isExpanded && (
                        <div className="mt-1.5 space-y-1 max-h-28 overflow-y-auto pr-1">
                          {skill.source_evidence.map((ev, eIdx) => (
                            <p key={eIdx} className="text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-100 italic leading-snug">
                              "{ev}"
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Manual Edit Dialog */}
      {editingSkill && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-sm w-full p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-900">Edit Skill Mapping</h3>
              <button
                type="button"
                onClick={() => setEditingSkill(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Original Name</label>
                <input
                  type="text"
                  disabled
                  value={editingSkill.original_name}
                  className="w-full px-2.5 py-1.5 bg-slate-100 border border-slate-200 rounded text-slate-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Canonical Name</label>
                <input
                  type="text"
                  value={editForm.canonical_name}
                  onChange={(e) => setEditForm({ ...editForm, canonical_name: e.target.value })}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Category</label>
                <select
                  value={editForm.category}
                  onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
                >
                  {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Skill Type</label>
                <select
                  value={editForm.skill_type}
                  onChange={(e) => setEditForm({ ...editForm, skill_type: e.target.value })}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-teal-500"
                >
                  <option value="technical">Technical</option>
                  <option value="soft">Soft Skill</option>
                  <option value="tool">Tool</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <Button size="sm" variant="outline" onClick={() => setEditingSkill(null)} className="h-8 text-xs">
                Cancel
              </Button>
              <Button size="sm" onClick={handleSaveEdit} className="h-8 text-xs bg-teal-700 hover:bg-teal-800 text-white">
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
