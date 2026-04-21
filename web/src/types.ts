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
  clothing?: ClothingMatch[]
}

export interface SearchResult {
  frame_id: string
  video_id: string
  timestamp: number
  image_path: string
  detections: Detection[]
}

export interface SearchPayload {
  video_ids: string[]
  query: string
}

export interface UploadVideoResponse {
  video_id: string
  status: string
}
