import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  TrendingUp,
  Compass,
  Award,
  Sparkles,
  ArrowRight,
  Clock,
  PlusCircle,
  Search,
  CheckCircle2,
} from 'lucide-react';
import { DashboardCard } from '../components/layout/DashboardCard';
import { EmptyState } from '../components/layout/EmptyState';
import { Button } from '../components/ui/button';

export function DashboardPage() {
  const quickActions = [
    { label: 'Upload Resume', path: '/resume', icon: PlusCircle },
    { label: 'Discover Jobs', path: '/jobs', icon: Search },
    { label: 'Skill Gap Analysis', path: '/skill-gap', icon: TrendingUp },
    { label: 'Career Roadmap', path: '/career', icon: Compass },
  ];

  const featureCards = [
    {
      title: 'Resume Intelligence',
      description: 'Parse, audit, and benchmark resume credentials against market criteria.',
      badge: 'Core Engine',
      path: '/resume',
      icon: FileText,
      status: 'Ready for upload',
    },
    {
      title: 'Job Matching',
      description: 'Evaluate semantic alignment between your profile and target openings.',
      badge: 'Discovery',
      path: '/matching',
      icon: Briefcase,
      status: 'Matching standing by',
    },
    {
      title: 'Skill Gap Analysis',
      description: 'Pinpoint missing qualifications and high-value competencies to acquire.',
      badge: 'Diagnostics',
      path: '/skill-gap',
      icon: TrendingUp,
      status: 'Audit required',
    },
    {
      title: 'Career Roadmap',
      description: 'Follow milestone-based progress towards target titles and compensation tiers.',
      badge: 'Progression',
      path: '/career',
      icon: Compass,
      status: 'Track pending',
    },
    {
      title: 'Skill Assessment',
      description: 'Verify practical proficiency through modular diagnostic checks.',
      badge: 'Validation',
      path: '/assessment',
      icon: Award,
      status: 'Ready for test',
    },
    {
      title: 'AI Career Copilot',
      description: 'Ask questions, refine talking points, and prepare strategic interview answers.',
      badge: 'Copilot',
      path: '/copilot',
      icon: Sparkles,
      status: 'Model initialized',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700 mb-2">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-600 animate-pulse" />
              SaaS Career Shell
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Welcome to Nexora AI
            </h2>
            <p className="mt-1 text-sm text-slate-500 max-w-2xl">
              Your career intelligence command center. Analyze resume strength, explore matched opportunities, and target your next career milestone.
            </p>
          </div>
          <div className="shrink-0">
            <Link to="/resume">
              <Button className="gap-2">
                <span>Start Evaluation</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Quick Actions Bar */}
        <div className="mt-6 pt-6 border-t border-slate-100">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Quick Actions
          </p>
          <div className="flex flex-wrap gap-2.5">
            {quickActions.map((action) => {
              const ActionIcon = action.icon;
              return (
                <Link key={action.path} to={action.path}>
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-medium text-slate-700 transition hover:border-teal-500 hover:bg-white hover:text-teal-700"
                  >
                    <ActionIcon className="h-3.5 w-3.5 text-slate-500" />
                    <span>{action.label}</span>
                  </button>
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Feature Pillar Cards Grid */}
      <section aria-labelledby="pillars-heading">
        <div className="mb-4 flex items-center justify-between">
          <h3 id="pillars-heading" className="text-base font-semibold text-slate-900">
            Career Intelligence Pillars
          </h3>
          <span className="text-xs text-slate-400">Layout Preview</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureCards.map((card) => (
            <Link key={card.path} to={card.path} className="block">
              <DashboardCard
                icon={card.icon}
                title={card.title}
                description={card.description}
                badge={card.badge}
                action={
                  <>
                    <span className="text-slate-500">{card.status}</span>
                    <span className="inline-flex items-center gap-1 text-teal-600 font-semibold group-hover:translate-x-0.5 transition-transform">
                      Open Module <ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </>
                }
              />
            </Link>
          ))}
        </div>
      </section>

      {/* Recent Activity Section with Empty State */}
      <section aria-labelledby="activity-heading">
        <div className="mb-4">
          <h3 id="activity-heading" className="text-base font-semibold text-slate-900">
            Recent Activity
          </h3>
          <p className="text-xs text-slate-500">
            Real-time feed of resume audits, job matches, and roadmap progress.
          </p>
        </div>
        <EmptyState
          icon={Clock}
          title="No recent activity yet"
          description="Your evaluations, analyzed job opportunities, and skill milestones will automatically be logged here."
          action={
            <Link to="/resume">
              <Button variant="outline" size="sm" className="gap-2">
                <CheckCircle2 className="h-4 w-4 text-teal-600" />
                <span>Initialize First Action</span>
              </Button>
            </Link>
          }
        />
      </section>
    </div>
  );
}
