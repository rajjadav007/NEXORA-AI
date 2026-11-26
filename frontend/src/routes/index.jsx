import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { RootLayout } from '../layouts/RootLayout';
import { MarketingLayout } from '../layouts/MarketingLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { RouteErrorFallback } from '../components/common/ErrorBoundary';
import { LandingPage } from '../pages/LandingPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ResumePage } from '../pages/ResumePage';
import { ResumePreviewPage } from '../pages/ResumePreviewPage';
import { ResumeAnalyticsPage } from '../pages/ResumeAnalyticsPage';
import { ResumeImprovementsPage } from '../pages/ResumeImprovementsPage';
import { ResumeReportPage } from '../pages/ResumeReportPage';
import { JobsPage } from '../pages/JobsPage';
import { JobDescriptionReportPage } from '../pages/JobDescriptionReportPage';
import { EmployerPage } from '../pages/EmployerPage';
import { MatchingPage } from '../pages/MatchingPage';
import { SkillGapPage } from '../pages/SkillGapPage';
import { CareerPage } from '../pages/CareerPage';
import { AssessmentPage } from '../pages/AssessmentPage';
import { CopilotPage } from '../pages/CopilotPage';
import { SettingsPage } from '../pages/SettingsPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { DesignSystemPage } from '../pages/DesignSystemPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RouteErrorFallback />,
    children: [
      // Marketing routes with public header & footer
      {
        element: <MarketingLayout />,
        children: [
          {
            index: true,
            element: <LandingPage />,
          },
          {
            path: 'design-system',
            element: <DesignSystemPage />,
          },
          {
            path: '*',
            element: <NotFoundPage />,
          },
        ],
      },
      // Authenticated Dashboard shell routes with Sidebar & TopNavbar
      {
        element: <DashboardLayout />,
        children: [
          {
            path: 'dashboard',
            element: <DashboardPage />,
          },
          {
            path: 'resume',
            element: <ResumePage />,
          },
          {
            path: 'resume/preview',
            element: <ResumePreviewPage />,
          },
          {
            path: 'resume/:resumeId/preview',
            element: <ResumePreviewPage />,
          },
          {
            path: 'resume/analytics',
            element: <ResumeAnalyticsPage />,
          },
          {
            path: 'resume/:resumeId/analytics',
            element: <ResumeAnalyticsPage />,
          },
          {
            path: 'resume/improvements',
            element: <ResumeImprovementsPage />,
          },
          {
            path: 'resume/:resumeId/improvements',
            element: <ResumeImprovementsPage />,
          },
          {
            path: 'resume/report',
            element: <ResumeReportPage />,
          },
          {
            path: 'resume/:resumeId/report',
            element: <ResumeReportPage />,
          },
          {
            path: 'jobs',
            element: <JobsPage />,
          },
          {
            path: 'jobs/report',
            element: <JobDescriptionReportPage />,
          },
          {
            path: 'jobs/:jobId/report',
            element: <JobDescriptionReportPage />,
          },
          {
            path: 'employer',
            element: <EmployerPage />,
          },
          {
            path: 'matching',
            element: <MatchingPage />,
          },
          {
            path: 'skill-gap',
            element: <SkillGapPage />,
          },
          {
            path: 'career',
            element: <CareerPage />,
          },
          {
            path: 'assessment',
            element: <AssessmentPage />,
          },
          {
            path: 'copilot',
            element: <CopilotPage />,
          },
          {
            path: 'settings',
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },
]);
