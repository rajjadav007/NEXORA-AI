import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  getResumeAnalyticsDashboard,
  getResumeSkillDistribution,
} from '../src/services/analyticsService.js';

describe('analyticsService - Feature 29 Skill Distribution', () => {
  it('analyticsService exports getResumeSkillDistribution function', () => {
    assert.strictEqual(typeof getResumeSkillDistribution, 'function');
  });

  it('getResumeSkillDistribution throws error when resumeId is missing', async () => {
    await assert.rejects(
      async () => {
        await getResumeSkillDistribution(null);
      },
      {
        message: 'resumeId is required to fetch skill distribution.',
      }
    );
  });

  it('getResumeSkillDistribution handles successful response', async () => {
    const originalFetch = global.fetch;
    const mockData = {
      success: true,
      data: {
        resume_id: 'test-uuid',
        total_skills: 8,
        categories: [
          { name: 'Programming Languages', count: 3, skills: ['Python', 'SQL', 'TypeScript'] },
          { name: 'Databases', count: 2, skills: ['PostgreSQL', 'Redis'] },
        ],
        summary: {
          total_skills: 8,
          total_categories: 2,
          most_populated_category: { name: 'Programming Languages', count: 3 },
          uncategorized_skills: [],
        },
      },
    };

    global.fetch = async (url) => {
      assert(url.includes('/resumes/test-uuid/analytics/skills'));
      return {
        ok: true,
        json: async () => mockData,
      };
    };

    try {
      const res = await getResumeSkillDistribution('test-uuid');
      assert.strictEqual(res.success, true);
      assert.strictEqual(res.data.total_skills, 8);
      assert.strictEqual(res.data.categories.length, 2);
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getResumeSkillDistribution throws when server returns error', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Resume not found' }),
    });

    try {
      await assert.rejects(
        async () => {
          await getResumeSkillDistribution('missing-uuid');
        },
        (err) => {
          assert.strictEqual(err.status, 404);
          assert(err.message.includes('Resume not found'));
          return true;
        }
      );
    } finally {
      global.fetch = originalFetch;
    }
  });
});
