import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeRecommendations,
  generateResumeRecommendations,
  updateRecommendationStatus,
} from '../src/services/recommendationService.js';
import {
  getResumeRecommendations as getFromResumeService,
  generateResumeRecommendations as generateFromResumeService,
  updateRecommendationStatus as updateFromResumeService,
} from '../src/services/resumeService.js';

test('recommendationService exports Feature 27 recommendation operations', () => {
  assert.equal(typeof getResumeRecommendations, 'function');
  assert.equal(typeof generateResumeRecommendations, 'function');
  assert.equal(typeof updateRecommendationStatus, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof generateFromResumeService, 'function');
  assert.equal(typeof updateFromResumeService, 'function');
});

test('getResumeRecommendations throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeRecommendations('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch recommendations.',
    }
  );
});

test('generateResumeRecommendations throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await generateResumeRecommendations(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to generate recommendations.',
    }
  );
});

test('updateRecommendationStatus throws error when resumeId or recommendationId is missing', async () => {
  await assert.rejects(
    async () => {
      await updateRecommendationStatus('', 'REC-TECH-01', true);
    },
    {
      name: 'Error',
      message: 'resumeId and recommendationId are required to update status.',
    }
  );
  await assert.rejects(
    async () => {
      await updateRecommendationStatus('res-123', '', true);
    },
    {
      name: 'Error',
      message: 'resumeId and recommendationId are required to update status.',
    }
  );
});

test('getResumeRecommendations handles successful response with query params', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-rec/recommendations'));
      assert.ok(url.includes('category=technical_skills'));
      assert.ok(url.includes('priority=High'));
      assert.ok(url.includes('is_completed=false'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-rec',
            total_recommendations_count: 8,
            completed_count: 2,
            pending_count: 6,
            completion_percentage: 25.0,
            recommendations: [
              {
                id: 'REC-TECH-01',
                title: 'Organize Technical Skills',
                category: 'technical_skills',
                priority: 'High',
                is_completed: false,
              },
            ],
          },
        }),
      };
    };

    const res = await getResumeRecommendations('test-uuid-rec', {
      category: 'technical_skills',
      priority: 'High',
      isCompleted: false,
    });

    assert.equal(res.success, true);
    assert.equal(res.data.resume_id, 'test-uuid-rec');
    assert.equal(res.data.total_recommendations_count, 8);
    assert.equal(res.data.completion_percentage, 25.0);
    assert.equal(res.data.recommendations[0].id, 'REC-TECH-01');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('generateResumeRecommendations handles forceRecalculate query', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-rec/recommendations/generate?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Generated successfully',
          data: {
            resume_id: 'test-uuid-rec',
            total_recommendations_count: 8,
            completed_count: 0,
            completion_percentage: 0.0,
          },
        }),
      };
    };

    const res = await generateResumeRecommendations('test-uuid-rec', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.total_recommendations_count, 8);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('updateRecommendationStatus sends PATCH with is_completed flag', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-rec/recommendations/REC-TECH-01/status'));
      assert.equal(options.method, 'PATCH');
      const body = JSON.parse(options.body);
      assert.equal(body.is_completed, true);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: "Recommendation 'REC-TECH-01' marked as completed.",
          data: {
            updated_item: {
              id: 'REC-TECH-01',
              is_completed: true,
              completed_at: '2026-11-21T12:00:00Z',
            },
            completed_count: 1,
            completion_percentage: 12.5,
          },
        }),
      };
    };

    const res = await updateRecommendationStatus('test-uuid-rec', 'REC-TECH-01', true);
    assert.equal(res.success, true);
    assert.equal(res.data.updated_item.is_completed, true);
    assert.equal(res.data.completed_count, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
