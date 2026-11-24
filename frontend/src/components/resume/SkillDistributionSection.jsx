import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Code2,
  Sparkles,
  BarChart2,
  Layers,
  Database,
  Cloud,
  Wrench,
  Tag,
  Search,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  PieChart as PieChartIcon,
  BarChart3,
  Award,
  HelpCircle,
  FolderOpen,
  Info,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import { getResumeSkillDistribution } from '../../services/analyticsService';
import { cn } from '../../utils/cn';

// Category style & metadata map
const CATEGORY_META = {
  'Programming Languages': {
    color: '#3b82f6',
    borderClass: 'border-blue-200',
    bgClass: 'bg-blue-50/50',
    badgeClass: 'bg-blue-100 text-blue-800 border-blue-200',
    pillClass: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
    icon: Code2,
  },
  'AI and Machine Learning': {
    color: '#8b5cf6',
    borderClass: 'border-purple-200',
    bgClass: 'bg-purple-50/50',
    badgeClass: 'bg-purple-100 text-purple-800 border-purple-200',
    pillClass: 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
    icon: Sparkles,
  },
  'Data Science and Analytics': {
    color: '#06b6d4',
    borderClass: 'border-cyan-200',
    bgClass: 'bg-cyan-50/50',
    badgeClass: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    pillClass: 'bg-cyan-50 text-cyan-700 border-cyan-200 hover:bg-cyan-100',
    icon: BarChart2,
  },
  'Frameworks and Libraries': {
    color: '#10b981',
    borderClass: 'border-emerald-200',
    bgClass: 'bg-emerald-50/50',
    badgeClass: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    pillClass: 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100',
    icon: Layers,
  },
  'Databases': {
    color: '#f59e0b',
    borderClass: 'border-amber-200',
    bgClass: 'bg-amber-50/50',
    badgeClass: 'bg-amber-100 text-amber-800 border-amber-200',
    pillClass: 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100',
    icon: Database,
  },
  'Cloud and DevOps': {
    color: '#f43f5e',
    borderClass: 'border-rose-200',
    bgClass: 'bg-rose-50/50',
    badgeClass: 'bg-rose-100 text-rose-800 border-rose-200',
    pillClass: 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100',
    icon: Cloud,
  },
  'Development Tools': {
    color: '#64748b',
    borderClass: 'border-slate-300',
    bgClass: 'bg-slate-50/50',
    badgeClass: 'bg-slate-200 text-slate-800 border-slate-300',
    pillClass: 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200',
    icon: Wrench,
  },
  'Other Skills': {
    color: '#71717a',
    borderClass: 'border-zinc-300',
    bgClass: 'bg-zinc-50/50',
    badgeClass: 'bg-zinc-200 text-zinc-800 border-zinc-300',
    pillClass: 'bg-zinc-100 text-zinc-700 border-zinc-200 hover:bg-zinc-200',
    icon: Tag,
  },
};

const DEFAULT_META = {
  color: '#64748b',
  borderClass: 'border-slate-200',
  bgClass: 'bg-slate-50/50',
  badgeClass: 'bg-slate-100 text-slate-800 border-slate-200',
  pillClass: 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100',
  icon: Tag,
};

/**
 * SkillDistributionSection Component
 * Phase 5 | Feature #29: Skill Distribution
 */
export function SkillDistributionSection({ resumeId, className }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Search and Filtering states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [chartView, setChartView] = useState('both'); // 'donut' | 'bar' | 'both'
  const [collapsedCategories, setCollapsedCategories] = useState({});
  const [hoveredSlice, setHoveredSlice] = useState(null);

  const fetchSkills = useCallback(
    async (showRefreshing = false) => {
      if (!resumeId) return;
      if (showRefreshing) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const res = await getResumeSkillDistribution(resumeId);
        setData(res.data);
      } catch (err) {
        setError(err.message || 'Failed to load skill distribution.');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [resumeId]
  );

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const toggleCategoryCollapse = (categoryName) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [categoryName]: !prev[categoryName],
    }));
  };

  const expandAll = () => setCollapsedCategories({});
  const collapseAll = () => {
    if (!data?.categories) return;
    const all = {};
    data.categories.forEach((cat) => {
      all[cat.name] = true;
    });
    setCollapsedCategories(all);
  };

  // Filtered categories and skills based on search & category filter
  const filteredCategories = useMemo(() => {
    if (!data?.categories) return [];
    const query = searchQuery.trim().toLowerCase();

    return data.categories
      .filter((cat) => {
        if (selectedCategory !== 'ALL' && cat.name !== selectedCategory) {
          return false;
        }
        return true;
      })
      .map((cat) => {
        const matchingSkills = query
          ? cat.skills.filter((s) => s.toLowerCase().includes(query))
          : cat.skills;
        return {
          ...cat,
          skills: matchingSkills,
          matchCount: matchingSkills.length,
        };
      })
      .filter((cat) => (query ? cat.skills.length > 0 : true));
  }, [data, searchQuery, selectedCategory]);

  const totalFilteredSkills = useMemo(() => {
    return filteredCategories.reduce((acc, cat) => acc + cat.skills.length, 0);
  }, [filteredCategories]);

  // SVG Donut calculation data
  const donutData = useMemo(() => {
    if (!data?.categories || data.total_skills === 0) return [];
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    let accumulatedOffset = 0;

    return data.categories.map((cat) => {
      const percentage = (cat.count / data.total_skills) * 100;
      const strokeLength = (percentage / 100) * circumference;
      const strokeDashoffset = -accumulatedOffset;
      accumulatedOffset += strokeLength;

      const meta = CATEGORY_META[cat.name] || DEFAULT_META;
      return {
        name: cat.name,
        count: cat.count,
        percentage: Math.round(percentage * 10) / 10,
        color: meta.color,
        strokeDasharray: `${strokeLength} ${circumference}`,
        strokeDashoffset,
        meta,
      };
    });
  }, [data]);

  // Loading state
  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white p-8">
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <LoadingIndicator size="lg" message="Analyzing resume skills and distributions..." />
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-rose-200 shadow-sm bg-white p-6">
        <Alert
          variant="error"
          title="Error Loading Skill Distribution"
          message={error}
          action={
            <Button
              size="sm"
              variant="outline"
              onClick={() => fetchSkills(true)}
              className="mt-3 text-xs border-rose-300 text-rose-800 hover:bg-rose-50"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry
            </Button>
          }
        />
      </Card>
    );
  }

  // Empty state (no data or 0 skills)
  if (!data || data.total_skills === 0) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
          <Code2 className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-slate-800">No Extracted Skills Found</h4>
        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          This resume does not currently contain extracted technical or professional skills.
          Ensure the resume file has readable text or re-extract skills in the Skills module.
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={() => fetchSkills(true)}
          className="text-xs text-slate-700 hover:bg-slate-50 inline-flex items-center gap-1.5"
        >
          <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin')} />
          <span>Refresh Analysis</span>
        </Button>
      </Card>
    );
  }

  const { summary } = data;
  const activeHoverCategory =
    hoveredSlice || (donutData.length > 0 ? donutData[0] : null);

  return (
    <div className={cn('space-y-6', className)}>
      {/* SECTION HEADER & CONTROLS */}
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader className="pb-4 border-b border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shadow-xs">
                  <Code2 className="w-4 h-4" />
                </div>
                <div>
                  <CardTitle className="text-base font-bold text-slate-900">
                    Skill Distribution & Analytics
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Phase 5 • Feature #29 • Categorized distribution across 8 technical domains
                  </CardDescription>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchSkills(true)}
                disabled={isRefreshing}
                className="text-xs h-8 border-slate-200 text-slate-700 hover:bg-slate-50 flex items-center gap-1.5"
                title="Refresh skill distribution metrics"
              >
                <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin')} />
                <span>Refresh</span>
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-6">
          {/* A. SKILL SUMMARY CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Total Skills */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Total Skills</span>
                <Code2 className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-2xl font-black text-slate-900">{summary.total_skills}</div>
              <div className="text-[11px] text-slate-500">Verified unique technical & soft skills</div>
            </div>

            {/* Card 2: Skill Categories */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Active Categories</span>
                <Layers className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-black text-slate-900">
                {summary.total_categories}
                <span className="text-xs font-normal text-slate-400 ml-1">/ 8</span>
              </div>
              <div className="text-[11px] text-slate-500">Domains represented in resume</div>
            </div>

            {/* Card 3: Top Category */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Top Category</span>
                <Award className="w-4 h-4 text-amber-600" />
              </div>
              <div className="text-lg font-bold text-slate-900 truncate" title={summary.most_populated_category?.name}>
                {summary.most_populated_category?.name || 'N/A'}
              </div>
              <div className="text-[11px] text-slate-500 font-medium">
                {summary.most_populated_category
                  ? `${summary.most_populated_category.count} skills (${Math.round(
                      (summary.most_populated_category.count / summary.total_skills) * 100
                    )}% of total)`
                  : 'No skills found'}
              </div>
            </div>

            {/* Card 4: Uncategorized / Other Skills */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Other / General</span>
                <Tag className="w-4 h-4 text-zinc-500" />
              </div>
              <div className="text-2xl font-black text-slate-900">
                {summary.uncategorized_skills?.length || 0}
              </div>
              <div className="text-[11px] text-slate-500">
                {summary.uncategorized_skills?.length > 0
                  ? 'General or cross-functional skills'
                  : 'All skills categorized in core domains'}
              </div>
            </div>
          </div>

          {/* B. VISUAL CHARTS (DONUT & BAR CHART) */}
          <div className="rounded-xl border border-slate-200 p-5 bg-white space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-teal-600" />
                  Skill Category Distribution
                </h3>
                <p className="text-xs text-slate-500">
                  Visual breakdown of skill concentration across categories
                </p>
              </div>

              {/* View Switcher */}
              <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs">
                <button
                  type="button"
                  onClick={() => setChartView('both')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-semibold transition-colors',
                    chartView === 'both' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  Both Views
                </button>
                <button
                  type="button"
                  onClick={() => setChartView('donut')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-semibold transition-colors flex items-center gap-1',
                    chartView === 'donut' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  <PieChartIcon className="w-3.5 h-3.5" /> Donut
                </button>
                <button
                  type="button"
                  onClick={() => setChartView('bar')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-semibold transition-colors flex items-center gap-1',
                    chartView === 'bar' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  <BarChart2 className="w-3.5 h-3.5" /> Bar
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              {/* Donut Chart View */}
              {(chartView === 'donut' || chartView === 'both') && (
                <div
                  className={cn(
                    'flex flex-col sm:flex-row items-center justify-center gap-6 p-4 rounded-xl bg-slate-50/60 border border-slate-100',
                    chartView === 'donut' ? 'lg:col-span-12' : 'lg:col-span-5'
                  )}
                >
                  {/* SVG Donut Circle */}
                  <div className="relative w-44 h-44 shrink-0">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
                      {/* Background base circle */}
                      <circle
                        cx="90"
                        cy="90"
                        r="70"
                        fill="transparent"
                        stroke="#e2e8f0"
                        strokeWidth="22"
                      />
                      {/* Slices */}
                      {donutData.map((slice) => (
                        <circle
                          key={slice.name}
                          cx="90"
                          cy="90"
                          r="70"
                          fill="transparent"
                          stroke={slice.color}
                          strokeWidth={hoveredSlice?.name === slice.name ? '26' : '22'}
                          strokeDasharray={slice.strokeDasharray}
                          strokeDashoffset={slice.strokeDashoffset}
                          className="transition-all duration-300 cursor-pointer"
                          onMouseEnter={() => setHoveredSlice(slice)}
                          onMouseLeave={() => setHoveredSlice(null)}
                        />
                      ))}
                    </svg>

                    {/* Donut Center Info */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none px-2">
                      <span className="text-xl font-extrabold text-slate-900 leading-tight">
                        {activeHoverCategory ? activeHoverCategory.count : data.total_skills}
                      </span>
                      <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider truncate max-w-[90px]">
                        {activeHoverCategory ? activeHoverCategory.name : 'Total Skills'}
                      </span>
                      {activeHoverCategory && (
                        <span className="text-[10px] font-mono font-bold text-teal-700 mt-0.5">
                          {activeHoverCategory.percentage}%
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Donut Legend */}
                  <div className="space-y-1.5 min-w-[140px] text-xs">
                    {donutData.map((slice) => (
                      <div
                        key={slice.name}
                        onMouseEnter={() => setHoveredSlice(slice)}
                        onMouseLeave={() => setHoveredSlice(null)}
                        className={cn(
                          'flex items-center justify-between gap-2 px-2 py-1 rounded-md transition-colors cursor-pointer',
                          hoveredSlice?.name === slice.name ? 'bg-white shadow-xs font-bold' : 'hover:bg-white/80'
                        )}
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: slice.color }}
                          />
                          <span className="text-slate-700 truncate" title={slice.name}>
                            {slice.name}
                          </span>
                        </div>
                        <span className="font-mono text-slate-500 font-semibold text-[11px] shrink-0">
                          {slice.count} ({slice.percentage}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Bar Chart Comparison View */}
              {(chartView === 'bar' || chartView === 'both') && (
                <div
                  className={cn(
                    'space-y-3 p-4 rounded-xl bg-slate-50/60 border border-slate-100',
                    chartView === 'bar' ? 'lg:col-span-12' : 'lg:col-span-7'
                  )}
                >
                  <div className="text-xs font-bold text-slate-700 flex items-center justify-between mb-1">
                    <span>Category Comparison</span>
                    <span className="text-[11px] font-normal text-slate-500">Count & Share</span>
                  </div>

                  {donutData.map((slice) => {
                    const IconComp = slice.meta.icon;
                    return (
                      <div key={slice.name} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-700 flex items-center gap-1.5 truncate">
                            <IconComp className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="truncate" title={slice.name}>
                              {slice.name}
                            </span>
                          </span>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="font-bold text-slate-900 font-mono text-xs">
                              {slice.count}
                            </span>
                            <span className="text-[11px] font-mono text-slate-500 min-w-[42px] text-right">
                              ({slice.percentage}%)
                            </span>
                          </div>
                        </div>

                        {/* Bar fill */}
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${slice.percentage}%`,
                              backgroundColor: slice.color,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* C. SEARCH AND FILTER CONTROLS */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search skills by name (e.g. Python, Docker, SQL)..."
                  className="w-full h-9 pl-9 pr-3 rounded-lg border border-slate-200 bg-white text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600 font-bold"
                  >
                    ✕
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={expandAll}
                  className="text-xs h-8 border-slate-200 text-slate-600 hover:bg-slate-50"
                >
                  Expand All
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={collapseAll}
                  className="text-xs h-8 border-slate-200 text-slate-600 hover:bg-slate-50"
                >
                  Collapse All
                </Button>
              </div>
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <button
                type="button"
                onClick={() => setSelectedCategory('ALL')}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-semibold border transition-colors',
                  selectedCategory === 'ALL'
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                )}
              >
                All Categories ({data.total_skills})
              </button>

              {data.categories.map((cat) => {
                const isSelected = selectedCategory === cat.name;
                return (
                  <button
                    key={cat.name}
                    type="button"
                    onClick={() => setSelectedCategory(cat.name)}
                    className={cn(
                      'px-3 py-1 rounded-full text-xs font-semibold border transition-colors flex items-center gap-1.5',
                      isSelected
                        ? 'bg-teal-700 text-white border-teal-700'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                    )}
                  >
                    <span>{cat.name}</span>
                    <span
                      className={cn(
                        'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
                        isSelected ? 'bg-teal-800 text-white' : 'bg-slate-100 text-slate-600'
                      )}
                    >
                      {cat.count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* D. SKILL CATEGORY CARDS */}
          <div className="space-y-4">
            {filteredCategories.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredCategories.map((cat) => {
                  const meta = CATEGORY_META[cat.name] || DEFAULT_META;
                  const IconComponent = meta.icon;
                  const isCollapsed = collapsedCategories[cat.name];

                  return (
                    <Card
                      key={cat.name}
                      className={cn(
                        'border transition-shadow hover:shadow-sm overflow-hidden',
                        meta.borderClass,
                        meta.bgClass
                      )}
                    >
                      {/* Card Header */}
                      <div
                        onClick={() => toggleCategoryCollapse(cat.name)}
                        className="p-3.5 flex items-center justify-between cursor-pointer select-none bg-white/70 hover:bg-white transition-colors"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <div
                            className="w-7 h-7 rounded-md flex items-center justify-center shrink-0"
                            style={{ backgroundColor: `${meta.color}20`, color: meta.color }}
                          >
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <span className="font-bold text-slate-900 text-sm truncate" title={cat.name}>
                            {cat.name}
                          </span>
                          <Badge variant="outline" className={cn('text-[10px] font-mono shrink-0', meta.badgeClass)}>
                            {cat.skills.length} {cat.skills.length === 1 ? 'skill' : 'skills'}
                          </Badge>
                        </div>

                        <div className="text-slate-400 hover:text-slate-600 pl-2">
                          {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                        </div>
                      </div>

                      {/* Card Body: Skill Tags */}
                      {!isCollapsed && (
                        <div className="p-4 pt-3 border-t border-slate-100 bg-white">
                          <div className="flex flex-wrap gap-1.5">
                            {cat.skills.map((skillName) => (
                              <span
                                key={skillName}
                                className={cn(
                                  'inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-md border transition-colors',
                                  meta.pillClass
                                )}
                              >
                                {skillName}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            ) : (
              /* Empty Search State */
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                <Search className="w-8 h-8 text-slate-300 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-700">No Matching Skills Found</h4>
                <p className="text-xs text-slate-400">
                  No skills matched &ldquo;{searchQuery}&rdquo; within the selected category filter.
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedCategory('ALL');
                  }}
                  className="mt-2 text-xs border-slate-200 text-slate-700"
                >
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default SkillDistributionSection;
