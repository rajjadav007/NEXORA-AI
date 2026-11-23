import test from 'node:test';
import assert from 'node:assert/strict';
import { getResumeAnalyticsDashboard } from '../src/services/analyticsService.js';
import { getResumeAnalyticsDashboard as getFromResumeService } from '../src/services/resumeService.js';

test('analyticsService exports Feature 28 dashboard operations', () => {
  assert.equal(typeof getResumeAnalyticsDashboard, 'function');
  assert.equal(typeof getFromResumeService, 'function');
});

test('getResumeAnalyticsDashboard throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeAnalyticsDashboard('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch analytics dashboard.',
    }
  );

  await assert.rejects(
    async () => {
      await getResumeAnalyticsDashboard(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch analytics dashboard.',
    }
  );
});

test('getResumeAnalyticsDashboard handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.match(url, /\/resumes\/resume-uuid-123\/analytics\/dashboard$/);
    return {
      ok: true,
      json: async () => ({
        success: true,
        message: 'Resume analytics dashboard retrieved successfully',
        data: {
          resume_id: 'resume-uuid-123',
          resume_header: {
            filename: 'test.pdf',
            analysis_status: 'COMPLETE',
            coverage_count: 6,
          },
          summary_cards: {
            quality_score: { score: 85.0, available: true },
            ats_compatibility: { score: 90, available: true },
            readability: { score: 88.0, available: true },
            content_completeness: { score: 95.0, available: true },
          },
          visual_analytics: {
            quality_category_breakdown: [],
            score_distribution: [],
          },
          resume_insights: {
            key_strengths: [],
            important_weaknesses: [],
          },
        },
      }),
    };
  };

  try {
    const res = await getResumeAnalyticsDashboard('resume-uuid-123');
    assert.equal(res.success, true);
    assert.equal(res.data.resume_id, 'resume-uuid-123');
    assert.equal(res.data.summary_cards.quality_score.score, 85.0);
    assert.equal(res.data.resume_header.analysis_status, 'COMPLETE');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getResumeAnalyticsDashboard throws when server returns error', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 404,
    json: async () => ({ detail: 'Resume not found' }),
  });

  try {
    await assert.rejects(
      async () => {
        await getResumeAnalyticsDashboard('missing-id');
      },
      (err) => {
        assert.equal(err.message, 'Resume not found');
        assert.equal(err.status, 404);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
