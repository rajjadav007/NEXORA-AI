/**
 * AI Resume Report API Service
 * Phase 5 | Feature 31: AI Resume Report
 */

import { API_BASE_URL } from '../config/constants.js';

/**
 * Generates or retrieves a comprehensive AI Resume Report.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {object} [options={}] - Options { forceRecalculate: bool, fallbackToDeterministic: bool }
 * @returns {Promise<object>} Standard API response envelope with report data.
 */
export async function generateResumeReport(resumeId, options = {}) {
  if (!resumeId) {
    throw new Error('resumeId is required to generate report.');
  }

  const queryParams = new URLSearchParams();
  if (options.forceRecalculate) queryParams.set('force_recalculate', 'true');
  if (options.fallbackToDeterministic) queryParams.set('fallback_to_deterministic', 'true');

  const qs = queryParams.toString();
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/reports/generate${qs ? `?${qs}` : ''}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to generate report with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves list of past generated reports for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>} Standard API response envelope with history list.
 */
export async function getResumeReportHistory(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch report history.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/reports`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch report history with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves the latest generated report for a resume.
 *
 * @param {string} resumeId - UUID of the resume.
 * @returns {Promise<object>} Standard API response envelope with report data.
 */
export async function getLatestResumeReport(resumeId) {
  if (!resumeId) {
    throw new Error('resumeId is required to fetch latest report.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/reports/latest`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch latest report with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves a specific report by report ID.
 *
 * @param {string} resumeId - UUID of the resume.
 * @param {string} reportId - UUID of the report.
 * @returns {Promise<object>} Standard API response envelope with report data.
 */
export async function getResumeReportById(resumeId, reportId) {
  if (!resumeId || !reportId) {
    throw new Error('resumeId and reportId are required to fetch report.');
  }

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/reports/${encodeURIComponent(reportId)}`;
  const response = await fetch(url);
  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch report with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
