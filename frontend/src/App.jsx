import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''

function App() {
  const [overview, setOverview] = useState(null)
  const [channels, setChannels] = useState([])
  const [messages, setMessages] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
  async function loadData() {
    try {
      const [overviewRes, channelsRes, messagesRes] = await Promise.all([
        fetch(`${API_BASE}/api/overview`),
        fetch(`${API_BASE}/api/channels`),
        fetch(`${API_BASE}/api/messages/recent?limit=8`),
      ])

      if (!overviewRes.ok || !channelsRes.ok || !messagesRes.ok) {
        throw new Error('API request failed. Start the backend with: make api')
      }

      setOverview(await overviewRes.json())
      setChannels(await channelsRes.json())
      setMessages(await messagesRes.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  loadData()
  }, [])

  if (loading) {
    return <p className="status">Loading workspace analytics...</p>
  }

  if (error) {
    return (
      <main className="page">
        <h1>Slack Community Analytics</h1>
        <p className="error">{error}</p>
        <p>Run: <code>make db-up</code>, <code>make db-load</code>, then <code>make api</code></p>
      </main>
    )
  }

  const postgres = overview.postgres
  const mongo = overview.mongo

  return (
    <main className="page">
      <header>
        <h1>Slack Community Analytics</h1>
        <p>Batch 6 workspace insights — React UI, Python API, PostgreSQL features, MongoDB archive</p>
      </header>

      <section className="cards">
        <article><h3>Channels</h3><p>{postgres.channel_count}</p></article>
        <article><h3>Active users</h3><p>{postgres.user_count}</p></article>
        <article><h3>Indexed messages</h3><p>{postgres.message_count}</p></article>
        <article><h3>Archived messages</h3><p>{mongo.messages}</p></article>
      </section>

      <section>
        <h2>Top channels by activity</h2>
        <table>
          <thead>
            <tr>
              <th>Channel</th>
              <th>Messages</th>
              <th>Replies</th>
              <th>Reactions</th>
            </tr>
          </thead>
          <tbody>
            {channels.slice(0, 8).map((row) => (
              <tr key={row.channel}>
                <td>{row.channel}</td>
                <td>{row.message_count}</td>
                <td>{row.reply_total}</td>
                <td>{row.reaction_total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Recent messages from the archive</h2>
        <ul className="messages">
          {messages.map((message, index) => (
            <li key={`${message.ts}-${index}`}>
              <strong>{message.channel}</strong> — {message.text}
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}

export default App
