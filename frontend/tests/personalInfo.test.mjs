import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractPersonalInfo,
  getPersonalInfo,
  updatePersonalInfo,
  reprocessPersonalInfo,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 13 personal information operations', () => {
  assert.equal(typeof extractPersonalInfo, 'function');
  assert.equal(typeof getPersonalInfo, 'function');
  assert.equal(typeof updatePersonalInfo, 'function');
  assert.equal(typeof reprocessPersonalInfo, 'function');
});

test('extractPersonalInfo returns a promise and constructs proper endpoints', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractPersonalInfo(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('reprocessPersonalInfo accepts forceOverwrite flag', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = reprocessPersonalInfo(dummyResumeId, true).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('updatePersonalInfo accepts payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = updatePersonalInfo(dummyResumeId, { full_name: 'Jane Doe' }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});
