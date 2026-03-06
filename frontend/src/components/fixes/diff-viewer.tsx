import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { useState } from 'react';
import { FileCode, Columns2, AlignJustify } from 'lucide-react';

interface DiffViewerProps {
  diff: string;
  filesChanged?: string | null;
}

interface DiffSegment {
  filePath: string;
  oldCode: string;
  newCode: string;
}

/**
 * Parse a unified diff string into per-file segments with old/new text.
 */
function parseUnifiedDiff(diff: string): DiffSegment[] {
  if (!diff || !diff.trim()) return [];

  const segments: DiffSegment[] = [];
  const lines = diff.split('\n');

  let currentFile = '';
  let oldLines: string[] = [];
  let newLines: string[] = [];
  let inHunk = false;

  const flushSegment = () => {
    if (currentFile || oldLines.length > 0 || newLines.length > 0) {
      segments.push({
        filePath: currentFile || 'unknown file',
        oldCode: oldLines.join('\n'),
        newCode: newLines.join('\n'),
      });
      oldLines = [];
      newLines = [];
    }
  };

  for (const line of lines) {
    // Detect file header: diff --git a/path b/path
    if (line.startsWith('diff --git')) {
      flushSegment();
      const match = line.match(/diff --git a\/(.+?) b\/(.+)/);
      currentFile = match ? match[2] : '';
      inHunk = false;
      continue;
    }

    // --- a/file or +++ b/file headers
    if (line.startsWith('---') && !inHunk) {
      if (!currentFile) {
        const match = line.match(/^--- a\/(.+)/);
        if (match) currentFile = match[1];
      }
      continue;
    }
    if (line.startsWith('+++') && !inHunk) {
      if (!currentFile) {
        const match = line.match(/^\+\+\+ b\/(.+)/);
        if (match) currentFile = match[1];
      }
      continue;
    }

    // Hunk header: @@ -x,y +a,b @@
    if (line.startsWith('@@')) {
      inHunk = true;
      // Add a context separator if we already have content
      if (oldLines.length > 0 || newLines.length > 0) {
        oldLines.push('');
        newLines.push('');
      }
      continue;
    }

    // Index, mode, similarity lines
    if (
      line.startsWith('index ') ||
      line.startsWith('old mode') ||
      line.startsWith('new mode') ||
      line.startsWith('similarity') ||
      line.startsWith('rename') ||
      line.startsWith('new file') ||
      line.startsWith('deleted file')
    ) {
      continue;
    }

    if (!inHunk) continue;

    // Diff content lines
    if (line.startsWith('-')) {
      oldLines.push(line.substring(1));
    } else if (line.startsWith('+')) {
      newLines.push(line.substring(1));
    } else if (line.startsWith(' ') || line === '') {
      const content = line.startsWith(' ') ? line.substring(1) : line;
      oldLines.push(content);
      newLines.push(content);
    } else if (line.startsWith('\\')) {
      // "\ No newline at end of file" — skip
      continue;
    } else {
      // Context line without leading space
      oldLines.push(line);
      newLines.push(line);
    }
  }

  flushSegment();

  // If no segments were parsed (plain diff without git headers), treat entire input as single diff
  if (segments.length === 0 && diff.trim()) {
    segments.push({
      filePath: 'changes',
      oldCode: '',
      newCode: diff,
    });
  }

  return segments;
}

const diffStyles = {
  variables: {
    dark: {
      diffViewerBackground: '#1a1a2e',
      diffViewerColor: '#e2e8f0',
      addedBackground: '#064e3b33',
      addedColor: '#6ee7b7',
      removedBackground: '#7f1d1d33',
      removedColor: '#fca5a5',
      wordAddedBackground: '#065f4640',
      wordRemovedBackground: '#991b1b40',
      addedGutterBackground: '#064e3b22',
      removedGutterBackground: '#7f1d1d22',
      gutterBackground: '#16213e',
      gutterBackgroundDark: '#0f172a',
      highlightBackground: '#2d3748',
      highlightGutterBackground: '#2d3748',
      codeFoldGutterBackground: '#1e293b',
      codeFoldBackground: '#1e293b',
      emptyLineBackground: '#1a1a2e',
      gutterColor: '#64748b',
      addedGutterColor: '#6ee7b7',
      removedGutterColor: '#fca5a5',
      codeFoldContentColor: '#94a3b8',
      diffViewerTitleBackground: '#16213e',
      diffViewerTitleColor: '#94a3b8',
      diffViewerTitleBorderColor: '#1e293b',
    },
  },
  line: {
    padding: '2px 10px',
    fontSize: '12px',
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  },
  gutter: {
    padding: '2px 10px',
    fontSize: '11px',
    minWidth: '40px',
  },
  contentText: {
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
    fontSize: '12px',
    lineHeight: '1.6',
  },
};

export function DiffViewer({ diff, filesChanged }: DiffViewerProps) {
  const [splitView, setSplitView] = useState(false);

  const segments = parseUnifiedDiff(diff);

  // Try to get file paths from filesChanged JSON
  let filePathsFromJson: string[] = [];
  if (filesChanged) {
    try {
      filePathsFromJson = JSON.parse(filesChanged);
    } catch {
      // not valid JSON, ignore
    }
  }

  if (segments.length === 0) {
    return (
      <div className="rounded-lg border border-gray-800 bg-[#1a1a2e] p-8 text-center">
        <p className="text-sm text-gray-500">No diff content available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* View toggle */}
      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setSplitView(false)}
          className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            !splitView
              ? 'bg-green-500/20 text-green-400'
              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
          }`}
        >
          <AlignJustify size={12} />
          Unified
        </button>
        <button
          onClick={() => setSplitView(true)}
          className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            splitView
              ? 'bg-green-500/20 text-green-400'
              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
          }`}
        >
          <Columns2 size={12} />
          Side by Side
        </button>
      </div>

      {/* Diff segments */}
      {segments.map((segment, index) => {
        const filePath =
          segment.filePath ||
          (filePathsFromJson.length > index ? filePathsFromJson[index] : `File ${index + 1}`);

        return (
          <div
            key={index}
            className="overflow-hidden rounded-lg border border-gray-800"
          >
            {/* File path header */}
            <div className="flex items-center gap-2 border-b border-gray-800 bg-[#16213e] px-4 py-2">
              <FileCode size={14} className="shrink-0 text-green-400" />
              <span className="font-mono text-xs text-gray-300">{filePath}</span>
            </div>

            {/* Diff content */}
            <div className="overflow-x-auto">
              <ReactDiffViewer
                oldValue={segment.oldCode}
                newValue={segment.newCode}
                splitView={splitView}
                useDarkTheme
                compareMethod={DiffMethod.WORDS}
                styles={diffStyles}
                hideLineNumbers={false}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
