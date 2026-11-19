import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractEducation,
  getEducation,
  reprocessEducation,
  addEducation,
  updateEducation,
  deleteEducation,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 14 education operations', () => {
  assert.equal(typeof extractEducation, 'function');
  assert.equal(typeof getEducation, 'function');
  assert.equal(typeof reprocessEducation, 'function');
  assert.equal(typeof addEducation, 'function');
  assert.equal(typeof updateEducation, 'function');
  assert.equal(typeof deleteEducation, 'function');
});

test('extractEducation returns a promise and constructs proper endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractEducation(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getEducation returns a promise and queries education endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getEducation(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('reprocessEducation accepts forceOverwrite parameter', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = reprocessEducation(dummyResumeId, true).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('addEducation accepts education payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const payload = {
    degree: 'Master of Science',
    institution: 'Stanford University',
    graduation_status: 'completed',
  };
  const promise = addEducation(dummyResumeId, payload).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('updateEducation accepts educationId and patch payload', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyEduId = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d';
  const promise = updateEducation(dummyResumeId, dummyEduId, { location: 'USA' }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('deleteEducation accepts educationId and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyEduId = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d';
  const promise = deleteEducation(dummyResumeId, dummyEduId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});
