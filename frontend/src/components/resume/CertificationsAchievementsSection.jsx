import React, { useState, useEffect, useCallback } from 'react';
import {
  Award,
  Medal,
  Scroll,
  BookOpen,
  Trophy,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Edit2,
  Trash2,
  Check,
  X,
  Plus,
  Users,
  Calendar,
  Layers,
  Sparkles,
  Search,
  Clock,
  ShieldCheck,
  Code,
  FolderGit2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  getCertifications,
  extractCertifications,
  reprocessCertifications,
  addCertification,
  updateCertification,
  deleteCertification,
  confirmCertification,
  getAchievements,
  extractAchievements,
  reprocessAchievements,
  addAchievement,
  updateAchievement,
  deleteAchievement,
  confirmAchievement,
  getProjects,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

const TABS = [
  { key: 'all', label: 'All Records' },
  { key: 'certifications', label: 'Certifications' },
  { key: 'achievements', label: 'Achievements' },
  { key: 'hackathons', label: 'Hackathons' },
  { key: 'publications', label: 'Publications' },
  { key: 'pending', label: 'Pending Review' },
];

const CERT_CATEGORY_COLORS = {
  cloud: 'bg-sky-50 text-sky-700 border-sky-200',
  ai_ml: 'bg-purple-50 text-purple-700 border-purple-200',
  data_science: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  security: 'bg-red-50 text-red-700 border-red-200',
  programming: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  project_management: 'bg-amber-50 text-amber-700 border-amber-200',
  technical: 'bg-blue-50 text-blue-700 border-blue-200',
  professional: 'bg-teal-50 text-teal-700 border-teal-200',
  course: 'bg-orange-50 text-orange-700 border-orange-200',
  training: 'bg-cyan-50 text-cyan-700 border-cyan-200',
  other: 'bg-slate-100 text-slate-700 border-slate-200',
};

const ACHIEVE_TYPE_COLORS = {
  award: 'bg-amber-50 text-amber-800 border-amber-300',
  ranking: 'bg-blue-50 text-blue-800 border-blue-300',
  publication: 'bg-purple-50 text-purple-800 border-purple-300',
  scholarship: 'bg-emerald-50 text-emerald-800 border-emerald-300',
  participation: 'bg-slate-100 text-slate-700 border-slate-300',
  recognition: 'bg-teal-50 text-teal-800 border-teal-300',
  other: 'bg-slate-50 text-slate-700 border-slate-200',
};

const EMPTY_CERT_FORM = {
  certification_name: '',
  normalized_name: '',
  issuing_organization: '',
  certification_category: 'cloud',
  issue_date: '',
  expiry_date: '',
  credential_id: '',
  credential_url: '',
  completion_status: 'completed',
};

const EMPTY_ACHIEVE_FORM = {
  achievement_title: '',
  normalized_title: '',
  achievement_category: 'hackathon',
  event_name: '',
  organization: '',
  achievement_type: 'award',
  rank_or_position: '1st Place',
  achievement_date: '',
  description: '',
  team_name: '',
  team_size: '',
  candidate_role: '',
  related_project_id: '',
  achievement_url: '',
};

export function CertificationsAchievementsSection({ resumeId, className }) {
  const [certifications, setCertifications] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals state
  const [certModalOpen, setCertModalOpen] = useState(false);
  const [achieveModalOpen, setAchieveModalOpen] = useState(false);
  const [editingCertId, setEditingCertId] = useState(null);
  const [editingAchieveId, setEditingAchieveId] = useState(null);
  const [certFormData, setCertFormData] = useState(EMPTY_CERT_FORM);
  const [achieveFormData, setAchieveFormData] = useState(EMPTY_ACHIEVE_FORM);

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState(null); // { type: 'cert' | 'achieve', id: string, name: string }

  const loadData = useCallback(async (autoExtract = true) => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      // 1. Load Projects for linking dropdown
      try {
        const pRes = await getProjects(resumeId);
        if (pRes?.data) setProjects(pRes.data);
      } catch {
        // Optional project loading
      }

      // 2. Fetch existing Certifications
      let cRes = await getCertifications(resumeId);
      let certList = cRes?.data || [];

      // Auto-extract if empty
      if (certList.length === 0 && autoExtract) {
        try {
          const extRes = await extractCertifications(resumeId);
          certList = extRes?.data || [];
        } catch {
          // Fallback to empty
        }
      }
      setCertifications(certList);

      // 3. Fetch existing Achievements
      let aRes = await getAchievements(resumeId);
      let achieveList = aRes?.data || [];

      // Auto-extract if empty
      if (achieveList.length === 0 && autoExtract) {
        try {
          const extAchieveRes = await extractAchievements(resumeId);
          achieveList = extAchieveRes?.data || [];
        } catch {
          // Fallback to empty
        }
      }
      setAchievements(achieveList);
    } catch (err) {
      setError(err.message || 'Failed to load certifications and achievements.');
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  const handleReprocessAll = async (forceOverwrite = false) => {
    if (!resumeId || isProcessing) return;
    setIsProcessing(true);
    setError(null);
    try {
      const [cRes, aRes] = await Promise.all([
        reprocessCertifications(resumeId, { forceOverwrite }),
        reprocessAchievements(resumeId, { forceOverwrite }),
      ]);
      setCertifications(cRes.data || []);
      setAchievements(aRes.data || []);
    } catch (err) {
      setError(err.message || 'Failed to reprocess records.');
    } finally {
      setIsProcessing(false);
    }
  };

  // --- CERTIFICATION CRUD HANDLERS ---

  const handleSaveCert = async (e) => {
    e.preventDefault();
    if (!certFormData.certification_name.trim()) return;
    setIsProcessing(true);
    try {
      if (editingCertId) {
        const res = await updateCertification(resumeId, editingCertId, certFormData);
        setCertifications((prev) =>
          prev.map((c) => (c.id === editingCertId ? res.data : c))
        );
      } else {
        const res = await addCertification(resumeId, certFormData);
        setCertifications((prev) => [...prev, res.data]);
      }
      setCertModalOpen(false);
      setEditingCertId(null);
      setCertFormData(EMPTY_CERT_FORM);
    } catch (err) {
      setError(err.message || 'Failed to save certification.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmCert = async (certId) => {
    try {
      const res = await confirmCertification(resumeId, certId);
      setCertifications((prev) =>
        prev.map((c) => (c.id === certId ? res.data : c))
      );
    } catch (err) {
      setError(err.message || 'Failed to confirm certification.');
    }
  };

  // --- ACHIEVEMENT CRUD HANDLERS ---

  const handleSaveAchieve = async (e) => {
    e.preventDefault();
    if (!achieveFormData.achievement_title.trim()) return;
    setIsProcessing(true);
    try {
      const payload = {
        ...achieveFormData,
        team_size: achieveFormData.team_size ? parseInt(achieveFormData.team_size, 10) : null,
        related_project_id: achieveFormData.related_project_id || null,
      };

      if (editingAchieveId) {
        const res = await updateAchievement(resumeId, editingAchieveId, payload);
        setAchievements((prev) =>
          prev.map((a) => (a.id === editingAchieveId ? res.data : a))
        );
      } else {
        const res = await addAchievement(resumeId, payload);
        setAchievements((prev) => [...prev, res.data]);
      }
      setAchieveModalOpen(false);
      setEditingAchieveId(null);
      setAchieveFormData(EMPTY_ACHIEVE_FORM);
    } catch (err) {
      setError(err.message || 'Failed to save achievement.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmAchieve = async (achieveId) => {
    try {
      const res = await confirmAchievement(resumeId, achieveId);
      setAchievements((prev) =>
        prev.map((a) => (a.id === achieveId ? res.data : a))
      );
    } catch (err) {
      setError(err.message || 'Failed to confirm achievement.');
    }
  };

  // --- DELETE MODAL HANDLER ---
  const handleExecuteDelete = async () => {
    if (!deleteTarget) return;
    setIsProcessing(true);
    try {
      if (deleteTarget.type === 'cert') {
        await deleteCertification(resumeId, deleteTarget.id);
        setCertifications((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      } else {
        await deleteAchievement(resumeId, deleteTarget.id);
        setAchievements((prev) => prev.filter((a) => a.id !== deleteTarget.id));
      }
      setDeleteTarget(null);
    } catch (err) {
      setError(err.message || 'Failed to delete record.');
    } finally {
      setIsProcessing(false);
    }
  };

  // --- METRICS CALCULATION ---
  const totalCerts = certifications.length;
  const completedCerts = certifications.filter((c) => c.completion_status === 'completed').length;
  const inProgressCerts = certifications.filter((c) => c.completion_status === 'in_progress').length;
  const expiredCerts = certifications.filter((c) => c.completion_status === 'expired').length;

  const totalAchieves = achievements.length;
  const totalAwards = achievements.filter((a) => a.achievement_type === 'award').length;
  const hackathonAwards = achievements.filter((a) => a.achievement_category === 'hackathon').length;
  const publications = achievements.filter((a) => a.achievement_category === 'publication').length;
  const pendingCount =
    certifications.filter((c) => c.review_status === 'pending' || c.review_status === 'needs_review').length +
    achievements.filter((a) => a.review_status === 'pending' || a.review_status === 'needs_review').length;

  // --- FILTERING ---
  const q = searchQuery.toLowerCase().trim();

  const filteredCerts = certifications.filter((c) => {
    if (activeTab === 'achievements' || activeTab === 'hackathons' || activeTab === 'publications') return false;
    if (activeTab === 'pending' && c.review_status !== 'pending' && c.review_status !== 'needs_review') return false;
    if (!q) return true;
    return (
      c.certification_name?.toLowerCase().includes(q) ||
      c.issuing_organization?.toLowerCase().includes(q) ||
      c.credential_id?.toLowerCase().includes(q)
    );
  });

  const filteredAchieves = achievements.filter((a) => {
    if (activeTab === 'certifications') return false;
    if (activeTab === 'hackathons' && a.achievement_category !== 'hackathon') return false;
    if (activeTab === 'publications' && a.achievement_category !== 'publication') return false;
    if (activeTab === 'pending' && a.review_status !== 'pending' && a.review_status !== 'needs_review') return false;
    if (!q) return true;
    return (
      a.achievement_title?.toLowerCase().includes(q) ||
      a.event_name?.toLowerCase().includes(q) ||
      a.organization?.toLowerCase().includes(q) ||
      a.rank_or_position?.toLowerCase().includes(q)
    );
  });

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header Bar */}
      <CardHeader className="bg-slate-50/70 border-b border-slate-100 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center shrink-0 border border-amber-500/20 shadow-xs">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base sm:text-lg font-bold text-slate-900">
                  Certifications & Achievements
                </CardTitle>
                <Badge variant="outline" className="text-[10px] font-bold border-amber-300 text-amber-700 bg-amber-50">
                  Phase 3 Feature #19
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                Verified credentials, hackathons, awards, competitions, and publications with canonical skill mapping
              </CardDescription>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleReprocessAll(false)}
              disabled={isProcessing || isLoading}
              className="text-xs h-9 border-slate-200 text-slate-700 hover:bg-slate-100"
              title="Re-extract accomplishments while preserving your edits"
            >
              <RotateCw className={cn('w-3.5 h-3.5 mr-1.5', isProcessing && 'animate-spin')} />
              Reprocess
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCertFormData(EMPTY_CERT_FORM);
                setEditingCertId(null);
                setCertModalOpen(true);
              }}
              className="text-xs h-9 border-slate-200 text-slate-700 hover:bg-slate-100"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5 text-primary" />
              Add Certification
            </Button>

            <Button
              variant="default"
              size="sm"
              onClick={() => {
                setAchieveFormData(EMPTY_ACHIEVE_FORM);
                setEditingAchieveId(null);
                setAchieveModalOpen(true);
              }}
              className="text-xs h-9 bg-primary text-white hover:bg-primary/90"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add Achievement
            </Button>
          </div>
        </div>

        {/* Analytics Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 mt-5 pt-5 border-t border-slate-200/60">
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Certifications</span>
            <span className="text-lg font-bold text-slate-800 font-mono">{totalCerts}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-emerald-600 block tracking-wider">Completed</span>
            <span className="text-lg font-bold text-emerald-700 font-mono">{completedCerts}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-amber-600 block tracking-wider">In Progress</span>
            <span className="text-lg font-bold text-amber-700 font-mono">{inProgressCerts}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Achievements</span>
            <span className="text-lg font-bold text-slate-800 font-mono">{totalAchieves}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-amber-600 block tracking-wider">Hackathons</span>
            <span className="text-lg font-bold text-amber-700 font-mono">{hackathonAwards}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-purple-600 block tracking-wider">Publications</span>
            <span className="text-lg font-bold text-purple-700 font-mono">{publications}</span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-rose-600 block tracking-wider">Pending Review</span>
            <span className="text-lg font-bold text-rose-700 font-mono">{pendingCount}</span>
          </div>
        </div>

        {/* Filter Tabs & Search Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors shrink-0',
                  activeTab === tab.key
                    ? 'bg-primary text-white shadow-xs'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search accomplishments..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-primary shadow-2xs"
            />
          </div>
        </div>
      </CardHeader>

      {/* Main Content Area */}
      <div className="p-6">
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="w-4 h-4 mr-2" />
            <p className="text-xs">{error}</p>
          </Alert>
        )}

        {isLoading ? (
          <div className="py-12 text-center space-y-3">
            <LoadingIndicator size="md" className="mx-auto text-primary" />
            <p className="text-xs text-slate-500 font-medium">Extracting and analyzing certifications & achievements...</p>
          </div>
        ) : filteredCerts.length === 0 && filteredAchieves.length === 0 ? (
          <div className="py-12 text-center space-y-2 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <Scroll className="w-8 h-8 mx-auto text-slate-400" />
            <h4 className="text-sm font-bold text-slate-700">No accomplishments found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No certifications or achievements match your current filter. You can add one manually using the buttons above.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Certifications Subsection */}
            {filteredCerts.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Scroll className="w-4 h-4 text-primary" />
                  <h3 className="text-xs uppercase font-bold text-slate-600 tracking-wider">
                    Certifications ({filteredCerts.length})
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredCerts.map((cert) => (
                    <div
                      key={cert.id}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:border-slate-300 transition-all shadow-2xs flex flex-col justify-between"
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="font-bold text-sm text-slate-900 block leading-tight">
                              {cert.certification_name}
                            </span>
                            {cert.issuing_organization && (
                              <span className="text-xs text-slate-500 font-medium block mt-0.5">
                                {cert.issuing_organization}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-[10px] font-semibold border',
                                CERT_CATEGORY_COLORS[cert.certification_category] || CERT_CATEGORY_COLORS.other
                              )}
                            >
                              {cert.certification_category?.replace('_', ' ')}
                            </Badge>

                            <Badge
                              variant="outline"
                              className={cn(
                                'text-[10px] font-bold border',
                                cert.completion_status === 'completed'
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                                  : cert.completion_status === 'in_progress'
                                  ? 'bg-amber-50 text-amber-700 border-amber-300'
                                  : 'bg-rose-50 text-rose-700 border-rose-300'
                              )}
                            >
                              {cert.completion_status === 'completed'
                                ? 'Completed'
                                : cert.completion_status === 'in_progress'
                                ? 'In Progress'
                                : 'Expired'}
                            </Badge>
                          </div>
                        </div>

                        {/* Dates & Credential Info */}
                        <div className="flex flex-wrap items-center gap-y-1 gap-x-3 text-xs text-slate-500">
                          {cert.issue_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-slate-400" />
                              Issued: {cert.issue_date}
                            </span>
                          )}
                          {cert.expiry_date && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-slate-400" />
                              Expires: {cert.expiry_date}
                            </span>
                          )}
                          {cert.credential_id && (
                            <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
                              ID: {cert.credential_id}
                            </span>
                          )}
                        </div>

                        {/* Linked Skills */}
                        {cert.related_skills && cert.related_skills.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1 pt-1">
                            {cert.related_skills.map((s, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-[10px] bg-slate-50 text-slate-600 border-slate-200"
                              >
                                {s.canonical_name || s.original_name}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Card Footer Actions */}
                      <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100">
                        <div>
                          {cert.credential_url ? (
                            <a
                              href={cert.credential_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary font-semibold flex items-center gap-1 hover:underline"
                            >
                              Verify Credential <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-[11px] text-slate-400">No verification link</span>
                          )}
                        </div>

                        <div className="flex items-center gap-1">
                          {cert.review_status !== 'confirmed' && (
                            <Button
                              variant="ghost"
                              size="xs"
                              onClick={() => handleConfirmCert(cert.id)}
                              className="text-xs text-emerald-700 hover:bg-emerald-50 h-7 px-2"
                              title="Confirm certification details"
                            >
                              <Check className="w-3.5 h-3.5 mr-1 text-emerald-600" /> Confirm
                            </Button>
                          )}

                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => {
                              setCertFormData({
                                certification_name: cert.certification_name,
                                normalized_name: cert.normalized_name,
                                issuing_organization: cert.issuing_organization || '',
                                certification_category: cert.certification_category || 'other',
                                issue_date: cert.issue_date || '',
                                expiry_date: cert.expiry_date || '',
                                credential_id: cert.credential_id || '',
                                credential_url: cert.credential_url || '',
                                completion_status: cert.completion_status || 'completed',
                              });
                              setEditingCertId(cert.id);
                              setCertModalOpen(true);
                            }}
                            className="text-xs text-slate-600 hover:text-slate-900 h-7 w-7 p-0"
                            title="Edit certification"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() =>
                              setDeleteTarget({
                                type: 'cert',
                                id: cert.id,
                                name: cert.certification_name,
                              })
                            }
                            className="text-xs text-rose-600 hover:text-rose-800 hover:bg-rose-50 h-7 w-7 p-0"
                            title="Delete certification"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Achievements Subsection */}
            {filteredAchieves.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-amber-600" />
                  <h3 className="text-xs uppercase font-bold text-slate-600 tracking-wider">
                    Achievements & Recognition ({filteredAchieves.length})
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredAchieves.map((achieve) => (
                    <div
                      key={achieve.id}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:border-slate-300 transition-all shadow-2xs flex flex-col justify-between"
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="font-bold text-sm text-slate-900 block leading-tight">
                              {achieve.achievement_title}
                            </span>
                            {(achieve.event_name || achieve.organization) && (
                              <span className="text-xs text-slate-500 font-medium block mt-0.5">
                                {[achieve.event_name, achieve.organization].filter(Boolean).join(' • ')}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            {achieve.rank_or_position && (
                              <Badge
                                variant="outline"
                                className="text-[10px] font-bold border bg-amber-50 text-amber-800 border-amber-300"
                              >
                                {achieve.rank_or_position}
                              </Badge>
                            )}

                            <Badge
                              variant="outline"
                              className={cn(
                                'text-[10px] font-semibold border',
                                ACHIEVE_TYPE_COLORS[achieve.achievement_type] || ACHIEVE_TYPE_COLORS.other
                              )}
                            >
                              {achieve.achievement_type?.toUpperCase()}
                            </Badge>
                          </div>
                        </div>

                        {/* Description */}
                        {achieve.description && (
                          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                            {achieve.description}
                          </p>
                        )}

                        {/* Meta info: Date, Team, Project */}
                        <div className="flex flex-wrap items-center gap-y-1 gap-x-3 text-xs text-slate-500">
                          {achieve.achievement_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-slate-400" />
                              {achieve.achievement_date}
                            </span>
                          )}
                          {achieve.team_size && (
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3 text-slate-400" />
                              Team of {achieve.team_size}
                            </span>
                          )}
                          {achieve.candidate_role && (
                            <span className="bg-slate-100 px-1.5 py-0.5 rounded text-[11px] text-slate-700">
                              Role: {achieve.candidate_role}
                            </span>
                          )}
                          {achieve.related_project_title && (
                            <span className="flex items-center gap-1 bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded text-[11px] font-semibold">
                              <FolderGit2 className="w-3 h-3" />
                              Project: {achieve.related_project_title}
                            </span>
                          )}
                        </div>

                        {/* Linked Skills */}
                        {achieve.related_skills && achieve.related_skills.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1 pt-1">
                            {achieve.related_skills.map((s, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-[10px] bg-slate-50 text-slate-600 border-slate-200"
                              >
                                {s.canonical_name || s.original_name}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Card Footer Actions */}
                      <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100">
                        <div>
                          {achieve.achievement_url ? (
                            <a
                              href={achieve.achievement_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary font-semibold flex items-center gap-1 hover:underline"
                            >
                              Supporting Link <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-[11px] text-slate-400">No external link</span>
                          )}
                        </div>

                        <div className="flex items-center gap-1">
                          {achieve.review_status !== 'confirmed' && (
                            <Button
                              variant="ghost"
                              size="xs"
                              onClick={() => handleConfirmAchieve(achieve.id)}
                              className="text-xs text-emerald-700 hover:bg-emerald-50 h-7 px-2"
                              title="Confirm achievement details"
                            >
                              <Check className="w-3.5 h-3.5 mr-1 text-emerald-600" /> Confirm
                            </Button>
                          )}

                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => {
                              setAchieveFormData({
                                achievement_title: achieve.achievement_title,
                                normalized_title: achieve.normalized_title,
                                achievement_category: achieve.achievement_category || 'other',
                                event_name: achieve.event_name || '',
                                organization: achieve.organization || '',
                                achievement_type: achieve.achievement_type || 'award',
                                rank_or_position: achieve.rank_or_position || '',
                                achievement_date: achieve.achievement_date || '',
                                description: achieve.description || '',
                                team_name: achieve.team_name || '',
                                team_size: achieve.team_size ? String(achieve.team_size) : '',
                                candidate_role: achieve.candidate_role || '',
                                related_project_id: achieve.related_project_id || '',
                                achievement_url: achieve.achievement_url || '',
                              });
                              setEditingAchieveId(achieve.id);
                              setAchieveModalOpen(true);
                            }}
                            className="text-xs text-slate-600 hover:text-slate-900 h-7 w-7 p-0"
                            title="Edit achievement"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() =>
                              setDeleteTarget({
                                type: 'achieve',
                                id: achieve.id,
                                name: achieve.achievement_title,
                              })
                            }
                            className="text-xs text-rose-600 hover:text-rose-800 hover:bg-rose-50 h-7 w-7 p-0"
                            title="Delete achievement"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* --- ADD / EDIT CERTIFICATION MODAL --- */}
      {certModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">
                {editingCertId ? 'Edit Certification' : 'Add Certification'}
              </h3>
              <button
                type="button"
                onClick={() => setCertModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCert} className="space-y-4 pt-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Certification Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AWS Certified Solutions Architect - Associate"
                  value={certFormData.certification_name}
                  onChange={(e) =>
                    setCertFormData({ ...certFormData, certification_name: e.target.value })
                  }
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Issuing Organization
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Amazon Web Services (AWS)"
                    value={certFormData.issuing_organization}
                    onChange={(e) =>
                      setCertFormData({ ...certFormData, issuing_organization: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Category
                  </label>
                  <select
                    value={certFormData.certification_category}
                    onChange={(e) =>
                      setCertFormData({ ...certFormData, certification_category: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-primary"
                  >
                    <option value="cloud">Cloud Certification</option>
                    <option value="ai_ml">AI/ML Certification</option>
                    <option value="data_science">Data Science</option>
                    <option value="security">Security</option>
                    <option value="programming">Programming</option>
                    <option value="project_management">Project Management</option>
                    <option value="technical">Technical</option>
                    <option value="professional">Professional</option>
                    <option value="course">Online Course</option>
                    <option value="training">Training</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Issue Date
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Oct 2023"
                    value={certFormData.issue_date}
                    onChange={(e) => setCertFormData({ ...certFormData, issue_date: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Expiry Date
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Oct 2026 (or leave empty)"
                    value={certFormData.expiry_date}
                    onChange={(e) => setCertFormData({ ...certFormData, expiry_date: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Credential ID
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. AWS-84920491"
                    value={certFormData.credential_id}
                    onChange={(e) => setCertFormData({ ...certFormData, credential_id: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Completion Status
                  </label>
                  <select
                    value={certFormData.completion_status}
                    onChange={(e) => setCertFormData({ ...certFormData, completion_status: e.target.value })}
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  >
                    <option value="completed">Completed</option>
                    <option value="in_progress">In Progress</option>
                    <option value="expired">Expired</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Verification URL
                </label>
                <input
                  type="url"
                  placeholder="https://www.credly.com/badges/..."
                  value={certFormData.credential_url}
                  onChange={(e) => setCertFormData({ ...certFormData, credential_url: e.target.value })}
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setCertModalOpen(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button type="submit" variant="default" size="sm" disabled={isProcessing} className="text-xs">
                  {isProcessing ? 'Saving...' : 'Save Certification'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- ADD / EDIT ACHIEVEMENT MODAL --- */}
      {achieveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">
                {editingAchieveId ? 'Edit Achievement' : 'Add Achievement'}
              </h3>
              <button
                type="button"
                onClick={() => setAchieveModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveAchieve} className="space-y-4 pt-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Achievement Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 1st Place Winner - HackMIT 2023"
                  value={achieveFormData.achievement_title}
                  onChange={(e) =>
                    setAchieveFormData({ ...achieveFormData, achievement_title: e.target.value })
                  }
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Event / Competition Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. HackMIT 2023"
                    value={achieveFormData.event_name}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, event_name: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Organizer / Institution
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. MIT"
                    value={achieveFormData.organization}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, organization: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Category
                  </label>
                  <select
                    value={achieveFormData.achievement_category}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, achievement_category: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  >
                    <option value="hackathon">Hackathon</option>
                    <option value="competition">Competition</option>
                    <option value="academic">Academic</option>
                    <option value="scholarship">Scholarship</option>
                    <option value="publication">Publication</option>
                    <option value="research">Research</option>
                    <option value="leadership">Leadership</option>
                    <option value="community">Community</option>
                    <option value="volunteer">Volunteer</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Type
                  </label>
                  <select
                    value={achieveFormData.achievement_type}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, achievement_type: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  >
                    <option value="award">Award</option>
                    <option value="ranking">Ranking</option>
                    <option value="participation">Participation</option>
                    <option value="publication">Publication</option>
                    <option value="scholarship">Scholarship</option>
                    <option value="recognition">Recognition</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Rank / Position
                  </label>
                  <input
                    type="text"
                    placeholder="1st Place, Finalist..."
                    value={achieveFormData.rank_or_position}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, rank_or_position: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Date
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Sep 2023"
                    value={achieveFormData.achievement_date}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, achievement_date: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Team Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    placeholder="e.g. 4"
                    value={achieveFormData.team_size}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, team_size: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Candidate Role
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Lead Developer"
                    value={achieveFormData.candidate_role}
                    onChange={(e) =>
                      setAchieveFormData({ ...achieveFormData, candidate_role: e.target.value })
                    }
                    className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              {/* Link to Feature #18 Candidate Project */}
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Linked Candidate Project (Feature #18)
                </label>
                <select
                  value={achieveFormData.related_project_id}
                  onChange={(e) =>
                    setAchieveFormData({ ...achieveFormData, related_project_id: e.target.value })
                  }
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                >
                  <option value="">-- No linked project --</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_title} ({p.project_category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Description & Impact
                </label>
                <textarea
                  rows="2"
                  placeholder="Detail your contribution, awards, or prize won..."
                  value={achieveFormData.description}
                  onChange={(e) =>
                    setAchieveFormData({ ...achieveFormData, description: e.target.value })
                  }
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Supporting URL / DOI Link
                </label>
                <input
                  type="url"
                  placeholder="https://..."
                  value={achieveFormData.achievement_url}
                  onChange={(e) =>
                    setAchieveFormData({ ...achieveFormData, achievement_url: e.target.value })
                  }
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-lg"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setAchieveModalOpen(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button type="submit" variant="default" size="sm" disabled={isProcessing} className="text-xs">
                  {isProcessing ? 'Saving...' : 'Save Achievement'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- DELETE CONFIRMATION MODAL --- */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="w-5 h-5" />
            </div>
            <div className="text-center space-y-1">
              <h4 className="text-sm font-bold text-slate-900">
                Delete {deleteTarget.type === 'cert' ? 'Certification' : 'Achievement'}?
              </h4>
              <p className="text-xs text-slate-500">
                Are you sure you want to permanently delete{' '}
                <span className="font-semibold text-slate-700">"{deleteTarget.name}"</span>? This action cannot be undone.
              </p>
            </div>
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteTarget(null)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleExecuteDelete}
                disabled={isProcessing}
                className="text-xs"
              >
                {isProcessing ? 'Deleting...' : 'Confirm Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
