import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeStrengths,
  analyzeResumeStrengths,
} from '../src/services/strengthService.js';
import {
  getResumeStrengths as getFromResumeService,
  analyzeResumeStrengths as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('strengthService exports Feature 22 strength analysis operations', () => {
  assert.equal(typeof getResumeStrengths, 'function');
  assert.equal(typeof analyzeResumeStrengths, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeStrengths throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeStrengths('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch strength analysis.',
    }
  );
});

test('analyzeResumeStrengths throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeStrengths(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze resume strengths.',
    }
  );
});

test('getResumeStrengths handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-123/strengths'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-123',
            executive_summary: 'Demonstrates strong cloud architectures and modern engineering skills.',
            strengths_count: 3,
            demonstrated_count: 2,
            potential_count: 1,
            is_sufficient_evidence: true,
            strengths: [
              {
                title: 'Full-Stack Distributed Systems',
                category: 'technical_skills',
                strength_type: 'demonstrated',
                confidence_level: 'High',
                relevance_rank: 1,
                explanation: 'Extensive hands-on experience designing cloud architectures.',
                evidence: 'Led microservices migration scaling to 1M daily active users.',
                professional_value: 'Directly applicable to senior infrastructure roles.',
              },
            ],
          },
        }),
      };
    };

    const res = await getResumeStrengths('test-uuid-123');
    assert.equal(res.success, true);
    assert.equal(res.data.strengths_count, 3);
    assert.equal(res.data.demonstrated_count, 2);
    assert.equal(res.data.is_sufficient_evidence, true);
    assert.equal(res.data.strengths[0].confidence_level, 'High');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeStrengths includes force_recalculate query param when specified', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-456/strengths/analyze?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            resume_id: 'test-uuid-456',
            executive_summary: 'Recalculated strengths summary.',
            strengths_count: 1,
            demonstrated_count: 1,
            potential_count: 0,
            is_sufficient_evidence: true,
          },
        }),
      };
    };

    const res = await analyzeResumeStrengths('test-uuid-456', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.strengths_count, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeStrengths handles 503 service unavailable error from Ollama', async () => {
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
        await analyzeResumeStrengths('test-uuid-789');
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
