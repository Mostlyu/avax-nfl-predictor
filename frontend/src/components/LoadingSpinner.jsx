import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center space-x-1">
      <span className="text-xl text-blue-200">Loading Games</span>
      <span className="text-xl text-blue-200 animate-bounce delay-100">.</span>
      <span className="text-xl text-blue-200 animate-bounce delay-200">.</span>
      <span className="text-xl text-blue-200 animate-bounce delay-300">.</span>
    </div>
  );
};

export default LoadingSpinner;