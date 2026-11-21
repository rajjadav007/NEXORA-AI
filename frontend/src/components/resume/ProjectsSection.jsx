import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  ExternalLink,
  GitBranch,
  Globe,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Edit2,
  Trash2,
  Check,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Users,
  Calendar,
  Layers,
  Sparkles,
  Trophy,
  Target,
  Cpu,
  Search,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  getProjects,
  extractProjects,
  reprocessProjects,
  addProject,
  updateProject,
  deleteProject,
  confirmProject,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

const CATEGORIES = [
  { key: 'all', label: 'All Projects' },
  { key: 'academic', label: 'Academic' },
  { key: 'personal', label: 'Personal' },
  { key: 'hackathon', label: 'Hackathon' },
  { key: 'research', label: 'Research' },
  { key: 'open_source', label: 'Open Source' },
  { key: 'professional', label: 'Professional' },
  { key: 'freelance', label: 'Freelance' },
  { key: 'other', label: 'Other' },
];

const CATEGORY_COLORS = {
  academic: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  personal: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  hackathon: 'bg-amber-50 text-amber-700 border-amber-200',
  research: 'bg-purple-50 text-purple-700 border-purple-200',
  open_source: 'bg-sky-50 text-sky-700 border-sky-200',
  professional: 'bg-blue-50 text-blue-700 border-blue-200',
  freelance: 'bg-teal-50 text-teal-700 border-teal-200',
  other: 'bg-slate-100 text-slate-700 border-slate-200',
};

const EMPTY_FORM = {
  project_title: '',
  project_category: 'personal',
  short_description: '',
  detailed_description: '',
  problem_statement: '',
  proposed_solution: '',
  domain: '',
  project_role: '',
  team_type: 'individual',
  team_size: null,
  start_date: '',
  end_date: '',
  is_ongoing: false,
  technologies: '',
  responsibilities: '',
  measurable_outcomes: '',
  github_url: '',
  demo_url: '',
};

export function ProjectsSection({ resumeId, className }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedDetails, setExpandedDetails] = useState({});

  // Modal State (Create or Edit)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProjectId, setEditingProjectId] = useState(null);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadProjects = useCallback(async () => {
    if (!resumeId) {
      setProjects([]);
      setSummary(null);
      setError(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      let res = await getProjects(resumeId);
      if (!res.data || res.data.length === 0) {
        res = await extractProjects(resumeId);
      }
      setProjects(res.data || []);
      setSummary(res.summary || null);
    } catch (err) {
      setError(err.message || 'Failed to load projects.');
      setProjects([]);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleReprocess = async (forceOverwrite = false) => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await reprocessProjects(resumeId, forceOverwrite);
      setProjects(res.data || []);
      setSummary(res.summary || null);
      setSuccessMessage('Projects reprocessed successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to reprocess projects.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirm = async (projectId) => {
    try {
      const res = await confirmProject(resumeId, projectId);
      if (res.data) {
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? res.data : p))
        );
        setSuccessMessage('Project review confirmed.');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      setError(err.message || 'Failed to confirm project.');
    }
  };

  const handleDelete = async (projectId, title) => {
    if (!window.confirm(`Delete project "${title}"?`)) return;
    try {
      await deleteProject(resumeId, projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
      setSuccessMessage(`Project "${title}" deleted.`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to delete project.');
    }
  };

  const toggleExpand = (projectId) => {
    setExpandedDetails((prev) => ({
      ...prev,
      [projectId]: !prev[projectId],
    }));
  };

  const openCreateModal = () => {
    setEditingProjectId(null);
    setFormData(EMPTY_FORM);
    setIsModalOpen(true);
  };

  const openEditModal = (proj) => {
    setEditingProjectId(proj.id);
    const gh = proj.project_links?.find((l) => l.link_type === 'github')?.url || '';
    const demo = proj.project_links?.find((l) => l.link_type === 'demo' || l.link_type === 'website')?.url || '';

    setFormData({
      project_title: proj.project_title || '',
      project_category: proj.project_category || 'personal',
      short_description: proj.short_description || '',
      detailed_description: proj.detailed_description || '',
      problem_statement: proj.problem_statement || '',
      proposed_solution: proj.proposed_solution || '',
      domain: proj.domain || '',
      project_role: proj.project_role || '',
      team_type: proj.team_type || 'individual',
      team_size: proj.team_size || null,
      start_date: proj.start_date || '',
      end_date: proj.end_date || '',
      is_ongoing: Boolean(proj.is_ongoing),
      technologies: (proj.technologies || []).join(', '),
      responsibilities: (proj.responsibilities || []).join('\n'),
      measurable_outcomes: (proj.measurable_outcomes || []).join('\n'),
      github_url: gh,
      demo_url: demo,
    });
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.project_title.trim()) {
      setError('Project title is required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const projectLinks = [];
    if (formData.github_url.trim()) {
      projectLinks.push({ url: formData.github_url.trim(), link_type: 'github', label: 'GitHub Repository' });
    }
    if (formData.demo_url.trim()) {
      projectLinks.push({ url: formData.demo_url.trim(), link_type: 'demo', label: 'Live Demo' });
    }

    const payload = {
      project_title: formData.project_title.trim(),
      project_category: formData.project_category,
      short_description: formData.short_description.trim() || null,
      detailed_description: formData.detailed_description.trim() || null,
      problem_statement: formData.problem_statement.trim() || null,
      proposed_solution: formData.proposed_solution.trim() || null,
      domain: formData.domain.trim() || null,
      project_role: formData.project_role.trim() || null,
      team_type: formData.team_type,
      team_size: formData.team_size ? parseInt(formData.team_size, 10) : null,
      start_date: formData.start_date.trim() || null,
      end_date: formData.end_date.trim() || null,
      is_ongoing: formData.is_ongoing,
      technologies: formData.technologies
        ? formData.technologies.split(',').map((t) => t.trim()).filter(Boolean)
        : [],
      responsibilities: formData.responsibilities
        ? formData.responsibilities.split('\n').map((r) => r.trim()).filter(Boolean)
        : [],
      measurable_outcomes: formData.measurable_outcomes
        ? formData.measurable_outcomes.split('\n').map((m) => m.trim()).filter(Boolean)
        : [],
      project_links: projectLinks,
    };

    try {
      if (editingProjectId) {
        const res = await updateProject(resumeId, editingProjectId, payload);
        if (res.data) {
          setProjects((prev) =>
            prev.map((p) => (p.id === editingProjectId ? res.data : p))
          );
          setSuccessMessage('Project updated successfully.');
        }
      } else {
        const res = await addProject(resumeId, payload);
        if (res.data) {
          setProjects((prev) => [res.data, ...prev]);
          setSuccessMessage('Project created successfully.');
        }
      }
      setIsModalOpen(false);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save project.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter projects by category and search
  const filteredProjects = projects.filter((p) => {
    const matchCat =
      selectedCategory === 'all' ||
      p.project_category?.toLowerCase() === selectedCategory.toLowerCase();
    if (!matchCat) return false;

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const titleMatch = (p.project_title || '').toLowerCase().includes(q);
    const domainMatch = (p.domain || '').toLowerCase().includes(q);
    const techMatch = (p.technologies || []).some((t) => t.toLowerCase().includes(q));
    const roleMatch = (p.project_role || '').toLowerCase().includes(q);
    return titleMatch || domainMatch || techMatch || roleMatch;
  });

  const pendingCount = projects.filter(
    (p) => p.review_status === 'pending' || p.review_status === 'needs_review'
  ).length;

  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-3 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="md" className="text-blue-600 mx-auto" />
        <h4 className="text-sm font-bold text-slate-800">Analyzing Project Intelligence...</h4>
        <p className="text-xs text-slate-500">
          Extracting project titles, narratives, technologies, and linking canonical skills.
        </p>
      </Card>
    );
  }

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-slate-900">
                  Project Intelligence
                </CardTitle>
                <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-800 text-[10px] font-bold">
                  Phase 3 • Feature 18
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                Structured candidate projects, architectures, roles, and linked skills
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleReprocess(false)}
              disabled={isProcessing}
              className="text-xs h-8 gap-1.5"
            >
              <RotateCw className={cn('w-3.5 h-3.5', isProcessing && 'animate-spin')} />
              <span>Reprocess</span>
            </Button>
            <Button
              size="sm"
              onClick={openCreateModal}
              className="text-xs h-8 gap-1.5 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Project</span>
            </Button>
          </div>
        </div>

        {/* Aggregate Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-4 pt-3 border-t border-slate-100">
          <div className="bg-white p-2.5 rounded-lg border border-slate-200/80">
            <span className="text-[10px] font-semibold text-slate-400 block uppercase">Total Projects</span>
            <span className="text-base font-bold text-slate-800 font-mono">
              {summary?.total_projects ?? projects.length}
            </span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200/80">
            <span className="text-[10px] font-semibold text-slate-400 block uppercase">Domains</span>
            <span className="text-base font-bold text-indigo-700 font-mono">
              {summary?.domains_count ?? new Set(projects.map((p) => p.domain).filter(Boolean)).size}
            </span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200/80">
            <span className="text-[10px] font-semibold text-slate-400 block uppercase">Unique Techs</span>
            <span className="text-base font-bold text-teal-700 font-mono">
              {summary?.unique_technologies_count ??
                new Set(projects.flatMap((p) => p.technologies || [])).size}
            </span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200/80">
            <span className="text-[10px] font-semibold text-slate-400 block uppercase">Repositories / Demos</span>
            <span className="text-base font-bold text-sky-700 font-mono">
              {(summary?.github_repos_count || 0) + (summary?.live_demos_count || 0)}
            </span>
          </div>
          <div className="bg-white p-2.5 rounded-lg border border-slate-200/80 col-span-2 sm:col-span-1">
            <span className="text-[10px] font-semibold text-slate-400 block uppercase">Pending Review</span>
            <span className={cn('text-base font-bold font-mono', pendingCount > 0 ? 'text-amber-600' : 'text-slate-600')}>
              {summary?.pending_review_count ?? pendingCount}
            </span>
          </div>
        </div>

        {/* Category Tabs & Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 mt-3 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.key}
                onClick={() => setSelectedCategory(cat.key)}
                className={cn(
                  'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors whitespace-nowrap',
                  selectedCategory === cat.key
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-200/60 bg-slate-100'
                )}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-56 shrink-0">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by title or skill..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-2.5 py-1 text-xs bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-6 space-y-4">
        {/* Alerts */}
        {error && (
          <Alert variant="destructive" className="py-2.5">
            <AlertTriangle className="w-4 h-4 mr-2 inline" />
            <span className="text-xs font-medium">{error}</span>
          </Alert>
        )}
        {successMessage && (
          <Alert variant="success" className="py-2.5 bg-emerald-50 text-emerald-800 border-emerald-200">
            <CheckCircle2 className="w-4 h-4 mr-2 inline text-emerald-600" />
            <span className="text-xs font-medium">{successMessage}</span>
          </Alert>
        )}

        {/* Empty State / Error State */}
        {!resumeId ? (
          <div className="p-8 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <FolderGit2 className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No Resume Selected</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Please select or upload a resume to view project intelligence.
            </p>
            <Button size="sm" onClick={() => navigate('/resume')} className="mt-4 text-xs">
              Go to Resume Upload
            </Button>
          </div>
        ) : error ? (
          <div className="p-8 text-center border border-dashed border-red-200 rounded-xl bg-red-50/60">
            <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-red-900">Project Intelligence Unavailable</h4>
            <p className="text-xs text-red-700 max-w-md mx-auto mt-1 mb-4 leading-relaxed">{error}</p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadProjects()}
                className="text-xs gap-1 bg-white border-red-200 text-red-800 hover:bg-red-50"
              >
                <RotateCw className="w-3.5 h-3.5" /> Try Again
              </Button>
              <Button size="sm" onClick={() => navigate('/resume')} className="text-xs">
                Return to Resume Selection or Upload
              </Button>
            </div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-200 rounded-lg">
            <FolderGit2 className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No projects found</p>
            <p className="text-xs text-slate-500 mt-1">
              {searchQuery
                ? 'Try a different search query or category filter.'
                : 'Click "Add Project" to record an academic, personal, or work project.'}
            </p>
          </div>
        ) : (
          /* Project Cards */
          <div className="space-y-4">
            {filteredProjects.map((proj) => {
              const isExpanded = Boolean(expandedDetails[proj.id]);
              const categoryColor =
                CATEGORY_COLORS[proj.project_category?.toLowerCase()] || CATEGORY_COLORS.other;
              const isPending =
                proj.review_status === 'pending' || proj.review_status === 'needs_review';

              const ghLink = proj.project_links?.find((l) => l.link_type === 'github');
              const demoLink = proj.project_links?.find(
                (l) => l.link_type === 'demo' || l.link_type === 'website'
              );

              return (
                <div
                  key={proj.id}
                  className={cn(
                    'bg-white border rounded-xl p-4 sm:p-5 transition-all shadow-sm',
                    isPending ? 'border-amber-200/90 bg-amber-50/20' : 'border-slate-200'
                  )}
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">
                          {proj.project_title}
                        </h3>
                        <span
                          className={cn(
                            'text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider',
                            categoryColor
                          )}
                        >
                          {proj.project_category?.replace('_', ' ') || 'Project'}
                        </span>
                        {proj.domain && (
                          <Badge variant="outline" className="text-[10px] border-slate-200 text-slate-600 bg-slate-50">
                            {proj.domain}
                          </Badge>
                        )}
                        {proj.is_ongoing && (
                          <Badge className="text-[10px] bg-emerald-100 text-emerald-800 border-emerald-200 font-semibold">
                            Ongoing
                          </Badge>
                        )}
                      </div>

                      {/* Sub-meta: Role, Timeline, Team */}
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 pt-0.5">
                        {proj.project_role && (
                          <span className="font-semibold text-slate-700">
                            Role: {proj.project_role}
                          </span>
                        )}
                        {(proj.start_date || proj.end_date) && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            {proj.start_date || 'Start'} —{' '}
                            {proj.is_ongoing ? 'Present' : proj.end_date || 'End'}
                          </span>
                        )}
                        {proj.team_type && (
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3 text-slate-400" />
                            {proj.team_type === 'team'
                              ? `Team (${proj.team_size || 'Multiple'} members)`
                              : 'Solo Project'}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions Menu */}
                    <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-start">
                      {isPending && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleConfirm(proj.id)}
                          className="text-xs h-7 gap-1 border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Confirm</span>
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditModal(proj)}
                        className="text-xs h-7 w-7 p-0 text-slate-500 hover:text-slate-800"
                        title="Edit project"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(proj.id, proj.project_title)}
                        className="text-xs h-7 w-7 p-0 text-slate-400 hover:text-red-600"
                        title="Delete project"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>

                  {/* Short Description */}
                  {proj.short_description && (
                    <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                      {proj.short_description}
                    </p>
                  )}

                  {/* Measurable Outcomes Callout */}
                  {proj.measurable_outcomes && proj.measurable_outcomes.length > 0 && (
                    <div className="mt-3 p-2.5 bg-emerald-50/60 border border-emerald-200/80 rounded-lg">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-800 mb-1">
                        <Trophy className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Key Measurable Outcomes</span>
                      </div>
                      <ul className="list-disc list-inside space-y-0.5 text-xs text-emerald-900">
                        {proj.measurable_outcomes.map((metric, i) => (
                          <li key={i}>{metric}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Technologies & Linked Skills Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3 border-t border-slate-100">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
                      Tech Stack:
                    </span>
                    {(proj.technologies || []).map((tech, idx) => {
                      // Check if mapped to Feature #17 canonical skill
                      const linkedSkill = (proj.skills || []).find(
                        (s) => s.skill_name?.toLowerCase() === tech.toLowerCase()
                      );
                      return (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200"
                          title={
                            linkedSkill?.canonical_name
                              ? `Mapped to Canonical Skill: ${linkedSkill.canonical_name} (${linkedSkill.category})`
                              : tech
                          }
                        >
                          <Cpu className="w-2.5 h-2.5 text-slate-400" />
                          <span>{tech}</span>
                          {linkedSkill?.canonical_name && (
                            <span className="w-1.5 h-1.5 rounded-full bg-teal-500" title="Canonical Skill Verified" />
                          )}
                        </span>
                      );
                    })}
                  </div>

                  {/* Links & Expand Toggle */}
                  <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2 text-xs">
                    <div className="flex items-center gap-2">
                      {ghLink && (
                        <a
                          href={ghLink.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-700 hover:text-black bg-slate-100 hover:bg-slate-200 px-2.5 py-1 rounded-md transition-colors"
                        >
                          <GitBranch className="w-3.5 h-3.5" />
                          <span>Repository</span>
                          <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
                        </a>
                      )}
                      {demoLink && (
                        <a
                          href={demoLink.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-md transition-colors"
                        >
                          <Globe className="w-3.5 h-3.5" />
                          <span>Live Demo</span>
                          <ExternalLink className="w-2.5 h-2.5 text-blue-400" />
                        </a>
                      )}
                    </div>

                    <button
                      onClick={() => toggleExpand(proj.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                    >
                      <span>{isExpanded ? 'Hide Architecture & Evidence' : 'View Architecture & Evidence'}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  {/* Expandable Deep Details Drawer */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-100 space-y-3 bg-slate-50/70 p-3.5 rounded-lg text-xs">
                      {proj.problem_statement && (
                        <div>
                          <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider mb-0.5">
                            Problem Addressed:
                          </span>
                          <p className="text-slate-600 leading-relaxed">{proj.problem_statement}</p>
                        </div>
                      )}

                      {proj.proposed_solution && (
                        <div>
                          <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider mb-0.5">
                            Proposed Architecture & Solution:
                          </span>
                          <p className="text-slate-600 leading-relaxed">{proj.proposed_solution}</p>
                        </div>
                      )}

                      {proj.responsibilities && proj.responsibilities.length > 0 && (
                        <div>
                          <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider mb-0.5">
                            Individual Contributions:
                          </span>
                          <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                            {proj.responsibilities.map((resp, idx) => (
                              <li key={idx}>{resp}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {proj.source_evidence && (
                        <div className="pt-2 border-t border-slate-200">
                          <span className="font-bold text-slate-500 block text-[10px] uppercase tracking-wider mb-0.5">
                            Source Resume Evidence:
                          </span>
                          <p className="font-mono text-[11px] text-slate-500 bg-white p-2 rounded border border-slate-200 whitespace-pre-wrap">
                            {proj.source_evidence}
                          </p>
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

      {/* Create / Edit Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-y-auto border border-slate-200">
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50/50">
              <h3 className="font-bold text-slate-900 text-sm">
                {editingProjectId ? 'Edit Project' : 'Add New Project'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="p-4 sm:p-5 space-y-3.5 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Project Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.project_title}
                  onChange={(e) => setFormData({ ...formData, project_title: e.target.value })}
                  placeholder="e.g. Distributed Task Queue"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Project Category
                  </label>
                  <select
                    value={formData.project_category}
                    onChange={(e) => setFormData({ ...formData, project_category: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  >
                    <option value="personal">Personal Project</option>
                    <option value="academic">Academic Project</option>
                    <option value="hackathon">Hackathon Project</option>
                    <option value="research">Research Project</option>
                    <option value="open_source">Open Source</option>
                    <option value="professional">Professional / Work</option>
                    <option value="freelance">Freelance</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Domain / Field
                  </label>
                  <input
                    type="text"
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    placeholder="e.g. Cloud Infrastructure, FinTech"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Candidate Role
                  </label>
                  <input
                    type="text"
                    value={formData.project_role}
                    onChange={(e) => setFormData({ ...formData, project_role: e.target.value })}
                    placeholder="e.g. Lead Developer"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Team Type
                  </label>
                  <select
                    value={formData.team_type}
                    onChange={(e) => setFormData({ ...formData, team_type: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  >
                    <option value="individual">Solo / Individual</option>
                    <option value="team">Team Collaboration</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Team Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.team_size || ''}
                    onChange={(e) => setFormData({ ...formData, team_size: e.target.value })}
                    placeholder="e.g. 4"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Start Date
                  </label>
                  <input
                    type="text"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    placeholder="e.g. Jan 2024"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    End Date
                  </label>
                  <input
                    type="text"
                    disabled={formData.is_ongoing}
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    placeholder={formData.is_ongoing ? 'Present' : 'e.g. May 2024'}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs disabled:bg-slate-100"
                  />
                </div>

                <div className="pb-1.5">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_ongoing}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          is_ongoing: e.target.checked,
                          end_date: e.target.checked ? '' : formData.end_date,
                        })
                      }
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="font-semibold text-slate-700 text-xs">Currently Ongoing</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Technologies (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.technologies}
                  onChange={(e) => setFormData({ ...formData, technologies: e.target.value })}
                  placeholder="e.g. Python, FastAPI, Docker, Redis, PostgreSQL"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Short Summary
                </label>
                <textarea
                  rows={2}
                  value={formData.short_description}
                  onChange={(e) => setFormData({ ...formData, short_description: e.target.value })}
                  placeholder="Brief 1-2 sentence project overview..."
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Problem Statement
                  </label>
                  <textarea
                    rows={2}
                    value={formData.problem_statement}
                    onChange={(e) => setFormData({ ...formData, problem_statement: e.target.value })}
                    placeholder="What challenge does this address?"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Proposed Solution
                  </label>
                  <textarea
                    rows={2}
                    value={formData.proposed_solution}
                    onChange={(e) => setFormData({ ...formData, proposed_solution: e.target.value })}
                    placeholder="How was the problem solved?"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Candidate Contributions (one per line)
                </label>
                <textarea
                  rows={2}
                  value={formData.responsibilities}
                  onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
                  placeholder="Built REST API endpoints&#10;Configured CI/CD deployment pipelines"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Measurable Outcomes (one per line)
                </label>
                <textarea
                  rows={2}
                  value={formData.measurable_outcomes}
                  onChange={(e) => setFormData({ ...formData, measurable_outcomes: e.target.value })}
                  placeholder="Reduced latency by 45%&#10;Handled 10,000+ requests/second"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    GitHub URL
                  </label>
                  <input
                    type="url"
                    value={formData.github_url}
                    onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                    placeholder="https://github.com/user/project"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    Live Demo / Site URL
                  </label>
                  <input
                    type="url"
                    value={formData.demo_url}
                    onChange={(e) => setFormData({ ...formData, demo_url: e.target.value })}
                    placeholder="https://myproject.demo.app"
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting ? 'Saving...' : editingProjectId ? 'Save Changes' : 'Create Project'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Card>
  );
}
