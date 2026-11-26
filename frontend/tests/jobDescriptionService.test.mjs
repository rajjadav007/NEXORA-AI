import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  JD_MIN_LENGTH,
  JD_MAX_LENGTH,
  EMPLOYMENT_TYPES,
  validateJobUrl,
  validateJobDescriptionInput,
  importJobDescriptionFromUrl,
  createJobDescription,
  listJobDescriptions,
  getJobDescriptionById,
  deleteJobDescription,
  extractJobRoleAnalysis,
  getJobRoleAnalysis,
} from '../src/services/jobDescriptionService.js';

const VALID_DESC =
  'We are seeking a Backend Engineer to build scalable Python and FastAPI microservices and PostgreSQL schemas.';

describe('jobDescriptionService - Feature 33 Job Description Input', () => {
  it('validates empty and short job descriptions', () => {
    const emptyRes = validateJobDescriptionInput({
      job_title: 'Engineer',
      company_name: 'Acme',
      description: '   ',
    });
    assert.strictEqual(emptyRes.isValid, false);
    assert.ok(emptyRes.errors.description.includes('empty'));

    const shortRes = validateJobDescriptionInput({
      job_title: 'Engineer',
      company_name: 'Acme',
      description: 'a'.repeat(JD_MIN_LENGTH - 1),
    });
    assert.strictEqual(shortRes.isValid, false);
    assert.ok(shortRes.errors.description.includes(String(JD_MIN_LENGTH)));
  });

  it('validates maximum character limit', () => {
    const longRes = validateJobDescriptionInput({
      job_title: 'Engineer',
      company_name: 'Acme',
      description: 'a'.repeat(JD_MAX_LENGTH + 1),
    });
    assert.strictEqual(longRes.isValid, false);
    assert.ok(longRes.errors.description.includes('exceed'));
  });

  it('validates required title, company, and employment type', () => {
    const missingRes = validateJobDescriptionInput({
      job_title: '',
      company_name: 'A',
      description: VALID_DESC,
      employment_type: 'InvalidType',
    });
    assert.strictEqual(missingRes.isValid, false);
    assert.ok(missingRes.errors.job_title);
    assert.ok(missingRes.errors.company_name);
    assert.ok(missingRes.errors.employment_type);
  });

  it('accepts valid input with missing optional fields', () => {
    const res = validateJobDescriptionInput({
      job_title: '  AI Engineer  ',
      company_name: '  Nexora  ',
      description: `  ${VALID_DESC}  `,
      location: '   ',
      employment_type: '',
    });
    assert.strictEqual(res.isValid, true);
    assert.strictEqual(res.normalized.job_title, 'AI Engineer');
    assert.strictEqual(res.normalized.company_name, 'Nexora');
    assert.strictEqual(res.normalized.location, null);
    assert.strictEqual(res.normalized.employment_type, null);
    assert.ok(EMPLOYMENT_TYPES.includes('Full-time'));
  });

  it('createJobDescription rejects invalid input without calling fetch', async () => {
    const originalFetch = global.fetch;
    let called = false;
    global.fetch = async () => {
      called = true;
      return { ok: true, json: async () => ({}) };
    };

    try {
      await assert.rejects(
        () =>
          createJobDescription({
            job_title: 'Engineer',
            company_name: 'Acme',
            description: 'too short',
          }),
        /at least 50 characters/
      );
      assert.strictEqual(called, false);
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('createJobDescription sends POST with X-User-Id and handles 409 duplicate', async () => {
    const originalFetch = global.fetch;
    let captured = null;

    global.fetch = async (url, opts) => {
      captured = { url, opts };
      return {
        ok: true,
        json: async () => ({
          success: true,
          message: 'Job description saved successfully.',
          data: { id: 'jd-1', job_title: 'Backend Engineer' },
        }),
      };
    };

    try {
      const res = await createJobDescription(
        {
          job_title: 'Backend Engineer',
          company_name: 'Nexora',
          description: VALID_DESC,
          location: 'Remote',
          employment_type: 'Full-time',
        },
        '11111111-1111-4111-8111-111111111111'
      );
      assert.strictEqual(res.success, true);
      assert.strictEqual(captured.opts.method, 'POST');
      assert.ok(captured.url.endsWith('/job-descriptions'));
      assert.strictEqual(
        captured.opts.headers['X-User-Id'],
        '11111111-1111-4111-8111-111111111111'
      );

      global.fetch = async () => ({
        ok: false,
        status: 409,
        json: async () => ({ detail: 'Duplicate submission: this job description has already been saved.' }),
      });

      await assert.rejects(
        () =>
          createJobDescription({
            job_title: 'Backend Engineer',
            company_name: 'Nexora',
            description: VALID_DESC,
          }),
        (err) => err.status === 409 && /duplicate/i.test(err.message)
      );
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('list, get, and delete send X-User-Id and validate IDs', async () => {
    const originalFetch = global.fetch;
    const calls = [];
    global.fetch = async (url, opts) => {
      calls.push({ url, method: opts.method, headers: opts.headers });
      return { ok: true, json: async () => ({ success: true, data: [] }) };
    };

    try {
      await listJobDescriptions('user-1');
      await getJobDescriptionById('jd-1', 'user-1');
      await deleteJobDescription('jd-1', 'user-1');

      assert.strictEqual(calls.length, 3);
      assert.strictEqual(calls[0].method, 'GET');
      assert.strictEqual(calls[1].method, 'GET');
      assert.strictEqual(calls[2].method, 'DELETE');
      assert.ok(calls.every((c) => c.headers['X-User-Id'] === 'user-1'));

      await assert.rejects(() => getJobDescriptionById(''), /required/);
      await assert.rejects(() => deleteJobDescription(''), /required/);
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('validateJobUrl and importJobDescriptionFromUrl enforce URL safety and call /import', async () => {
    assert.strictEqual(validateJobUrl('').isValid, false);
    assert.strictEqual(validateJobUrl('ftp://example.com/job').isValid, false);
    assert.strictEqual(validateJobUrl('http://localhost/job').isValid, false);
    assert.strictEqual(validateJobUrl('http://169.254.169.254/latest').isValid, false);
    assert.strictEqual(validateJobUrl('https://careers.example.com/jobs/1').isValid, true);

    const originalFetch = global.fetch;
    let calledUrl = '';
    global.fetch = async (url, opts) => {
      calledUrl = url;
      assert.strictEqual(opts.method, 'POST');
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: { job_title: 'AI Engineer', source_url: 'https://careers.example.com/jobs/1' },
        }),
      };
    };

    try {
      await assert.rejects(() => importJobDescriptionFromUrl('http://127.0.0.1/job'), /Localhost/);
      const res = await importJobDescriptionFromUrl('https://careers.example.com/jobs/1', 'user-1');
      assert.ok(calledUrl.endsWith('/job-descriptions/import'));
      assert.strictEqual(res.data.job_title, 'AI Engineer');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('extractJobRoleAnalysis and getJobRoleAnalysis call role-analysis endpoints', async () => {
    const originalFetch = global.fetch;
    const calls = [];
    global.fetch = async (url, opts) => {
      calls.push({ url, method: opts.method, headers: opts.headers });
      return {
        ok: true,
        json: async () => ({
          success: true,
          data: { standardized_role: 'AI Engineer', seniority: 'Internship', confidence_score: 0.92 },
        }),
      };
    };

    try {
      await assert.rejects(() => extractJobRoleAnalysis(''), /required/);
      await assert.rejects(() => getJobRoleAnalysis(''), /required/);

      const postRes = await extractJobRoleAnalysis('jd-123', { forceRecalculate: true, userId: 'user-1' });
      const getRes = await getJobRoleAnalysis('jd-123', 'user-1');

      assert.strictEqual(postRes.data.standardized_role, 'AI Engineer');
      assert.strictEqual(getRes.data.seniority, 'Internship');
      assert.strictEqual(calls.length, 2);
      assert.ok(calls[0].url.endsWith('/job-descriptions/jd-123/role-analysis?force_recalculate=true'));
      assert.strictEqual(calls[0].method, 'POST');
      assert.ok(calls[1].url.endsWith('/job-descriptions/jd-123/role-analysis'));
      assert.strictEqual(calls[1].method, 'GET');
      assert.ok(calls.every((c) => c.headers['X-User-Id'] === 'user-1'));
    } finally {
      global.fetch = originalFetch;
    }
  });
});
