import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getResumeGrammar,
  analyzeResumeGrammar,
} from '../src/services/grammarService.js';
import {
  getResumeGrammar as getFromResumeService,
  analyzeResumeGrammar as analyzeFromResumeService,
} from '../src/services/resumeService.js';

test('grammarService exports Feature 25 grammar analysis operations', () => {
  assert.equal(typeof getResumeGrammar, 'function');
  assert.equal(typeof analyzeResumeGrammar, 'function');
  assert.equal(typeof getFromResumeService, 'function');
  assert.equal(typeof analyzeFromResumeService, 'function');
});

test('getResumeGrammar throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await getResumeGrammar('');
    },
    {
      name: 'Error',
      message: 'resumeId is required to fetch grammar analysis.',
    }
  );
});

test('analyzeResumeGrammar throws error when resumeId is missing', async () => {
  await assert.rejects(
    async () => {
      await analyzeResumeGrammar(null);
    },
    {
      name: 'Error',
      message: 'resumeId is required to analyze resume grammar.',
    }
  );
});

test('getResumeGrammar handles successful response', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      assert.ok(url.includes('/resumes/test-uuid-grammar/grammar'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: 'Retrieved',
          data: {
            resume_id: 'test-uuid-grammar',
            writing_score: 88,
            writing_grade: 'Professional',
            overall_assessment: 'Strong technical diction with minor passive verb usage.',
            readability_metrics: {
              readability_score: 62.5,
              grade_level: 'Professional (Grade 10-12)',
              avg_words_per_sentence: 14.2,
              total_words: 340,
              complexity_assessment: 'Optimal standard for technical resumes.',
            },
            category_counts: {
              grammar: 1,
              spelling: 0,
              clarity: 2,
              tone: 1,
            },
            issues: [
              {
                id: 'grammar_issue_1',
                category: 'tone',
                category_name: 'Professional Tone',
                original_text: 'I am a passionate developer who likes building things',
                suggested_text: 'Full Stack Developer with expertise in web architecture',
                explanation: 'Avoid first-person pronouns; frame directly around professional title.',
                severity: 'High',
                section: 'Summary',
              },
            ],
            sentence_comparisons: [
              {
                original_sentence: 'Responsible for maintaining backend APIs.',
                improved_sentence: 'Maintained and scaled high-availability backend APIs.',
                reason: 'Replaces passive duty construction with authoritative action verb.',
                section: 'Experience',
              },
            ],
          },
        }),
      };
    };

    const res = await getResumeGrammar('test-uuid-grammar');
    assert.equal(res.success, true);
    assert.equal(res.data.writing_score, 88);
    assert.equal(res.data.writing_grade, 'Professional');
    assert.equal(res.data.issues[0].severity, 'High');
    assert.equal(res.data.sentence_comparisons.length, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeResumeGrammar includes force_recalculate query param when specified', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.includes('/resumes/test-uuid-999/grammar/analyze?force_recalculate=true'));
      assert.equal(options.method, 'POST');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            resume_id: 'test-uuid-999',
            writing_score: 92,
          },
        }),
      };
    };

    const res = await analyzeResumeGrammar('test-uuid-999', { forceRecalculate: true });
    assert.equal(res.success, true);
    assert.equal(res.data.writing_score, 92);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
