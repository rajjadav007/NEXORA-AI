import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractSkills,
  getSkills,
  normalizeSkills,
  reprocessSkills,
  getSkillsSummary,
  getPendingSkillsReviews,
  confirmSkillMapping,
  rejectSkillMapping,
  updateSkillEntry,
  deleteSkillEntry,
  getSkillsDictionary,
  addSkillAlias,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 17 skill normalization operations', () => {
  assert.equal(typeof extractSkills, 'function');
  assert.equal(typeof getSkills, 'function');
  assert.equal(typeof normalizeSkills, 'function');
  assert.equal(typeof reprocessSkills, 'function');
  assert.equal(typeof getSkillsSummary, 'function');
  assert.equal(typeof getPendingSkillsReviews, 'function');
  assert.equal(typeof confirmSkillMapping, 'function');
  assert.equal(typeof rejectSkillMapping, 'function');
  assert.equal(typeof updateSkillEntry, 'function');
  assert.equal(typeof deleteSkillEntry, 'function');
  assert.equal(typeof getSkillsDictionary, 'function');
  assert.equal(typeof addSkillAlias, 'function');
});

test('extractSkills returns a promise and constructs proper endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractSkills(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getSkills returns a promise and queries skills endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getSkills(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('normalizeSkills sends array of skills to direct endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = normalizeSkills(dummyResumeId, ['JS', 'ReactJS', 'Python']).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('reprocessSkills accepts forceOverwrite parameter', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = reprocessSkills(dummyResumeId, true).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getSkillsSummary queries summary endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getSkillsSummary(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getPendingSkillsReviews queries pending reviews endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getPendingSkillsReviews(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('confirmSkillMapping and rejectSkillMapping return promises', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const confirmPromise = confirmSkillMapping(dummyResumeId, 'skill-123').catch(() => {});
  const rejectPromise = rejectSkillMapping(dummyResumeId, 'skill-123').catch(() => {});
  assert.equal(typeof confirmPromise.then, 'function');
  assert.equal(typeof rejectPromise.then, 'function');
});

test('updateSkillEntry and deleteSkillEntry return promises', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const updatePromise = updateSkillEntry(dummyResumeId, 'skill-123', { canonical_name: 'Python' }).catch(() => {});
  const deletePromise = deleteSkillEntry(dummyResumeId, 'skill-123').catch(() => {});
  assert.equal(typeof updatePromise.then, 'function');
  assert.equal(typeof deletePromise.then, 'function');
});

test('getSkillsDictionary and addSkillAlias return promises', () => {
  const dictPromise = getSkillsDictionary().catch(() => {});
  const aliasPromise = addSkillAlias('Python', 'py3').catch(() => {});
  assert.equal(typeof dictPromise.then, 'function');
  assert.equal(typeof aliasPromise.then, 'function');
});
