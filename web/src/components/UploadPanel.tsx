import { type FormEvent, useRef, useState } from 'react'
import { CircleAlert, CircleCheck, Info, Upload } from 'lucide-react'

import { useSkyEyeStore } from '../store/useSkyEyeStore'

export function UploadPanel() {
  const [videoName, setVideoName] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadAndProcess = useSkyEyeStore((state) => state.uploadAndProcess)
  const uploading = useSkyEyeStore((state) => state.uploading)
  const uploadStatus = useSkyEyeStore((state) => state.uploadStatus)

  const StatusIcon = uploadStatus?.tone === 'success'
    ? CircleCheck
    : uploadStatus?.tone === 'error'
      ? CircleAlert
      : Info

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedFile || uploading) {
      return
    }

    await uploadAndProcess(selectedFile, videoName)

    setSelectedFile(null)
    setVideoName('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-head">
        <h2 className="panel-title">
          <Upload className="panel-icon" size={18} aria-hidden="true" />
          上传视频
        </h2>
        <p>上传后系统会自动抽帧并识别目标与衣物属性。</p>
      </div>

      <form className="form-stack" onSubmit={(event) => void handleSubmit(event)}>
        <label className="field-label" htmlFor="videoName">
          视频名称
        </label>
        <input
          id="videoName"
          className="text-input"
          value={videoName}
          onChange={(event) => setVideoName(event.target.value)}
          placeholder="不填则使用文件名"
        />

        <label className="field-label" htmlFor="videoFile">
          视频文件
        </label>
        <input
          id="videoFile"
          ref={fileInputRef}
          className="file-input"
          type="file"
          accept="video/*"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />

        <button className="primary-btn" type="submit" disabled={!selectedFile || uploading}>
          <span className="btn-content">
            <Upload size={16} aria-hidden="true" />
            {uploading ? '上传中...' : '上传并处理'}
          </span>
        </button>
      </form>

      {uploadStatus ? (
        <p className={`status-message ${uploadStatus.tone}`}>
          <span className="status-content">
            <StatusIcon className="status-icon" size={15} aria-hidden="true" />
            {uploadStatus.text}
          </span>
        </p>
      ) : (
        <p className="status-placeholder">
          <span className="status-content">
            <Info className="status-icon" size={15} aria-hidden="true" />
            建议上传 720p 或以上清晰度视频以获得更稳定的检索结果。
          </span>
        </p>
      )}
    </section>
  )
}
