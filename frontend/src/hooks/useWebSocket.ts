import { useState, useEffect, useCallback, useMemo } from 'react';
import websocketService, { EventType } from '../services/websocket';

/**
 * Configuration options for the WebSocket hook
 */
interface UseWebSocketOptions {
  autoConnect?: boolean;
  apiBaseUrl?: string;
  token?: string | null;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: any) => void;
}

/**
 * WebSocket hook for React components
 * 
 * @param options WebSocket options
 * @returns WebSocket hook methods and state
 */
export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    autoConnect = true,
    apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000',
    token = null,
    onOpen,
    onClose,
    onError
  } = options;

  // Calculate WebSocket URL
  const wsBaseUrl = useMemo(() => {
    // Convert HTTP(S) URL to WS(S)
    const url = new URL(apiBaseUrl);
    url.protocol = url.protocol.replace('http', 'ws');
    return url.toString();
  }, [apiBaseUrl]);
  
  const [connected, setConnected] = useState<boolean>(false);
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [clientId, setClientId] = useState<string | null>(null);

  // Auto-connect when the component mounts
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Subscribe to connection established event
  useEffect(() => {
    const unsubscribe = websocketService.on(EventType.CONNECTION_ESTABLISHED, (data) => {
      setConnected(true);
      setAuthenticated(data.authenticated || false);
      setClientId(data.client_id || null);
      
      if (onOpen) {
        onOpen();
      }
    });
    
    return unsubscribe;
  }, [onOpen]);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    websocketService.connect(wsBaseUrl, token || undefined);
  }, [wsBaseUrl, token]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    websocketService.disconnect();
    setConnected(false);
    setAuthenticated(false);
    setClientId(null);
    
    if (onClose) {
      onClose();
    }
  }, [onClose]);

  /**
   * Subscribe to a specific event type
   * Returns an unsubscribe function
   */
  const subscribe = useCallback((eventType: EventType, callback: (data: any) => void) => {
    return websocketService.on(eventType, callback);
  }, []);

  return {
    connected,
    authenticated,
    clientId,
    connect,
    disconnect,
    subscribe,
    EventType
  };
};

export default useWebSocket;
