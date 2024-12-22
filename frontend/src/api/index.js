// src/api/index.js
const API_URL = import.meta.env.VITE_API_URL;

export const fetchSchedule = async () => {
  try {
    const response = await fetch(`${API_URL}/schedule`);
    if (!response.ok) {
      throw new Error('Failed to fetch schedule');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching schedule:', error);
    throw error;
  }
};