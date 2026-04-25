import { Clock, Video, X } from 'lucide-react'

import { buildAnnotatedFrameUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultPreviewModalProps {
  result: SearchResult | null
  videoName: string
  onClose: () => void
}

const normalizePrompt = (prompt: string) => prompt.replace(/^a person wearing\s+/i, '')

const formatConfidence = (value: number) => `${Math.round(value * 100)}%`

export function ResultPreviewModal({ result, videoName, onClose }: ResultPreviewModalProps) {
  if (!result) {
    return null
  }

  const detectionIndices = result.detections.map((_, index) => index)
  const imageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)

  return (
    <div
      role="presentation"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 30,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: 'rgba(16, 42, 58, 0.45)',
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="result-preview-title"
        style={{
          width: 'min(960px, 100%)',
          maxHeight: 'min(88vh, 900px)',
          overflow: 'auto',
        }}
      >
        <section className="panel" style={{ margin: 0 }}>
          <div className="row-between" style={{ alignItems: 'flex-start', marginBottom: '16px' }}>
            <div className="panel-head" style={{ marginBottom: 0 }}>
              <h2 id="result-preview-title" className="panel-title">
                <Video className="panel-icon" size={18} aria-hidden="true" />
                结果预览
              </h2>
              <p>{videoName}</p>
            </div>

            <button type="button" className="ghost-btn" onClick={onClose} aria-label="关闭预览">
              <span className="btn-content">
                <X size={16} aria-hidden="true" />
                关闭
              </span>
            </button>
          </div>

          <div style={{ display: 'grid', gap: '18px' }}>
            <img
              src={imageUrl}
              alt={`${videoName} 在 ${result.timestamp.toFixed(2)} 秒的标注帧`}
              style={{
                display: 'block',
                width: '100%',
                maxHeight: '60vh',
                objectFit: 'contain',
                borderRadius: '14px',
                border: '1px solid var(--border)',
                background: '#d9e7f0',
              }}
            />

            <div className="result-headline">
              <h3 className="result-title" style={{ maxWidth: '100%' }}>
                <Video size={14} aria-hidden="true" />
                {videoName}
              </h3>
              <p className="time-chip">
                <Clock size={13} aria-hidden="true" />
                {result.timestamp.toFixed(2)}s
              </p>
            </div>

            <div className="result-tags" style={{ marginTop: 0 }}>
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
        </section>
      </div>
    </div>
  )
}
