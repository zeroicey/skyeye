import { useEffect } from 'react'

import { PageHeader } from './components/PageHeader'
import { SearchPanel } from './components/SearchPanel'
import { SearchResultsPanel } from './components/SearchResultsPanel'
import { TabNav } from './components/TabNav'
import { UploadPanel } from './components/UploadPanel'
import { VideoSelectorPanel } from './components/VideoSelectorPanel'
import { useSkyEyeStore } from './store/useSkyEyeStore'

function App() {
  const loadVideos = useSkyEyeStore((state) => state.loadVideos)
  const activeTab = useSkyEyeStore((state) => state.activeTab)

  useEffect(() => {
    void loadVideos()
  }, [loadVideos])

  return (
    <div className="app-background">
      <div className="app-shell">
        <PageHeader />
        <TabNav />
        <main className={`main-content control-grid ${activeTab === 'upload' ? 'upload-tab-grid' : 'search-tab-grid'}`}>
          {activeTab === 'upload' ? (
            <>
              <UploadPanel />
              <VideoSelectorPanel />
            </>
          ) : (
            <>
              <VideoSelectorPanel />
              <SearchPanel />
            </>
          )}
        </main>
        {activeTab === 'search' && <SearchResultsPanel />}
      </div>
    </div>
  )
}

export default App
