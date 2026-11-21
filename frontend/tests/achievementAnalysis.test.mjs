import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeAchievements,
  analyzeResumeAchievements,
} from '../src/services/achievementService.js';
import {
  getResumeAchievements as getFromResumeService,
  analyzeResumeAchievements as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('achievementService exports Feature 26 achievement analysis operations', () => {
  assert.equal(typeof getResumeAchievements, 'function');
  assert.equal(typeof analyzeResumeAchievements, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeAchievements throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeAchievements('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch achievement analysis.',
    }
  );
});

test('analyzeResumeAchievements throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeAchievements(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze resume achievements.',
    }
  );
});

test('getResumeAchievements handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-achieve/achievements/analysis'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-achieve',
            achievement_score: 85,
            score_grade: 'Exceptional',
            executive_summary: 'Strong quantifiable track record with verified metrics.',
            total_achievements_count: 5,
            quantified_count: 4,
            unquantified_count: 1,
            quantification_rate: 80.0,
            category_breakdown: {
              experience: {
                category_key: 'experience',
                category_name: 'Work & Internship Experience',
                total_count: 3,
                quantified_count: 3,
                unquantified_count: 0,
                top_highlight: 'Reduced latency by 42%.',
              },
            },
            rubric_breakdown: {
              quantification_rate_score: 28.0,
              impact_magnitude_score: 22.0,
              cross_category_diversity_score: 12.0,
              action_clarity_score: 13.0,
              metric_verification_fidelity_score: 10.0,
              total_score: 85,
            },
            achievements: [
              {
                id: 'achieve_1',
                title: 'Latency Reduction',
                category: 'experience',
                category_name: 'Work & Internship Experience',
                original_statement: 'Reduced API latency by 42% via Redis caching.',
                is_quantified: true,
                measurable_metrics: {
                  percentages: ['42%'],
                  numbers: [],
                  time_saved: ['42% faster'],
                  users_impacted: [],
                  performance_gain: ['latency reduced by 42%'],
                },
                has_verified_metrics: true,
                evidence: ['Reduced API latency by 42%'],
                impact_level: 'High',
                professional_relevance: 'High',
                quality_rating: 'Strong',
                suggested_statement: 'Reduced API response latency by 42% by designing and deploying a multi-tier Redis caching layer.',
                explanation: 'Excellent quantifiable outcome demonstrating backend optimization.',
              },
            ],
          },
        }),
      };
    };

    const res = await getResumeAchievements('test-uuid-achieve');
    assert.equal(res.success, true);
    assert.equal(res.data.achievement_score, 85);
    assert.equal(res.data.score_grade, 'Exceptional');
    assert.equal(res.data.total_achievements_count, 5);
    assert.equal(res.data.quantified_count, 4);
    assert.equal(res.data.achievements[0].is_quantified, true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeAchievements passes forceRecalculate parameter properly', async () => {
  const originalFetch = globalThis.fetch;
  try {
    let capturedUrl = '';
    let capturedMethod = '';

    globalThis.fetch = async (url, options) => {
      capturedUrl = url;
      capturedMethod = options?.method;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Analysis generated',
          data: {
            achievement_score: 90,
            score_grade: 'Exceptional',
            total_achievements_count: 3,
            quantified_count: 3,
            unquantified_count: 0,
            quantification_rate: 100.0,
          },
        }),
      };
    };

    const res = await analyzeResumeAchievements('uuid-123', { forceRecalculate: true });
    assert.ok(capturedUrl.includes('/resumes/uuid-123/achievements/analyze?force_recalculate=true'));
    assert.equal(capturedMethod, 'POST');
    assert.equal(res.data.achievement_score, 90);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getResumeAchievements throws when server returns error', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'No achievement analysis found.' }),
    });

    await assert.rejects(
      async () => {
        await getResumeAchievements('missing-id');
      },
      (err) => {
        assert.equal(err.status, 404);
        assert.match(err.message, /No achievement analysis found/);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
