import { useEffect } from "react";

import { settings } from "@/conf";
import EventEmitter from "eventemitter3";

const ee = new EventEmitter();

export const useSSE = (): EventEmitter => {
  useEffect(() => {
    const eventSource = new EventSource(`${settings.API_URL}/sse`, {
      withCredentials: true,
    });

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      ee.emit(data.type, data);
    };

    eventSource.onerror = (error) => {
      console.error("SSE Error:", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return ee;
};
