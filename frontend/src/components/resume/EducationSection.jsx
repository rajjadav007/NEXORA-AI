import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  Building2,
  Calendar,
  Award,
  BookOpen,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  Check,
  AlertCircle,
  X,
  Save,
  MapPin,
  Clock,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  extractEducation,
  getEducation,
  addEducation,
  updateEducation,
  deleteEducation,
  reprocessEducation,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

/**
 * Format degree level for badge display
 */
function formatDegreeLevel(level) {
  if (!level) return null;
  const map = {
    undergraduate: 'Undergraduate',
    postgraduate: 'Postgraduate',
    doctorate: 'Doctorate',
    diploma: 'Diploma',
    higher_secondary: '12th / Intermediate',
    high_school: '10th / Secondary',
    certification: 'Certification',
    other: 'Academic Program',
  };
  return map[level] || level.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * EducationSection Component
 * Phase 3 | Feature 14: Education Analysis
 */
export function EducationSection({ resumeId, className }) {
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Modal / Form state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null); // null if adding new

  const [formState, setFormState] = useState({
    degree: '',
    institution: '',
    field_of_study: '',
    degree_level: 'undergraduate',
    location: '',
    start_date: '',
    end_date: '',
    graduation_status: 'completed',
    grade_value: '',
    grade_type: 'CGPA',
    grade_scale: '10',
    coursework: '',
    achievements: '',
  });

  const loadData = useCallback(async () => {
    if (!resumeId) {
      setEntries([]);
      setError(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      // First attempt extract (auto-returns cached/existing if already saved)
      const res = await extractEducation(resumeId);
      if (res && res.data) {
        setEntries(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load education records.');
      setEntries([]);
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openAddModal = () => {
    setEditingEntry(null);
    setFormState({
      degree: '',
      institution: '',
      field_of_study: '',
      degree_level: 'undergraduate',
      location: '',
      start_date: '',
      end_date: '',
      graduation_status: 'completed',
      grade_value: '',
      grade_type: 'CGPA',
      grade_scale: '10',
      coursework: '',
      achievements: '',
    });
    setIsModalOpen(true);
    setError(null);
  };

  const openEditModal = (entry) => {
    setEditingEntry(entry);
    setFormState({
      degree: entry.degree || '',
      institution: entry.institution || '',
      field_of_study: entry.field_of_study || '',
      degree_level: entry.degree_level || 'undergraduate',
      location: entry.location || '',
      start_date: entry.start_date || '',
      end_date: entry.end_date || '',
      graduation_status: entry.graduation_status || 'completed',
      grade_value: entry.grade?.value !== null && entry.grade?.value !== undefined ? String(entry.grade.value) : '',
      grade_type: entry.grade?.type || 'CGPA',
      grade_scale: entry.grade?.scale ? String(entry.grade.scale) : '10',
      coursework: (entry.coursework || []).join(', '),
      achievements: (entry.achievements || []).join(', '),
    });
    setIsModalOpen(true);
    setError(null);
  };

  const handleSaveModal = async (e) => {
    e.preventDefault();
    if (!formState.degree && !formState.institution) {
      setError('Please provide at least a degree or an institution.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    const gradeData = formState.grade_value ? {
      value: isNaN(Number(formState.grade_value)) ? formState.grade_value : Number(formState.grade_value),
      type: formState.grade_type,
      scale: formState.grade_scale ? Number(formState.grade_scale) : null,
      raw_grade: `${formState.grade_value}${formState.grade_scale ? '/' + formState.grade_scale : ''}`,
    } : null;

    const courseworkList = formState.coursework
      ? formState.coursework.split(',').map((c) => c.strip ? c.strip() : c.trim()).filter(Boolean)
      : [];

    const achievementsList = formState.achievements
      ? formState.achievements.split(',').map((a) => a.strip ? a.strip() : a.trim()).filter(Boolean)
      : [];

    const payload = {
      degree: formState.degree || null,
      institution: formState.institution || null,
      field_of_study: formState.field_of_study || null,
      degree_level: formState.degree_level || null,
      location: formState.location || null,
      start_date: formState.start_date || null,
      end_date: formState.end_date || null,
      graduation_status: formState.graduation_status || 'completed',
      grade: gradeData,
      coursework: courseworkList,
      achievements: achievementsList,
    };

    try {
      if (editingEntry) {
        const res = await updateEducation(resumeId, editingEntry.id, payload);
        setEntries((prev) => prev.map((item) => (item.id === editingEntry.id ? res.data : item)));
        setSuccessMessage('Education record updated successfully.');
      } else {
        const res = await addEducation(resumeId, payload);
        setEntries((prev) => [res.data, ...prev]);
        setSuccessMessage('Education record added successfully.');
      }
      setIsModalOpen(false);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to save education record.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (educationId) => {
    if (!window.confirm('Are you sure you want to delete this education record?')) return;
    setIsProcessing(true);
    setError(null);
    try {
      await deleteEducation(resumeId, educationId);
      setEntries((prev) => prev.filter((item) => item.id !== educationId));
      setSuccessMessage('Education record deleted successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to delete education record.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReprocess = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await reprocessEducation(resumeId);
      setEntries(res.data || []);
      setSuccessMessage('Education qualifications reprocessed successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to reprocess education records.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <Card className={cn('p-6 text-center space-y-3 border-slate-200 bg-white/60 shadow-sm', className)}>
        <LoadingIndicator size="md" className="text-teal-600 mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Analyzing education qualifications and timeline...</p>
      </Card>
    );
  }

  return (
    <Card className={cn('border-slate-200 shadow-sm bg-white overflow-hidden', className)}>
      <CardHeader className="border-b border-slate-100 bg-slate-50/60 pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                Education & Academic History
                <Badge variant="outline" className="text-[10px] text-teal-800 bg-teal-50 border-teal-200">
                  {entries.length} {entries.length === 1 ? 'Record' : 'Records'}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Verified degrees, institutions, GPA/CGPA, coursework, and chronological academic progression
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={openAddModal}
              disabled={isProcessing}
              className="text-xs h-8 flex items-center gap-1.5 border-teal-200 text-teal-800 bg-teal-50/50 hover:bg-teal-100"
            >
              <Plus className="w-3.5 h-3.5" /> Add Degree
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleReprocess}
              disabled={isProcessing}
              className="text-xs h-8 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:text-slate-900"
              title="Re-extract education qualifications from resume text"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isProcessing && 'animate-spin')} />
              <span>Reprocess</span>
            </Button>
          </div>
        </div>

        {successMessage && (
          <Alert variant="default" className="mt-3 border-teal-200 bg-teal-50 text-teal-800 text-xs py-2">
            <Check className="w-4 h-4 text-teal-600 inline mr-1.5" />
            {successMessage}
          </Alert>
        )}

      </CardHeader>

      <div className="p-5">
        {!resumeId ? (
          <div className="text-center py-8 space-y-2 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <GraduationCap className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-semibold text-slate-800">No Resume Selected</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Please select or upload a resume to view education & academic history.
            </p>
            <Button size="sm" onClick={() => navigate('/resume')} className="mt-4 text-xs">
              Go to Resume Upload
            </Button>
          </div>
        ) : error ? (
          <div className="text-center py-8 space-y-3 bg-red-50/60 rounded-xl border border-dashed border-red-200 p-6">
            <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-red-900">Education Details Unavailable</h4>
            <p className="text-xs text-red-700 max-w-md mx-auto leading-relaxed">{error}</p>
            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadData()}
                className="text-xs gap-1 bg-white border-red-200 text-red-800 hover:bg-red-50"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Try Again
              </Button>
              <Button size="sm" onClick={() => navigate('/resume')} className="text-xs">
                Return to Resume Selection or Upload
              </Button>
            </div>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-8 space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <GraduationCap className="w-5 h-5" />
            </div>
            <p className="text-xs text-slate-500 font-medium">No education qualifications detected in this resume.</p>
            <Button
              variant="outline"
              size="sm"
              onClick={openAddModal}
              className="text-xs h-8 text-teal-700 border-teal-200 hover:bg-teal-50"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Education Manually
            </Button>
          </div>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
            {entries.map((item, index) => {
              const isOngoing = item.graduation_status === 'ongoing' || item.graduation_status === 'expected';
              return (
                <div key={item.id || index} className="relative group">
                  {/* Timeline Dot */}
                  <div
                    className={cn(
                      'absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 bg-white transition-colors',
                      isOngoing ? 'border-teal-600 bg-teal-50' : 'border-slate-400'
                    )}
                  />

                  {/* Degree Card */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 hover:bg-white hover:shadow-xs transition-all space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-sm font-bold text-slate-900">
                            {item.normalized_degree || item.degree || 'Degree Not Specified'}
                          </h4>
                          {item.degree_level && (
                            <Badge
                              variant="outline"
                              className="text-[10px] font-semibold bg-blue-50 text-blue-700 border-blue-200"
                            >
                              {formatDegreeLevel(item.degree_level)}
                            </Badge>
                          )}
                          {item.graduation_status && (
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-[10px] font-medium',
                                isOngoing
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : 'bg-slate-100 text-slate-600 border-slate-200'
                              )}
                            >
                              {item.graduation_status.replace('_', ' ').toUpperCase()}
                            </Badge>
                          )}
                          {item.is_manually_edited && (
                            <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-700 border-amber-200">
                              Edited
                            </Badge>
                          )}
                        </div>

                        {/* Institution and Field of Study */}
                        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
                          {item.institution && (
                            <span className="flex items-center gap-1 font-medium text-slate-800">
                              <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                              <span>{item.institution}</span>
                            </span>
                          )}
                          {item.location && (
                            <span className="flex items-center gap-1 text-slate-500">
                              <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                              <span>{item.location}</span>
                            </span>
                          )}
                          {item.field_of_study && (
                            <span className="flex items-center gap-1 text-teal-800 font-medium">
                              <BookOpen className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                              <span>{item.field_of_study}</span>
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 self-start shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModal(item)}
                          disabled={isProcessing}
                          className="text-xs h-7 px-2 text-slate-600 hover:text-slate-900"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(item.id)}
                          disabled={isProcessing}
                          className="text-xs h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>

                    {/* Timeline Dates & Grade Row */}
                    <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-slate-100 text-xs">
                      {(item.start_date || item.end_date) && (
                        <span className="flex items-center gap-1 text-slate-500">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {item.start_date || 'Start'} – {item.end_date || 'Present'}
                          </span>
                        </span>
                      )}

                      {/* Grade Badge */}
                      {item.grade && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200">
                          <Award className="w-3 h-3 text-teal-600" />
                          <span>
                            {item.grade.type || 'Grade'}:{' '}
                            {item.grade.value !== null && item.grade.value !== undefined
                              ? item.grade.value
                              : item.grade.raw_grade}
                            {item.grade.scale && item.grade.type !== 'Percentage' ? `/${item.grade.scale}` : ''}
                            {item.grade.type === 'Percentage' ? '%' : ''}
                          </span>
                        </div>
                      )}

                      {item.extraction_confidence && (
                        <span className="text-[10px] text-slate-400 ml-auto">
                          {Math.round(item.extraction_confidence * 100)}% confidence
                        </span>
                      )}
                    </div>

                    {/* Coursework tags */}
                    {item.coursework && item.coursework.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                          Relevant Coursework:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {item.coursework.map((course, cIdx) => (
                            <span
                              key={cIdx}
                              className="text-[11px] px-2 py-0.5 rounded bg-slate-200/70 text-slate-700 font-medium"
                            >
                              {course}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Achievements */}
                    {item.achievements && item.achievements.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                          Achievements:
                        </span>
                        <ul className="list-disc list-inside text-xs text-slate-600 space-y-0.5">
                          {item.achievements.map((ach, aIdx) => (
                            <li key={aIdx}>{ach}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal Dialog for Add / Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingEntry ? 'Edit Education Qualification' : 'Add Education Qualification'}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsModalOpen(false)}
                className="h-8 w-8 p-0 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <form onSubmit={handleSaveModal} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Degree Title *</label>
                <input
                  type="text"
                  value={formState.degree}
                  onChange={(e) => setFormState({ ...formState, degree: e.target.value })}
                  placeholder="e.g. Bachelor of Technology or BCA"
                  required
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Institution Name *</label>
                <input
                  type="text"
                  value={formState.institution}
                  onChange={(e) => setFormState({ ...formState, institution: e.target.value })}
                  placeholder="e.g. National Institute of Technology"
                  required
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Field of Study</label>
                  <input
                    type="text"
                    value={formState.field_of_study}
                    onChange={(e) => setFormState({ ...formState, field_of_study: e.target.value })}
                    placeholder="e.g. Computer Science"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Degree Level</label>
                  <select
                    value={formState.degree_level}
                    onChange={(e) => setFormState({ ...formState, degree_level: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 bg-white"
                  >
                    <option value="undergraduate">Undergraduate (Bachelor's)</option>
                    <option value="postgraduate">Postgraduate (Master's)</option>
                    <option value="doctorate">Doctorate (PhD)</option>
                    <option value="diploma">Diploma</option>
                    <option value="higher_secondary">12th / Higher Secondary</option>
                    <option value="high_school">10th / Secondary</option>
                    <option value="certification">Certification</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Year</label>
                  <input
                    type="text"
                    value={formState.start_date}
                    onChange={(e) => setFormState({ ...formState, start_date: e.target.value })}
                    placeholder="e.g. 2020"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Year</label>
                  <input
                    type="text"
                    value={formState.end_date}
                    onChange={(e) => setFormState({ ...formState, end_date: e.target.value })}
                    placeholder="e.g. 2024 or Present"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Status</label>
                  <select
                    value={formState.graduation_status}
                    onChange={(e) => setFormState({ ...formState, graduation_status: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 bg-white"
                  >
                    <option value="completed">Completed</option>
                    <option value="ongoing">Ongoing</option>
                    <option value="expected">Expected</option>
                    <option value="discontinued">Discontinued</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Grade Value</label>
                  <input
                    type="text"
                    value={formState.grade_value}
                    onChange={(e) => setFormState({ ...formState, grade_value: e.target.value })}
                    placeholder="e.g. 7.47 or 85"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Grade Type</label>
                  <select
                    value={formState.grade_type}
                    onChange={(e) => setFormState({ ...formState, grade_type: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 bg-white"
                  >
                    <option value="CGPA">CGPA</option>
                    <option value="GPA">GPA</option>
                    <option value="Percentage">Percentage (%)</option>
                    <option value="Classification">Classification</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Scale</label>
                  <input
                    type="text"
                    value={formState.grade_scale}
                    onChange={(e) => setFormState({ ...formState, grade_scale: e.target.value })}
                    placeholder="10, 4, or 100"
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Relevant Coursework (comma-separated)</label>
                <input
                  type="text"
                  value={formState.coursework}
                  onChange={(e) => setFormState({ ...formState, coursework: e.target.value })}
                  placeholder="e.g. Data Structures, Database Systems, Cloud Computing"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Academic Achievements (comma-separated)</label>
                <input
                  type="text"
                  value={formState.achievements}
                  onChange={(e) => setFormState({ ...formState, achievements: e.target.value })}
                  placeholder="e.g. Dean's List, 1st Rank in Department"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isProcessing}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isProcessing}
                  className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isProcessing ? 'Saving...' : 'Save Record'}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Card>
  );
}
