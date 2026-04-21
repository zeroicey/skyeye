import { type KeyboardEvent } from 'react'
import { ScanSearch, Search } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'

const quickExamples = ['person', '白色衬衫', '蓝色裤子', 'car']

export function SearchPanel() {
  const query = useSkyEyeStore((state) => state.query)
  const searching = useSkyEyeStore((state) => state.searching)
  const selectedCount = useSkyEyeStore((state) => state.selectedVideoIds.length)
  const errorMessage = useSkyEyeStore((state) => state.errorMessage)
  const setQuery = useSkyEyeStore((state) => state.setQuery)
  const search = useSkyEyeStore((state) => state.search)

  const onEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      void search()
    }
  }

  return (
    <section className="panel search-panel">
      <div className="panel-head">
        <h2 className="panel-title">
          <ScanSearch className="panel-icon" size={18} aria-hidden="true" />
          3. 语义搜索
        </h2>
        <p>当前已选择 {selectedCount} 个视频作为检索范围。</p>
      </div>

      <label className="field-label" htmlFor="searchQuery">
        搜索条件
      </label>
      <input
        id="searchQuery"
        className="text-input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={onEnter}
        placeholder="例如: person, 白色衬衫, 蓝色裤子"
      />

      <button className="primary-btn" type="button" disabled={searching} onClick={() => void search()}>
        <span className="btn-content">
          <Search size={16} aria-hidden="true" />
          {searching ? '搜索中...' : '开始搜索'}
        </span>
      </button>

      <div className="quick-tags">
        {quickExamples.map((example) => (
          <button
            key={example}
            className="quick-tag"
            type="button"
            onClick={() => setQuery(example)}
          >
            {example}
          </button>
        ))}
      </div>

      {errorMessage ? <p className="error-text">{errorMessage}</p> : null}
    </section>
  )
}
