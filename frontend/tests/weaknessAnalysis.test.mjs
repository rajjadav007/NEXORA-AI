import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeWeaknesses,
  analyzeResumeWeaknesses,
} from '../src/services/weaknessService.js';
import {
  getResumeWeaknesses as getFromResumeService,
  analyzeResumeWeaknesses as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('weaknessService exports Feature 23 weakness analysis operations', () => {
  assert.equal(typeof getResumeWeaknesses, 'function');
  assert.equal(typeof analyzeResumeWeaknesses, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeWeaknesses throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeWeaknesses('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch weakness analysis.',
    }
  );
});

test('analyzeResumeWeaknesses throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeWeaknesses(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze resume weaknesses.',
    }
  );
});

test('getResumeWeaknesses handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-weakness/weaknesses'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-weakness',
            total_weaknesses_count: 2,
            priority_breakdown: {
              critical: 1,
              high: 1,
              medium: 0,
              low: 0,
            },
            overall_summary: 'Lacks measurable business metrics in work experience and projects.',
            weaknesses: [
              {
                title: 'Passive Duty Descriptions Without Quantified Impact',
                category: 'experience',
                category_name: 'Work & Internship Experience',
                explanation: 'Bullet points list responsibilities rather than achievements.',
                evidence: ['Responsible for bug fixes and testing'],
                why_it_matters: 'Hiring managers cannot evaluate impact without numbers.',
                suggested_improvement: 'Rewrite with measurable numbers and technologies.',
                priority: 'Critical',
                relevance_rank: 1,
                weakness_type: 'lacks_measurable_impact',
              },
            ],
            missing_information: [
              {
                section: 'Education',
                item: 'Graduation Year',
                relevance: 'Shows timeline',
                impact_level: 'High',
                is_optional: false,
              },
            ],
          },
        }),
      };
    };

    const res = await getResumeWeaknesses('test-uuid-weakness');
    assert.equal(res.success, true);
    assert.equal(res.data.total_weaknesses_count, 2);
    assert.equal(res.data.priority_breakdown.critical, 1);
    assert.equal(res.data.weaknesses[0].priority, 'Critical');
    assert.equal(res.data.missing_information[0].is_optional, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeWeaknesses includes force_recalculate query param when specified', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-456/weaknesses/analyze?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            resume_id: 'test-uuid-456',
            total_weaknesses_count: 1,
          },
        }),
      };
    };

    const res = await analyzeResumeWeaknesses('test-uuid-456', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.total_weaknesses_count, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeWeaknesses handles 503 service unavailable error from Ollama', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 503,
      json: async () => ({
        detail: 'Ollama LLM service is unavailable at http://localhost:11434. Please ensure Ollama is running.',
      }),
    });

    await assert.rejects(
      async () => {
        await analyzeResumeWeaknesses('test-resume-123');
      },
      (err) => {
        assert.equal(err.status, 503);
        assert.ok(err.message.includes('Ollama LLM service is unavailable'));
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
