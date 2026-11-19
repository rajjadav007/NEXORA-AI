import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Globe,
  Link as LinkIcon,
  Edit2,
  RefreshCw,
  Check,
  AlertCircle,
  ExternalLink,
  Save,
  X,
  ShieldCheck,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import {
  extractPersonalInfo,
  updatePersonalInfo,
  reprocessPersonalInfo,
} from '../../services/resumeService';
import { cn } from '../../utils/cn';

function LinkedInIcon(props) {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" {...props}>
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.64a1.64 1.64 0 1 0 0 3.28 1.64 1.64 0 0 0 0-3.28Z" />
    </svg>
  );
}

function GitHubIcon(props) {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" {...props}>
      <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2Z" />
    </svg>
  );
}

/**
 * Format confidence percentage label
 */
function formatConfidence(score) {
  if (score === null || score === undefined) return null;
  const pct = Math.round(score * 100);
  return `${pct}%`;
}

/**
 * PersonalInfoCard Component
 * Phase 3 | Feature 13: Personal Information Extraction
 */
export function PersonalInfoCard({ resumeId, className }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // Edit form state
  const [editForm, setEditForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    country_code: '',
    city: '',
    state: '',
    country: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
  });

  const loadData = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      // First attempt extract (auto-returns cached/existing if already saved)
      const res = await extractPersonalInfo(resumeId);
      if (res && res.data) {
        setData(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load personal information.');
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const startEditing = () => {
    setEditForm({
      full_name: data?.full_name || '',
      email: data?.email || '',
      phone: data?.phone || '',
      country_code: data?.country_code || '',
      city: data?.location?.city || '',
      state: data?.location?.state || '',
      country: data?.location?.country || '',
      linkedin_url: data?.linkedin_url || '',
      github_url: data?.github_url || '',
      portfolio_url: data?.portfolio_url || '',
    });
    setIsEditing(true);
    setSuccessMessage(null);
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);
    setError(null);

    const payload = {
      full_name: editForm.full_name || null,
      email: editForm.email || null,
      phone: editForm.phone || null,
      country_code: editForm.country_code || null,
      location: (editForm.city || editForm.state || editForm.country) ? {
        city: editForm.city || null,
        state: editForm.state || null,
        country: editForm.country || null,
      } : null,
      linkedin_url: editForm.linkedin_url || null,
      github_url: editForm.github_url || null,
      portfolio_url: editForm.portfolio_url || null,
    };

    try {
      const res = await updatePersonalInfo(resumeId, payload);
      setData(res.data);
      setIsEditing(false);
      setSuccessMessage('Personal information updated successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to save changes.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReprocess = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await reprocessPersonalInfo(resumeId);
      setData(res.data);
      setSuccessMessage('Personal information reprocessed successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to reprocess personal information.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <Card className={cn('p-6 text-center space-y-3 border-slate-200 bg-white/60 shadow-sm', className)}>
        <LoadingIndicator size="md" className="text-teal-600 mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Extracting candidate personal information...</p>
      </Card>
    );
  }

  if (error && !data) {
    return (
      <Card className={cn('p-6 border-red-200 bg-red-50/30 text-center space-y-3 shadow-sm', className)}>
        <div className="w-10 h-10 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-red-950">Extraction Error</h4>
          <p className="text-xs text-red-800">{error}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          className="text-xs border-red-300 text-red-700 bg-white hover:bg-red-50 mx-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry Extraction
        </Button>
      </Card>
    );
  }

  const locationStr = [
    data?.location?.city,
    data?.location?.state,
    data?.location?.country,
  ].filter(Boolean).join(', ');

  const confidence = data?.confidence || {};

  return (
    <Card className={cn('border-slate-200 shadow-sm bg-white overflow-hidden', className)}>
      <CardHeader className="border-b border-slate-100 bg-slate-50/60 pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
              <User className="w-4 h-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                Personal Information
                {data?.is_manually_edited && (
                  <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-700 border-amber-200">
                    Manually Edited
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Verified candidate contact details, identity, and professional profiles
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {!isEditing ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startEditing}
                  disabled={isProcessing}
                  className="text-xs h-8 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:text-slate-900"
                >
                  <Edit2 className="w-3.5 h-3.5" /> Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReprocess}
                  disabled={isProcessing}
                  className="text-xs h-8 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:text-slate-900"
                  title="Re-extract personal information from resume text"
                >
                  <RefreshCw className={cn('w-3.5 h-3.5', isProcessing && 'animate-spin')} />
                  <span>Reprocess</span>
                </Button>
              </>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(false)}
                className="text-xs h-8 text-slate-500 hover:text-slate-700"
              >
                <X className="w-3.5 h-3.5 mr-1" /> Cancel
              </Button>
            )}
          </div>
        </div>

        {successMessage && (
          <Alert variant="default" className="mt-3 border-teal-200 bg-teal-50 text-teal-800 text-xs py-2">
            <Check className="w-4 h-4 text-teal-600 inline mr-1.5" />
            {successMessage}
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className="mt-3 text-xs py-2">
            <AlertCircle className="w-4 h-4 inline mr-1.5" />
            {error}
          </Alert>
        )}
      </CardHeader>

      <div className="p-5">
        {isEditing ? (
          /* Inline Edit Form */
          <form onSubmit={handleSaveEdit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  placeholder="Candidate Full Name"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  placeholder="candidate@example.com"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Phone Number</label>
                <input
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  placeholder="+91 9876543210"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Country Code</label>
                <input
                  type="text"
                  value={editForm.country_code}
                  onChange={(e) => setEditForm({ ...editForm, country_code: e.target.value })}
                  placeholder="+91"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                <input
                  type="text"
                  value={editForm.city}
                  onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                  placeholder="Bengaluru"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                <input
                  type="text"
                  value={editForm.state}
                  onChange={(e) => setEditForm({ ...editForm, state: e.target.value })}
                  placeholder="Karnataka"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Country</label>
                <input
                  type="text"
                  value={editForm.country}
                  onChange={(e) => setEditForm({ ...editForm, country: e.target.value })}
                  placeholder="India"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">LinkedIn URL</label>
                <input
                  type="url"
                  value={editForm.linkedin_url}
                  onChange={(e) => setEditForm({ ...editForm, linkedin_url: e.target.value })}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">GitHub URL</label>
                <input
                  type="url"
                  value={editForm.github_url}
                  onChange={(e) => setEditForm({ ...editForm, github_url: e.target.value })}
                  placeholder="https://github.com/username"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Portfolio URL</label>
                <input
                  type="url"
                  value={editForm.portfolio_url}
                  onChange={(e) => setEditForm({ ...editForm, portfolio_url: e.target.value })}
                  placeholder="https://myportfolio.dev"
                  className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(false)}
                disabled={isProcessing}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isProcessing}
                className="text-xs bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{isProcessing ? 'Saving...' : 'Save Corrections'}</span>
              </Button>
            </div>
          </form>
        ) : (
          /* View Mode */
          <div className="space-y-4">
            {/* Candidate Identity Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg font-bold text-slate-900">
                    {data?.full_name || (
                      <span className="text-slate-400 italic font-normal">Candidate Name Not Detected</span>
                    )}
                  </h3>
                  {data?.full_name && confidence.full_name && (
                    <Badge variant="outline" className="text-[10px] text-teal-700 bg-teal-50 border-teal-200">
                      {formatConfidence(confidence.full_name)} confidence
                    </Badge>
                  )}
                </div>
                {locationStr ? (
                  <p className="text-xs text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{locationStr}</span>
                    {confidence.location && (
                      <span className="text-[10px] text-slate-400">({formatConfidence(confidence.location)})</span>
                    )}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400 italic flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-300" />
                    <span>Location not provided</span>
                  </p>
                )}
              </div>
            </div>

            {/* Contact Details Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {/* Email */}
              <div className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                  <span>Email</span>
                  {data?.email && (
                    <span className="text-teal-600 font-normal">
                      {formatConfidence(confidence.email || 1.0)}
                    </span>
                  )}
                </span>
                {data?.email ? (
                  <a
                    href={`mailto:${data.email}`}
                    className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1.5 truncate"
                    title={data.email}
                  >
                    <Mail className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{data.email}</span>
                  </a>
                ) : (
                  <span className="text-xs text-slate-400 italic">Not provided</span>
                )}
              </div>

              {/* Phone */}
              <div className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                  <span>Phone</span>
                  {data?.phone && (
                    <span className="text-teal-600 font-normal">
                      {formatConfidence(confidence.phone || 0.95)}
                    </span>
                  )}
                </span>
                {data?.phone ? (
                  <a
                    href={`tel:${data.phone}`}
                    className="text-xs font-semibold text-slate-800 hover:text-teal-700 flex items-center gap-1.5 truncate"
                  >
                    <Phone className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                    <span>{data.phone}</span>
                    {data.country_code && (
                      <span className="text-[10px] px-1 bg-slate-200 text-slate-600 rounded">
                        {data.country_code}
                      </span>
                    )}
                  </a>
                ) : (
                  <span className="text-xs text-slate-400 italic">Not provided</span>
                )}
              </div>

              {/* Location */}
              <div className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                  <span>Location</span>
                  {locationStr && (
                    <span className="text-teal-600 font-normal">
                      {formatConfidence(confidence.location || 0.85)}
                    </span>
                  )}
                </span>
                <p className="text-xs font-medium text-slate-800 flex items-center gap-1.5 truncate">
                  <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                  <span className="truncate">{locationStr || <span className="text-slate-400 italic font-normal">Not provided</span>}</span>
                </p>
              </div>
            </div>

            {/* Professional Links */}
            <div className="pt-2 space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Professional Links
              </span>
              <div className="flex flex-wrap gap-2">
                {/* LinkedIn */}
                {data?.linkedin_url ? (
                  <a
                    href={data.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-200 bg-blue-50/60 text-blue-800 text-xs font-medium hover:bg-blue-100 transition-colors"
                  >
                    <LinkedInIcon className="w-3.5 h-3.5 text-blue-600" />
                    <span>LinkedIn</span>
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </a>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 text-slate-400 text-xs italic">
                    <LinkedInIcon className="w-3.5 h-3.5" /> No LinkedIn
                  </span>
                )}

                {/* GitHub */}
                {data?.github_url ? (
                  <a
                    href={data.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-slate-100 text-slate-800 text-xs font-medium hover:bg-slate-200 transition-colors"
                  >
                    <GitHubIcon className="w-3.5 h-3.5" />
                    <span>GitHub</span>
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </a>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 text-slate-400 text-xs italic">
                    <GitHubIcon className="w-3.5 h-3.5" /> No GitHub
                  </span>
                )}

                {/* Portfolio */}
                {data?.portfolio_url ? (
                  <a
                    href={data.portfolio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-teal-200 bg-teal-50 text-teal-800 text-xs font-medium hover:bg-teal-100 transition-colors"
                  >
                    <Globe className="w-3.5 h-3.5 text-teal-600" />
                    <span>Portfolio</span>
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </a>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 text-slate-400 text-xs italic">
                    <Globe className="w-3.5 h-3.5" /> No Portfolio
                  </span>
                )}

                {/* Other URLs */}
                {data?.other_urls && data.other_urls.length > 0 && data.other_urls.map((link, idx) => (
                  <a
                    key={idx}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors"
                    title={link}
                  >
                    <LinkIcon className="w-3.5 h-3.5 text-slate-500" />
                    <span className="max-w-[120px] truncate">{link.replace(/^https?:\/\//, '')}</span>
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
