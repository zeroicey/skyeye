import { useMemo } from 'react'
import { Clock, ListFilter, ScanSearch, SearchCheck, Video } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'

export function PageHeader() {
  const videos = useSkyEyeStore((state) => state.videos)
  const selectedCount = useSkyEyeStore((state) => state.selectedVideoIds.length)

  const stats = useMemo(() => {
    const total = videos.length
    const ready = videos.filter((video) => video.status === 'ready').length
    const processing = videos.filter((video) => video.status === 'processing').length

    return { total, ready, processing, selected: selectedCount }
  }, [videos, selectedCount])

  return (
    <header className="page-header">
      <div className="title-block">
        <p className="eyebrow">SkyEye Command Center</p>
        <h1 className="heading-with-icon">
          <ScanSearch className="title-icon" size={30} strokeWidth={2.2} aria-hidden="true" />
          视频语义检索工作台
        </h1>
        <p className="subtitle">
          从上传到检索全部集中在一个页面完成，支持目标类别和衣物属性联合搜索。
        </p>
      </div>

      <div className="stat-grid">
        <article className="stat-card">
          <p className="stat-label with-icon">
            <Video size={14} aria-hidden="true" />
            视频总数
          </p>
          <p className="stat-value">{stats.total}</p>
        </article>
        <article className="stat-card">
          <p className="stat-label with-icon">
            <SearchCheck size={14} aria-hidden="true" />
            可检索
          </p>
          <p className="stat-value">{stats.ready}</p>
        </article>
        <article className="stat-card">
          <p className="stat-label with-icon">
            <Clock size={14} aria-hidden="true" />
            处理中
          </p>
          <p className="stat-value">{stats.processing}</p>
        </article>
        <article className="stat-card">
          <p className="stat-label with-icon">
            <ListFilter size={14} aria-hidden="true" />
            已选范围
          </p>
          <p className="stat-value">{stats.selected}</p>
        </article>
      </div>
    </header>
  )
}
