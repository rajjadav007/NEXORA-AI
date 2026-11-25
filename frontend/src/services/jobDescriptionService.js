import { apiRequest } from './api.js';

export const JD_MIN_LENGTH = 50;
export const JD_MAX_LENGTH = 15000;
export const TITLE_MIN_LENGTH = 2;
export const TITLE_MAX_LENGTH = 255;

export const EMPLOYMENT_TYPES = [
  'Full-time',
  'Part-time',
  'Contract',
  'Internship',
  'Temporary',
  'Freelance',
];

const USER_ID_STORAGE_KEY = 'nexora_user_id';

/**
 * Returns a persistent UUID for the current browser session.
 * Falls back to a deterministic UUID if localStorage is unavailable (e.g., SSR/Node tests).
 */
export function getActiveUserId() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return '00000000-0000-4000-8000-000000000001';
  }
  let userId = window.localStorage.getItem(USER_ID_STORAGE_KEY);
  if (!userId) {
    userId =
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID()
        : '00000000-0000-4000-8000-000000000001';
    window.localStorage.setItem(USER_ID_STORAGE_KEY, userId);
  }
  return userId;
}

/**
 * Validates job description form fields on the client before submission.
 */
export function validateJobDescriptionInput(form = {}) {
  const errors = {};
  const jobTitle = String(form.job_title ?? '').trim();
  const companyName = String(form.company_name ?? '').trim();
  const description = String(form.description ?? '').trim();
  const location = String(form.location ?? '').trim();
  const employmentType = String(form.employment_type ?? '').trim();

  if (!jobTitle) {
    errors.job_title = 'Job title is required.';
  } else if (jobTitle.length < TITLE_MIN_LENGTH || jobTitle.length > TITLE_MAX_LENGTH) {
    errors.job_title = `Job title must be between ${TITLE_MIN_LENGTH} and ${TITLE_MAX_LENGTH} characters.`;
  }

  if (!companyName) {
    errors.company_name = 'Company name is required.';
  } else if (companyName.length < TITLE_MIN_LENGTH || companyName.length > TITLE_MAX_LENGTH) {
    errors.company_name = `Company name must be between ${TITLE_MIN_LENGTH} and ${TITLE_MAX_LENGTH} characters.`;
  }

  if (!description) {
    errors.description = 'Job description cannot be empty.';
  } else if (description.length < JD_MIN_LENGTH) {
    errors.description = `Job description must be at least ${JD_MIN_LENGTH} characters (currently ${description.length}).`;
  } else if (description.length > JD_MAX_LENGTH) {
    errors.description = `Job description cannot exceed ${JD_MAX_LENGTH.toLocaleString()} characters.`;
  }

  if (location.length > TITLE_MAX_LENGTH) {
    errors.location = `Location cannot exceed ${TITLE_MAX_LENGTH} characters.`;
  }

  if (employmentType && !EMPLOYMENT_TYPES.includes(employmentType)) {
    errors.employment_type = 'Please select a valid employment type.';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
    normalized: {
      job_title: jobTitle,
      company_name: companyName,
      description,
      location: location || null,
      employment_type: employmentType || null,
    },
  };
}

function buildHeaders(userId) {
  return {
    'X-User-Id': userId || getActiveUserId(),
  };
}

export async function createJobDescription(payload, userId) {
  const { isValid, errors, normalized } = validateJobDescriptionInput(payload);
  if (!isValid) {
    const firstError = Object.values(errors)[0] || 'Invalid job description input.';
    const error = new Error(firstError);
    error.validationErrors = errors;
    throw error;
  }

  return apiRequest('/job-descriptions', {
    method: 'POST',
    headers: buildHeaders(userId),
    body: JSON.stringify(normalized),
  });
}

export async function listJobDescriptions(userId) {
  return apiRequest('/job-descriptions', {
    method: 'GET',
    headers: buildHeaders(userId),
  });
}

export async function getJobDescriptionById(jobDescriptionId, userId) {
  if (!jobDescriptionId) {
    throw new Error('jobDescriptionId is required.');
  }
  return apiRequest(`/job-descriptions/${encodeURIComponent(jobDescriptionId)}`, {
    method: 'GET',
    headers: buildHeaders(userId),
  });
}

export async function deleteJobDescription(jobDescriptionId, userId) {
  if (!jobDescriptionId) {
    throw new Error('jobDescriptionId is required.');
  }
  return apiRequest(`/job-descriptions/${encodeURIComponent(jobDescriptionId)}`, {
    method: 'DELETE',
    headers: buildHeaders(userId),
  });
}
