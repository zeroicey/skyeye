# Result Card Preview Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a click-to-enlarge modal preview for search result cards so users can inspect annotated frames at a readable size.

**Architecture:** Keep preview state local to `SearchResultsPanel`, make `ResultCard` an accessible interactive surface, and introduce a dedicated `ResultPreviewModal` component that reuses the current annotated-frame URL builder. Use the project's Vite and Bun tooling for compile and lint verification, and use browser-based manual checks for the modal interaction because the project does not currently include a frontend component test harness.

**Tech Stack:** React 19, TypeScript, Vite, Bun, Lucide React, project CSS variables and layout styles, in-app browser manual verification

---

## File Map

- Create: `web/src/components/ResultPreviewModal.tsx`
- Modify: `web/src/components/ResultCard.tsx`
- Modify: `web/src/components/SearchResultsPanel.tsx`
- Modify: `web/src/index.css`

### Task 1: Wire Preview State and Clickable Result Cards

**Files:**
- Create: `web/src/components/ResultPreviewModal.tsx`
- Modify: `web/src/components/ResultCard.tsx`
- Modify: `web/src/components/SearchResultsPanel.tsx`

- [ ] **Step 1: Write the failing integration change in `SearchResultsPanel`**

```tsx
import { useMemo, useState } from 'react'
import { Search, SearchX } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'
import type { SearchResult } from '../types'
import { ResultCard } from './ResultCard'
import { ResultPreviewModal } from './ResultPreviewModal'

export function SearchResultsPanel() {
  const videos = useSkyEyeStore((state) => state.videos)
  const results = useSkyEyeStore((state) => state.results)
  const hasSearched = useSkyEyeStore((state) => state.hasSearched)
  const searching = useSkyEyeStore((state) => state.searching)
  const [previewResult, setPreviewResult] = useState<SearchResult | null>(null)

  const videoNameMap = useMemo(() => {
    return new Map(videos.map((video) => [video.id, video.name]))
  }, [videos])

  const previewVideoName = previewResult ? (videoNameMap.get(previewResult.video_id) ?? previewResult.video_id) : ''

  return (
    <section className="panel results-panel">
      <div className="panel-head">
        <h2 className="panel-title">
          <Search className="panel-icon" size={18} aria-hidden="true" />
          检索结果
        </h2>
        <p>{searching ? '系统正在分析匹配结果...' : `共返回 ${results.length} 条候选结果`}</p>
      </div>

      {searching ? (
        <div className="results-grid skeleton-grid">
          {[0, 1, 2].map((key) => (
            <article key={key} className="result-card skeleton-card">
              <div className="skeleton-image" />
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
            </article>
          ))}
        </div>
      ) : null}

      {!searching && hasSearched && results.length === 0 ? (
        <div className="empty-state">
          <SearchX className="empty-state-icon" size={24} aria-hidden="true" />
          <p>没有找到匹配结果，请尝试更换关键词或扩大视频选择范围。</p>
        </div>
      ) : null}

      {!searching && results.length > 0 ? (
        <div className="results-grid">
          {results.map((result) => (
            <ResultCard
              key={result.frame_id}
              result={result}
              videoName={videoNameMap.get(result.video_id) ?? result.video_id}
              onPreview={setPreviewResult}
            />
          ))}
        </div>
      ) : null}

      <ResultPreviewModal
        result={previewResult}
        videoName={previewVideoName}
        onClose={() => setPreviewResult(null)}
      />
    </section>
  )
}
```

- [ ] **Step 2: Run the build to verify it fails**

Run: `cd web && bun run build`
Expected: FAIL because `./ResultPreviewModal` does not exist yet and `ResultCard` does not accept `onPreview`.

- [ ] **Step 3: Implement the minimal interactive card API**

```tsx
import { Clock, Video } from 'lucide-react'

import { buildAnnotatedFrameUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultCardProps {
  result: SearchResult
  videoName: string
  onPreview: (result: SearchResult) => void
}

const normalizePrompt = (prompt: string) => prompt.replace(/^a person wearing\s+/i, '')

const formatConfidence = (value: number) => `${Math.round(value * 100)}%`

export function ResultCard({ result, videoName, onPreview }: ResultCardProps) {
  const detectionIndices = result.detections.map((_, index) => index)
  const imageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)

  return (
    <button
      type="button"
      className="result-card result-card-button"
      onClick={() => onPreview(result)}
    >
      <img className="frame-preview" src={imageUrl} alt={`Frame ${result.frame_id}`} loading="lazy" />

      <div className="result-info">
        <div className="result-headline">
          <h3 className="result-title">
            <Video size={14} aria-hidden="true" />
            {videoName}
          </h3>
          <p className="time-chip">
            <Clock size={13} aria-hidden="true" />
            {result.timestamp.toFixed(2)}s
          </p>
        </div>

        <div className="result-tags">
          {result.detections.map((detection, detectionIndex) => (
            <div className="tag-group" key={`${result.frame_id}-${detection.class}-${detectionIndex}`}>
              <span className="tag detection">
                {detection.class} {formatConfidence(detection.confidence)}
              </span>
              {detection.clothing?.slice(0, 2).map((clothing, clothingIndex) => (
                <span
                  className="tag clothing"
                  key={`${result.frame_id}-${detectionIndex}-${clothing.prompt}-${clothingIndex}`}
                >
                  {normalizePrompt(clothing.prompt)} {formatConfidence(clothing.confidence)}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </button>
  )
}
```

- [ ] **Step 4: Implement the minimal modal shell**

```tsx
import { X } from 'lucide-react'

import { buildAnnotatedFrameUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultPreviewModalProps {
  result: SearchResult | null
  videoName: string
  onClose: () => void
}

export function ResultPreviewModal({ result, videoName, onClose }: ResultPreviewModalProps) {
  if (!result) {
    return null
  }

  const detectionIndices = result.detections.map((_, index) => index)
  const imageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)

  return (
    <div className="preview-backdrop">
      <section className="preview-modal" aria-label="检索结果大图预览">
        <button
          type="button"
          className="preview-close"
          onClick={onClose}
          aria-label="关闭预览"
        >
          <X size={18} aria-hidden="true" />
        </button>

        <div className="preview-media-wrap">
          <img className="preview-image" src={imageUrl} alt={`${videoName} ${result.timestamp.toFixed(2)} 秒预览`} />
        </div>

        <div className="preview-meta">
          <p className="preview-kicker">已放大查看</p>
          <h3>{videoName}</h3>
          <p>{result.timestamp.toFixed(2)}s</p>
        </div>
      </section>
    </div>
  )
}
```

- [ ] **Step 5: Run the build to verify it passes**

Run: `cd web && bun run build`
Expected: PASS with a successful Vite production build.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/ResultCard.tsx web/src/components/SearchResultsPanel.tsx web/src/components/ResultPreviewModal.tsx
git commit -m "feat: add result preview modal shell"
```

### Task 2: Add Modal Dismissal Behavior and Search Result Synchronization

**Files:**
- Modify: `web/src/components/ResultPreviewModal.tsx`
- Modify: `web/src/components/SearchResultsPanel.tsx`

- [ ] **Step 1: Perform the manual red check**

Run: `cd web && bun run dev -- --host 127.0.0.1 --port 4173`
Then open `http://127.0.0.1:4173` in the in-app browser, click a result card, and confirm these gaps still exist before implementing:

1. Clicking the backdrop does not close the preview
2. Pressing `Esc` does not close the preview
3. Running a new search does not explicitly clear the previous preview state

Expected: The first modal shell opens, but dismissal behavior is incomplete.

- [ ] **Step 2: Implement `Esc` and backdrop dismissal in the modal**

```tsx
import { useEffect } from 'react'
import { X } from 'lucide-react'

import { buildAnnotatedFrameUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultPreviewModalProps {
  result: SearchResult | null
  videoName: string
  onClose: () => void
}

export function ResultPreviewModal({ result, videoName, onClose }: ResultPreviewModalProps) {
  useEffect(() => {
    if (!result) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [result, onClose])

  if (!result) {
    return null
  }

  const detectionIndices = result.detections.map((_, index) => index)
  const imageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)

  return (
    <div className="preview-backdrop" onClick={onClose} role="presentation">
      <section
        className="preview-modal"
        aria-label="检索结果大图预览"
        onClick={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          className="preview-close"
          onClick={onClose}
          aria-label="关闭预览"
        >
          <X size={18} aria-hidden="true" />
        </button>

        <div className="preview-media-wrap">
          <img className="preview-image" src={imageUrl} alt={`${videoName} ${result.timestamp.toFixed(2)} 秒预览`} />
        </div>

        <div className="preview-meta">
          <p className="preview-kicker">已放大查看</p>
          <h3>{videoName}</h3>
          <p>{result.timestamp.toFixed(2)}s</p>
          <p>点击遮罩空白处或按 Esc 键关闭预览。</p>
        </div>
      </section>
    </div>
  )
}
```

- [ ] **Step 3: Clear stale preview state when results change**

```tsx
import { useEffect, useMemo, useState } from 'react'
import { Search, SearchX } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'
import type { SearchResult } from '../types'
import { ResultCard } from './ResultCard'
import { ResultPreviewModal } from './ResultPreviewModal'

export function SearchResultsPanel() {
  const videos = useSkyEyeStore((state) => state.videos)
  const results = useSkyEyeStore((state) => state.results)
  const hasSearched = useSkyEyeStore((state) => state.hasSearched)
  const searching = useSkyEyeStore((state) => state.searching)
  const [previewResult, setPreviewResult] = useState<SearchResult | null>(null)

  const videoNameMap = useMemo(() => {
    return new Map(videos.map((video) => [video.id, video.name]))
  }, [videos])

  useEffect(() => {
    if (!previewResult) {
      return
    }

    const stillExists = results.some((result) => result.frame_id === previewResult.frame_id)
    if (!stillExists) {
      setPreviewResult(null)
    }
  }, [previewResult, results])

  const previewVideoName = previewResult ? (videoNameMap.get(previewResult.video_id) ?? previewResult.video_id) : ''

  return (
    <section className="panel results-panel">
      <div className="panel-head">
        <h2 className="panel-title">
          <Search className="panel-icon" size={18} aria-hidden="true" />
          检索结果
        </h2>
        <p>{searching ? '系统正在分析匹配结果...' : `共返回 ${results.length} 条候选结果`}</p>
      </div>

      {searching ? (
        <div className="results-grid skeleton-grid">
          {[0, 1, 2].map((key) => (
            <article key={key} className="result-card skeleton-card">
              <div className="skeleton-image" />
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
            </article>
          ))}
        </div>
      ) : null}

      {!searching && hasSearched && results.length === 0 ? (
        <div className="empty-state">
          <SearchX className="empty-state-icon" size={24} aria-hidden="true" />
          <p>没有找到匹配结果，请尝试更换关键词或扩大视频选择范围。</p>
        </div>
      ) : null}

      {!searching && results.length > 0 ? (
        <div className="results-grid">
          {results.map((result) => (
            <ResultCard
              key={result.frame_id}
              result={result}
              videoName={videoNameMap.get(result.video_id) ?? result.video_id}
              onPreview={setPreviewResult}
            />
          ))}
        </div>
      ) : null}

      <ResultPreviewModal
        result={previewResult}
        videoName={previewVideoName}
        onClose={() => setPreviewResult(null)}
      />
    </section>
  )
}
```

- [ ] **Step 4: Re-run manual verification**

Run: `cd web && bun run dev -- --host 127.0.0.1 --port 4173`
Manual checks in the browser:

1. Click a result card and confirm the modal opens
2. Click the dark backdrop and confirm it closes
3. Press `Esc` and confirm it closes
4. Run another search and confirm stale previews do not remain open

Expected: All four checks pass.

- [ ] **Step 5: Run the lint command**

Run: `cd web && bun run lint`
Expected: PASS with no ESLint errors.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/ResultPreviewModal.tsx web/src/components/SearchResultsPanel.tsx
git commit -m "feat: add result preview dismissal interactions"
```

### Task 3: Add Responsive Styling and Final Verification

**Files:**
- Modify: `web/src/index.css`

- [ ] **Step 1: Do the visual red check against the current modal shell**

Run: `cd web && bun run dev -- --host 127.0.0.1 --port 4173`
Manual checks before styling:

1. The modal lacks the final darkened backdrop treatment
2. The enlarged image does not yet feel intentionally framed
3. The card focus and hover states do not clearly communicate click-to-preview
4. Narrow screens need tighter spacing and image sizing rules

Expected: The modal works, but polish and responsive affordances are still incomplete.

- [ ] **Step 2: Implement card and modal styles**

```css
.result-card-button {
	display: block;
	width: 100%;
	padding: 0;
	text-align: left;
	cursor: zoom-in;
	color: inherit;
}

.result-card-button:focus-visible {
	outline: 3px solid rgba(29, 138, 164, 0.4);
	outline-offset: 3px;
}

.preview-backdrop {
	position: fixed;
	inset: 0;
	z-index: 40;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 26px;
	background: rgba(8, 25, 35, 0.72);
	backdrop-filter: blur(8px);
}

.preview-modal {
	position: relative;
	width: min(980px, 100%);
	max-height: min(88vh, 920px);
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 16px;
	padding: 18px;
	border-radius: 24px;
	border: 1px solid rgba(211, 226, 235, 0.5);
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(243, 248, 251, 0.94));
	box-shadow: 0 28px 80px rgba(7, 22, 31, 0.32);
}

.preview-close {
	position: absolute;
	top: 14px;
	right: 14px;
	width: 40px;
	height: 40px;
	border: none;
	border-radius: 999px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	background: rgba(16, 42, 58, 0.08);
	color: var(--text-strong);
	cursor: pointer;
}

.preview-media-wrap {
	overflow: hidden;
	border-radius: 18px;
	background:
		radial-gradient(circle at top, rgba(29, 138, 164, 0.14), transparent 58%),
		#dbe8ef;
}

.preview-image {
	display: block;
	width: 100%;
	max-height: 68vh;
	object-fit: contain;
}

.preview-meta {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.preview-kicker {
	margin: 0;
	font-size: 0.74rem;
	letter-spacing: 0.12em;
	text-transform: uppercase;
	font-weight: 700;
	color: var(--accent-deep);
}

.preview-meta h3,
.preview-meta p {
	margin: 0;
}

@media (max-width: 680px) {
	.preview-backdrop {
		padding: 12px;
	}

	.preview-modal {
		padding: 14px;
		border-radius: 18px;
	}

	.preview-image {
		max-height: 56vh;
	}
}
```

- [ ] **Step 3: Run build and lint after styling**

Run: `cd web && bun run build && bun run lint`
Expected: PASS with a successful production build and no lint errors.

- [ ] **Step 4: Run the final browser verification**

Run: `cd web && bun run dev -- --host 127.0.0.1 --port 4173`
Manual checks in the browser:

1. The result card clearly looks clickable
2. Clicking a card opens a large centered preview
3. The close button, backdrop click, and `Esc` all close the preview
4. Desktop layout keeps the image large and readable
5. Mobile-width responsive mode still shows the preview clearly without overflow

Expected: All five checks pass.

- [ ] **Step 5: Commit**

```bash
git add web/src/index.css
git commit -m "feat: polish result preview modal styles"
```

## Self-Review Checklist

- Spec coverage:
  - Click-to-open preview is covered in Task 1.
  - Modal close button, backdrop click, and `Esc` support are covered in Task 2.
  - Responsive and visual polish are covered in Task 3.
  - Frontend-only scope is preserved across all tasks.
- Placeholder scan:
  - No `TODO`, `TBD`, or `...` placeholders remain.
  - All code-changing steps include concrete code blocks.
- Type consistency:
  - `previewResult` is consistently `SearchResult | null`.
  - `ResultPreviewModal` consistently accepts `result`, `videoName`, and `onClose`.
  - `ResultCard` consistently receives `onPreview`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-25-result-card-preview-modal.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
