import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Building2,
  Calendar,
  Clock,
  MapPin,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  Check,
  AlertCircle,
  X,
  Save,
  Award,
  Code2,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  extractExperience,
  getExperience,
  addExperience,
  updateExperience,
  deleteExperience,
  reprocessExperience,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

/**
 * Formats employment type for badge display.
 */
function formatEmploymentType(type) {
  if (!type) return 'Full-Time';
  const map = {
    full_time: 'Full-Time',
    part_time: 'Part-Time',
    internship: 'Internship',
    freelance: 'Freelance',
    contract: 'Contract',
    apprenticeship: 'Apprenticeship',
    research: 'Research',
    volunteer: 'Volunteer',
    other: 'Other',
    unknown: 'Experience',
  };
  return map[type] || type.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Formats duration in months to human readable text e.g. "1 yr 2 mos" or "6 mos".
 */
function formatDuration(months) {
  if (!months || months <= 0) return null;
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;

  const parts = [];
  if (years > 0) parts.push(`${years} yr${years > 1 ? 's' : ''}`);
  if (remainingMonths > 0) parts.push(`${remainingMonths} mo${remainingMonths > 1 ? 's' : ''}`);
  return parts.join(' ');
}

/**
 * ExperienceSection Component
 * Phase 3 | Feature 15: Experience Analysis
 */
export function ExperienceSection({ resumeId, className }) {
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Modal / Form state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null); // null if adding new

  const [formState, setFormState] = useState({
    company: '',
    job_title: '',
    employment_type: 'full_time',
    location: '',
    start_date: '',
    end_date: '',
    is_current: false,
    responsibilities: '',
    technical_contributions: '',
    technologies: '',
    achievements: '',
    measurable_impact: '',
  });

  const loadData = useCallback(async () => {
    if (!resumeId) {
      setEntries([]);
      setSummary(null);
      setError(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await extractExperience(resumeId);
      if (res && res.data) {
        setEntries(res.data);
        if (res.summary) {
          setSummary(res.summary);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load experience records.');
      setEntries([]);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleReprocess = async (forceOverwrite = false) => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await reprocessExperience(resumeId, forceOverwrite);
      if (res && res.data) {
        setEntries(res.data);
        if (res.summary) setSummary(res.summary);
        setSuccessMessage('Experience reprocessed successfully.');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      setError(err.message || 'Failed to reprocess experience.');
    } finally {
      setIsProcessing(false);
    }
  };

  const openAddModal = () => {
    setEditingEntry(null);
    setFormState({
      company: '',
      job_title: '',
      employment_type: 'full_time',
      location: '',
      start_date: '',
      end_date: '',
      is_current: false,
      responsibilities: '',
      technical_contributions: '',
      technologies: '',
      achievements: '',
      measurable_impact: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (entry) => {
    setEditingEntry(entry);
    setFormState({
      company: entry.company || '',
      job_title: entry.job_title || '',
      employment_type: entry.employment_type || 'full_time',
      location: entry.location || '',
      start_date: entry.start_date || '',
      end_date: entry.end_date || '',
      is_current: Boolean(entry.is_current),
      responsibilities: (entry.responsibilities || []).join('\n'),
      technical_contributions: (entry.technical_contributions || []).join('\n'),
      technologies: (entry.technologies || []).join(', '),
      achievements: (entry.achievements || []).join('\n'),
      measurable_impact: (entry.measurable_impact || []).join(', '),
    });
    setIsModalOpen(true);
  };

  const handleSaveModal = async (e) => {
    e.preventDefault();
    setIsProcessing(true);
    setError(null);

    const parseLines = (str) =>
      str
        ? str
            .split('\n')
            .map((s) => s.trim())
            .filter(Boolean)
        : [];

    const parseComma = (str) =>
      str
        ? str
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
        : [];

    const payload = {
      company: formState.company.trim() || null,
      job_title: formState.job_title.trim() || null,
      employment_type: formState.employment_type,
      location: formState.location.trim() || null,
      start_date: formState.start_date.trim() || null,
      end_date: formState.is_current ? null : formState.end_date.trim() || null,
      is_current: formState.is_current,
      responsibilities: parseLines(formState.responsibilities),
      technical_contributions: parseLines(formState.technical_contributions),
      technologies: parseComma(formState.technologies),
      achievements: parseLines(formState.achievements),
      measurable_impact: parseComma(formState.measurable_impact),
    };

    try {
      if (editingEntry) {
        await updateExperience(resumeId, editingEntry.id, payload);
        setSuccessMessage('Experience record updated.');
      } else {
        await addExperience(resumeId, payload);
        setSuccessMessage('Experience record added.');
      }
      setIsModalOpen(false);
      await loadData();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save experience record.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this experience record?')) return;
    setIsProcessing(true);
    try {
      await deleteExperience(resumeId, entryId);
      setSuccessMessage('Experience record deleted.');
      await loadData();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to delete record.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <Card className={cn('p-6 bg-white border-slate-200 shadow-sm', className)}>
        <div className="flex items-center gap-3">
          <LoadingIndicator size="sm" />
          <span className="text-sm font-medium text-slate-600">Analyzing professional experience...</span>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="bg-slate-50/60 border-b border-slate-200/80 p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg shrink-0">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base sm:text-lg font-bold text-slate-900">
                  Professional Experience
                </CardTitle>
                <Badge variant="outline" className="text-xs bg-slate-100 font-medium">
                  {entries.length} {entries.length === 1 ? 'Role' : 'Roles'}
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                Structured employment history, technical contributions, and career progression
              </CardDescription>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleReprocess(false)}
              disabled={isProcessing}
              className="text-xs h-8 gap-1.5"
              title="Reprocess experience while preserving manual edits"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isProcessing && 'animate-spin')} />
              <span>Reprocess</span>
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={openAddModal}
              disabled={isProcessing}
              className="text-xs h-8 gap-1.5 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Role</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Messages */}
      {successMessage && (
        <div className="p-3 bg-emerald-50 border-b border-emerald-100 text-xs text-emerald-800 flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Summary Metrics Bar */}
      {!error && summary && summary.employment_count > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-4 bg-slate-50/40 border-b border-slate-100">
          <div className="bg-white p-3 rounded-lg border border-slate-200/70 shadow-2xs">
            <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-blue-500" />
              <span>Total Duration</span>
            </div>
            <div className="text-lg font-bold text-slate-900 mt-1">
              {summary.total_experience_years > 0
                ? `${summary.total_experience_years} yrs`
                : `${summary.total_experience_months} mos`}
            </div>
            <div className="text-[10px] text-slate-400">Non-overlapping unique experience</div>
          </div>

          <div className="bg-white p-3 rounded-lg border border-slate-200/70 shadow-2xs">
            <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
              <Briefcase className="w-3.5 h-3.5 text-indigo-500" />
              <span>Full-Time Roles</span>
            </div>
            <div className="text-lg font-bold text-slate-900 mt-1">{summary.full_time_count}</div>
            <div className="text-[10px] text-slate-400">Permanent positions</div>
          </div>

          <div className="bg-white p-3 rounded-lg border border-slate-200/70 shadow-2xs">
            <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Internships</span>
            </div>
            <div className="text-lg font-bold text-slate-900 mt-1">{summary.internship_count}</div>
            <div className="text-[10px] text-slate-400">Training & internships</div>
          </div>

          <div className="bg-white p-3 rounded-lg border border-slate-200/70 shadow-2xs">
            <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
              <span>Freelance / Contract</span>
            </div>
            <div className="text-lg font-bold text-slate-900 mt-1">
              {summary.freelance_count + summary.contract_count}
            </div>
            <div className="text-[10px] text-slate-400">Independent contracts</div>
          </div>
        </div>
      )}

      {/* Main Content Area: Experience Timeline */}
      <div className="p-4 sm:p-6 space-y-5">
        {!resumeId ? (
          <div className="text-center py-10 px-4 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
              <Briefcase className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-800">No Resume Selected</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Please select or upload a resume to view professional experience.
            </p>
            <Button
              size="sm"
              onClick={() => navigate('/resume')}
              className="mt-4 text-xs gap-1.5"
            >
              Go to Resume Upload
            </Button>
          </div>
        ) : error ? (
          <div className="text-center py-10 px-4 bg-red-50/60 rounded-xl border border-dashed border-red-200">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-3">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-red-900">Experience Analysis Unavailable</h4>
            <p className="text-xs text-red-700 max-w-md mx-auto mt-1 mb-4 leading-relaxed">{error}</p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadData()}
                className="text-xs gap-1 bg-white border-red-200 text-red-800 hover:bg-red-50"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Try Again
              </Button>
              <Button
                size="sm"
                onClick={() => navigate('/resume')}
                className="text-xs gap-1"
              >
                Return to Resume Selection or Upload
              </Button>
            </div>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-10 px-4 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
              <Briefcase className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-800">No Work Experience Records Found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              No professional employment history was detected in the resume text, or the resume may only contain academic projects.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={openAddModal}
              className="mt-4 text-xs gap-1.5 bg-white"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Experience Record</span>
            </Button>
          </div>
        ) : (
          <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2.5 sm:before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
            {entries.map((role) => {
              const formattedDuration = formatDuration(role.duration_months);

              return (
                <div key={role.id} className="relative group">
                  {/* Timeline Node Dot */}
                  <div
                    className={cn(
                      'absolute -left-6 sm:-left-8 top-3 w-4 h-4 rounded-full border-2 border-white shadow-xs',
                      role.is_current ? 'bg-emerald-500 ring-4 ring-emerald-100' : 'bg-blue-600'
                    )}
                  />

                  {/* Card Container */}
                  <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-2xs hover:shadow-xs transition-shadow">
                    {/* Top Row: Title, Company, Actions */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 border-b border-slate-100 pb-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-base font-bold text-slate-900">
                            {role.job_title || 'Untitled Role'}
                          </h3>
                          <Badge
                            variant="secondary"
                            className={cn(
                              'text-[10px] font-semibold uppercase tracking-wider',
                              role.employment_type === 'internship' && 'bg-amber-50 text-amber-700 border-amber-200',
                              role.employment_type === 'freelance' && 'bg-purple-50 text-purple-700 border-purple-200',
                              role.employment_type === 'contract' && 'bg-indigo-50 text-indigo-700 border-indigo-200',
                              role.employment_type === 'full_time' && 'bg-blue-50 text-blue-700 border-blue-200'
                            )}
                          >
                            {formatEmploymentType(role.employment_type)}
                          </Badge>
                          {role.is_current && (
                            <Badge className="text-[10px] bg-emerald-600 text-white font-semibold">
                              Current Role
                            </Badge>
                          )}
                          {role.is_manually_edited && (
                            <Badge variant="outline" className="text-[10px] text-amber-700 border-amber-300 bg-amber-50">
                              Edited
                            </Badge>
                          )}
                        </div>

                        {/* Company & Location */}
                        <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-600">
                          {role.company && (
                            <span className="flex items-center gap-1 font-medium text-slate-800">
                              <Building2 className="w-3.5 h-3.5 text-slate-400" />
                              {role.company}
                            </span>
                          )}
                          {role.location && (
                            <span className="flex items-center gap-1 text-slate-500">
                              <MapPin className="w-3.5 h-3.5 text-slate-400" />
                              {role.location}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Right: Dates & Action buttons */}
                      <div className="flex items-center sm:flex-col sm:items-end justify-between gap-1.5 shrink-0">
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 text-xs font-semibold text-slate-700">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            <span>
                              {role.start_date || 'Start'} – {role.is_current ? 'Present' : role.end_date || 'End'}
                            </span>
                          </div>
                          {formattedDuration && (
                            <Badge variant="outline" className="text-[10px] text-slate-500 font-normal">
                              {formattedDuration}
                            </Badge>
                          )}
                        </div>

                        <div className="flex items-center gap-1 mt-1 opacity-90 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(role)}
                            className="h-7 w-7 p-0 text-slate-500 hover:text-blue-600"
                            title="Edit this role"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(role.id)}
                            className="h-7 w-7 p-0 text-slate-500 hover:text-red-600"
                            title="Delete this role"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Middle: Responsibilities & Technical Contributions */}
                    <div className="mt-3 space-y-3 text-xs text-slate-700">
                      {role.responsibilities && role.responsibilities.length > 0 && (
                        <div>
                          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                            Key Responsibilities
                          </div>
                          <ul className="space-y-1 list-disc list-outside pl-4">
                            {role.responsibilities.map((resp, idx) => (
                              <li key={idx} className="leading-relaxed">
                                {resp}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Technical Contributions */}
                      {role.technical_contributions && role.technical_contributions.length > 0 && (
                        <div>
                          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <Code2 className="w-3 h-3 text-blue-500" />
                            <span>Technical Contributions</span>
                          </div>
                          <ul className="space-y-1 list-disc list-outside pl-4 text-slate-800">
                            {role.technical_contributions.map((tc, idx) => (
                              <li key={idx} className="leading-relaxed">
                                {tc}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Achievements & Measurable Impact */}
                      {role.achievements && role.achievements.length > 0 && (
                        <div className="bg-amber-50/50 p-2.5 rounded-lg border border-amber-100/80">
                          <div className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <Award className="w-3 h-3 text-amber-600" />
                            <span>Key Achievements & Impact</span>
                          </div>
                          <ul className="space-y-1 list-disc list-outside pl-4 text-amber-950">
                            {role.achievements.map((ach, idx) => (
                              <li key={idx} className="leading-relaxed">
                                {ach}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Measurable Impact Pills */}
                      {role.measurable_impact && role.measurable_impact.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase">Impact:</span>
                          {role.measurable_impact.map((imp, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-[10px] bg-emerald-50 text-emerald-700 border-emerald-200 font-medium"
                            >
                              {imp}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* Technologies Tag Cloud */}
                      {role.technologies && role.technologies.length > 0 && (
                        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase">Tech Stack:</span>
                          {role.technologies.map((tech, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="text-[11px] bg-slate-100 text-slate-700 hover:bg-slate-200 border-slate-200 font-normal py-0.5"
                            >
                              {tech}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal Dialog for Add / Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xs">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-100 bg-slate-50/50">
              <h3 className="text-base font-bold text-slate-900">
                {editingEntry ? 'Edit Experience Record' : 'Add Professional Experience'}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsModalOpen(false)}
                className="h-8 w-8 p-0 text-slate-400 hover:text-slate-600 rounded-full"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSaveModal} className="p-4 sm:p-6 overflow-y-auto space-y-4 flex-1">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={formState.job_title}
                    onChange={(e) => setFormState({ ...formState, job_title: e.target.value })}
                    placeholder="e.g. Software Engineer"
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formState.company}
                    onChange={(e) => setFormState({ ...formState, company: e.target.value })}
                    placeholder="e.g. Acme Corporation"
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Employment Type
                  </label>
                  <select
                    value={formState.employment_type}
                    onChange={(e) => setFormState({ ...formState, employment_type: e.target.value })}
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                  >
                    <option value="full_time">Full-Time</option>
                    <option value="internship">Internship</option>
                    <option value="freelance">Freelance</option>
                    <option value="contract">Contract</option>
                    <option value="part_time">Part-Time</option>
                    <option value="apprenticeship">Apprenticeship</option>
                    <option value="research">Research</option>
                    <option value="volunteer">Volunteer</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formState.location}
                    onChange={(e) => setFormState({ ...formState, location: e.target.value })}
                    placeholder="e.g. Bengaluru, India or Remote"
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Date Ranges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Start Date (YYYY-MM or YYYY)
                  </label>
                  <input
                    type="text"
                    value={formState.start_date}
                    onChange={(e) => setFormState({ ...formState, start_date: e.target.value })}
                    placeholder="e.g. 2023-06"
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    End Date (YYYY-MM or YYYY)
                  </label>
                  <input
                    type="text"
                    disabled={formState.is_current}
                    value={formState.is_current ? '' : formState.end_date}
                    onChange={(e) => setFormState({ ...formState, end_date: e.target.value })}
                    placeholder={formState.is_current ? 'Present' : 'e.g. 2024-08'}
                    className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-slate-50 disabled:text-slate-400"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_current"
                  checked={formState.is_current}
                  onChange={(e) => setFormState({ ...formState, is_current: e.target.checked })}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="is_current" className="text-xs font-medium text-slate-700">
                  I currently work here (Ongoing position)
                </label>
              </div>

              {/* Technologies */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Technologies and Tools (comma separated)
                </label>
                <input
                  type="text"
                  value={formState.technologies}
                  onChange={(e) => setFormState({ ...formState, technologies: e.target.value })}
                  placeholder="e.g. Python, FastAPI, React, Docker, PostgreSQL"
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Responsibilities */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Responsibilities (one per line)
                </label>
                <textarea
                  rows={3}
                  value={formState.responsibilities}
                  onChange={(e) => setFormState({ ...formState, responsibilities: e.target.value })}
                  placeholder="Developed backend services using FastAPI&#10;Collaborated with cross-functional teams"
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                />
              </div>

              {/* Technical Contributions */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Technical Contributions (one per line)
                </label>
                <textarea
                  rows={2}
                  value={formState.technical_contributions}
                  onChange={(e) => setFormState({ ...formState, technical_contributions: e.target.value })}
                  placeholder="Architected async Celery task queues&#10;Implemented model inference pipelines"
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                />
              </div>

              {/* Achievements */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Achievements and Measurable Impact (one per line)
                </label>
                <textarea
                  rows={2}
                  value={formState.achievements}
                  onChange={(e) => setFormState({ ...formState, achievements: e.target.value })}
                  placeholder="Reduced API latency by 40%&#10;Awarded Top Performer Q3 2024"
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                />
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                  className="text-xs h-8"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isProcessing}
                  className="text-xs h-8 bg-blue-600 hover:bg-blue-700 text-white gap-1.5"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{editingEntry ? 'Update Role' : 'Save Role'}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Card>
  );
}
