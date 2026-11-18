import test from 'node:test';
import assert from 'node:assert/strict';

import {
  formatFileSize,
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  MIN_FILE_SIZE_BYTES,
  getErrorSuggestion,
} from '../src/hooks/useResumeUpload.js';

test('formatFileSize formats byte units correctly', () => {
  assert.equal(formatFileSize(0), '0 B');
  assert.equal(formatFileSize(500), '500.0 B');
  assert.equal(formatFileSize(1024), '1.0 KB');
  assert.equal(formatFileSize(1024 * 1024 * 2.5), '2.50 MB');
  assert.equal(formatFileSize(10 * 1024 * 1024), '10.00 MB');
  assert.equal(formatFileSize(-1), '0 B');
  assert.equal(formatFileSize(null), '0 B');
});

test('Allowed extensions and size constants match specification', () => {
  assert.deepEqual(ALLOWED_EXTENSIONS, ['.pdf', '.docx']);
  assert.equal(MAX_FILE_SIZE_BYTES, 10 * 1024 * 1024);
  assert.equal(MIN_FILE_SIZE_BYTES, 64);
});

test('Client validation rejects unsupported extensions', () => {
  const invalidFiles = ['test.txt', 'image.png', 'script.js', 'resume.pdf.exe', 'resume.doc'];
  for (const name of invalidFiles) {
    const isAllowed = ALLOWED_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext));
    assert.equal(isAllowed, false, `Expected ${name} to be rejected`);
  }
});

test('Client validation accepts PDF and DOCX files', () => {
  const validFiles = ['resume.pdf', 'MyResume.DOCX', 'Candidate_Profile.docx', 'test.PDF'];
  for (const name of validFiles) {
    const isAllowed = ALLOWED_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext));
    assert.equal(isAllowed, true, `Expected ${name} to be accepted`);
  }
});

test('getErrorSuggestion maps validation error codes to helpful guidance', () => {
  assert.match(getErrorSuggestion('PASSWORD_PROTECTED_FILE'), /password/i);
  assert.match(getErrorSuggestion('CORRUPTED_FILE'), /damaged/i);
  assert.match(getErrorSuggestion('INVALID_DOCUMENT_STRUCTURE'), /ZIP archive/i);
  assert.match(getErrorSuggestion('INVALID_FILE_SIGNATURE'), /signature/i);
  assert.match(getErrorSuggestion('FILE_TOO_LARGE'), /10 MB/i);
  assert.match(getErrorSuggestion('UNSUPPORTED_FILE_TYPE'), /PDF.*DOCX/i);
});

test('resumeService exports uploadResume, extractResumeText, cleanResumeText, getResumePreview, and getResumeFileUrl', async () => {
  const service = await import('../src/services/resumeService.js');
  assert.equal(typeof service.uploadResume, 'function');
  assert.equal(typeof service.extractResumeText, 'function');
  assert.equal(typeof service.cleanResumeText, 'function');
  assert.equal(typeof service.getResumePreview, 'function');
  assert.equal(typeof service.getResumeFileUrl, 'function');
});

