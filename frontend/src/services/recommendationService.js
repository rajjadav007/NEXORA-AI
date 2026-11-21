/**
 * Resume Improvement Recommendations API Service
 * Phase 4 | Feature 27: Resume Improvement Recommendations
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves persisted recommendations for a resume with optional filters.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [filters]
 * @param {string} [filters.category] - Filter by category key.
 * @param {string} [filters.priority] - Filter by priority (Critical, High, Medium, Low).
 * @param {boolean} [filters.isCompleted] - Filter by completion status.
 * @returns {Promise<object>}
 */
export async function getResumeRecommendations(resumeId, { category, priority, isCompleted } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch recommendations.');
  }

  const queryParams = new URLSearchParams();
  if (category) queryParams.append('category', category);
  if (priority) queryParams.append('priority', priority);
  if (typeof isCompleted === 'boolean') queryParams.append('is_completed', isCompleted.toString());

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/recommendations${queryString}`;

  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch recommendations with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Generates personalized improvement recommendations using LangGraph workflow.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options]
 * @param {boolean} [options.forceRecalculate=false] - Whether to re-run AI evaluation.
 * @returns {Promise<object>}
 */
export async function generateResumeRecommendations(resumeId, { forceRecalculate = false } = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to generate recommendations.');
  }

  const query = forceRecalculate ? '?force_recalculate=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/recommendations/generate${query}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to generate recommendations with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Updates the completion status of a specific recommendation item.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {string} recommendationId - Identifier of the recommendation (e.g. REC-TECH-01).
 * @param {boolean} isCompleted - Desired completion status.
 * @returns {Promise<object>}
 */
export async function updateRecommendationStatus(resumeId, recommendationId, isCompleted) {
  if (!resumeId || !recommendationId) {
    throw new Error('resumeId and recommendationId are required to update status.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/recommendations/${encodeURIComponent(recommendationId)}/status`;

  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_completed: isCompleted }),
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to update recommendation status with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
