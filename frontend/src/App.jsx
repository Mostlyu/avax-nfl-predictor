import React, { useState, useEffect } from 'react';

const DebugApp = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState({
    apiUrl: '',
    fetchStarted: false,
    fetchCompleted: false,
    responseReceived: false
  });

  const fetchGames = async () => {
    try {
      setLoading(true);
      setDebugInfo(prev => ({ ...prev, fetchStarted: true }));

      // Get API URL from environment variable
      const apiUrl = import.meta.env.VITE_API_URL;
      setDebugInfo(prev => ({ ...prev, apiUrl }));

      console.log('Attempting to fetch from:', apiUrl);

      const response = await fetch(`${apiUrl}/schedule`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });

      setDebugInfo(prev => ({ ...prev, responseReceived: true }));

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);

      setDebugInfo(prev => ({ ...prev, fetchCompleted: true }));

      if (data.success && Array.isArray(data.schedule)) {
        setGames(data.schedule);
        setError(null);
      } else {
        throw new Error('Invalid data format received');
      }
    } catch (err) {
      console.error('Error fetching games:', err);
      setError(`Error loading games schedule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  return (
    <div className="p-4">
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <h2 className="text-lg font-bold mb-2">Debug Information</h2>
        <pre className="whitespace-pre-wrap">
          {JSON.stringify(debugInfo, null, 2)}
        </pre>
      </div>

      {loading && (
        <div className="mb-4">Loading games...</div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {games.length > 0 && (
        <div className="grid gap-4">
          {games.map((game) => (
            <div key={game.id} className="p-4 border rounded">
              <div className="font-bold">{game.home_team} vs {game.away_team}</div>
              <div>{game.date} at {game.time}</div>
              <div>{game.stadium}, {game.city}</div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={fetchGames}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Retry Fetch
      </button>
    </div>
  );
};

export default DebugApp;