import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  generateResumeReport,
  getResumeReportHistory,
  getLatestResumeReport,
  getResumeReportById,
  exportResumeReportPdf,
} from '../src/services/reportService.js';

describe('reportService - Feature 31 AI Resume Report & Feature 32 PDF Export', () => {
  it('exports all report service functions', () => {
    assert.strictEqual(typeof generateResumeReport, 'function');
    assert.strictEqual(typeof getResumeReportHistory, 'function');
    assert.strictEqual(typeof getLatestResumeReport, 'function');
    assert.strictEqual(typeof getResumeReportById, 'function');
    assert.strictEqual(typeof exportResumeReportPdf, 'function');
  });

  it('generateResumeReport throws error when resumeId is missing', async () => {
    await assert.rejects(
      async () => {
        await generateResumeReport(null);
      },
      {
        message: 'resumeId is required to generate report.',
      }
    );
  });

  it('generateResumeReport sends POST request and parses query flags', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';
    let methodCalled = '';

    const mockResponse = {
      success: true,
      message: 'AI Resume Report generated successfully',
      data: {
        report_id: 'report-123',
        resume_id: 'resume-abc',
        status: 'COMPLETED',
        model: 'gemma4:12b',
        sections: {
          executive_summary: { overall_assessment: 'Strong profile.' },
        },
      },
    };

    global.fetch = async (url, opts) => {
      requestedUrl = url;
      methodCalled = opts.method;
      return {
        ok: true,
        json: async () => mockResponse,
      };
    };

    try {
      const res = await generateResumeReport('resume-abc', {
        forceRecalculate: true,
        fallbackToDeterministic: true,
      });

      assert.strictEqual(methodCalled, 'POST');
      assert(requestedUrl.includes('/resumes/resume-abc/reports/generate'));
      assert(requestedUrl.includes('force_recalculate=true'));
      assert(requestedUrl.includes('fallback_to_deterministic=true'));
      assert.strictEqual(res.success, true);
      assert.strictEqual(res.data.report_id, 'report-123');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('generateResumeReport properly propagates 503 Ollama unavailable error', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Ollama LLM service is unavailable at http://localhost:11434.' }),
    });

    try {
      await assert.rejects(
        async () => {
          await generateResumeReport('resume-abc');
        },
        (err) => {
          assert.strictEqual(err.status, 503);
          assert(err.message.includes('unavailable'));
          return true;
        }
      );
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getResumeReportHistory retrieves report history list', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';

    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: [{ report_id: 'rep-1', model: 'gemma4:12b' }],
        }),
      };
    };

    try {
      const res = await getResumeReportHistory('resume-xyz');
      assert(requestedUrl.includes('/resumes/resume-xyz/reports'));
      assert.strictEqual(res.data.length, 1);
      assert.strictEqual(res.data[0].report_id, 'rep-1');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getLatestResumeReport queries latest report endpoint', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';

    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: { report_id: 'latest-rep', status: 'COMPLETED' },
        }),
      };
    };

    try {
      const res = await getLatestResumeReport('resume-xyz');
      assert(requestedUrl.includes('/resumes/resume-xyz/reports/latest'));
      assert.strictEqual(res.data.report_id, 'latest-rep');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('getResumeReportById throws when reportId is missing', async () => {
    await assert.rejects(
      async () => {
        await getResumeReportById('resume-xyz', null);
      },
      {
        message: 'resumeId and reportId are required to fetch report.',
      }
    );
  });

  it('exportResumeReportPdf throws when resumeId or reportId is missing', async () => {
    await assert.rejects(
      async () => {
        await exportResumeReportPdf(null, 'report-123');
      },
      {
        message: 'resumeId is required to export report PDF.',
      }
    );

    await assert.rejects(
      async () => {
        await exportResumeReportPdf('resume-xyz', null);
      },
      {
        message: 'reportId is required to export report PDF.',
      }
    );
  });

  it('exportResumeReportPdf fetches PDF stream and parses Content-Disposition filename', async () => {
    const originalFetch = global.fetch;
    let requestedUrl = '';

    global.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        headers: {
          get: (headerName) => {
            if (headerName.toLowerCase() === 'content-disposition') {
              return 'attachment; filename="Nexora_AI_Resume_Report_custom_marcus_12345678.pdf"';
            }
            return null;
          },
        },
        blob: async () => new Blob(['%PDF-1.4 test'], { type: 'application/pdf' }),
      };
    };

    try {
      const res = await exportResumeReportPdf('resume-xyz', 'report-12345678');
      assert(requestedUrl.includes('/resumes/resume-xyz/reports/report-12345678/pdf'));
      assert.strictEqual(res.filename, 'Nexora_AI_Resume_Report_custom_marcus_12345678.pdf');
      assert(res.blob instanceof Blob);
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('exportResumeReportPdf throws descriptive error on server failure', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Report with ID report-999 not found.' }),
    });

    try {
      await assert.rejects(
        async () => {
          await exportResumeReportPdf('resume-xyz', 'report-999');
        },
        (err) => {
          assert.strictEqual(err.status, 404);
          assert(err.message.includes('not found'));
          return true;
        }
      );
    } finally {
      global.fetch = originalFetch;
    }
  });
});
