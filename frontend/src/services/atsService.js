/**
 * Resume ATS Compatibility Analysis API Service
 * Phase 4 | Feature 24: ATS Compatibility Analysis
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves the previously saved ATS compatibility analysis for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeATS(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch ATS analysis.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/ats`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch ATS analysis with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Runs deterministic ATS compatibility analysis across 8 categories,
 * detecting layout risks, section headings, and contextual AI recommendations.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeATS(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze resume ATS compatibility.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/ats/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to analyze resume ATS compatibility with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
