import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Sparkles } from 'lucide-react';

export function CopilotPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Career Copilot"
        description="Interactive career advisory, resume feedback assistant, and interview coaching."
        badge="Placeholder"
      />
      <EmptyState
        icon={Sparkles}
        title="AI Career Copilot Shell Ready"
        description="LLM-assisted coaching dialogues and intelligent guidance workflows will be activated in later stages."
      />
    </div>
  );
}
