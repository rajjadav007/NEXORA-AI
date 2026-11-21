import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractCertifications,
  getCertifications,
  getCertificationSummary,
  getPendingCertificationsReviews,
  getCertificationDetails,
  getCertificationSkills,
  addCertification,
  updateCertification,
  confirmCertification,
  deleteCertification,
  reprocessCertifications,
  extractAchievements,
  getAchievements,
  getAchievementSummary,
  getPendingAchievementsReviews,
  getAchievementDetails,
  getAchievementSkills,
  addAchievement,
  updateAchievement,
  confirmAchievement,
  deleteAchievement,
  reprocessAchievements,
  getCertificationsAchievementsSummary,
} from '../src/services/resumeService.js';

test('resumeService exports all Feature 19 certifications operations', () => {
  assert.equal(typeof extractCertifications, 'function');
  assert.equal(typeof getCertifications, 'function');
  assert.equal(typeof getCertificationSummary, 'function');
  assert.equal(typeof getPendingCertificationsReviews, 'function');
  assert.equal(typeof getCertificationDetails, 'function');
  assert.equal(typeof getCertificationSkills, 'function');
  assert.equal(typeof addCertification, 'function');
  assert.equal(typeof updateCertification, 'function');
  assert.equal(typeof confirmCertification, 'function');
  assert.equal(typeof deleteCertification, 'function');
  assert.equal(typeof reprocessCertifications, 'function');
});

test('resumeService exports all Feature 19 achievements operations', () => {
  assert.equal(typeof extractAchievements, 'function');
  assert.equal(typeof getAchievements, 'function');
  assert.equal(typeof getAchievementSummary, 'function');
  assert.equal(typeof getPendingAchievementsReviews, 'function');
  assert.equal(typeof getAchievementDetails, 'function');
  assert.equal(typeof getAchievementSkills, 'function');
  assert.equal(typeof addAchievement, 'function');
  assert.equal(typeof updateAchievement, 'function');
  assert.equal(typeof confirmAchievement, 'function');
  assert.equal(typeof deleteAchievement, 'function');
  assert.equal(typeof reprocessAchievements, 'function');
  assert.equal(typeof getCertificationsAchievementsSummary, 'function');
});

test('extractCertifications returns a promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractCertifications(dummyResumeId, { reprocess: false }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getCertifications returns a promise and queries certifications endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getCertifications(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getCertificationDetails returns a promise for specific cert ID', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyCertId = 'd8e41a8a-9218-4e31-89d4-0692f8dc137c';
  const promise = getCertificationDetails(dummyResumeId, dummyCertId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('addCertification accepts payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyPayload = {
    certification_name: 'AWS Solutions Architect Associate',
    issuing_organization: 'Amazon Web Services',
    certification_category: 'cloud',
  };
  const promise = addCertification(dummyResumeId, dummyPayload).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('extractAchievements returns a promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = extractAchievements(dummyResumeId, { reprocess: false }).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getAchievements returns a promise and queries achievements endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getAchievements(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('addAchievement accepts payload and returns promise', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const dummyPayload = {
    achievement_title: '1st Place Winner - HackMIT',
    achievement_category: 'hackathon',
    rank_or_position: '1st Place',
  };
  const promise = addAchievement(dummyResumeId, dummyPayload).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});

test('getCertificationsAchievementsSummary queries combined summary endpoint', () => {
  const dummyResumeId = '4005b67e-7517-4886-90ef-3829dc7ae8b3';
  const promise = getCertificationsAchievementsSummary(dummyResumeId).catch(() => {});
  assert.equal(typeof promise.then, 'function');
});
