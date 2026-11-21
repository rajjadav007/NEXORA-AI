/**
 * Resume Quality Score API Service
 * Phase 4 | Feature 21: Resume Quality Score Engine
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves the previously saved quality score for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumeQualityScore(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch quality score.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/quality-score`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch quality score with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Triggers quality score evaluation for a resume using LangChain ChatOllama and deterministic metrics.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function analyzeResumeQualityScore(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to analyze quality score.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/quality-score/analyze${query}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Quality score analysis failed with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
