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
      `Failed to load resumes with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves a single permanently stored resume and its historical versions.
 *
 * @param {string} resumeId - UUID of the resume to retrieve.
 * @returns {Promise<object>}
 */
export async function getStoredResume(resumeId) {
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

export const getSavedResume = getStoredResume;

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

// --------------------------------------------------------------------------
// Feature #13: Personal Information Operations
// --------------------------------------------------------------------------

/**
 * Extracts personal information from cleaned resume text.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [reprocess=false] - Whether to re-run extraction.
 * @param {boolean} [forceOverwrite=false] - Whether to overwrite manual user edits.
 * @returns {Promise<object>}
 */
export async function extractPersonalInfo(resumeId, reprocess = false, forceOverwrite = false) {
  const query = new URLSearchParams({
    reprocess: String(reprocess),
    force_overwrite: String(forceOverwrite),
  });
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/personal-info/extract?${query.toString()}`;
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
      `Failed to extract personal info with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves previously extracted personal information for a resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getPersonalInfo(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/personal-info`;
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
      `Failed to load personal info with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Updates candidate personal information manually.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {object} payload - Partial personal info fields to update.
 * @returns {Promise<object>}
 */
export async function updatePersonalInfo(resumeId, payload) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/personal-info`;
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
      `Failed to update personal info with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Reprocesses personal information extraction on the resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [forceOverwrite=false] - Whether to discard manual edits.
 * @returns {Promise<object>}
 */
export async function reprocessPersonalInfo(resumeId, forceOverwrite = false) {
  const query = new URLSearchParams({
    force_overwrite: String(forceOverwrite),
  });
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/personal-info/reprocess?${query.toString()}`;
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
      `Failed to reprocess personal info with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

// --------------------------------------------------------------------------
// Feature #14: Education Analysis Operations
// --------------------------------------------------------------------------

/**
 * Extracts education qualifications from cleaned resume text.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [reprocess=false] - Whether to re-run extraction.
 * @param {boolean} [forceOverwrite=false] - Whether to overwrite manual user edits.
 * @returns {Promise<object>}
 */
export async function extractEducation(resumeId, reprocess = false, forceOverwrite = false) {
  const query = new URLSearchParams({
    reprocess: String(reprocess),
    force_overwrite: String(forceOverwrite),
  });
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education/extract?${query.toString()}`;
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
      `Failed to extract education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves previously extracted education records for a resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getEducation(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education`;
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
      `Failed to load education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Reprocesses education extraction on the resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [forceOverwrite=false] - Whether to discard manual edits.
 * @returns {Promise<object>}
 */
export async function reprocessEducation(resumeId, forceOverwrite = false) {
  const query = new URLSearchParams({
    force_overwrite: String(forceOverwrite),
  });
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education/reprocess?${query.toString()}`;
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
      `Failed to reprocess education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Adds a new manual education record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {object} payload - New education details.
 * @returns {Promise<object>}
 */
export async function addEducation(resumeId, payload) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education`;
  const response = await fetch(url, {
    method: 'POST',
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
      `Failed to add education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Updates an existing education record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {string} educationId - UUID of the education record.
 * @param {object} payload - Partial education fields to update.
 * @returns {Promise<object>}
 */
export async function updateEducation(resumeId, educationId, payload) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education/${encodeURIComponent(educationId)}`;
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
      `Failed to update education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Deletes an education record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {string} educationId - UUID of the education record.
 * @returns {Promise<object>}
 */
export async function deleteEducation(resumeId, educationId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/education/${encodeURIComponent(educationId)}`;
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
      `Failed to delete education with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

// ============================================================================
// Phase 3 | Feature 15: Experience Analysis API Operations
// ============================================================================

/**
 * Extracts, normalizes, validates, and orders work experience entries from a resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [reprocess=false] - Whether to re-extract experience.
 * @param {boolean} [forceOverwrite=false] - Whether to overwrite user manual edits on reprocess.
 * @returns {Promise<object>}
 */
export async function extractExperience(resumeId, reprocess = false, forceOverwrite = false) {
  const params = new URLSearchParams();
  if (reprocess) params.append('reprocess', 'true');
  if (forceOverwrite) params.append('force_overwrite', 'true');
  const query = params.toString() ? `?${params.toString()}` : '';

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/extract${query}`;
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
      `Failed to extract experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves extracted work experience records for a given resume.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getExperience(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience`;
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
      `Failed to retrieve experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Reprocesses work experience extraction while protecting manual user edits.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {boolean} [forceOverwrite=false] - Whether to discard manual edits.
 * @returns {Promise<object>}
 */
export async function reprocessExperience(resumeId, forceOverwrite = false) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/reprocess`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ force_overwrite: forceOverwrite }),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to reprocess experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Adds a new manual experience record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {object} payload - New experience details.
 * @returns {Promise<object>}
 */
export async function addExperience(resumeId, payload) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience`;
  const response = await fetch(url, {
    method: 'POST',
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
      `Failed to add experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Updates an existing experience record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {string} experienceId - UUID of the experience record.
 * @param {object} payload - Partial experience fields to update.
 * @returns {Promise<object>}
 */
export async function updateExperience(resumeId, experienceId, payload) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/${encodeURIComponent(experienceId)}`;
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
      `Failed to update experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Deletes an experience record.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @param {string} experienceId - UUID of the experience record.
 * @returns {Promise<object>}
 */
export async function deleteExperience(resumeId, experienceId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/${encodeURIComponent(experienceId)}`;
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
      `Failed to delete experience with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves aggregate experience summary metrics.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getExperienceSummary(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/summary`;
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
      `Failed to retrieve experience summary with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}

/**
 * Retrieves career progression analysis and transitions.
 *
 * @param {string} resumeId - UUID or staging ID of the resume.
 * @returns {Promise<object>}
 */
export async function getCareerProgression(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/experience/progression`;
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
      `Failed to retrieve career progression with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return responseBody;
}
