# UI_UX_GUIDELINES.md

# Nexora AI: UI/UX Guidelines

## 1. Purpose

This document defines the user interface and user experience guidelines for Nexora AI.

The goal is to create a modern, simple, responsive, and user-friendly career intelligence platform.

Nexora AI should help users understand their career position, analyze opportunities, identify skill gaps, and plan their career development through a single dashboard.

### Primary UX Goals

- Make career information easy to understand.
- Keep navigation simple and consistent.
- Present AI-generated insights clearly.
- Make resume and job analysis easy to follow.
- Show meaningful progress and recommendations.
- Avoid overwhelming users with too much information.
- Provide a consistent experience across desktop, tablet, and mobile.

---

## 2. Target Users

Nexora AI is designed for:

| User Type | Main Requirement |
|---|---|
| Students | Understand skills and career options |
| Freshers | Find internships and entry-level jobs |
| Job Seekers | Match resumes with job requirements |
| Early-Career Professionals | Identify growth opportunities |
| Career Switchers | Understand transferable skills and gaps |

The interface should be understandable even for users who have limited technical knowledge.

---

## 3. Design Principles

### 3.1 Simplicity

- Use clean layouts.
- Avoid unnecessary visual elements.
- Keep important actions easy to find.
- Use clear labels instead of complex technical terms.

### 3.2 Consistency

- Maintain consistent spacing.
- Reuse UI components.
- Keep button styles consistent.
- Use the same card and table patterns across modules.

### 3.3 Clarity

- Explain scores and recommendations.
- Separate facts from AI-generated suggestions.
- Highlight missing information.
- Show the reason behind important recommendations.

### 3.4 Accessibility

- Maintain readable text sizes.
- Provide sufficient color contrast.
- Support keyboard navigation.
- Use clear focus indicators.
- Add accessible labels to form controls.
- Do not use color as the only way to communicate status.

### 3.5 Responsiveness

- Design for desktop first, then adapt to smaller screens.
- Keep navigation usable on mobile.
- Make tables horizontally scrollable or convert them into cards.
- Ensure forms and dialogs fit smaller screens.

---

## 4. Visual Design Direction

### Design Style

Nexora AI should use a modern SaaS dashboard style.

Recommended visual direction:

- Clean and minimal interface.
- Professional typography.
- Soft neutral backgrounds.
- Clear card layouts.
- Subtle borders and shadows.
- Consistent spacing.
- Simple icons.
- Limited use of gradients and animations.

Avoid excessive gradients, glowing effects, and unnecessary animations.

### Suggested Color Palette

The following palette is a starting point. It can be adjusted during implementation.

| Purpose | Color | Hex |
|---|---|---|
| Primary | Teal | #0F766E |
| Primary Hover | Dark Teal | #115E59 |
| Secondary | Slate | #475569 |
| Main Background | Light Gray | #F8FAFC |
| Card Background | White | #FFFFFF |
| Main Text | Dark Slate | #0F172A |
| Secondary Text | Gray | #64748B |
| Border | Light Slate | #E2E8F0 |
| Success | Green | #16A34A |
| Warning | Amber | #D97706 |
| Error | Red | #DC2626 |
| Information | Blue | #2563EB |

### Color Usage Rules

- Use teal for primary actions and active navigation.
- Use neutral colors for most backgrounds.
- Use green for positive results.
- Use amber for warnings and attention.
- Use red for errors and critical issues.
- Maintain readable contrast between text and background.

### Typography

Recommended font: Inter.

| Element | Recommended Size |
|---|---|
| Main Page Heading | 24–30px |
| Section Heading | 18–22px |
| Card Heading | 16–18px |
| Body Text | 14–16px |
| Secondary Text | 12–14px |
| Button Text | 14px |
| Small Labels | 12px |

Use a consistent font weight hierarchy:

- Page headings: 600 or 700.
- Section headings: 600.
- Body text: 400.
- Labels: 500.

---

## 5. Application Layout

The main application should use a dashboard layout.

### Desktop Layout

```text
+------------------------------------------------------+
|                     TOP NAVBAR                       |
+----------------+-------------------------------------+
|                |                                     |
|                |                                     |
|    SIDEBAR     |          MAIN CONTENT               |
|                |                                     |
|                |                                     |
|                |                                     |
|                |                                     |
|                |                                     |
+----------------+-------------------------------------+
```

### Main Layout Components

| Component | Responsibility |
|---|---|
| Sidebar | Main navigation |
| Top Navbar | Search, notifications, profile |
| Main Content | Current page content |
| Page Header | Title, description, actions |
| Content Cards | Display information |
| Footer | Optional legal and support links |

### Sidebar Navigation

Recommended navigation structure:

```text
NEXORA AI

Overview

CAREER INTELLIGENCE
- Resume Intelligence
- Job Analyzer
- Employer Intelligence
- Job Discovery
- Job Matching
- Skill Gap Analysis

CAREER DEVELOPMENT
- Career Readiness
- Career Roadmap
- Skill Assessments

AI TOOLS
- Career Copilot
- Mock Interviews
- GitHub Analysis

MY CAREER
- Saved Jobs
- Applications
- My Skills
- My Progress

SETTINGS
- Profile
- Account Settings
- Privacy
```

Only show modules that are available to the user. Features should not appear as fully functional when they are still under development.

### Top Navbar

Include:

- Search entry point.
- Notifications.
- User profile menu.
- Settings shortcut where useful.

Keep the top navbar simple.

---

## 6. Dashboard Design

### Purpose

The dashboard is the user's central career overview.

It should answer:

1. What is my current career status?
2. What should I work on next?
3. Which opportunities match my profile?
4. How much progress have I made?

### Dashboard Components

#### Welcome Section

Display:

- Personalized greeting.
- Short career summary.
- Primary action to upload or analyze a resume.

#### Career Overview Cards

Recommended cards:

| Card | Information |
|---|---|
| Resume Score | Latest resume quality score |
| Career Readiness | Readiness for selected role |
| Skills Identified | Number of recognized skills |
| Job Matches | Number of relevant job matches |
| Skill Gaps | Number of important missing skills |

Show the calculation date and explain what each score means.

#### Recommended Next Actions

Examples:

- Complete resume analysis.
- Add missing project details.
- Improve a priority skill.
- Review recommended internships.
- Complete a technical assessment.

#### Recent Activity

Display:

- Recent resume analysis.
- Recently viewed jobs.
- Updated career roadmap.
- Completed assessments.
- Application status changes.

#### Dashboard Wireframe

```text
+------------------------------------------------------+
| Welcome Back                         Upload Resume   |
| Your career intelligence overview                   |
+------------------------------------------------------+
| Resume Score | Readiness | Job Matches | Skill Gaps  |
+------------------------------------------------------+
|                                                      |
| Career Progress             Recommended Actions      |
|                                                      |
+------------------------------------------------------+
| Recommended Jobs                                   |
|                                                      |
+------------------------------------------------------+
| Recent Activity                                      |
+------------------------------------------------------+
```

---

## 7. Page-Level UI Guidelines

## 7.1 Resume Upload

**Related features:** 7–12

### Required UI Elements

- Upload area.
- Drag-and-drop support.
- Browse file button.
- Supported file format information.
- File size information.
- Upload progress.
- Processing status.
- Resume preview.

### User Flow

```text
Upload Resume
     |
Validate File
     |
Extract Text
     |
Show Preview
     |
User Confirms
     |
Save Resume
     |
Start Analysis
```

### UX Requirements

- Support PDF and DOCX.
- Show clear validation errors.
- Do not lose the selected file after a recoverable error.
- Show progress during processing.
- Allow users to review extracted content.
- Clearly explain what happens to uploaded resume data.

---

## 7.2 Resume Intelligence

**Related features:** 13–20

Organize resume information into separate sections.

### Recommended Sections

- Personal Information.
- Education.
- Experience.
- Skills.
- Projects.
- Certifications.
- Resume Structure.

Use editable information cards.

Users should be able to correct extraction mistakes before continuing.

---

## 7.3 Resume Quality Analysis

**Related features:** 21–27

### Main UI Components

- Resume Quality Score.
- Strengths.
- Weaknesses.
- ATS Compatibility.
- Grammar and Clarity.
- Achievement Analysis.
- Improvement Recommendations.

### Score Display

Use a progress indicator or circular score visualization.

Every score must include:

- Score value.
- Short explanation.
- Factors used in calculation.
- Improvement suggestions.

Avoid displaying a score without explaining how it was calculated.

### Recommendation Layout

Separate recommendations into:

- High Priority.
- Medium Priority.
- Low Priority.

Show the specific resume section related to each recommendation.

---

## 7.4 Resume Intelligence Report

**Related features:** 28–32

### Main Components

- Resume analytics.
- Skill distribution chart.
- Improvement tracker.
- AI-generated report.
- Export PDF action.

Use charts only when they help users understand their data.

Allow users to download reports and revisit previous analyses.

---

## 7.5 Job Description Analyzer

**Related features:** 33–38

### Input Methods

- Paste job description.
- Import job description from URL.

### Results Layout

Display:

- Job title.
- Company name, if available.
- Required skills.
- Preferred skills.
- Experience requirements.
- Education requirements.
- Job description summary.

Clearly indicate fields that could not be extracted.

---

## 7.6 Employer Intelligence

**Related features:** 39–45

### Main Components

- Company search.
- Company overview.
- Employer research.
- Hiring requirements.
- Required skills.
- Fresher and internship opportunities.
- Employer intelligence report.

### UX Requirements

- Display source links.
- Show when information was last checked.
- Separate verified facts from AI-generated analysis.
- Avoid presenting unverified company information as confirmed.

---

## 7.7 Job Discovery

**Related features:** 46–51

### Main Components

- Job search bar.
- Role filters.
- Location filters.
- Experience filters.
- Job cards.
- Save job action.

### Job Card Information

Each job card should show:

- Job title.
- Company name.
- Location.
- Experience requirement.
- Employment type, when available.
- Important skills.
- Posted date, when available.
- View details action.
- Save job action.

Only show information provided by the job source.

---

## 7.8 Job Matching

**Related features:** 52–57

### Main Components

- Selected resume.
- Selected job.
- Overall match score.
- Skill match breakdown.
- Experience match.
- Education match.
- Relevant projects.
- Match explanation.

### Recommended Layout

```text
+--------------------------------------+
|          JOB MATCH RESULT            |
+--------------------------------------+
|                                      |
|             82 / 100                 |
|          Overall Match               |
|                                      |
+--------------------------------------+
| Matching Skills                      |
| Missing Skills                       |
| Experience Match                     |
| Education Match                      |
| Project Relevance                    |
+--------------------------------------+
|             Explanation              |
+--------------------------------------+
|          Recommended Actions         |
+--------------------------------------+
```

The displayed score must come from the matching engine.

Do not imply that an 82% match means an 82% chance of getting hired.

---

## 7.9 Skill Gap Intelligence

**Related features:** 58–62

### Main Components

- Existing skills.
- Missing skills.
- Transferable skills.
- Priority levels.
- Skill gap comparison.

Use clear labels:

- Matched.
- Missing.
- Transferable.
- Needs Verification.

Each missing skill should include a short reason and recommended next step.

---

## 7.10 Career Readiness

**Related features:** 63–66

### Main Components

- Overall readiness score.
- Selected target role.
- Skill readiness.
- Experience readiness.
- Education readiness.
- Project readiness.
- Progress history.

Show the readiness breakdown instead of displaying only one number.

Allow users to compare progress over time using consistent scoring rules.

---

## 7.11 Career Roadmap

**Related features:** 67–72

### Main Components

- Career goal selection.
- Recommended roadmap.
- Learning stages.
- Learning resources.
- Project recommendations.
- Priority labels.
- Progress tracker.

### Roadmap Structure

```text
Career Goal
    |
    v
Current Skill Analysis
    |
    v
Priority Skill Gaps
    |
    v
Learning Plan
    |
    v
Practical Projects
    |
    v
Assessment
    |
    v
Progress Review
```

### UX Requirements

- Divide roadmaps into manageable stages.
- Show estimated time only when supported by the plan.
- Allow users to mark tasks as completed.
- Save progress automatically.
- Let users revisit and update their goals.

---

## 7.12 Skill Assessment

**Related features:** 73–77

### Main Components

- Assessment list.
- Skill selection.
- Difficulty selection.
- Question interface.
- Timer, when applicable.
- Answer submission.
- Result report.
- Skill evidence profile.

### UX Requirements

- Explain assessment rules before starting.
- Show progress through questions.
- Prevent accidental loss of answers.
- Provide clear evaluation feedback.
- Explain incorrect answers.
- Distinguish completed assessments from verified real-world experience.

---

## 7.13 AI Career Copilot

**Related features:** 78

### Chat Interface

The Copilot should use a familiar chat layout.

Required components:

- Conversation history.
- Message input.
- Send button.
- Loading indicator.
- Suggested prompts.
- Response feedback.
- Clear conversation action.

### Suggested Prompts

Examples:

- Analyze my career profile.
- Which skills should I learn next?
- Find suitable AI internships.
- Improve my resume for this job.
- Help me prepare for an interview.

### UX Requirements

- Keep responses readable.
- Support structured recommendations.
- Display relevant source links.
- Show when the assistant lacks enough information.
- Avoid presenting generated information as verified facts.

---

## 7.14 Mock Interview

**Related features:** 79–80

### Main Components

- Target role selection.
- Interview type.
- Difficulty level.
- Question interface.
- Answer input.
- Interview completion screen.
- Feedback report.

### Feedback Categories

- Technical knowledge.
- Communication.
- Answer structure.
- Relevance.
- Improvement areas.

Clearly explain that automated interview feedback is an estimate, not a definitive measure of interview performance.

---

## 7.15 GitHub Project Analysis

**Related features:** 81

### Main Components

- GitHub repository URL input.
- Repository details.
- Project overview.
- Technology stack.
- Code quality observations.
- Project strengths.
- Improvement recommendations.

Show the repository and files that support important observations.

Never claim that a repository was analyzed if its contents could not be accessed.

---

## 7.16 Internship Recommendations

**Related features:** 82

### Main Components

- Recommended internships.
- Role and skill match.
- Eligibility information.
- Missing requirements.
- Application link.
- Save internship action.

Prioritize relevance over the number of recommendations.

Display the original source and availability date when known.

---

## 7.17 Application Tracker

**Related features:** 83–84

### Main Components

- Application list.
- Company name.
- Job title.
- Application date.
- Application status.
- Next action.
- Notes.

### Suggested Status Values

- Interested.
- Preparing.
- Applied.
- Assessment.
- Interview.
- Offer.
- Rejected.
- Withdrawn.

Allow users to update statuses and add notes.

---

## 8. Reusable UI Components

Build reusable components instead of creating each page independently.

### Layout Components

- AppLayout.
- Sidebar.
- TopNavbar.
- PageHeader.
- PageContainer.
- MobileNavigation.

### Data Components

- StatCard.
- ScoreCard.
- ProgressBar.
- SkillBadge.
- StatusBadge.
- DataTable.
- EmptyState.
- ChartCard.

### Form Components

- TextInput.
- SearchInput.
- SelectInput.
- FileUpload.
- FormField.
- FormError.
- SubmitButton.

### AI Components

- AIResponseCard.
- AIRecommendationCard.
- AnalysisStatus.
- MatchScore.
- SkillGapCard.
- SourceReference.
- ChatMessage.
- FeedbackPanel.

### Feedback Components

- LoadingSkeleton.
- ErrorState.
- SuccessMessage.
- ConfirmationDialog.
- ToastNotification.

Use Shadcn UI components as the base where suitable.

---

## 9. Responsive Design Guidelines

### Desktop

- Use a persistent sidebar.
- Show dashboard cards in a grid.
- Use multi-column layouts where useful.
- Keep content width readable.

### Tablet

- Collapse the sidebar when needed.
- Reduce the number of columns.
- Keep important actions visible.
- Avoid overcrowded cards.

### Mobile

- Use compact navigation.
- Stack cards vertically.
- Use full-width forms.
- Make buttons easy to tap.
- Keep charts readable.
- Convert complex tables into mobile-friendly layouts.
- Keep chat input accessible.

### Responsive Breakpoints

Use Tailwind CSS breakpoints as the initial standard:

| Breakpoint | Width |
|---|---|
| Small | 640px |
| Medium | 768px |
| Large | 1024px |
| Extra Large | 1280px |
| 2XL | 1536px |

Test actual layouts rather than relying only on breakpoint definitions.

---

## 10. Interaction and Feedback States

Every interactive component must have clear states.

### Loading State

Examples:

- Resume uploading.
- Resume analysis running.
- Job matching running.
- AI generating a response.
- Report exporting.

Show meaningful progress where available.

Do not display fake percentage progress when the backend cannot measure actual progress.

### Empty State

Examples:

- No resume uploaded.
- No saved jobs.
- No applications.
- No assessments.
- No roadmap created.

Each empty state should explain what the user can do next.

### Error State

Examples:

- Invalid file.
- Network failure.
- AI model unavailable.
- Invalid job URL.
- Failed analysis.

Provide a clear message and a recovery action.

### Success State

Examples:

- Resume uploaded.
- Analysis completed.
- Job saved.
- Assessment completed.
- Roadmap updated.

Use short confirmation messages.

---

## 11. Accessibility Guidelines

Follow accessible design practices throughout the application.

- Use semantic HTML.
- Maintain keyboard navigation.
- Use visible focus states.
- Provide labels for all inputs.
- Add accessible names to icon-only buttons.
- Use sufficient contrast.
- Provide alternative text for meaningful images.
- Support screen readers.
- Avoid flashing animations.
- Respect reduced-motion preferences.
- Use clear error messages.

Aim for WCAG 2.2 AA accessibility.

---

## 12. Animation Guidelines

Use subtle animations to improve interaction feedback.

Recommended animations:

- Sidebar transitions.
- Card hover states.
- Dropdown transitions.
- Modal transitions.
- Loading indicators.
- Progress updates.

Avoid:

- Excessive page transitions.
- Continuous background animations.
- Distracting motion.
- Animations that delay important actions.

Use Framer Motion only when a clear interaction benefit exists. CSS transitions are sufficient for most basic effects.

---

## 13. Frontend Technology

### Selected Stack

| Technology | Responsibility |
|---|---|
| React | UI development |
| JavaScript | Frontend programming |
| Vite | Development and build tooling |
| Tailwind CSS | Styling |
| Shadcn UI | Reusable UI components |
| React Router | Navigation |
| TanStack Query | Server state and API caching |
| React Hook Form | Form management |
| Zod | Frontend validation |
| Recharts | Data visualization |
| Lucide React | Icons |

These libraries should be introduced as needed, not all at once.

### Suggested Frontend Structure

```text
frontend/
|
+-- public/
|
+-- src/
    |
    +-- assets/
    |
    +-- components/
    |   +-- ui/
    |   +-- layout/
    |   +-- dashboard/
    |   +-- resume/
    |   +-- jobs/
    |   +-- matching/
    |   +-- career/
    |   +-- copilot/
    |
    +-- pages/
    |   +-- auth/
    |   +-- dashboard/
    |   +-- resume/
    |   +-- jobs/
    |   +-- employer/
    |   +-- matching/
    |   +-- skills/
    |   +-- roadmap/
    |   +-- assessments/
    |   +-- copilot/
    |   +-- applications/
    |   +-- settings/
    |
    +-- hooks/
    |
    +-- services/
    |
    +-- context/
    |
    +-- routes/
    |
    +-- utils/
    |
    +-- styles/
    |
    +-- App.jsx
    +-- main.jsx
```

---

## 14. Frontend Development Rules

1. Use reusable components.
2. Keep page components focused.
3. Separate API calls from UI components.
4. Use consistent naming conventions.
5. Keep shared styles centralized.
6. Avoid duplicating layout code.
7. Validate forms before API submission.
8. Handle loading, empty, and error states.
9. Use reusable API services.
10. Keep sensitive data out of browser storage.
11. Do not hardcode AI-generated results.
12. Use real backend data for production screens.

---

## 15. User Experience Flow

### First-Time User

```text
Landing Page
     |
Register
     |
Complete Profile
     |
Upload Resume
     |
Review Extracted Information
     |
Resume Analysis
     |
Dashboard
     |
Choose Career Goal
     |
Explore Job Matches
     |
View Skill Gaps
     |
Create Career Roadmap
```

### Returning User

```text
Login
  |
Dashboard
  |
Review Career Progress
  |
Continue Roadmap
  |
Explore New Jobs
  |
Analyze Job Match
  |
Prepare Application
```

The user should be able to reach important actions without navigating through unnecessary pages.

---

## 16. UI Performance Guidelines

- Lazy-load large page modules.
- Avoid unnecessary component re-renders.
- Paginate large result lists.
- Cache suitable API responses.
- Optimize images and assets.
- Avoid rendering large datasets all at once.
- Use skeleton loaders for slower requests.
- Keep charts lightweight.
- Monitor frontend loading performance.

Long-running AI operations should be handled by backend tasks, not by blocking the user interface.

---

## 17. UI Testing Strategy

Use:

- Vitest.
- React Testing Library.
- Browser-based end-to-end testing when needed.

### Testing Requirements

Test:

- Navigation.
- Forms.
- File upload.
- Validation.
- Loading states.
- Error states.
- Responsive layouts.
- Dashboard components.
- API integration.
- Accessibility basics.

Test important user journeys from start to finish.

---

## 18. UI Development Phases

| Stage | UI Work |
|---|---|
| Phase 1 | Dashboard shell, navigation, design system |
| Phase 2 | Resume upload and preview |
| Phase 3 | Resume intelligence screens |
| Phase 4 | Resume quality analysis |
| Phase 5 | Resume report and analytics |
| Phase 6 | Job description analyzer |
| Phase 7 | Employer intelligence |
| Phase 8 | Job discovery |
| Phase 9 | Job matching |
| Phase 10 | Skill gap analysis |
| Phase 11 | Career readiness dashboard |
| Phase 12 | Career roadmap |
| Phase 13 | Skill assessment interface |
| Phase 14 | Career Copilot and interview tools |
| Phase 15 | Authentication, security, testing, and deployment |

Build and test each interface alongside its backend functionality.

---

## 19. Final UI/UX Principles

Nexora AI must provide:

1. A clean and professional SaaS interface.
2. Simple and predictable navigation.
3. Clear resume and job analysis reports.
4. Explainable matching and readiness scores.
5. Actionable skill gap recommendations.
6. Personalized career roadmaps.
7. Responsive layouts.
8. Accessible interactions.
9. Consistent reusable components.
10. Reliable loading, error, and success states.

**Final Goal:** Build an intuitive career intelligence platform where users can understand their career profile, discover relevant opportunities, improve missing skills, and make better career decisions through one consistent experience.