import { Clock, Fingerprint, Video } from 'lucide-react'

import { buildAnnotatedFrameUrl, buildPersonImageUrl } from '../lib/api'
import type { SearchResult } from '../types'

interface ResultCardProps {
  result: SearchResult
  videoName: string
}

const normalizePrompt = (prompt: string) => prompt.replace(/^a person wearing\s+/i, '')

const formatConfidence = (value: number) => `${Math.round(value * 100)}%`

export function ResultCard({ result, videoName }: ResultCardProps) {
  const detectionIndices = result.detections.map((_, index) => index)
  const annotatedImageUrl = buildAnnotatedFrameUrl(result.frame_id, detectionIndices)
  const cropImageUrl = result.crop_uri ? buildPersonImageUrl(result.crop_uri) : annotatedImageUrl
  const contextImageUrl = result.context_uri ? buildPersonImageUrl(result.context_uri) : annotatedImageUrl
  const featureEntries = Object.entries(result.features ?? {}).filter(([, value]) => {
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return value !== null && value !== undefined && value !== ''
  })

  return (
    <article className={`result-card ${result.person_track_id ? 'person-result-card' : ''}`}>
      <div className="person-visuals">
        <img className="frame-preview person-crop-preview" src={cropImageUrl} alt={`Person result ${result.frame_id}`} loading="lazy" />
        {result.crop_uri ? (
          <img className="context-preview" src={contextImageUrl} alt={`Context frame ${result.frame_id}`} loading="lazy" />
        ) : null}
      </div>

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

        {result.person_track_id ? (
          <div className="person-identity">
            <Fingerprint size={13} aria-hidden="true" />
            人物 {result.track_id ?? result.person_track_id.slice(0, 8)}
            {result.start_timestamp !== undefined && result.end_timestamp !== undefined ? (
              <span>{result.start_timestamp.toFixed(1)}s - {result.end_timestamp.toFixed(1)}s</span>
            ) : null}
          </div>
        ) : null}

        <div className="result-tags">
          {result.detections.map((detection, detectionIndex) => (
            <div className="tag-group" key={`${result.frame_id}-${detection.class}-${detectionIndex}`}>
              <span className="tag detection">
                {detection.class}
                {detection.track_id !== undefined ? ` ID:${detection.track_id}` : ''} {formatConfidence(detection.confidence)}
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
          {featureEntries.slice(0, 3).map(([key, value]) => (
            <span className="tag feature" key={`${result.frame_id}-${key}`}>
              {key}: {Array.isArray(value) ? `${value.length} items` : String(value)}
            </span>
          ))}
        </div>
      </div>
    </article>
  )
}
