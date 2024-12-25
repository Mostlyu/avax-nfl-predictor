import React, { useState, useEffect } from 'react';

const App = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Hardcode the API URL temporarily for debugging
  const API_URL = 'https://avax-nfl-predictor.onrender.com';

  const fetchGames = async () => {
    try {
      setLoading(true);
      console.log('Fetching from:', API_URL); // Debug log

      const response = await fetch(`${API_URL}/schedule`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status); // Debug log

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data); // Debug log

      if (data.success && Array.isArray(data.schedule)) {
        setGames(data.schedule);
        setError(null);
      } else {
        throw new Error('Invalid data format received');
      }
    } catch (err) {
      console.error('Detailed error:', err); // Debug log
      setError(`Error loading games schedule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  // Add manual refresh button for testing
  const handleRefresh = () => {
    fetchGames();
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-bold mb-2">NFL Games Schedule</h1>
        <button
          onClick={handleRefresh}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Refresh Games
        </button>
      </div>

      {/* Debug info */}
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <p>API URL: {API_URL}</p>
        <p>Loading: {loading.toString()}</p>
        <p>Error: {error || 'None'}</p>
      </div>

      {loading && (
        <div className="text-center py-4">Loading...</div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {games.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {games.map((game) => (
            <div key={game.id} className="border rounded p-4 shadow">
              <div className="font-bold">{game.home_team} vs {game.away_team}</div>
              <div>{game.date} at {game.time}</div>
              <div>{game.stadium}, {game.city}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default App;