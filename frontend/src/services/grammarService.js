/**
 * Resume Grammar & Clarity Analysis API Service
 * Phase 4 | Feature 25: Grammar & Clarity Analysis
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves previously saved grammar and clarity analysis for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeGrammar(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch grammar analysis.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/grammar?optional=true`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch grammar analysis with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Analyzes candidate resume grammar, spelling, clarity, professional tone,
 * and sentence structure, producing before-and-after suggestions.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeGrammar(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze resume grammar.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/grammar/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to analyze resume grammar with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
