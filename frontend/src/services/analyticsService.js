/**
 * Resume Analytics Dashboard API Service
 * Phase 5 | Feature 28: Resume Analytics Dashboard
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves aggregated visual insights, summary cards, distributions,
 * and synthesized insights for an uploaded resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>} Standard API response envelope with data.
 */
export async function getResumeAnalyticsDashboard(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch analytics dashboard.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/analytics/dashboard`;

  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch resume analytics with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
