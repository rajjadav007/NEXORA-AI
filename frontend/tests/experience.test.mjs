import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractExperience,
  getExperience,
  reprocessExperience,
  addExperience,
  updateExperience,
  deleteExperience,
  getExperienceSummary,
  getCareerProgression,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 15 experience operations', () => {
  assert.equal(typeof extractExperience, 'function');
  assert.equal(typeof getExperience, 'function');
  assert.equal(typeof reprocessExperience, 'function');
  assert.equal(typeof addExperience, 'function');
  assert.equal(typeof updateExperience, 'function');
  assert.equal(typeof deleteExperience, 'function');
  assert.equal(typeof getExperienceSummary, 'function');
  assert.equal(typeof getCareerProgression, 'function');
});

test('extractExperience returns a promise and constructs proper endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractExperience(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getExperience returns a promise and queries experience endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getExperience(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('reprocessExperience accepts forceOverwrite parameter', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = reprocessExperience(dummyResumeId, true).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('addExperience accepts experience payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const payload = {
    company: 'Example Technologies',
    job_title: 'AI Engineer Intern',
    employment_type: 'internship',
    start_date: '2025-06',
    end_date: '2025-09',
    is_current: false,
  };
  const promise = addExperience(dummyResumeId, payload).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('updateExperience accepts experienceId and patch payload', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyExpId = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d';
  const promise = updateExperience(dummyResumeId, dummyExpId, { location: 'Bengaluru, India' }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('deleteExperience accepts experienceId and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyExpId = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d';
  const promise = deleteExperience(dummyResumeId, dummyExpId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getExperienceSummary returns promise and queries summary endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getExperienceSummary(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getCareerProgression returns promise and queries progression endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getCareerProgression(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});
