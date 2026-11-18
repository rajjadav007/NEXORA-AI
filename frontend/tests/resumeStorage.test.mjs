import test from 'node:test';
import assert from 'node:assert/strict';
import {
  saveResume,
  getSavedResumes,
  getSavedResume,
  deleteStoredResume,
  getResumeFileUrl,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 6 storage operations', () => {
  assert.equal(typeof saveResume, 'function');
  assert.equal(typeof getSavedResumes, 'function');
  assert.equal(typeof getSavedResume, 'function');
  assert.equal(typeof deleteStoredResume, 'function');
});

test('getResumeFileUrl constructs download and view URLs for stored resumes', () => {
  const resumeId = '65b88f96-8885-4310-9edd-8186e3e55425';
  const viewUrl = getResumeFileUrl(resumeId);
  const downloadUrl = getResumeFileUrl(resumeId, true);

  assert.equal(viewUrl.includes(`/resumes/${resumeId}/file`), true);
  assert.equal(downloadUrl.includes(`/resumes/${resumeId}/file?download=true`), true);
});
