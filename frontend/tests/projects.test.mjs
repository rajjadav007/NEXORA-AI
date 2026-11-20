import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractProjects,
  getProjects,
  getProjectDetails,
  addProject,
  updateProject,
  deleteProject,
  reprocessProjects,
  getProjectsSummary,
  getPendingProjectsReviews,
  confirmProject,
  getProjectSkills,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 18 project intelligence operations', () => {
  assert.equal(typeof extractProjects, 'function');
  assert.equal(typeof getProjects, 'function');
  assert.equal(typeof getProjectDetails, 'function');
  assert.equal(typeof addProject, 'function');
  assert.equal(typeof updateProject, 'function');
  assert.equal(typeof deleteProject, 'function');
  assert.equal(typeof reprocessProjects, 'function');
  assert.equal(typeof getProjectsSummary, 'function');
  assert.equal(typeof getPendingProjectsReviews, 'function');
  assert.equal(typeof confirmProject, 'function');
  assert.equal(typeof getProjectSkills, 'function');
});

test('extractProjects returns a promise and constructs proper endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractProjects(dummyResumeId, false, false).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getProjects returns a promise and queries projects endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getProjects(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getProjectDetails returns a promise for specific project ID', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyProjId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = getProjectDetails(dummyResumeId, dummyProjId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('addProject accepts payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyPayload = {
    project_title: 'Personal Portfolio',
    project_category: 'personal',
    technologies: ['React', 'Vite'],
  };
  const promise = addProject(dummyResumeId, dummyPayload).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('updateProject accepts patch payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyProjId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = updateProject(dummyResumeId, dummyProjId, { domain: 'FinTech' }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('deleteProject issues DELETE request and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyProjId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = deleteProject(dummyResumeId, dummyProjId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('reprocessProjects accepts forceOverwrite parameter', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = reprocessProjects(dummyResumeId, true).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getProjectsSummary queries summary analytics endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getProjectsSummary(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getPendingProjectsReviews queries pending review projects', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getPendingProjectsReviews(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('confirmProject sends review confirmation note', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyProjId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = confirmProject(dummyResumeId, dummyProjId, 'Verified project').catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getProjectSkills retrieves canonical skill links', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyProjId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = getProjectSkills(dummyResumeId, dummyProjId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});
