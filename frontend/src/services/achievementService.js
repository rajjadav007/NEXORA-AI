/**
 * Resume Achievement Analysis API Service
 * Phase 4 | Feature 26: Achievement Analysis
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves previously saved achievement analysis for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeAchievements(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch achievement analysis.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/analysis`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch achievement analysis with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Analyzes candidate accomplishments across experience, projects, hackathons,
 * awards, and leadership; extracts measurable metrics and generates Google X-Y-Z statements.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeAchievements(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze resume achievements.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to analyze resume achievements with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
