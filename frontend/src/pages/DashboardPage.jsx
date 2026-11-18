import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { LayoutDashboard, Compass, Briefcase, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const cards = [
    { title: 'Resume Readiness', desc: 'Manage and parse your active resumes.', path: '/resume', icon: FileText },
    { title: 'Job Matching', desc: 'Browse aligned opportunities and requirements.', path: '/jobs', icon: Briefcase },
    { title: 'Career Roadmap', desc: 'Track your personalized skill progression path.', path: '/career', icon: Compass },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Welcome to your Nexora AI career intelligence overview."
        badge="Foundation"
      />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.path}
                to={card.path}
                className="group block rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-teal-500 hover:shadow-md"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-600 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900 group-hover:text-teal-700">
                  {card.title}
                </h3>
                <p className="mt-1 text-sm text-slate-500">{card.desc}</p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
