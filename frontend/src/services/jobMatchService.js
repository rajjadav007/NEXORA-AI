import { apiRequest } from './api.js';
import { getActiveUserId } from './jobDescriptionService.js';

function buildHeaders(userId) {
  return {
    'X-User-Id': userId || getActiveUserId(),
  };
}

/**
 * Compare a resume against a job description (creates or returns cached match).
 */
export async function compareResumeAndJob(
  { resumeId, jobDescriptionId, regenerate = false },
  userId
) {
  return apiRequest('/job-matches', {
    method: 'POST',
    headers: buildHeaders(userId),
    body: JSON.stringify({
      resume_id: resumeId,
      job_description_id: jobDescriptionId,
      regenerate,
    }),
  });
}

/**
 * List saved job matches for the active user.
 */
export async function listJobMatches(params = {}, userId) {
  const qs = new URLSearchParams();
  if (params.resumeId) qs.set('resume_id', params.resumeId);
  if (params.jobDescriptionId) qs.set('job_description_id', params.jobDescriptionId);
  const query = qs.toString() ? `?${qs.toString()}` : '';
  return apiRequest(`/job-matches${query}`, {
    method: 'GET',
    headers: buildHeaders(userId),
  });
}

/**
 * Retrieve a previously generated job match by ID.
 */
export async function getJobMatchById(matchId, userId) {
  return apiRequest(`/job-matches/${encodeURIComponent(matchId)}`, {
    method: 'GET',
    headers: buildHeaders(userId),
  });
}
