import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../App'
import {
  getBatch,
  getBatchComparison,
  getBatchEntities,
  getBatchProgress,
  getEntityFiles,
  getOpenAISettings,
  saveOpenAISettings,
} from '../services/api'

function statusClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'completed_with_errors' || s === 'done' || s === 'success') {
    return 'badge success'
  }
  if (s === 'processing' || s === 'running' || s === 'in_progress' || s === 'queued') {
    return 'badge warn'
  }
  if (s === 'failed' || s === 'error') return 'badge danger'
  return 'badge'
}

function EntityTable({ rows, onEntityClick, emptyLabel }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Text</th>
            <th>Label</th>
            <th>Score</th>
            <th>File</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={4} className="empty-cell">
                {emptyLabel}
              </td>
            </tr>
          )}
          {rows.map((entity, idx) => (
            <tr key={entity.id || `${entity.text}-${entity.label}-${idx}`}>
              <td>
                <button
                  type="button"
                  className="entity-link"
                  onClick={() => onEntityClick(entity)}
                  title="Show files containing this entity"
                >
                  {entity.text || '—'}
                </button>
              </td>
              <td>
                <span className="badge">{entity.label || '—'}</span>
              </td>
              <td>
                {entity.score != null ? Number(entity.score).toFixed(3) : '—'}
              </td>
              <td className="mono">
                {entity.filename ||
                  entity.file_path?.split(/[/\\]/).pop() ||
                  '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function BatchDetailPage() {
  const { id } = useParams()
  const { isAdmin } = useAuth()
  const [batch, setBatch] = useState(null)
  const [progress, setProgress] = useState(null)
  const [entities, setEntities] = useState([])
  const [labelFilter, setLabelFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('gliner')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filePanel, setFilePanel] = useState(null)
  const [fileLoading, setFileLoading] = useState(false)
  const [comparison, setComparison] = useState(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [comparisonError, setComparisonError] = useState('')
  const [openaiStatus, setOpenaiStatus] = useState(null)
  const [inlineKey, setInlineKey] = useState('')
  const [savingKey, setSavingKey] = useState(false)
  const [keyMessage, setKeyMessage] = useState('')

  useEffect(() => {
    let active = true
    let timer = null

    const load = async () => {
      try {
        const [batchData, entitiesData, progressData, openaiData] = await Promise.all([
          getBatch(id),
          getBatchEntities(id),
          getBatchProgress(id).catch(() => null),
          getOpenAISettings().catch(() => null),
        ])
        if (!active) return
        setBatch(batchData)
        const list = Array.isArray(entitiesData)
          ? entitiesData
          : entitiesData?.entities || entitiesData?.items || []
        setEntities(list)
        setProgress(progressData)
        setOpenaiStatus(openaiData)
        setError('')

        const status = (progressData?.status || batchData?.status || '').toLowerCase()
        if (
          !['completed', 'completed_with_errors', 'done', 'success', 'failed', 'error'].includes(
            status,
          )
        ) {
          timer = setTimeout(load, 1500)
        }
      } catch (err) {
        if (active) {
          setError(err?.response?.data?.detail || err?.message || 'Failed to load batch')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    load()
    return () => {
      active = false
      if (timer) clearTimeout(timer)
    }
  }, [id])

  const glinerEntities = useMemo(
    () => entities.filter((e) => String(e.source || '').toLowerCase() !== 'openai'),
    [entities],
  )

  const labels = useMemo(() => {
    const set = new Set()
    glinerEntities.forEach((e) => {
      if (e.label) set.add(e.label)
    })
    return Array.from(set).sort()
  }, [glinerEntities])

  const filtered = useMemo(() => {
    let rows = sourceFilter === 'all' ? entities : glinerEntities
    if (labelFilter) rows = rows.filter((e) => e.label === labelFilter)
    return rows
  }, [entities, glinerEntities, labelFilter, sourceFilter])

  const onEntityClick = async (entity) => {
    setFileLoading(true)
    setFilePanel({ text: entity.text, label: entity.label, files: [], file_count: 0 })
    try {
      const data = await getEntityFiles(id, entity.text, entity.label)
      setFilePanel(data)
    } catch (err) {
      setFilePanel({
        text: entity.text,
        label: entity.label,
        files: [],
        file_count: 0,
        error: err?.response?.data?.detail || err?.message || 'Failed to load files',
      })
    } finally {
      setFileLoading(false)
    }
  }

  const loadComparison = async (refresh = false) => {
    setComparisonLoading(true)
    setComparisonError('')
    try {
      const data = await getBatchComparison(id, refresh)
      setComparison(data)
      setOpenaiStatus((prev) => ({
        ...(prev || {}),
        configured: !!data.openai_configured,
      }))
    } catch (err) {
      setComparisonError(
        err?.response?.data?.detail || err?.message || 'Comparison failed',
      )
    } finally {
      setComparisonLoading(false)
    }
  }

  const saveInlineOpenAIKey = async (event) => {
    event.preventDefault()
    if (!isAdmin || !inlineKey.trim()) return
    setSavingKey(true)
    setKeyMessage('')
    setComparisonError('')
    try {
      const data = await saveOpenAISettings({
        api_key: inlineKey.trim(),
        model: 'gpt-4o-mini',
      })
      setOpenaiStatus(data)
      setInlineKey('')
      setKeyMessage(data.message || 'OpenAI enabled.')
      await loadComparison(true)
    } catch (err) {
      setComparisonError(
        err?.response?.data?.detail || err?.message || 'Failed to save OpenAI API key',
      )
    } finally {
      setSavingKey(false)
    }
  }

  const exportJson = () => {
    const payload = {
      batch,
      entities: filtered,
      comparison,
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch-${id}-entities.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <div className="page-loading">Loading batch...</div>
  }

  if (error) {
    return (
      <div className="page">
        <div className="alert danger">{error}</div>
        <Link to="/" className="link">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const processed = progress?.processed_files ?? batch?.processed_files ?? 0
  const total = progress?.total_files ?? batch?.total_files ?? 0
  const percent =
    progress?.percent_complete ??
    progress?.percent ??
    (total ? Math.round((processed / total) * 100) : 0)

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{batch?.job_name || batch?.name || `Batch #${id}`}</h1>
          <p className="muted">Batch ID: {id}</p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn btn-secondary" onClick={exportJson}>
            Export JSON
          </button>
          <Link to="/history" className="btn btn-ghost">
            History
          </Link>
        </div>
      </div>

      <div className="meta-grid">
        <div className="meta-card">
          <div className="meta-label">Status</div>
          <div>
            <span className={statusClass(progress?.status || batch?.status)}>
              {progress?.status || batch?.status || 'unknown'}
            </span>
          </div>
        </div>
        <div className="meta-card">
          <div className="meta-label">Progress</div>
          <div>
            {processed} / {total} files ({percent}%)
          </div>
        </div>
        <div className="meta-card">
          <div className="meta-label">Entities</div>
          <div>{glinerEntities.length}</div>
        </div>
        <div className="meta-card">
          <div className="meta-label">Created</div>
          <div>
            {batch?.created_at ? new Date(batch.created_at).toLocaleString() : '—'}
          </div>
        </div>
      </div>

      <div className="progress-block panel-pad">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${percent}%` }} />
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Entities</h2>
          <div className="filter-row">
            <label htmlFor="sourceFilter">Source</label>
            <select
              id="sourceFilter"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
            >
              <option value="gliner">GLiNER / rules</option>
              <option value="all">All sources</option>
            </select>
            <label htmlFor="labelFilter">Label</label>
            <select
              id="labelFilter"
              value={labelFilter}
              onChange={(e) => setLabelFilter(e.target.value)}
            >
              <option value="">All labels</option>
              {labels.map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <p className="muted panel-hint">
          Click an entity text to see filenames where it appears (content is never shown).
        </p>
        <EntityTable
          rows={filtered}
          onEntityClick={onEntityClick}
          emptyLabel={`No entities found${labelFilter ? ` for label "${labelFilter}"` : ''}.`}
        />
      </section>

      {filePanel && (
        <section className="panel file-panel">
          <div className="panel-header">
            <h2>Files for entity</h2>
            <button type="button" className="btn btn-ghost" onClick={() => setFilePanel(null)}>
              Close
            </button>
          </div>
          <p>
            <strong>{filePanel.text}</strong>{' '}
            <span className="badge">{filePanel.label}</span>
          </p>
          {fileLoading && <p className="muted">Loading filenames...</p>}
          {filePanel.error && <div className="alert danger">{filePanel.error}</div>}
          {!fileLoading && !filePanel.error && (
            <>
              <p className="muted">{filePanel.file_count || 0} file(s)</p>
              <ul className="file-list">
                {(filePanel.files || []).map((name) => (
                  <li key={name} className="mono">
                    {name}
                  </li>
                ))}
              </ul>
              {(filePanel.files || []).length === 0 && (
                <p className="muted">No filenames found for this entity.</p>
              )}
            </>
          )}
        </section>
      )}

      <section className="panel">
        <div className="panel-header">
          <h2>GLiNER vs OpenAI</h2>
          <div className="header-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => loadComparison(false)}
              disabled={comparisonLoading}
            >
              {comparisonLoading ? 'Comparing...' : 'Run comparison'}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => loadComparison(true)}
              disabled={comparisonLoading}
            >
              Refresh OpenAI
            </button>
          </div>
        </div>
        {comparisonError && <div className="alert danger">{comparisonError}</div>}
        {keyMessage && <div className="alert success">{keyMessage}</div>}
        {!openaiStatus?.configured && (
          <div className="openai-setup panel-pad">
            <p className="muted">
              OpenAI is not configured. Add an API key to enable comparison.
              {isAdmin ? '' : ' Ask an admin, or open Settings.'}
            </p>
            {isAdmin ? (
              <form className="inline-key-form" onSubmit={saveInlineOpenAIKey}>
                <input
                  type="password"
                  value={inlineKey}
                  onChange={(e) => setInlineKey(e.target.value)}
                  placeholder="Paste OpenAI API key (sk-...)"
                  autoComplete="off"
                  required
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={savingKey || !inlineKey.trim()}
                >
                  {savingKey ? 'Saving...' : 'Save & enable OpenAI'}
                </button>
                <Link to="/settings" className="btn btn-ghost">
                  Settings
                </Link>
              </form>
            ) : (
              <Link to="/settings" className="btn btn-secondary">
                Open Settings
              </Link>
            )}
          </div>
        )}
        {openaiStatus?.configured && (
          <p className="muted panel-hint">
            OpenAI ready ({openaiStatus.model || 'gpt-4o-mini'}
            {openaiStatus.api_key_masked ? `, key ${openaiStatus.api_key_masked}` : ''}).
            Manage in <Link to="/settings">Settings</Link>.
          </p>
        )}
        {!comparison && !comparisonLoading && openaiStatus?.configured && (
          <p className="muted panel-hint">
            Compare entities detected by GLiNER and OpenAI on the same uploaded files.
          </p>
        )}
        {comparison && (
          <>
            <div className="meta-grid">
              <div className="meta-card">
                <div className="meta-label">Both</div>
                <div>{comparison.counts?.both ?? 0}</div>
              </div>
              <div className="meta-card">
                <div className="meta-label">GLiNER only</div>
                <div>{comparison.counts?.gliner_only ?? 0}</div>
              </div>
              <div className="meta-card">
                <div className="meta-label">OpenAI only</div>
                <div>{comparison.counts?.openai_only ?? 0}</div>
              </div>
              <div className="meta-card">
                <div className="meta-label">Type diffs</div>
                <div>{comparison.counts?.type_differences ?? 0}</div>
              </div>
            </div>
            {!comparison.openai_configured && (
              <div className="alert warn">
                OpenAI is not configured. Add an API key above or in Settings.
              </div>
            )}
            {comparison.openai_status && comparison.openai_status.startsWith('error') && (
              <div className="alert danger">{comparison.openai_status}</div>
            )}

            <h3 className="section-sub">Detected by both</h3>
            <EntityTable
              rows={comparison.both || []}
              onEntityClick={onEntityClick}
              emptyLabel="No shared entities."
            />

            <h3 className="section-sub">GLiNER only</h3>
            <EntityTable
              rows={comparison.gliner_only || []}
              onEntityClick={onEntityClick}
              emptyLabel="No GLiNER-only entities."
            />

            <h3 className="section-sub">OpenAI only</h3>
            <EntityTable
              rows={comparison.openai_only || []}
              onEntityClick={onEntityClick}
              emptyLabel="No OpenAI-only entities."
            />

            <h3 className="section-sub">Entity-type differences</h3>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>GLiNER labels</th>
                    <th>OpenAI labels</th>
                  </tr>
                </thead>
                <tbody>
                  {(comparison.type_differences || []).length === 0 && (
                    <tr>
                      <td colSpan={3} className="empty-cell">
                        No type differences.
                      </td>
                    </tr>
                  )}
                  {(comparison.type_differences || []).map((row) => (
                    <tr key={row.text}>
                      <td>{row.text}</td>
                      <td>{(row.gliner_labels || []).join(', ')}</td>
                      <td>{(row.openai_labels || []).join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
    </div>
  )
}
