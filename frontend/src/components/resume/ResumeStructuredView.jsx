import React, { useState } from 'react';
import {
  List,
  AlignLeft,
  Copy,
  Check,
  Search,
  Sparkles,
  FileText,
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '../../utils/cn';

/**
 * ResumeStructuredView component
 * Phase 2 | Feature 5: Task 2 (Cleaned Text Display) & Task 3 (Resume Structure Display)
 */
export function ResumeStructuredView({
  blocks = [],
  cleanedText = '',
  cleaningActions = [],
  className,
}) {
  const [viewMode, setViewMode] = useState('structured'); // 'structured' | 'plain'
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleCopy = async () => {
    if (!cleanedText) return;
    try {
      await navigator.clipboard.writeText(cleanedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const filteredBlocks = searchQuery.trim()
    ? blocks.filter((b) =>
        b.content.toLowerCase().includes(searchQuery.toLowerCase().trim())
      )
    : blocks;

  return (
    <div className={cn('space-y-4', className)}>
      {/* View Options & Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl">
        {/* Toggle between Structured View & Normalized Plain Text */}
        <div className="flex items-center gap-1.5 p-1 bg-white border border-slate-200 rounded-lg">
          <button
            type="button"
            onClick={() => setViewMode('structured')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors',
              viewMode === 'structured'
                ? 'bg-primary text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            )}
            title="View formatted sections, headings, and lists"
          >
            <List className="w-3.5 h-3.5" />
            <span>Structured View</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode('plain')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors',
              viewMode === 'plain'
                ? 'bg-primary text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            )}
            title="View normalized continuous text"
          >
            <AlignLeft className="w-3.5 h-3.5" />
            <span>Cleaned Text</span>
          </button>
        </div>

        {/* Search within document & Copy */}
        <div className="flex items-center gap-2">
          {viewMode === 'structured' && (
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Find in resume..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-primary w-36 sm:w-48"
              />
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="text-xs h-8 flex items-center gap-1.5 border-slate-300 text-slate-700 bg-white hover:bg-slate-50"
            title="Copy cleaned text to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-green-600" />
                <span className="text-green-700 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy Text</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Content Container */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs max-h-[650px] overflow-y-auto">
        {viewMode === 'structured' ? (
          /* Structured Content Blocks */
          <div className="space-y-3">
            {filteredBlocks.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">
                {searchQuery ? 'No sections matched your search.' : 'No content available.'}
              </p>
            ) : (
              filteredBlocks.map((block, idx) => {
                if (block.type === 'heading') {
                  return (
                    <div
                      key={idx}
                      className="pt-4 first:pt-0 pb-1 border-b border-slate-100 flex items-center gap-2"
                    >
                      <span className="w-1.5 h-4 bg-teal-600 rounded-full shrink-0" />
                      <h3 className="text-sm font-bold text-slate-900 tracking-wide uppercase">
                        {block.content}
                      </h3>
                    </div>
                  );
                }

                if (block.type === 'list_item') {
                  // Format bullet or list item
                  const cleanContent = block.content.replace(/^[•\*\-\+]\s+/, '');
                  return (
                    <div
                      key={idx}
                      className="flex items-start gap-2.5 text-xs text-slate-700 pl-3 leading-relaxed"
                    >
                      <span className="text-teal-600 font-bold select-none">•</span>
                      <span className="flex-1 break-words">{cleanContent}</span>
                    </div>
                  );
                }

                // Default paragraph
                return (
                  <p
                    key={idx}
                    className="text-xs sm:text-sm text-slate-700 leading-relaxed break-words whitespace-pre-wrap"
                  >
                    {block.content}
                  </p>
                );
              })
            )}
          </div>
        ) : (
          /* Normalized Plain Cleaned Text */
          <div className="font-mono text-xs sm:text-[13px] text-slate-800 whitespace-pre-wrap leading-relaxed select-text break-words">
            {cleanedText}
          </div>
        )}
      </div>

      {/* Applied Normalizations Footnote */}
      {cleaningActions && cleaningActions.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500 pt-1">
          <span className="font-semibold text-slate-600 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-indigo-500" /> Normalizations:
          </span>
          {cleaningActions.map((act) => (
            <span
              key={act}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200/60"
            >
              {act.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
