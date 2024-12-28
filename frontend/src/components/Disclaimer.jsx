// Disclaimer.jsx
import React from 'react';

const Disclaimer = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900 py-12">
      <div className="container mx-auto px-4">
        <div className="bg-white bg-opacity-95 rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-6 text-gray-800">Prediction Disclaimer</h1>

          <div className="prose prose-blue max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Important Notice</h2>
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <p className="text-yellow-700">
                  All predictions provided by PickWizard.io are for entertainment and informational
                  purposes only. Never make financial decisions based solely on our predictions.
                </p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Understanding Our Predictions</h2>
              <ul className="list-disc pl-6 text-gray-600 mb-4">
                <li className="mb-2">Predictions are based on historical data and statistical analysis</li>
                <li className="mb-2">Past performance does not guarantee future results</li>
                <li className="mb-2">Many factors can affect game outcomes that cannot be predicted</li>
                <li className="mb-2">Always do your own research before making any decisions</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Risk Acknowledgment</h2>
              <p className="text-gray-600 mb-4">
                By using our service, you acknowledge and accept that:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4">
                <li className="mb-2">Predictions may not be accurate</li>
                <li className="mb-2">We are not responsible for any losses</li>
                <li className="mb-2">Sports outcomes are inherently unpredictable</li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Disclaimer;