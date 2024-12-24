import React, { useState, useEffect } from 'react';

const App = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true);
        setError(null);

        // Log the URL we're trying to fetch from
        const url = 'https://avax-nfl-predictor.onrender.com/schedule';
        console.log('Fetching from:', url);

        const response = await fetch(url);
        console.log('Response status:', response.status);

        const data = await response.json();
        console.log('Received data:', data);

        if (data.success && Array.isArray(data.schedule)) {
          setGames(data.schedule);
        } else {
          throw new Error('Invalid data format');
        }
      } catch (err) {
        console.error('Full error:', err);
        setError('Error loading games schedule: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchGames();
  }, []);

  if (loading) return <div className="p-4">Loading...</div>;

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-600">{error}</div>
        <div className="mt-4">
          <h3 className="font-bold">Debug Info:</h3>
          <p>Backend URL: https://avax-nfl-predictor.onrender.com</p>
          <p>Check browser console for more details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">NFL Games</h1>
      {games.length === 0 ? (
        <p>No games found</p>
      ) : (
        <div className="grid gap-4">
          {games.map((game) => (
            <div key={game.id} className="border p-4 rounded">
              <p className="font-bold">{game.home_team} vs {game.away_team}</p>
              <p>{game.date} - {game.time}</p>
              <p>{game.stadium}, {game.city}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default App;