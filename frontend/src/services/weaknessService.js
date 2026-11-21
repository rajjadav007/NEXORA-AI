/**
 * Resume Weakness Analysis API Service
 * Phase 4 | Feature 23: Resume Weakness Analysis
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves the previously saved weakness analysis for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeWeaknesses(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch weakness analysis.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/weaknesses`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch weakness analysis with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Analyzes candidate weaknesses across technical skills, projects,
 * work experience, education, achievements, summary, and clarity.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeWeaknesses(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze resume weaknesses.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/weaknesses/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to analyze resume weaknesses with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
