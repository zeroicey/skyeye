import { useEffect } from 'react'

import { PageHeader } from './components/PageHeader'
import { SearchPanel } from './components/SearchPanel'
import { SearchResultsPanel } from './components/SearchResultsPanel'
import { UploadPanel } from './components/UploadPanel'
import { VideoSelectorPanel } from './components/VideoSelectorPanel'
import { useSkyEyeStore } from './store/useSkyEyeStore'

function App() {
  const loadVideos = useSkyEyeStore((state) => state.loadVideos)

  useEffect(() => {
    void loadVideos()
  }, [loadVideos])

  return (
    <div className="app-background">
      <div className="app-shell">
        <PageHeader />
        <main className="control-grid">
          <UploadPanel />
          <VideoSelectorPanel />
          <SearchPanel />
        </main>
        <SearchResultsPanel />
      </div>
    </div>
  )
}

export default App
