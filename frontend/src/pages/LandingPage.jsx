import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';

export function LandingPage() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-700 text-xs font-semibold mb-6">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Next-Generation Career Intelligence</span>
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-6xl">
          Empowering Your Career with <span className="text-teal-600">Nexora AI</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
          Transform resume evaluations, job discovery, and skill-gap readiness into an intelligent, data-driven journey.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button size="lg" className="gap-2">
              Go to Dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link to="/resume">
            <Button variant="outline" size="lg">
              Explore Resume Intelligence
            </Button>
          </Link>
        </div>
      </section>

      {/* Feature Pillars Preview */}
      <section className="border-t border-slate-100 bg-slate-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="rounded-lg bg-white p-6 shadow-sm border border-slate-200">
              <CheckCircle2 className="h-6 w-6 text-teal-600 mb-3" />
              <h3 className="text-lg font-semibold text-slate-900">Resume Intelligence</h3>
              <p className="mt-2 text-sm text-slate-600">
                Deep contextual parsing of skills, experience, and profile alignment.
              </p>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-sm border border-slate-200">
              <CheckCircle2 className="h-6 w-6 text-teal-600 mb-3" />
              <h3 className="text-lg font-semibold text-slate-900">Skill Gap Diagnosis</h3>
              <p className="mt-2 text-sm text-slate-600">
                Identify discrepancies between your current portfolio and employer expectations.
              </p>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-sm border border-slate-200">
              <CheckCircle2 className="h-6 w-6 text-teal-600 mb-3" />
              <h3 className="text-lg font-semibold text-slate-900">Personalized Roadmaps</h3>
              <p className="mt-2 text-sm text-slate-600">
                Actionable step-by-step guidance tailored to target roles.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
