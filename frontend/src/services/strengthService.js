/**
 * Resume Strength Analysis API Service
 * Phase 4 | Feature 22: Resume Strength Analysis
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves the previously saved strength analysis for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeStrengths(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch strength analysis.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/strengths`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch strength analysis with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Analyzes candidate strengths across technical, project, work experience,
 * education, achievement, leadership, and communication categories.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeStrengths(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze resume strengths.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/strengths/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Strength analysis failed with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
