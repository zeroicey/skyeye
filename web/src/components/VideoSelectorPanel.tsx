import { useMemo } from 'react'
import { CircleAlert, CircleCheck, Clock, ListFilter, RefreshCw } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'

export function VideoSelectorPanel() {
  const videos = useSkyEyeStore((state) => state.videos)
  const selectedVideoIds = useSkyEyeStore((state) => state.selectedVideoIds)
  const loadingVideos = useSkyEyeStore((state) => state.loadingVideos)
  const toggleVideo = useSkyEyeStore((state) => state.toggleVideo)
  const loadVideos = useSkyEyeStore((state) => state.loadVideos)

  const selectedCount = useMemo(() => selectedVideoIds.length, [selectedVideoIds])

  return (
    <section className="panel selector-panel">
      <div className="panel-head row-between">
        <div>
          <h2 className="panel-title">
            <ListFilter className="panel-icon" size={18} aria-hidden="true" />
            视频列表
            {selectedCount > 0 && <span className="selected-badge">{selectedCount}</span>}
          </h2>
          <p>勾选视频以设置为搜索范围，支持多选。</p>
        </div>
        <button
          className="ghost-btn"
          type="button"
          onClick={() => void loadVideos()}
          disabled={loadingVideos}
        >
          <span className="btn-content">
            <RefreshCw className={loadingVideos ? 'spin' : ''} size={15} aria-hidden="true" />
            {loadingVideos ? '刷新中...' : '刷新列表'}
          </span>
        </button>
      </div>

      <div className="video-list">
        {videos.length === 0 ? (
          <p className="empty-text">暂无视频，请先上传。</p>
        ) : (
          videos.map((video) => {
            const checked = selectedVideoIds.includes(video.id)
            const selectable = video.status === 'ready'

            return (
              <label
                key={video.id}
                className={`video-row ${checked ? 'selected' : ''} ${!selectable ? 'disabled' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={!selectable}
                  onChange={() => toggleVideo(video.id)}
                />
                <span className="video-name" title={video.name}>
                  {video.name}
                </span>
                <span className={`video-status ${video.status}`}>
                  {video.status === 'ready' ? <CircleCheck size={12} aria-hidden="true" /> : null}
                  {video.status === 'processing' ? <Clock size={12} aria-hidden="true" /> : null}
                  {video.status === 'error' ? <CircleAlert size={12} aria-hidden="true" /> : null}
                  {video.status}
                </span>
              </label>
            )
          })
        )}
      </div>
    </section>
  )
}
