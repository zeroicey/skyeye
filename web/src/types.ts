export type VideoStatus = 'processing' | 'ready' | 'error'

export interface VideoItem {
  id: string
  name: string
  status: VideoStatus
  frame_count: number | null
}

export interface ClothingMatch {
  prompt: string
  confidence: number
  category?: string
}

export interface Detection {
  class: string
  confidence: number
  bbox?: number[]
  track_id?: number
  clothing?: ClothingMatch[]
}

export interface GalleryPreviewItem {
  id: string
  timestamp: number
  crop_uri?: string | null
  context_uri?: string | null
}

export interface SearchResult {
  frame_id: string
  video_id: string
  timestamp: number
  image_path: string
  detections: Detection[]
  track_id?: number | null
  person_track_id?: string
  crop_uri?: string | null
  context_uri?: string | null
  gallery_preview?: GalleryPreviewItem[]
  features?: Record<string, unknown>
  start_timestamp?: number
  end_timestamp?: number
}

export interface SearchPayload {
  video_ids: string[]
  query: string
}

export interface UploadVideoResponse {
  video_id: string
  status: string
}
