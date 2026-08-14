import { api } from "@/lib/api/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface TtsStatus {
  available: boolean;
  provider: string;
}

export const ttsApi = {
  /** Whether real (non-mock) TTS is configured server-side for this user. */
  getStatus: () => api.get<TtsStatus>("/voice/tts/status"),

  /**
   * Synthesize a text into audio and return an object URL for it.
   *
   * Uses a raw fetch (the shared client is JSON-only) and requires the
   * caller to pass the current access token, matching the WS/Deepgram path.
   */
  async synthesizeToBlobUrl(token: string, text: string): Promise<string> {
    const response = await fetch(`${API_BASE}/voice/tts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      throw new Error(`TTS synthesis failed (${response.status})`);
    }
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  },
};
