/**
 * WebSocket service for real-time updates
 * Handles connection management and event listeners
 */

// Define WebSocket event types to match backend
export enum EventType {
  ANALYSIS_STARTED = "analysis_started",
  ANALYSIS_PROGRESS = "analysis_progress",
  ANALYSIS_COMPLETE = "analysis_complete",
  ANALYSIS_ERROR = "analysis_error",
  VULNERABILITY_DETECTED = "vulnerability_detected",
  CONNECTION_ESTABLISHED = "connection_established",
  BATCH_PROGRESS = "batch_progress",
  SYSTEM_NOTIFICATION = "system_notification"
}

// WebSocket event interface
export interface WebSocketEvent {
  event: EventType;
  data: any;
  timestamp: string;
}

// Progress data interface
export interface ProgressData {
  analysis_id: string;
  percent: number;
  step: string;
  details?: string;
}

// Analysis data interface
export interface AnalysisData {
  analysis_id: string;
  contract_name: string;
  file_count: number;
  status: string;
  results_summary?: {
    vulnerability_count: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

// Vulnerability data interface
export interface VulnerabilityData {
  analysis_id: string;
  vulnerability: {
    type: string;
    severity: string;
    line_number?: number;
    description: string;
    file_name: string;
  }
}

// Batch data interface
export interface BatchData {
  batch_id: string;
  total_contracts: number;
  completed: number;
  in_progress: number;
  failed: number;
  estimated_completion_time?: string;
}

// WebSocket event callback type
type EventCallback = (data: any) => void;

/**
 * WebSocket Manager class for frontend
 */
class WebSocketService {
  private socket: WebSocket | null = null;
  private eventListeners: Map<EventType, EventCallback[]> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private clientId: string | null = null;
  private authenticated: boolean = false;
  private userId: string | null = null;
  private url: string = "";
  private authToken: string | null = null;

  /**
   * Initialize WebSocket connection
   * @param baseUrl Base URL for WebSocket connection
   * @param token Authentication token (optional)
   */
  public connect(baseUrl: string, token?: string): void {
    this.url = baseUrl;
    this.authToken = token || null;
    
    const wsUrl = token 
      ? `${baseUrl}/ws/authenticated?token=${token}`
      : `${baseUrl}/ws`;
    
    this.socket = new WebSocket(wsUrl);
    
    // Set up event handlers
    this.socket.onopen = this.handleOpen.bind(this);
    this.socket.onclose = this.handleClose.bind(this);
    this.socket.onerror = this.handleError.bind(this);
    this.socket.onmessage = this.handleMessage.bind(this);
    
    console.log("WebSocket: Connecting to", wsUrl);
  }

  /**
   * Disconnect WebSocket
   */
  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.clientId = null;
      this.authenticated = false;
      console.log("WebSocket: Disconnected");
    }
  }

  /**
   * Subscribe to a specific event type
   * @param eventType Event type to subscribe to
   * @param callback Callback function to execute when event occurs
   * @returns Unsubscribe function
   */
  public on(eventType: EventType, callback: EventCallback): () => void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    
    const listeners = this.eventListeners.get(eventType) as EventCallback[];
    listeners.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  /**
   * Check if WebSocket is connected
   */
  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    return this.authenticated;
  }

  /**
   * Get client ID
   */
  public getClientId(): string | null {
    return this.clientId;
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(event: Event): void {
    console.log("WebSocket: Connection established");
    this.reconnectAttempts = 0;
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket: Connection closed (${event.code}): ${event.reason}`);
    
    // Attempt to reconnect if not intentionally closed
    if (event.code !== 1000) {
      this.attemptReconnect();
    }
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(event: Event): void {
    console.error("WebSocket: Error", event);
    this.attemptReconnect();
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketEvent;
      
      // Handle connection established event specially
      if (message.event === EventType.CONNECTION_ESTABLISHED) {
        this.clientId = message.data.client_id;
        this.authenticated = message.data.authenticated;
        this.userId = message.data.user_id;
        console.log(`WebSocket: Client ID ${this.clientId} established`);
      }
      
      // Dispatch to all listeners for this event type
      if (this.eventListeners.has(message.event)) {
        const listeners = this.eventListeners.get(message.event) as EventCallback[];
        listeners.forEach(callback => callback(message.data));
      }
    } catch (error) {
      console.error("WebSocket: Failed to parse message", error);
    }
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      
      console.log(`WebSocket: Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        this.connect(this.url, this.authToken || undefined);
      }, delay);
    } else {
      console.error("WebSocket: Max reconnection attempts reached");
    }
  }
}

// Create and export singleton instance
export const websocketService = new WebSocketService();

export default websocketService;
