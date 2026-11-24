/**
 * Resume Improvement Tracker API Service
 * Phase 5 | Feature 30: Resume Improvement Tracker
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Retrieves complete aggregated improvement tracking overview.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>} Standard API response envelope with data.
 */
export async function getResumeImprovements(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch improvement tracking data.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/improvements`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch improvements with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves chronological analysis snapshots and scores over time.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>} Standard API response envelope with data.
 */
export async function getResumeImprovementHistory(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch improvement history.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/improvements/history`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch improvement history with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves actionable improvement tasks with optional filters.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [filters={}] - Optional status and priority filters.
 * @returns {Promise<object>} Standard API response envelope with data.
 */
export async function getResumeImprovementTasks(resumeId, filters = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch improvement tasks.');
  }

  const queryParams = new URLSearchParams();
  if (filters.status) queryParams.set('status', filters.status);
  if (filters.priority) queryParams.set('priority', filters.priority);

  const qs = queryParams.toString();
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/improvements/tasks${qs ? `?${qs}` : ''}`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch improvement tasks with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Updates status or priority of an individual improvement task.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {string} taskId - UUID of the task.
 * @param {object} payload - { status: 'Pending'|'In Progress'|'Completed', priority?: 'High'|'Medium'|'Low' }
 * @returns {Promise<object>} Standard API response envelope with data.
 */
export async function updateResumeImprovementTask(resumeId, taskId, payload) {
  if (!resumeId || !taskId) {
    throw new Error('resumeId and taskId are required to update improvement task.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/improvements/tasks/${encodeURIComponent(taskId)}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to update task with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Compares two resume versions side-by-side.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {number} [v1] - First version number.
 * @param {number} [v2] - Second version number.
 * @returns {Promise<object>} Standard API response envelope with comparison data.
 */
export async function compareResumeVersions(resumeId, v1, v2) {
  if (!resumeId) {
    throw new Error('resumeId is required to compare versions.');
  }

  const queryParams = new URLSearchParams();
  if (v1 !== undefined && v1 !== null) queryParams.set('v1', v1);
  if (v2 !== undefined && v2 !== null) queryParams.set('v2', v2);

  const qs = queryParams.toString();
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/improvements/compare${qs ? `?${qs}` : ''}`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to compare versions with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
