import { create } from 'zustand'

import { fetchVideos, searchFrames, uploadVideo } from '../lib/api'
import type { SearchResult, VideoItem } from '../types'

const POLL_INTERVAL_MS = 3000

const wait = (ms: number) =>
  new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })

type StatusTone = 'info' | 'success' | 'error'

export type TabType = 'upload' | 'search'

export interface StatusMessage {
  tone: StatusTone
  text: string
}

interface SkyEyeStoreState {
  activeTab: TabType
  videos: VideoItem[]
  selectedVideoIds: string[]
  query: string
  results: SearchResult[]
  loadingVideos: boolean
  uploading: boolean
  searching: boolean
  hasSearched: boolean
  uploadStatus: StatusMessage | null
  errorMessage: string | null
  setActiveTab: (tab: TabType) => void
  setQuery: (query: string) => void
  toggleVideo: (videoId: string) => void
  loadVideos: () => Promise<void>
  uploadAndProcess: (file: File, name: string) => Promise<void>
  search: () => Promise<void>
}

export const useSkyEyeStore = create<SkyEyeStoreState>()((set, get) => {
  const syncVideos = (videos: VideoItem[]) => {
    set((state) => ({
      videos,
      selectedVideoIds: state.selectedVideoIds.filter((id) =>
        videos.some((video) => video.id === id),
      ),
    }))
  }

  const pollVideoStatus = async (videoId: string) => {
    while (true) {
      await wait(POLL_INTERVAL_MS)

      try {
        const videos = await fetchVideos()
        syncVideos(videos)

        const targetVideo = videos.find((video) => video.id === videoId)
        if (!targetVideo) {
          continue
        }

        if (targetVideo.status === 'ready') {
          set({
            uploadStatus: {
              tone: 'success',
              text: '处理完成，可以开始检索。',
            },
          })
          return
        }

        if (targetVideo.status === 'error') {
          set({
            uploadStatus: {
              tone: 'error',
              text: '视频处理失败，请重新上传。',
            },
          })
          return
        }
      } catch {
        // Keep polling to tolerate temporary network failures.
      }
    }
  }

  return {
    activeTab: 'upload',
    videos: [],
    selectedVideoIds: [],
    query: '',
    results: [],
    loadingVideos: false,
    uploading: false,
    searching: false,
    hasSearched: false,
    uploadStatus: null,
    errorMessage: null,

    setActiveTab: (tab) => {
      set({ activeTab: tab })
    },

    setQuery: (query) => {
      set({ query })
    },

    toggleVideo: (videoId) => {
      set((state) => {
        const exists = state.selectedVideoIds.includes(videoId)
        return {
          selectedVideoIds: exists
            ? state.selectedVideoIds.filter((id) => id !== videoId)
            : [...state.selectedVideoIds, videoId],
        }
      })
    },

    loadVideos: async () => {
      set({ loadingVideos: true, errorMessage: null })
      try {
        const videos = await fetchVideos()
        syncVideos(videos)
      } catch {
        set({ errorMessage: '加载视频列表失败，请确认后端服务已启动。' })
      } finally {
        set({ loadingVideos: false })
      }
    },

    uploadAndProcess: async (file, name) => {
      set({
        uploading: true,
        uploadStatus: {
          tone: 'info',
          text: '正在上传视频...',
        },
        errorMessage: null,
      })

      try {
        const payloadName = name.trim() || file.name
        const response = await uploadVideo(file, payloadName)

        set({
          uploading: false,
          uploadStatus: {
            tone: 'info',
            text: '上传完成，正在进行检测与识别...',
          },
        })

        const latestVideos = await fetchVideos()
        syncVideos(latestVideos)

        await pollVideoStatus(response.video_id)
      } catch {
        set({
          uploading: false,
          uploadStatus: {
            tone: 'error',
            text: '上传失败，请重试。',
          },
        })
      }
    },

    search: async () => {
      const query = get().query.trim()
      const selectedVideoIds = get().selectedVideoIds

      if (!query) {
        set({ errorMessage: '请输入搜索内容。' })
        return
      }

      if (selectedVideoIds.length === 0) {
        set({ errorMessage: '请至少选择一个视频作为检索范围。' })
        return
      }

      set({
        searching: true,
        hasSearched: true,
        errorMessage: null,
        results: [],
      })

      try {
        const results = await searchFrames({ video_ids: selectedVideoIds, query })
        set({ results })
      } catch {
        set({ errorMessage: '搜索失败，请稍后重试。' })
      } finally {
        set({ searching: false })
      }
    },
  }
})
