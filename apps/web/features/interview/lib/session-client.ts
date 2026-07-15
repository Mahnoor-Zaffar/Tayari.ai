/** WebSocket client for the interview session protocol.

Handles connection lifecycle, reconnection with backoff,
heartbeat, and message parsing.
*/

const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 15_000;
const HEARTBEAT_INTERVAL_MS = 10_000;
const MAX_RECONNECT_ATTEMPTS = 10;

export type SessionClientEvent =
  | { type: "open" }
  | { type: "close"; code: number; reason: string }
  | { type: "message"; data: Record<string, unknown> }
  | { type: "error"; error: string };

export type SessionClientListener = (event: SessionClientEvent) => void;

export class SessionClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private listeners: Set<SessionClientListener> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private closed = false;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.closed = false;
    this._emit({ type: "error", error: "" });
    this._open();
  }

  private _open(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this._emit({ type: "open" });
        this._startHeartbeat();
        this._send({ type: "session.join", payload: { token: this.token } });
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as Record<string, unknown>;
          this._emit({ type: "message", data });
        } catch {
          // Ignore unparseable messages
        }
      };

      this.ws.onclose = (event: CloseEvent) => {
        this._stopHeartbeat();
        this._emit({ type: "close", code: event.code, reason: event.reason });
        if (!this.closed) {
          this._scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        // onclose will fire after onerror, reconnection is handled there
      };
    } catch (err) {
      this._emit({ type: "error", error: String(err) });
      if (!this.closed) {
        this._scheduleReconnect();
      }
    }
  }

  send(type: string, payload: Record<string, unknown> = {}): void {
    this._send({ type, payload });
  }

  private _send(msg: { type: string; payload: Record<string, unknown> }): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  close(): void {
    this.closed = true;
    this._stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close(1000, "Client closed");
    this.ws = null;
  }

  subscribe(listener: SessionClientListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private _emit(event: SessionClientEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch {
        // Silently handle listener errors
      }
    }
  }

  private _scheduleReconnect(): void {
    if (this.closed || this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) return;
    this.reconnectAttempts++;
    this._emit({ type: "error", error: "reconnecting" });
    const delay = Math.min(
      RECONNECT_BASE_DELAY_MS * Math.pow(2, this.reconnectAttempts - 1),
      RECONNECT_MAX_DELAY_MS,
    );
    this.reconnectTimer = setTimeout(() => this._open(), delay);
  }

  private _startHeartbeat(): void {
    this._stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this._send({ type: "heartbeat", payload: { timestamp: Date.now() } });
    }, HEARTBEAT_INTERVAL_MS);
  }

  private _stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  get attemptCount(): number {
    return this.reconnectAttempts;
  }
}
