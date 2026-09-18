import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getBatchProgress,
  uploadArchiveBatch,
  uploadFilesBatch,
  uploadFolderBatch,
} from '../services/api'

const MAX_FILE_BYTES = 100 * 1024 * 1024
const ARCHIVE_EXT = ['.zip', '.tar', '.7z', '.tar.gz', '.tgz']

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let n = bytes
  let i = 0
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024
    i += 1
  }
  return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function isArchiveName(name) {
  const lower = name.toLowerCase()
  return ARCHIVE_EXT.some((ext) => lower.endsWith(ext))
}

export default function BatchUploadPage() {
  const [mode, setMode] = useState('files')
  const [jobName, setJobName] = useState('')
  const [files, setFiles] = useState([])
  const [error, setError] = useState('')
  const [uploadPercent, setUploadPercent] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [batchId, setBatchId] = useState(null)
  const [progress, setProgress] = useState(null)
  const pollRef = useRef(null)
  const fileInputRef = useRef(null)
  const folderInputRef = useRef(null)
  const archiveInputRef = useRef(null)

  const totals = useMemo(() => {
    const totalSize = files.reduce((sum, f) => sum + (f.size || 0), 0)
    const oversized = files.filter((f) => f.size > MAX_FILE_BYTES)
    return { count: files.length, totalSize, oversized }
  }, [files])

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const resetSelection = () => {
    setFiles([])
    setError('')
    setUploadPercent(0)
    setBatchId(null)
    setProgress(null)
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const handleModeChange = (next) => {
    setMode(next)
    resetSelection()
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (folderInputRef.current) folderInputRef.current.value = ''
    if (archiveInputRef.current) archiveInputRef.current.value = ''
  }

  const validateAndSetFiles = (list) => {
    const arr = Array.from(list || [])
    if (mode === 'archive') {
      if (arr.length !== 1) {
        setError('Select a single archive file (.zip, .tar, .7z).')
        setFiles([])
        return
      }
      if (!isArchiveName(arr[0].name)) {
        setError('Archive must be .zip, .tar, or .7z.')
        setFiles([])
        return
      }
    }
    const oversized = arr.filter((f) => f.size > MAX_FILE_BYTES)
    if (oversized.length) {
      setError(
        `${oversized.length} file(s) exceed the 100MB limit: ${oversized
          .slice(0, 3)
          .map((f) => f.name)
          .join(', ')}${oversized.length > 3 ? '...' : ''}`
      )
    } else {
      setError('')
    }
    setFiles(arr)
    setBatchId(null)
    setProgress(null)
    setUploadPercent(0)
  }

  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current)
    const tick = async () => {
      try {
        const data = await getBatchProgress(id)
        setProgress(data)
        const status = (data.status || '').toLowerCase()
        if (['completed', 'done', 'success', 'failed', 'error'].includes(status)) {
          clearInterval(pollRef.current)
          pollRef.current = null
        }
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Progress polling failed')
      }
    }
    tick()
    pollRef.current = setInterval(tick, 1500)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    setError('')

    if (!files.length) {
      setError('Select at least one file to upload.')
      return
    }
    if (totals.oversized.length) {
      setError('Remove files over 100MB before uploading.')
      return
    }

    const formData = new FormData()
    const name = jobName.trim() || `Scan ${new Date().toLocaleString()}`
    formData.append('job_name', name)

    if (mode === 'archive') {
      formData.append('file', files[0])
    } else {
      const relativePaths = files.map((f) => f.webkitRelativePath || f.name)
      formData.append('relative_paths_json', JSON.stringify(relativePaths))
      files.forEach((f) => formData.append('files', f))
    }

    setUploading(true)
    setUploadPercent(0)
    setProgress(null)
    setBatchId(null)

    const onUploadProgress = (evt) => {
      if (!evt.total) return
      setUploadPercent(Math.round((evt.loaded / evt.total) * 100))
    }

    try {
      let result
      if (mode === 'files') {
        result = await uploadFilesBatch(formData, onUploadProgress)
      } else if (mode === 'folder') {
        result = await uploadFolderBatch(formData, onUploadProgress)
      } else {
        result = await uploadArchiveBatch(formData, onUploadProgress)
      }
      const id = result.id || result.batch_id
      setBatchId(id)
      setUploadPercent(100)
      startPolling(id)
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.response?.data?.message ||
          err?.message ||
          'Upload failed'
      )
    } finally {
      setUploading(false)
    }
  }

  const processed = progress?.processed_files ?? progress?.processed ?? 0
  const total = progress?.total_files ?? progress?.total ?? 0
  const remaining = Math.max(total - processed, 0)
  const percentDone =
    progress?.percent ??
    progress?.progress_percent ??
    (total ? Math.round((processed / total) * 100) : 0)
  const status = (progress?.status || '').toLowerCase()
  const isComplete = ['completed', 'done', 'success'].includes(status)

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Scan Upload</h1>
          <p className="muted">
            Upload files, a folder, or an archive for NER scanning. No file count limit; each file
            max 100MB.
          </p>
        </div>
      </div>

      <div className="mode-tabs">
        {[
          { id: 'files', label: 'Files' },
          { id: 'folder', label: 'Folder' },
          { id: 'archive', label: 'Archive' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={mode === tab.id ? 'mode-tab active' : 'mode-tab'}
            onClick={() => handleModeChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form className="panel upload-panel" onSubmit={handleUpload}>
        <label htmlFor="jobName">Job name</label>
        <input
          id="jobName"
          type="text"
          placeholder="Optional job name"
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
        />

        {mode === 'files' && (
          <div className="file-picker">
            <label htmlFor="filesInput">Select files</label>
            <input
              id="filesInput"
              ref={fileInputRef}
              type="file"
              multiple
              onChange={(e) => validateAndSetFiles(e.target.files)}
            />
          </div>
        )}

        {mode === 'folder' && (
          <div className="file-picker">
            <label htmlFor="folderInput">Select folder</label>
            <input
              id="folderInput"
              ref={folderInputRef}
              type="file"
              webkitdirectory=""
              directory=""
              multiple
              onChange={(e) => validateAndSetFiles(e.target.files)}
            />
          </div>
        )}

        {mode === 'archive' && (
          <div className="file-picker">
            <label htmlFor="archiveInput">Select archive (.zip / .tar / .7z)</label>
            <input
              id="archiveInput"
              ref={archiveInputRef}
              type="file"
              accept=".zip,.tar,.7z,.tgz,.tar.gz,application/zip,application/x-tar,application/x-7z-compressed"
              onChange={(e) => validateAndSetFiles(e.target.files)}
            />
          </div>
        )}

        <div className="selection-summary">
          <div>
            <strong>{totals.count}</strong> file{totals.count === 1 ? '' : 's'} selected
          </div>
          <div>Total size: <strong>{formatBytes(totals.totalSize)}</strong></div>
        </div>

        {error && <div className="alert danger">{error}</div>}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={uploading || !files.length || totals.oversized.length > 0}
        >
          {uploading ? `Uploading ${uploadPercent}%` : 'Start Upload'}
        </button>

        {(uploading || uploadPercent > 0) && (
          <div className="progress-block">
            <div className="progress-label">Upload progress</div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${uploadPercent}%` }} />
            </div>
            <div className="progress-meta">{uploadPercent}%</div>
          </div>
        )}
      </form>

      {batchId && (
        <section className="panel">
          <div className="panel-header">
            <h2>Processing batch #{batchId}</h2>
            {isComplete && (
              <Link to={`/batches/${batchId}`} className="btn btn-primary">
                Open batch detail
              </Link>
            )}
          </div>
          <div className="progress-block">
            <div className="progress-label">Scan progress</div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${percentDone}%` }} />
            </div>
            <div className="progress-meta">
              <span>
                {processed} / {total} files
              </span>
              <span>{percentDone}% done</span>
              <span>{remaining} remaining</span>
              <span className="status-pill">{progress?.status || 'processing'}</span>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
