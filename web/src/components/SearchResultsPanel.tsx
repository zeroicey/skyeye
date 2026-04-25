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
        videoName={previewResult ? videoNameMap.get(previewResult.video_id) ?? previewResult.video_id : ''}
        onClose={() => setPreviewResult(null)}
      />
    </section>
  )
}
