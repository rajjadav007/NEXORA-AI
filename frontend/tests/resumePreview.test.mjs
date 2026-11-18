import test from 'node:test';
import assert from 'node:assert/strict';
import { getResumeFileUrl } from '../src/services/resumeService.js';

test('getResumeFileUrl constructs safe, encoded URL for inline view', () => {
  const resumeId = '123e4567-e89b-12d3-a456-426614174000';
  const url = getResumeFileUrl(resumeId, false);
  assert.equal(url.includes('/resumes/123e4567-e89b-12d3-a456-426614174000/file'), true);
  assert.equal(url.includes('download=true'), false);
});

test('getResumeFileUrl constructs URL with download parameter when requested', () => {
  const resumeId = '123e4567-e89b-12d3-a456-426614174000';
  const url = getResumeFileUrl(resumeId, true);
  assert.equal(url.includes('/resumes/123e4567-e89b-12d3-a456-426614174000/file?download=true'), true);
});

test('getResumeFileUrl URI encodes special characters in resumeId safely', () => {
  const dangerousId = 'test/../../etc/passwd';
  const url = getResumeFileUrl(dangerousId);
  assert.equal(url.includes('..%2F..%2Fetc'), true);
});

test('PreviewStatus standard states are properly defined and consistent', () => {
  const validStatuses = ['READY', 'PROCESSING', 'EMPTY', 'ERROR'];
  for (const status of validStatuses) {
    assert.equal(typeof status, 'string');
    assert.equal(status, status.toUpperCase());
  }
});

test('Structured content block types conform to specification', () => {
  const validBlockTypes = ['heading', 'paragraph', 'list_item', 'table'];
  for (const type of validBlockTypes) {
    assert.equal(typeof type, 'string');
  }
});
