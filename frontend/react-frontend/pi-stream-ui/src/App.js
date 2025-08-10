// This is the main React app for the wildlife monitoring dashboard
// It handles video streaming, sensor data display, and mode switching between streaming and motion detection

import React, { useEffect, useRef, useState, useCallback } from "react";
import Hls from "hls.js";
import "./App.css";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Config
const RETRY = { maxAttempts: 20, intervalMs: 2000 };
const POLL = {
  sensorMs: 10_000,
  imageMs: 30_000,
  modeMs: 5_000,
};
const MODE = { STREAM: "stream", MOTION: "motion", UNKNOWN: "unknown" };

// Mode labels and spinner
function ModeBadge({ mode, loading }) {
  if (loading) return <div className="spinner" aria-label="Switching mode…" />;
  const label =
    mode === MODE.STREAM
      ? "Streaming Active"
      : mode === MODE.MOTION
      ? "Motion Detection Active"
      : "Mode Unknown";
  return <span className={`badge ${mode}`}>{label}</span>;
}

function SensorChart({ data }) {
  if (!data?.length) return null;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" tick={{ fontSize: 10 }} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="temperature" stroke="#ff7300" dot={false} />
        <Line type="monotone" dataKey="humidity" stroke="#007bff" dot={false} />
        <Line type="monotone" dataKey="pressure" stroke="#28a745" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Main app component
function App() {
  const videoRef = useRef(null);

  const [sensorData, setSensorData] = useState(null);
  const [sensorHistory, setSensorHistory] = useState([]);
  const [lastSensorUpdate, setLastSensorUpdate] = useState(null);

  const [imageURL, setImageURL] = useState(null);

  const [mode, setMode] = useState(MODE.UNKNOWN);
  const [modeLoading, setModeLoading] = useState(false);

  const [apiOnline, setApiOnline] = useState(true);
  const [error, setError] = useState(null);

  // .env load
  const streamURL = process.env.REACT_APP_STREAM_URL;
  const sensorURL = process.env.REACT_APP_SENSOR_URL;
  const apiBase = process.env.REACT_APP_API_BASE;
  const imageEndpoint = `${apiBase}/latest-image`;
  const captureEndpoint = `${apiBase}/capture`;

  // Check if HLS is supported. Attach to <video> element.
  // If not supported, fallback to native HLS support in Safari.
  const attachHls = useCallback(
    (url) => {
      const video = videoRef.current;
      if (!video) return;

      let hls;
      if (Hls.isSupported()) {
        hls = new Hls();
        hls.loadSource(url);
        hls.attachMedia(video);
        hls.on(Hls.Events.ERROR, (_evt, data) => {
          // Log HLS errors
          console.warn("HLS error:", data?.details || data);
        });
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = url;
      } else {
        setError("HLS is not supported in this browser.");
      }
      return () => hls?.destroy();
    },
    [setError]
  );

  const retryLoadStream = useCallback(() => {
    let attempts = 0;

    const check = () => {
      fetch(streamURL, { method: "HEAD" })
        .then((res) => {
          if (!res.ok) throw new Error("Stream not ready");
          const cleanup = attachHls(streamURL);
          return cleanup;
        })
        .catch(() => {
          attempts += 1;
          if (attempts < RETRY.maxAttempts) {
            setTimeout(check, RETRY.intervalMs);
          } else {
            setError("Stream unavailable after retries.");
          }
        });
    };

    check();
  }, [attachHls, streamURL]);

  // When in STREAM mode, attach HLS to the <video>. On mode change, hard-reset the element.
  useEffect(() => {
    if (mode !== MODE.STREAM) return;

    const cleanup = attachHls(streamURL);
    return () => {
      const video = videoRef.current;
      if (video) {
        try {
          video.pause();
          video.removeAttribute("src");
          video.load();
        } catch (_) {}
      }
      cleanup?.();
    };
  }, [mode, attachHls, streamURL]);

  // Poll sensors and keep a history for the chart
  useEffect(() => {
    let cancelled = false;

    const fetchSensor = async () => {
      try {
        const res = await fetch(sensorURL);
        if (!res.ok) throw new Error("Bad sensor response");
        const data = await res.json();
        if (cancelled) return;

        setSensorData(data);
        setLastSensorUpdate(new Date().toLocaleTimeString());

        setSensorHistory((prev) => {
          // Keep the last X points so the chart stays readable
          const entry = {
            time: new Date().toLocaleTimeString(),
            temperature: Number.parseFloat(Number(data.temperature).toFixed(2)),
            humidity: Number.parseFloat(Number(data.humidity).toFixed(2)),
            // Convert Pa to kPa
            pressure: Number.parseFloat(Number(data.pressure / 1000).toFixed(2)),
          };
          const MAX_POINTS = 20;
          return [...prev, entry].slice(-MAX_POINTS);
        });
      } catch {
        if (!cancelled) setError("Sensor offline");
      }
    };

    fetchSensor();
    const id = setInterval(fetchSensor, POLL.sensorMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [sensorURL]);

  // Refresh the "latest still" image periodically
  useEffect(() => {
    const refresh = () => setImageURL(`${imageEndpoint}?t=${Date.now()}`);
    refresh();
    const id = setInterval(refresh, POLL.imageMs);
    return () => clearInterval(id);
  }, [imageEndpoint]);

  // Keep UI in sync with backend mode (stream vs motion). If API drops, show banner.
  useEffect(() => {
    let cancelled = false;

    const fetchMode = async () => {
      try {
        const res = await fetch(`${apiBase}/mode`);
        if (!res.ok) throw new Error("Bad mode response");
        const data = await res.json();
        if (cancelled) return;

        if (data?.mode) setMode(data.mode);
        setApiOnline(true);
      } catch {
        if (!cancelled) setApiOnline(false);
      }
    };

    fetchMode();
    const id = setInterval(fetchMode, POLL.modeMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [apiBase]);

  // Switch between motion and stream.
  const toggleMode = async () => {
    const target = mode === MODE.MOTION ? MODE.STREAM : MODE.MOTION;
    setModeLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBase}/set-mode/${target}`, { method: "POST" });
      if (!res.ok) throw new Error("Toggle failed");

      // Poll briefly until the server reports a definite mode
      let next = null;
      for (let i = 0; i < 10; i++) {
        const m = await fetch(`${apiBase}/mode`).then((r) => r.json());
        if (m?.mode && m.mode !== MODE.UNKNOWN) {
          next = m.mode;
          break;
        }
        // eslint-disable-next-line no-await-in-loop
        await new Promise((r) => setTimeout(r, 1000));
      }

      if (!next) throw new Error("Mode did not settle");
      setMode(next);
      if (next === MODE.STREAM) retryLoadStream();
    } catch {
      setError("Failed to toggle mode");
    } finally {
      setModeLoading(false);
    }
  };

  // Ask backend to take a still; wait 3 sec, then refresh image preview
  const handleCapture = async () => {
    try {
      const res = await fetch(captureEndpoint, { method: "POST" });
      if (!res.ok) throw new Error("Capture failed");

      // Give backend time to process the image / upload it
      setTimeout(() => setImageURL(`${imageEndpoint}?t=${Date.now()}`), 3000);
    } catch {
      setError("Failed to capture image");
    }
  };

  // Render
  return (
    <div className="container">
      <h1>Wildlife Monitoring Dashboard</h1>

      {/* If the API drops, make it obvious */}
      {!apiOnline && <p className="error">Backend API offline</p>}

      <div className="video-wrapper">
        <video ref={videoRef} controls autoPlay muted />
        <div className="mode-status">
          <ModeBadge mode={mode} loading={modeLoading} />
        </div>
        <button onClick={toggleMode} disabled={modeLoading} title="Toggle streaming/motion detection">
          {modeLoading
            ? "Switching..."
            : mode === MODE.MOTION
            ? "Switch to Streaming"
            : mode === MODE.STREAM
            ? "Switch to Motion Detection"
            : "Toggle Mode"}
        </button>
      </div>

      <div className="sensor-box">
        <h2>Sensor Data</h2>
        {sensorData ? (
          <>
            <p>
              <strong>Temp:</strong> {Number(sensorData.temperature).toFixed(2)} °C
            </p>
            <p>
              <strong>Pressure:</strong> {(Number(sensorData.pressure) / 1000).toFixed(2)} kPa
            </p>
            <p>
              <strong>Humidity:</strong> {Number(sensorData.humidity).toFixed(2)} %
            </p>
            <p className="timestamp">Last updated: {lastSensorUpdate}</p>

            <div style={{ marginTop: 20 }}>
              <h3>Sensor Trends (last ~3 min)</h3>
              <SensorChart data={sensorHistory} />
            </div>
          </>
        ) : error ? (
          <p className="error">{error}</p>
        ) : (
          // Avoid a broken-image feel while sensors load
          <div className="spinner" aria-label="Loading sensors…" />
        )}
      </div>

      <div className="capture-section">
        <h2>Still Capture</h2>
        <button onClick={handleCapture} title="Trigger remote capture">
          Capture Photo
        </button>
        {imageURL && (
          <img
            src={imageURL}
            alt="Latest still"
            onError={(e) => {
              // Fallback so the UI doesn't show a broken image while the file is still uploading
              e.currentTarget.src = "/placeholder.jpg";
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App;
