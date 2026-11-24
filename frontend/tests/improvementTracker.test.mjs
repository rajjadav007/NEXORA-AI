import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  getResumeImprovements,
  getResumeImprovementHistory,
  getResumeImprovementTasks,
  updateResumeImprovementTask,
  compareResumeVersions,
} from '../src/services/improvementService.js';

describe('improvementService - Feature 30 Resume Improvement Tracker', () => {
  it('exports all Feature 30 service functions', () => {
    assert.strictEqual(typeof getResumeImprovements, 'function');
    assert.strictEqual(typeof getResumeImprovementHistory, 'function');
    assert.strictEqual(typeof getResumeImprovementTasks, 'function');
    assert.strictEqual(typeof updateResumeImprovementTask, 'function');
    assert.strictEqual(typeof compareResumeVersions, 'function');
  });

  it('getResumeImprovements throws error when resumeId is missing', async () => {
    await assert.rejects(
      async () => {
        await getResumeImprovements(null);
      },
      {
        message: 'resumeId is required to fetch improvement tracking data.',
      }
    );
  });

  it('getResumeImprovements handles successful response', async () => {
    const originalFetch = global.fetch;
    const mockData = {
      success: true,
      data: {
        resume_id: 'test-resume-123',
        filename: 'resume.pdf',
        score_comparison: {
          overall_score: { previous_score: 70, latest_score: 85, delta: 15, status: 'improved' },
        },
        progress_overview: {
          total_tasks: 4,
          completed_tasks: 2,
          completion_percentage: 50.0,
        },
        tasks: [],
        timeline: [],
      },
    };

    global.fetch = async (url) => {
      assert(url.includes('/resumes/test-resume-123/improvements'));
      return {
        ok: true,
        json: async () => mockData,
      };
    };

    try {
      const res = await getResumeImprovements('test-resume-123');
      assert.strictEqual(res.success, true);
      assert.strictEqual(res.data.resume_id, 'test-resume-123');
      assert.strictEqual(res.data.progress_overview.completion_percentage, 50.0);
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getResumeImprovementHistory calls history endpoint and handles error', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'History not found' }),
    });

    try {
      await assert.rejects(
        async () => {
          await getResumeImprovementHistory('missing-id');
        },
        (err) => {
          assert.strictEqual(err.status, 404);
          assert(err.message.includes('History not found'));
          return true;
        }
      );
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getResumeImprovementTasks passes status and priority filters properly', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';

    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: { tasks: [], progress: { total_tasks: 0, completed_tasks: 0, completion_percentage: 0 } },
        }),
      };
    };

    try {
      await getResumeImprovementTasks('test-id', { status: 'Completed', priority: 'High' });
      assert(requestedUrl.includes('/resumes/test-id/improvements/tasks'));
      assert(requestedUrl.includes('status=Completed'));
      assert(requestedUrl.includes('priority=High'));
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('updateResumeImprovementTask sends PATCH with payload', async () => {
    const originalFetch = global.fetch;
    let methodCalled = '';
    let bodySent = null;

    global.fetch = async (url, options) => {
      methodCalled = options.method;
      bodySent = JSON.parse(options.body);
      assert(url.includes('/resumes/test-id/improvements/tasks/task-99'));
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: { id: 'task-99', status: 'Completed' },
        }),
      };
    };

    try {
      const res = await updateResumeImprovementTask('test-id', 'task-99', { status: 'Completed' });
      assert.strictEqual(methodCalled, 'PATCH');
      assert.strictEqual(bodySent.status, 'Completed');
      assert.strictEqual(res.data.status, 'Completed');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('compareResumeVersions properly appends v1 and v2 query parameters', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';

    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: {
            version_1: { version_number: 1 },
            version_2: { version_number: 2 },
            score_comparison: {},
          },
        }),
      };
    };

    try {
      const res = await compareResumeVersions('test-id', 1, 2);
      assert(requestedUrl.includes('/resumes/test-id/improvements/compare?v1=1&v2=2'));
      assert.strictEqual(res.data.version_1.version_number, 1);
      assert.strictEqual(res.data.version_2.version_number, 2);
    } finally {
      global.fetch = originalFetch;
    }
  });
});
