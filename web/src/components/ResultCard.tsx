import { Clock, Video } from 'lucide-react'

import { buildAnnotatedFrameUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultCardProps {
  result: SearchResult
  videoName: string
}

const normalizePrompt = (prompt: string) => prompt.replace(/^a person wearing\s+/i, '')

const formatConfidence = (value: number) => `${Math.round(value * 100)}%`

export function ResultCard({ result, videoName }: ResultCardProps) {
  const detectionIndices = result.detections.map((_, index) => index)
  const imageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)

  return (
    <article className="result-card">
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
    </article>
  )
}
