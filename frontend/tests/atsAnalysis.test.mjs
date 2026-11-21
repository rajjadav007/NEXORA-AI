import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeATS,
  analyzeResumeATS,
} from '../src/services/atsService.js';
import {
  getResumeATS as getFromResumeService,
  analyzeResumeATS as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('atsService exports Feature 24 ATS compatibility operations', () => {
  assert.equal(typeof getResumeATS, 'function');
  assert.equal(typeof analyzeResumeATS, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeATS throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeATS('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch ATS analysis.',
    }
  );
});

test('analyzeResumeATS throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeATS(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze resume ATS compatibility.',
    }
  );
});

test('getResumeATS handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-ats/ats'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-ats',
            ats_score: 85,
            score_grade: 'Excellent',
            score_interpretation: 'High probability of accurate field parsing.',
            category_scores: {
              contact_info: {
                key: 'contact_info',
                name: 'Contact Information Completeness',
                score: 15.0,
                max_score: 15.0,
                status: 'Pass',
                feedback: 'All contact details present.',
              },
            },
            verified_issues: [],
            formatting_risks: [],
            detected_sections: [
              {
                section_key: 'experience',
                section_name: 'Work Experience',
                detected: true,
                is_standard_heading: true,
                status: 'Standard',
              },
            ],
            missing_sections: [],
            keyword_findings: {
              total_detected_keywords: 12,
              top_technical_keywords: ['Python', 'FastAPI'],
              top_action_verbs: ['Engineered', 'Optimized'],
              recommended_keywords: ['Scalable'],
              keyword_density_note: 'Strong density',
            },
            ai_feedback: {
              executive_summary: 'Clean structure with high ATS readiness.',
              tailored_recommendations: [],
              keyword_optimization_advice: 'Continue incorporating metrics.',
            },
            disclaimer: 'This score is an algorithmic heuristic estimate.',
          },
        }),
      };
    };

    const res = await getResumeATS('test-uuid-ats');
    assert.equal(res.success, true);
    assert.equal(res.data.ats_score, 85);
    assert.equal(res.data.score_grade, 'Excellent');
    assert.equal(res.data.category_scores.contact_info.score, 15.0);
    assert.ok(res.data.disclaimer.includes('heuristic'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeATS includes force_recalculate query param when specified', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-789/ats/analyze?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            resume_id: 'test-uuid-789',
            ats_score: 78,
          },
        }),
      };
    };

    const res = await analyzeResumeATS('test-uuid-789', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.ats_score, 78);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
