import { useEffect, useState, useRef } from 'react'

interface WebSocketMessage {
  type: 'progress' | 'result' | 'error'
  step?: string
  status?: string
  data?: any
  message?: string
}

export function useWebSocket(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!sessionId) return

    const wsUrl = `ws://localhost:8000/ws/${sessionId}`
    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }

    ws.current.onmessage = (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        setMessages((prev: WebSocketMessage[]) => [...prev, message])
      } catch (error: unknown) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.current.onerror = (error: Event) => {
      console.error('WebSocket error:', error)
    }

    ws.current.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [sessionId])

  const sendMessage = (message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }

  return { isConnected, messages, sendMessage }
}
