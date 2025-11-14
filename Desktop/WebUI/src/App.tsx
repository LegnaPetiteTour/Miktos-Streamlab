import { useState, useEffect } from 'react';

interface HealthMetrics {
  fps: number;
  cpu_usage: number;
  dropped_frames: number;
  network_status: string;
}

interface Scene {
  name: string;
  active: boolean;
}

interface Destination {
  name: string;
  status: string;
  bitrate: string;
}

function App() {
  const [health, setHealth] = useState<HealthMetrics>({
    fps: 0,
    cpu_usage: 0,
    dropped_frames: 0,
    network_status: 'unknown'
  });
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [currentScene, setCurrentScene] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [destinations] = useState<Destination[]>([
    { name: 'YouTube', status: 'ready', bitrate: '0 Mbps' },
    { name: 'Facebook', status: 'ready', bitrate: '0 Mbps' },
    { name: 'Twitch', status: 'ready', bitrate: '0 Mbps' }
  ]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          const data = await response.json();
          setHealth(data.metrics);
        }
      } catch (error) {
        console.error('Error fetching health:', error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchScenes = async () => {
      try {
        const response = await fetch('/api/scenes');
        if (response.ok) {
          const data = await response.json();
          setScenes(data.scenes);
          setCurrentScene(data.current_scene);
        }
      } catch (error) {
        console.error('Error fetching scenes:', error);
      }
    };

    fetchScenes();
  }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'health_update') {
        setHealth(data.data);
      }
    };

    return () => ws.close();
  }, []);

  const handleSceneSwitch = async (sceneName: string) => {
    try {
      const response = await fetch('/api/scenes/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scene_name: sceneName })
      });

      if (response.ok) {
        setCurrentScene(sceneName);
        setScenes(scenes.map(s => ({ ...s, active: s.name === sceneName })));
      }
    } catch (error) {
      console.error('Error switching scene:', error);
    }
  };

  const handleStartStream = async () => {
    try {
      const response = await fetch('/api/streaming/start', { method: 'POST' });
      if (response.ok) setIsStreaming(true);
    } catch (error) {
      console.error('Error starting stream:', error);
    }
  };

  const handleStopStream = async () => {
    try {
      const response = await fetch('/api/streaming/stop', { method: 'POST' });
      if (response.ok) setIsStreaming(false);
    } catch (error) {
      console.error('Error stopping stream:', error);
    }
  };

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col">
      <div className="bg-gray-800 p-4 flex justify-between items-center border-b border-gray-700">
        <h1 className="text-xl font-bold">🎬 Miktos Streamlab</h1>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-400">Connected to API</span>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-[300px_1fr_300px] gap-4 p-4 overflow-hidden">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <h2 className="text-lg font-bold mb-4">Scenes</h2>
          <div className="space-y-2">
            {scenes.length > 0 ? scenes.map((scene) => (
              <button
                key={scene.name}
                onClick={() => handleSceneSwitch(scene.name)}
                className={`w-full p-3 rounded text-left font-medium transition-colors ${
                  scene.active || scene.name === currentScene
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                {scene.name} {(scene.active || scene.name === currentScene) && '◄'}
              </button>
            )) : (
              <div className="text-gray-500 text-sm">Loading scenes...</div>
            )}
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex flex-col">
          <h2 className="text-lg font-bold mb-4">Preview</h2>
          <div className="bg-black rounded-lg flex-1 flex items-center justify-center border-2 border-gray-700">
            <div className="text-center">
              <div className="text-6xl mb-4">🎥</div>
              <p className="text-gray-500">No preview available</p>
              <p className="text-gray-600 text-sm mt-2">Preview will show live output</p>
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm mb-2 text-gray-400">Preview Volume</label>
            <input type="range" className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer" defaultValue="50" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <h2 className="text-lg font-bold mb-4">Health</h2>

          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
              <span className="text-gray-400 text-sm">FPS</span>
              <span className="font-mono text-green-400">{health.fps.toFixed(1)} ✅</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
              <span className="text-gray-400 text-sm">CPU</span>
              <span className="font-mono text-green-400">{health.cpu_usage}% ✅</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
              <span className="text-gray-400 text-sm">Network</span>
              <span className="font-mono text-green-400 capitalize">{health.network_status} ✅</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-gray-700 rounded">
              <span className="text-gray-400 text-sm">Dropped</span>
              <span className="font-mono text-green-400">{health.dropped_frames} ✅</span>
            </div>
          </div>

          <h3 className="font-bold mb-3 text-gray-300">Destinations</h3>
          <div className="space-y-2">
            {destinations.map(dest => (
              <div key={dest.name} className="p-2 bg-gray-700 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{dest.name}</span>
                  <span className="text-xs text-green-500">✅ Ready</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">{dest.bitrate}</div>
              </div>
            ))}
          </div>

          <button className="w-full mt-4 bg-gray-700 hover:bg-gray-600 py-2 rounded transition-colors text-sm">
            View Incident Log
          </button>
        </div>
      </div>

      <div className="bg-gray-800 p-4 flex gap-4 justify-center border-t border-gray-700">
        {!isStreaming ? (
          <button onClick={handleStartStream} className="bg-green-600 hover:bg-green-700 px-8 py-3 rounded-lg font-semibold transition-colors shadow-lg">
            🟢 Start Stream
          </button>
        ) : (
          <button onClick={handleStopStream} className="bg-red-600 hover:bg-red-700 px-8 py-3 rounded-lg font-semibold transition-colors shadow-lg">
            🔴 Stop Stream
          </button>
        )}
        <button className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg transition-colors">
          ⚙️ Settings
        </button>
      </div>
    </div>
  );
}

export default App;
