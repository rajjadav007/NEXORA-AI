import React, { useState } from 'react';
import {
  Button,
  PrimaryButton,
  SecondaryButton,
  OutlineButton,
  IconButton,
  Input,
  Textarea,
  Select,
  Checkbox,
  Label,
  Badge,
  Alert,
  AlertTitle,
  AlertDescription,
  LoadingIndicator,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Container,
  Divider,
  useToast,
} from '../components/ui';
import { PageHeader } from '../components/layout/PageHeader';
import {
  Sparkles,
  Send,
  Trash2,
  Bell,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Search,
} from 'lucide-react';

export function DesignSystemPage() {
  const { toast } = useToast();
  const [checkboxState, setCheckboxState] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [selectValue, setSelectValue] = useState('fullstack');

  return (
    <div className="bg-slate-50 min-h-screen pb-16">
      <PageHeader
        badge="Design System"
        title="Nexora AI Design System"
        description="Core UI tokens, reusable accessible components, responsive layouts and visual foundation."
        action={
          <PrimaryButton
            onClick={() =>
              toast({
                title: 'Design System Loaded',
                description: 'All components rendered successfully.',
                variant: 'success',
              })
            }
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Test Toast
          </PrimaryButton>
        }
      />

      <Container className="mt-8 space-y-12">
        {/* Section 1: Design Tokens & Palette */}
        <section aria-labelledby="tokens-heading">
          <h2 id="tokens-heading" className="text-xl font-bold text-slate-900 mb-4">
            1. Design Tokens & Color Palette
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div className="p-4 rounded-lg bg-teal-600 text-white shadow-xs">
              <div className="font-semibold text-sm">Primary</div>
              <div className="text-xs opacity-90">#0D9488</div>
              <div className="text-xs opacity-75 mt-2">Teal 600</div>
            </div>
            <div className="p-4 rounded-lg bg-teal-50 text-teal-900 border border-teal-200">
              <div className="font-semibold text-sm">Teal Light</div>
              <div className="text-xs opacity-90">#F0FDFA</div>
              <div className="text-xs opacity-75 mt-2">Teal 50</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-900 text-white shadow-xs">
              <div className="font-semibold text-sm">Dark Charcoal</div>
              <div className="text-xs opacity-90">#0F172A</div>
              <div className="text-xs opacity-75 mt-2">Slate 900</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-500 text-white shadow-xs">
              <div className="font-semibold text-sm">Muted Gray</div>
              <div className="text-xs opacity-90">#64748B</div>
              <div className="text-xs opacity-75 mt-2">Slate 500</div>
            </div>
            <div className="p-4 rounded-lg bg-white text-slate-900 border border-slate-200 shadow-xs">
              <div className="font-semibold text-sm">Surface/Border</div>
              <div className="text-xs opacity-75">#FFFFFF / #E2E8F0</div>
              <div className="text-xs opacity-50 mt-2">White / Slate 200</div>
            </div>
            <div className="p-4 rounded-lg bg-green-600 text-white shadow-xs">
              <div className="font-semibold text-sm">Success</div>
              <div className="text-xs opacity-90">#16A34A</div>
              <div className="text-xs opacity-75 mt-2">Semantic</div>
            </div>
          </div>
        </section>

        <Divider label="Buttons" />

        {/* Section 2: Buttons */}
        <section aria-labelledby="buttons-heading">
          <h2 id="buttons-heading" className="text-xl font-bold text-slate-900 mb-4">
            2. Buttons
          </h2>
          <Card>
            <CardHeader>
              <CardTitle>Button Variants & Sizes</CardTitle>
              <CardDescription>
                Primary, secondary, outline, ghost, destructive, and icon button implementations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Variants */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Variants</h4>
                <div className="flex flex-wrap items-center gap-3">
                  <PrimaryButton>Primary Button</PrimaryButton>
                  <SecondaryButton>Secondary Button</SecondaryButton>
                  <OutlineButton>Outline Button</OutlineButton>
                  <Button variant="ghost">Ghost Button</Button>
                  <Button variant="destructive">
                    <Trash2 className="w-4 h-4 mr-2" />
                    Destructive
                  </Button>
                  <Button variant="link">Link Style</Button>
                </div>
              </div>

              {/* Sizes */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Sizes</h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="sm">Small (sm)</Button>
                  <Button size="md">Medium (md)</Button>
                  <Button size="lg">Large (lg)</Button>
                  <IconButton label="Notifications">
                    <Bell className="w-4 h-4 text-slate-700" />
                  </IconButton>
                </div>
              </div>

              {/* States */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">States & Icons</h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Button disabled>Disabled Button</Button>
                  <Button>
                    <Send className="w-4 h-4 mr-2" />
                    With Icon
                  </Button>
                  <Button variant="outline">
                    <Search className="w-4 h-4 mr-2" />
                    Search Action
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <Divider label="Form Components" />

        {/* Section 3: Forms */}
        <section aria-labelledby="forms-heading">
          <h2 id="forms-heading" className="text-xl font-bold text-slate-900 mb-4">
            3. Form Components
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Text Inputs & Textarea</CardTitle>
                <CardDescription>
                  Inputs with label binding, placeholder styling, focus rings, and error states.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="demo-name" required>
                    Full Name
                  </Label>
                  <Input
                    id="demo-name"
                    placeholder="e.g. Alex Morgan"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="demo-error">Email Address (Error State)</Label>
                  <Input
                    id="demo-error"
                    type="email"
                    defaultValue="invalid-email@"
                    error
                  />
                  <p className="mt-1 text-xs text-red-600">Please provide a valid email address.</p>
                </div>

                <div>
                  <Label htmlFor="demo-disabled">Disabled Input</Label>
                  <Input id="demo-disabled" disabled value="Readonly / Disabled Field" />
                </div>

                <div>
                  <Label htmlFor="demo-textarea">Career Objective (Textarea)</Label>
                  <Textarea
                    id="demo-textarea"
                    placeholder="Describe your current focus and target engineering positions..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Select & Checkbox Controls</CardTitle>
                <CardDescription>
                  Accessible dropdowns and custom styled checkbox controls.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="demo-select">Target Specialization (Select)</Label>
                  <Select
                    id="demo-select"
                    value={selectValue}
                    onChange={(e) => setSelectValue(e.target.value)}
                  >
                    <option value="frontend">Frontend Engineering</option>
                    <option value="backend">Backend Engineering</option>
                    <option value="fullstack">Full Stack AI Systems</option>
                    <option value="ml">Machine Learning / RAG</option>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="demo-select-error">Location (Error State)</Label>
                  <Select id="demo-select-error" error defaultValue="">
                    <option value="" disabled>Select target location...</option>
                    <option value="remote">Remote</option>
                    <option value="onsite">On-site</option>
                  </Select>
                  <p className="mt-1 text-xs text-red-600">Location selection is required.</p>
                </div>

                <div className="pt-2 space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Checkboxes</h4>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="opt-notifications"
                      checked={checkboxState}
                      onChange={(e) => setCheckboxState(e.target.checked)}
                    />
                    <label htmlFor="opt-notifications" className="text-sm text-slate-700 select-none cursor-pointer">
                      Receive weekly skill gap analysis updates
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <Checkbox id="opt-disabled" disabled defaultChecked />
                    <label htmlFor="opt-disabled" className="text-sm text-slate-400 select-none cursor-not-allowed">
                      Auto-apply to matched jobs (Disabled)
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <Divider label="Feedback Components" />

        {/* Section 4: Feedback */}
        <section aria-labelledby="feedback-heading">
          <h2 id="feedback-heading" className="text-xl font-bold text-slate-900 mb-4">
            4. Feedback Components
          </h2>
          <Card>
            <CardHeader>
              <CardTitle>Badges, Alerts, Loading & Toasts</CardTitle>
              <CardDescription>
                System feedback, status indicators, and user alert notifications.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Badges */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Badges</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="primary">Teal Primary</Badge>
                  <Badge variant="secondary">Secondary Slate</Badge>
                  <Badge variant="outline">Outline</Badge>
                  <Badge variant="success">Success</Badge>
                  <Badge variant="warning">Warning</Badge>
                  <Badge variant="error">Error</Badge>
                  <Badge variant="info">Info</Badge>
                </div>
              </div>

              {/* Alerts */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Alerts</h4>
                <div className="space-y-3">
                  <Alert variant="info">
                    <AlertTitle>Profile Incomplete</AlertTitle>
                    <AlertDescription>
                      Upload your latest resume to generate role readiness scoring.
                    </AlertDescription>
                  </Alert>

                  <Alert variant="success">
                    <AlertTitle>Analysis Completed</AlertTitle>
                    <AlertDescription>
                      Successfully extracted 14 technical skills and matched 8 job requisitions.
                    </AlertDescription>
                  </Alert>

                  <Alert variant="warning">
                    <AlertTitle>Attention Required</AlertTitle>
                    <AlertDescription>
                      Missing experience metrics in project descriptions may lower ATS score.
                    </AlertDescription>
                  </Alert>

                  <Alert variant="destructive">
                    <AlertTitle>Upload Failed</AlertTitle>
                    <AlertDescription>
                      File format unsupported. Please upload PDF or DOCX file.
                    </AlertDescription>
                  </Alert>
                </div>
              </div>

              {/* Loading & Toasts */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Loading Indicators & Toasts</h4>
                <div className="flex flex-wrap items-center gap-6">
                  <div className="flex items-center gap-3">
                    <LoadingIndicator size="sm" />
                    <LoadingIndicator size="md" />
                    <LoadingIndicator size="lg" />
                    <span className="text-sm text-slate-500">Spinners (sm, md, lg)</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        toast({
                          title: 'Success Toast',
                          description: 'Action completed without error.',
                          variant: 'success',
                        })
                      }
                    >
                      <CheckCircle className="w-3.5 h-3.5 mr-1.5 text-green-600" />
                      Trigger Success Toast
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        toast({
                          title: 'Warning Toast',
                          description: 'Please review your input fields.',
                          variant: 'warning',
                        })
                      }
                    >
                      <AlertCircle className="w-3.5 h-3.5 mr-1.5 text-amber-600" />
                      Trigger Warning Toast
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        toast({
                          title: 'Info Toast',
                          description: 'New feature updates available.',
                          variant: 'info',
                        })
                      }
                    >
                      <HelpCircle className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
                      Trigger Info Toast
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <Divider label="Layout Components" />

        {/* Section 5: Layout */}
        <section aria-labelledby="layout-heading">
          <h2 id="layout-heading" className="text-xl font-bold text-slate-900 mb-4">
            5. Layout Components
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Modular Card</CardTitle>
                <CardDescription>Standardized container with subtle border & shadow.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600">
                  Cards provide structural grouping for all SaaS dashboard widgets and data lists.
                </p>
              </CardContent>
              <CardFooter className="justify-between">
                <Badge variant="primary">Active</Badge>
                <Button size="sm" variant="ghost">Learn More</Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Container</CardTitle>
                <CardDescription>Responsive horizontal bounding with standard gutters.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600">
                  Supports breakpoints: sm (3xl), md (5xl), lg (7xl), xl (2xl), and full-width.
                </p>
              </CardContent>
              <CardFooter>
                <span className="text-xs text-slate-400">Zero horizontal overflow</span>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Dividers</CardTitle>
                <CardDescription>Subtle visual breaks with optional centered label.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Divider />
                <Divider label="OR" />
              </CardContent>
              <CardFooter>
                <span className="text-xs text-slate-400">role="separator" accessible</span>
              </CardFooter>
            </Card>
          </div>
        </section>
      </Container>
    </div>
  );
}

export default DesignSystemPage;
