import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeQualityScore,
  analyzeResumeQualityScore,
} from '../src/services/qualityScoreService.js';
import {
  getResumeQualityScore as getFromResumeService,
  analyzeResumeQualityScore as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('qualityScoreService exports Feature 21 quality score operations', () => {
  assert.equal(typeof getResumeQualityScore, 'function');
  assert.equal(typeof analyzeResumeQualityScore, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeQualityScore throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeQualityScore('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch quality score.',
    }
  );
});

test('analyzeResumeQualityScore throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeQualityScore(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze quality score.',
    }
  );
});

test('getResumeQualityScore handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-123/quality-score'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-123',
            overall_score: 87.5,
            rating_level: 'Strong',
            category_scores: {
              completeness: { score: 14.0, max_score: 15.0, weight_percentage: 15.0 },
            },
          },
        }),
      };
    };

    const res = await getResumeQualityScore('test-uuid-123');
    assert.equal(res.success, true);
    assert.equal(res.data.overall_score, 87.5);
    assert.equal(res.data.rating_level, 'Strong');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeQualityScore includes force_recalculate query param when specified', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-456/quality-score/analyze?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            resume_id: 'test-uuid-456',
            overall_score: 92.0,
            rating_level: 'Exceptional',
          },
        }),
      };
    };

    const res = await analyzeResumeQualityScore('test-uuid-456', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.overall_score, 92.0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeQualityScore handles 503 service unavailable error from Ollama', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 503,
      json: async () => ({
        detail: 'Ollama LLM service is unavailable at http://localhost:11434.',
      }),
    });

    await assert.rejects(
      async () => {
        await analyzeResumeQualityScore('test-uuid-789');
      },
      (err) => {
        assert.equal(err.status, 503);
        assert.ok(err.message.includes('unavailable'));
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
