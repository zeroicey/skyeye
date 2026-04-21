import { Search, Upload } from 'lucide-react'

import { useSkyEyeStore, type TabType } from '../store/useSkyEyeStore'

const tabs: { id: TabType; label: string; icon: typeof Upload }[] = [
  { id: 'upload', label: '上传视频', icon: Upload },
  { id: 'search', label: '视频搜索', icon: Search },
]

export function TabNav() {
  const activeTab = useSkyEyeStore((state) => state.activeTab)
  const setActiveTab = useSkyEyeStore((state) => state.setActiveTab)

  return (
    <nav className="tab-nav" role="tablist" aria-label="功能导航">
      {tabs.map((tab) => {
        const Icon = tab.icon
        const isActive = activeTab === tab.id

        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            className={`tab-btn ${isActive ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
