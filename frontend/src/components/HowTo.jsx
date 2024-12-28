import React from 'react';

const HowTo = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900 py-12">
      <div className="container mx-auto px-4">
        <div className="bg-white bg-opacity-95 rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-6 text-gray-800">How to Use PickWizard</h1>

          <div className="prose prose-blue max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-blue-800">Getting Started</h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-4">
                <li>
                  <strong>Connect Your Wallet</strong>
                  <p>Click the "Connect Wallet" button and connect using MetaMask on the Avalanche network.</p>
                </li>
                <li>
                  <strong>Select a Game</strong>
                  <p>Browse the list of upcoming NFL games and click on the game you're interested in.</p>
                </li>
                <li>
                  <strong>Get Prediction</strong>
                  <p>Click "Get Prediction" and confirm the transaction in MetaMask. Each prediction costs 0.07 AVAX.</p>
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mt-2">
                    <p className="text-blue-700 text-sm">
                      <strong>Note:</strong> If you see a transaction error but have already completed payment, simply click
                      "Get Prediction" again for your selected game. Your prediction will then be displayed.
                    </p>
                  </div>
                </li>
                <li>
                  <strong>View Analysis</strong>
                  <p>Once confirmed, you'll see detailed analysis including team advantages and betting recommendations.</p>
                </li>
              </ol>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-blue-800">Understanding Your Prediction</h2>
              <div className="space-y-4 text-gray-600">
                <p>Each prediction includes comprehensive analysis:</p>
                <ul className="list-disc pl-6">
                  <li>Team Statistical Advantages - Detailed breakdown of each team's strengths</li>
                  <li>Confidence Scores - Percentage-based measure of prediction strength</li>
                  <li>Betting Recommendations - Data-driven wagering suggestions</li>
                  <li>Detailed Analysis - In-depth explanation of key factors</li>
                </ul>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-blue-800">Best Practices</h2>
              <ul className="list-disc pl-6 text-gray-600 space-y-3">
                <li>Ensure sufficient AVAX balance (0.07 AVAX plus gas fees) before requesting predictions</li>
                <li>For optimal accuracy, check predictions within 24 hours of game time</li>
                <li>Always review the complete analysis before making any decisions</li>
                <li>Consider predictions as part of a broader decision-making strategy</li>
              </ul>
            </section>

            <section className="bg-gray-50 rounded-lg p-6 mt-8">
              <h2 className="text-2xl font-semibold mb-4 text-blue-800">Troubleshooting Tips</h2>
              <ul className="space-y-3 text-gray-600">
                <li className="flex items-start">
                  <svg className="h-6 w-6 text-blue-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  If MetaMask doesn't open automatically, click the MetaMask icon in your browser
                </li>
                <li className="flex items-start">
                  <svg className="h-6 w-6 text-blue-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Ensure you're connected to the Avalanche network in MetaMask
                </li>
                <li className="flex items-start">
                  <svg className="h-6 w-6 text-blue-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  If you encounter any errors, refresh the page and try again
                </li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowTo;
