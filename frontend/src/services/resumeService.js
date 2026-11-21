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



// ==========================================

// Phase 3 | Feature 17: Skill Normalization

// ==========================================



/**

 * Extracts and normalizes skills from resume text.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {boolean} [reprocess=false] - Re-run extraction.

 * @param {boolean} [forceOverwrite=false] - Overwrite manual edits.

 * @returns {Promise<object>}

 */

export async function extractSkills(resumeId, reprocess = false, forceOverwrite = false) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/extract?reprocess=${reprocess}&force_overwrite=${forceOverwrite}`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to extract skills with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Retrieves normalized skills and summary for a resume.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @returns {Promise<object>}

 */

export async function getSkills(resumeId) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills`;

  const response = await fetch(url, {

    method: 'GET',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to retrieve skills with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Normalizes an arbitrary list of raw skill strings.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {string[]} skills - Array of raw skill strings.

 * @param {string} [contextText=''] - Optional context text.

 * @returns {Promise<object>}

 */

export async function normalizeSkills(resumeId, skills, contextText = '') {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/normalize`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify({ skills, context_text: contextText }),

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to normalize skill list with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Reprocesses skill normalization for a resume.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {boolean} [forceOverwrite=false] - Whether to overwrite manual edits.

 * @returns {Promise<object>}

 */

export async function reprocessSkills(resumeId, forceOverwrite = false) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/reprocess?force_overwrite=${forceOverwrite}`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to reprocess skills with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Retrieves skill normalization summary statistics.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @returns {Promise<object>}

 */

export async function getSkillsSummary(resumeId) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/summary`;

  const response = await fetch(url, {

    method: 'GET',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to retrieve skills summary with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Retrieves skills pending human review.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @returns {Promise<object>}

 */

export async function getPendingSkillsReviews(resumeId) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/pending-reviews`;

  const response = await fetch(url, {

    method: 'GET',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to retrieve pending reviews with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Confirms a proposed canonical mapping.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {string} skillId - Skill record ID or name.

 * @param {string} [canonicalName=null] - Optional override name.

 * @returns {Promise<object>}

 */

export async function confirmSkillMapping(resumeId, skillId, canonicalName = null) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/${encodeURIComponent(skillId)}/confirm`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify(canonicalName ? { canonical_name: canonicalName } : {}),

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to confirm skill mapping with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Rejects a proposed canonical mapping.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {string} skillId - Skill record ID or name.

 * @param {string} [reason=null] - Optional rejection reason.

 * @returns {Promise<object>}

 */

export async function rejectSkillMapping(resumeId, skillId, reason = null) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/${encodeURIComponent(skillId)}/reject`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify(reason ? { reason } : {}),

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to reject skill mapping with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Manually updates a normalized skill record.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {string} skillId - Skill record ID or name.

 * @param {object} patchData - Fields to update.

 * @returns {Promise<object>}

 */

export async function updateSkillEntry(resumeId, skillId, patchData) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/${encodeURIComponent(skillId)}`;

  const response = await fetch(url, {

    method: 'PATCH',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify(patchData),

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to update skill entry with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Deletes a normalized skill record.

 *

 * @param {string} resumeId - UUID or staging ID.

 * @param {string} skillId - Skill record ID or name.

 * @returns {Promise<object>}

 */

export async function deleteSkillEntry(resumeId, skillId) {

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/skills/${encodeURIComponent(skillId)}`;

  const response = await fetch(url, {

    method: 'DELETE',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to delete skill with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Retrieves the global canonical skill dictionary.

 *

 * @returns {Promise<object>}

 */

export async function getSkillsDictionary() {

  const url = `${API_BASE_URL}/skills/dictionary`;

  const response = await fetch(url, {

    method: 'GET',

    headers: { 'Content-Type': 'application/json' },

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to retrieve dictionary with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}



/**

 * Adds an alias to the canonical dictionary.

 *

 * @param {string} canonicalName - Target canonical skill name.

 * @param {string} alias - New alias string.

 * @param {string} [category=null] - Category.

 * @param {string} [skillType='technical'] - Skill type.

 * @returns {Promise<object>}

 */

export async function addSkillAlias(canonicalName, alias, category = null, skillType = 'technical') {

  const url = `${API_BASE_URL}/skills/dictionary/alias`;

  const response = await fetch(url, {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify({

      canonical_name: canonicalName,

      alias,

      category,

      skill_type: skillType,

    }),

  });



  const responseBody = await response.json().catch(() => ({}));

  if (!response.ok) {

    const errorMsg =

      responseBody.error?.message ||

      responseBody.detail ||

      `Failed to add skill alias with status ${response.status}`;

    const err = new Error(errorMsg);

    err.status = response.status;

    throw err;

  }



  return responseBody;

}

// ==========================================

// ==========================================
// FEATURE 18: PROJECT INTELLIGENCE METHODS
// ==========================================

/**
 * Extracts and structures project information for a resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {boolean} [reprocess=false] - Whether to re-run extraction.
 * @param {boolean} [forceOverwrite=false] - Whether to overwrite manual edits.
 * @returns {Promise<object>}
 */
export async function extractProjects(resumeId, reprocess = false, forceOverwrite = false) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/extract?reprocess=${reprocess}&force_overwrite=${forceOverwrite}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to extract projects with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves all extracted projects and summary analytics for a resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getProjects(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch projects with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves single project details.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} projectId - Project identifier.
 * @returns {Promise<object>}
 */
export async function getProjectDetails(resumeId, projectId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/${encodeURIComponent(projectId)}`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch project details with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Adds a new project manually.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} projectData - Project payload.
 * @returns {Promise<object>}
 */
export async function addProject(resumeId, projectData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(projectData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to create project with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Updates an existing project.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} projectId - Project identifier.
 * @param {object} patchData - Fields to update.
 * @returns {Promise<object>}
 */
export async function updateProject(resumeId, projectId, patchData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/${encodeURIComponent(projectId)}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patchData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to update project with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Deletes a project.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} projectId - Project identifier.
 * @returns {Promise<object>}
 */
export async function deleteProject(resumeId, projectId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/${encodeURIComponent(projectId)}`;
  const response = await fetch(url, {
    method: 'DELETE',
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to delete project with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Reprocesses projects extraction preserving manual edits.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {boolean} [forceOverwrite=false] - Whether to overwrite manual edits.
 * @returns {Promise<object>}
 */
export async function reprocessProjects(resumeId, forceOverwrite = false) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/reprocess?force_overwrite=${forceOverwrite}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to reprocess projects with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves aggregate project metrics summary for a resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getProjectsSummary(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/summary`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch project summary with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves projects pending user review.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getPendingProjectsReviews(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/pending-reviews`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch pending project reviews with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Confirms an extracted project review status.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} projectId - Project identifier.
 * @param {string} [notes=''] - Optional confirmation review note.
 * @returns {Promise<object>}
 */
export async function confirmProject(resumeId, projectId, notes = '') {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/${encodeURIComponent(projectId)}/confirm`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to confirm project with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves canonical skill links for a project.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} projectId - Project identifier.
 * @returns {Promise<Array>}
 */
export async function getProjectSkills(resumeId, projectId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/projects/${encodeURIComponent(projectId)}/skills`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch project skills with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




// =========================================================================
// PHASE 3 | FEATURE 19: CERTIFICATIONS & ACHIEVEMENTS INTELLIGENCE
// =========================================================================

/**
 * Extracts and structures certifications from resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} [options]
 * @param {boolean} [options.reprocess=false]
 * @param {boolean} [options.forceOverwrite=false]
 * @returns {Promise<object>}
 */
export async function extractCertifications(resumeId, { reprocess = false, forceOverwrite = false } = {}) {
  const params = new URLSearchParams();
  if (reprocess) params.append('reprocess', 'true');
  if (forceOverwrite) params.append('force_overwrite', 'true');
  const query = params.toString() ? `?${params.toString()}` : '';

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/extract${query}`;
  const response = await fetch(url, { method: 'POST' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to extract certifications with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves candidate certifications for a resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getCertifications(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch certifications with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves aggregate certification analytics.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getCertificationSummary(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/summary`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch certification summary with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves certifications pending user review.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getPendingCertificationsReviews(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/pending-reviews`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch pending certification reviews with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves details for a specific certification.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} certificationId - Certification identifier.
 * @returns {Promise<object>}
 */
export async function getCertificationDetails(resumeId, certificationId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/${encodeURIComponent(certificationId)}`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch certification details with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves canonical skill links for a certification.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} certificationId - Certification identifier.
 * @returns {Promise<Array>}
 */
export async function getCertificationSkills(resumeId, certificationId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/${encodeURIComponent(certificationId)}/skills`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch certification skills with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Adds a new certification entry manually.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} certificationData - Certification payload.
 * @returns {Promise<object>}
 */
export async function addCertification(resumeId, certificationData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(certificationData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to add certification with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Updates an existing certification entry manually.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} certificationId - Certification identifier.
 * @param {object} patchData - Fields to update.
 * @returns {Promise<object>}
 */
export async function updateCertification(resumeId, certificationId, patchData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/${encodeURIComponent(certificationId)}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patchData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to update certification with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Confirms review status for a certification.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} certificationId - Certification identifier.
 * @param {string} [notes=''] - Review note.
 * @returns {Promise<object>}
 */
export async function confirmCertification(resumeId, certificationId, notes = '') {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/${encodeURIComponent(certificationId)}/confirm`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to confirm certification with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Deletes a certification record.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} certificationId - Certification identifier.
 * @returns {Promise<object>}
 */
export async function deleteCertification(resumeId, certificationId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/${encodeURIComponent(certificationId)}`;
  const response = await fetch(url, { method: 'DELETE' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to delete certification with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Reprocesses certifications while preserving manual edits.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} [options]
 * @param {boolean} [options.forceOverwrite=false]
 * @returns {Promise<object>}
 */
export async function reprocessCertifications(resumeId, { forceOverwrite = false } = {}) {
  const query = forceOverwrite ? '?force_overwrite=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications/reprocess${query}`;
  const response = await fetch(url, { method: 'POST' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to reprocess certifications with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




// -------------------------------------------------------------------------
// ACHIEVEMENTS OPERATIONS
// -------------------------------------------------------------------------

/**
 * Extracts candidate accomplishments from resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} [options]
 * @param {boolean} [options.reprocess=false]
 * @param {boolean} [options.forceOverwrite=false]
 * @returns {Promise<object>}
 */
export async function extractAchievements(resumeId, { reprocess = false, forceOverwrite = false } = {}) {
  const params = new URLSearchParams();
  if (reprocess) params.append('reprocess', 'true');
  if (forceOverwrite) params.append('force_overwrite', 'true');
  const query = params.toString() ? `?${params.toString()}` : '';

  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/extract${query}`;
  const response = await fetch(url, { method: 'POST' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to extract achievements with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves candidate achievements for a resume.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getAchievements(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch achievements with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves aggregate achievement analytics.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getAchievementSummary(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/summary`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch achievement summary with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves achievements pending user review.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getPendingAchievementsReviews(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/pending-reviews`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch pending achievement reviews with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves details for a specific achievement.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} achievementId - Achievement identifier.
 * @returns {Promise<object>}
 */
export async function getAchievementDetails(resumeId, achievementId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/${encodeURIComponent(achievementId)}`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch achievement details with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves canonical skill links for an achievement.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} achievementId - Achievement identifier.
 * @returns {Promise<Array>}
 */
export async function getAchievementSkills(resumeId, achievementId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/${encodeURIComponent(achievementId)}/skills`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch achievement skills with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Adds a new achievement entry manually.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} achievementData - Achievement payload.
 * @returns {Promise<object>}
 */
export async function addAchievement(resumeId, achievementData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(achievementData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to add achievement with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Updates an existing achievement entry manually.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} achievementId - Achievement identifier.
 * @param {object} patchData - Fields to update.
 * @returns {Promise<object>}
 */
export async function updateAchievement(resumeId, achievementId, patchData) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/${encodeURIComponent(achievementId)}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patchData),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to update achievement with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Confirms review status for an achievement.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} achievementId - Achievement identifier.
 * @param {string} [notes=''] - Review note.
 * @returns {Promise<object>}
 */
export async function confirmAchievement(resumeId, achievementId, notes = '') {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/${encodeURIComponent(achievementId)}/confirm`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to confirm achievement with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Deletes an achievement record.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {string} achievementId - Achievement identifier.
 * @returns {Promise<object>}
 */
export async function deleteAchievement(resumeId, achievementId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/${encodeURIComponent(achievementId)}`;
  const response = await fetch(url, { method: 'DELETE' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to delete achievement with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Reprocesses achievements while preserving manual edits.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @param {object} [options]
 * @param {boolean} [options.forceOverwrite=false]
 * @returns {Promise<object>}
 */
export async function reprocessAchievements(resumeId, { forceOverwrite = false } = {}) {
  const query = forceOverwrite ? '?force_overwrite=true' : '';
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/achievements/reprocess${query}`;
  const response = await fetch(url, { method: 'POST' });

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to reprocess achievements with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}




/**
 * Retrieves combined summary of certifications and achievements.
 *
 * @param {string} resumeId - UUID or staging ID.
 * @returns {Promise<object>}
 */
export async function getCertificationsAchievementsSummary(resumeId) {
  const url = `${API_BASE_URL}/resumes/${encodeURIComponent(resumeId)}/certifications-achievements/summary`;
  const response = await fetch(url);

  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg =
      responseBody.error?.message ||
      responseBody.detail ||
      `Failed to fetch combined summary with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }
  return responseBody;
}

export { getResumeQualityScore, analyzeResumeQualityScore } from './qualityScoreService.js';
export { getResumeStrengths, analyzeResumeStrengths } from './strengthService.js';
export { getResumeWeaknesses, analyzeResumeWeaknesses } from './weaknessService.js';
export { getResumeATS, analyzeResumeATS } from './atsService.js';
export { getResumeGrammar, analyzeResumeGrammar } from './grammarService.js';
export { getResumeAchievements, analyzeResumeAchievements } from './achievementService.js';
export {
  getResumeRecommendations,
  generateResumeRecommendations,
  updateRecommendationStatus,
} from './recommendationService.js';







