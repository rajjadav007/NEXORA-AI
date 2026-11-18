import { API_BASE_URL } from '../config/constants.js';

/**
 * Uploads a resume document (PDF or DOCX) with real-time upload progress.
 *
 * @param {File} file - The resume file to upload.
 * @param {Function} [onProgress] - Optional callback receiving progress percentage (0 - 100).
 * @returns {{ promise: Promise<object>, abort: () => void }}
 */
export function uploadResume(file, onProgress) {
  const xhr = new XMLHttpRequest();

  const promise = new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percentCompleted = Math.round((event.loaded * 100) / event.total);
        onProgress(percentCompleted);
      }
    });

    xhr.addEventListener('load', () => {
      let responseBody = {};
      try {
        responseBody = JSON.parse(xhr.responseText);
      } catch {
        responseBody = { detail: xhr.responseText || 'Unexpected server response' };
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(responseBody);
      } else {
        const errorMessage =
          responseBody.error?.message ||
          responseBody.detail ||
          responseBody.message ||
          `Upload failed with HTTP status ${xhr.status}`;
        const error = new Error(errorMessage);
        error.code = responseBody.error?.code || 'FILE_VALIDATION_FAILED';
        error.category = responseBody.error?.category || 'validation';
        error.details = responseBody.error?.details || {};
        error.status = xhr.status;
        reject(error);
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error during file upload. Please check your connection.'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload was cancelled.'));
    });

    const uploadUrl = `${API_BASE_URL}/resumes/upload`;
    const formData = new FormData();
    formData.append('file', file);

    xhr.open('POST', uploadUrl, true);
    xhr.send(formData);
  });

  return {
    promise,
    abort: () => xhr.abort(),
  };
}

/**
 * Extracts raw readable text, pages, and document blocks from a staged resume.
 *
 * @param {string} resumeId - Upload / Staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function extractResumeText(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/extract`;
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
      `Extraction failed with status ${response.status}`;
    const err = new Error(errorMsg);
    err.code = responseBody.error?.code || 'EXTRACTION_FAILED';
    throw err;
  }

  return responseBody;
}

/**
 * Cleans and normalizes extracted resume text.
 *
 * @param {string} resumeId - Upload / Staging ID of the resume.
 * @param {string} [rawText] - Optional raw text override.
 * @returns {Promise<object>}
 */
export async function cleanResumeText(resumeId, rawText = null) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/clean`;
  const body = rawText !== null ? JSON.stringify({ raw_text: rawText }) : null;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    ...(body ? { body } : {}),
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Cleaning failed with status ${response.status}`;
    const err = new Error(errorMsg);
    err.code = responseBody.error?.code || 'CLEANING_FAILED';
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves resume preview data (cleaned text, structured blocks, file metadata).
 *
 * @param {string} resumeId - Upload / Staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getResumePreview(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/preview`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to load preview with status ${response.status}`;
    const err = new Error(errorMsg);
    err.code = responseBody.error?.code || 'PREVIEW_LOAD_FAILED';
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Constructs the secure URL for original document access/download.
 *
 * @param {string} resumeId - Upload / Staging ID of the resume.
 * @param {boolean} [download=false] - Whether to force file download disposition.
 * @returns {string}
 */
export function getResumeFileUrl(resumeId, download = false) {
  const baseUrl = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/file`;
  return download ? `${baseUrl}?download=true` : baseUrl;
}

/**
 * Saves a validated staged resume to permanent storage and database.
 *
 * @param {string} resumeId - Upload / Staging ID of the resume.
 * @param {object} [userMeta={}] - Optional user identification { userId, userEmail }.
 * @returns {Promise<object>}
 */
export async function saveResume(resumeId, userMeta = {}) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/save`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userMeta),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to save resume with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Lists all permanently stored resumes.
 *
 * @param {string} [userId] - Optional user UUID to filter resumes.
 * @returns {Promise<object>}
 */
export async function getSavedResumes(userId = null) {
  const url = userId
    ? `${API_BASE_URL}/resumes?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/resumes`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to list resumes with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves details and version history for a stored resume.
 *
 * @param {string} resumeId - UUID of the stored resume.
 * @returns {Promise<object>}
 */
export async function getSavedResume(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to retrieve resume with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Permanently deletes a stored resume and its associated storage files.
 *
 * @param {string} resumeId - UUID of the resume to delete.
 * @returns {Promise<object>}
 */
export async function deleteStoredResume(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to delete resume with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}



