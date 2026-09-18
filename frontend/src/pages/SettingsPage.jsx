import { useEffect, useState } from 'react'
import { useAuth } from '../App'
import {
  clearOpenAISettings,
  getOpenAISettings,
  saveOpenAISettings,
} from '../services/api'

export default function SettingsPage() {
  const { isAdmin } = useAuth()
  const [status, setStatus] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('gpt-4o-mini')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getOpenAISettings()
      setStatus(data)
      setModel(data.model || 'gpt-4o-mini')
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onSave = async (event) => {
    event.preventDefault()
    if (!isAdmin) return
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const data = await saveOpenAISettings({ api_key: apiKey.trim(), model })
      setStatus(data)
      setApiKey('')
      setMessage(data.message || 'OpenAI API key saved.')
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to save API key')
    } finally {
      setSaving(false)
    }
  }

  const onClear = async () => {
    if (!isAdmin) return
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const data = await clearOpenAISettings()
      setStatus(data)
      setMessage(data.message || 'OpenAI API key cleared.')
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to clear API key')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="page-loading">Loading settings...</div>
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="muted">Configure OpenAI for GLiNER vs OpenAI comparison</p>
        </div>
      </div>

      {message && <div className="alert success">{message}</div>}
      {error && <div className="alert danger">{error}</div>}

      <section className="panel settings-panel">
        <div className="panel-header">
          <h2>OpenAI</h2>
          <span className={`badge ${status?.configured ? 'success' : 'warn'}`}>
            {status?.configured ? 'Configured' : 'Not configured'}
          </span>
        </div>

        <div className="meta-grid panel-pad">
          <div className="meta-card">
            <div className="meta-label">Status</div>
            <div>{status?.configured ? 'Ready' : 'Missing API key'}</div>
          </div>
          <div className="meta-card">
            <div className="meta-label">Model</div>
            <div>{status?.model || 'gpt-4o-mini'}</div>
          </div>
          <div className="meta-card">
            <div className="meta-label">Key</div>
            <div className="mono">{status?.api_key_masked || '—'}</div>
          </div>
        </div>

        {!isAdmin && (
          <p className="muted panel-hint">
            Only admins can add or change the OpenAI API key. Ask an admin to configure it.
          </p>
        )}

        {isAdmin && (
          <form className="settings-form" onSubmit={onSave}>
            <label htmlFor="openaiKey">OpenAI API key</label>
            <input
              id="openaiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
              required
            />

            <label htmlFor="openaiModel">Model</label>
            <select
              id="openaiModel"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4.1-mini">gpt-4.1-mini</option>
              <option value="gpt-4.1">gpt-4.1</option>
            </select>

            <div className="header-actions">
              <button type="submit" className="btn btn-primary" disabled={saving || !apiKey.trim()}>
                {saving ? 'Saving...' : 'Save & enable OpenAI'}
              </button>
              {status?.configured && (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={onClear}
                  disabled={saving}
                >
                  Clear key
                </button>
              )}
            </div>
          </form>
        )}
      </section>
    </div>
  )
}
