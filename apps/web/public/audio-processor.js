/**
 * AudioWorklet processor for capturing raw PCM audio.
 *
 * Receives audio samples from the microphone, downmixes to mono,
 * resamples to 16kHz, and sends Int16 PCM chunks via MessagePort.
 */

class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = new Float32Array(0);
    this._targetSampleRate = 16000;
    this._chunkDuration = 0.5; // seconds per chunk
    this._chunkSize = Math.floor(this._targetSampleRate * this._chunkDuration);
    this._resampleRatio = sampleRate / this._targetSampleRate;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    // Downmix to mono (take first channel)
    const channelData = input[0];
    if (!channelData) return true;

    // Resample from sampleRate to 16kHz
    const resampled = this._resample(channelData, this._resampleRatio);

    // Append to buffer
    const newBuffer = new Float32Array(this._buffer.length + resampled.length);
    newBuffer.set(this._buffer, 0);
    newBuffer.set(resampled, this._buffer.length);
    this._buffer = newBuffer;

    // Send chunks when we have enough
    while (this._buffer.length >= this._chunkSize) {
      const chunk = this._buffer.slice(0, this._chunkSize);
      this._buffer = this._buffer.slice(this._chunkSize);

      // Convert Float32 to Int16 PCM
      const pcm = this._float32ToInt16(chunk);
      this.port.postMessage(pcm, [pcm.buffer]);
    }

    return true;
  }

  _resample(data, ratio) {
    if (ratio === 1) return data;

    const newLength = Math.round(data.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const srcIdx = i * ratio;
      const idx = Math.floor(srcIdx);
      const frac = srcIdx - idx;

      if (idx + 1 < data.length) {
        result[i] = data[idx] * (1 - frac) + data[idx + 1] * frac;
      } else {
        result[i] = data[idx] || 0;
      }
    }

    return result;
  }

  _float32ToInt16(float32Array) {
    const int16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
