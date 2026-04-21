import ky from 'ky'

import type { SearchPayload, SearchResult, UploadVideoResponse, VideoItem } from '../types'

const resolveApiBaseUrl = () => {
  const envValue = import.meta.env.VITE_API_BASE_URL
  if (!envValue) {
    return '/api/'
  }

  return envValue.endsWith('/') ? envValue : `${envValue}/`
}

const apiBaseUrl = resolveApiBaseUrl()

const apiClient = ky.create({
  baseUrl: apiBaseUrl,
  timeout: 20000,
})

export const fetchVideos = async () => apiClient.get('videos').json<VideoItem[]>()

export const uploadVideo = async (file: File, name: string) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)

  return apiClient
    .post('videos/upload', {
      body: formData,
      timeout: false,
    })
    .json<UploadVideoResponse>()
}

export const searchFrames = async (payload: SearchPayload) =>
  apiClient.post('search', { json: payload }).json<SearchResult[]>()

export const buildAnnotatedFrameUrl = (frameId: string, detectionIndices: number[]) => {
  const params = new URLSearchParams()
  if (detectionIndices.length > 0) {
    params.set('detection_indices', detectionIndices.join(','))
  }

  const suffix = params.toString()
  return `${apiBaseUrl}frames/${frameId}/annotated${suffix ? `?${suffix}` : ''}`
}
