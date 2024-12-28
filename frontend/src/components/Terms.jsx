// Terms.jsx
import React from 'react';

const Terms = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900 py-12">
      <div className="container mx-auto px-4">
        <div className="bg-white bg-opacity-95 rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-6 text-gray-800">Terms of Service</h1>

          <div className="prose prose-blue max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">1. Agreement to Terms</h2>
              <p className="text-gray-600 mb-4">
                By accessing and using PickWizard.io, you agree to be bound by these Terms of Service.
                If you do not agree to these terms, please do not use our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">2. Service Description</h2>
              <p className="text-gray-600 mb-4">
                PickWizard.io provides NFL game predictions based on statistical analysis.
                Our predictions are for entertainment and informational purposes only.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">3. User Responsibilities</h2>
              <ul className="list-disc pl-6 text-gray-600 mb-4">
                <li className="mb-2">You must be at least 18 years old to use this service</li>
                <li className="mb-2">You are responsible for maintaining the security of your wallet</li>
                <li className="mb-2">You agree not to abuse or attempt to manipulate our service</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">4. Payments and Refunds</h2>
              <p className="text-gray-600 mb-4">
                All payments are processed through smart contracts on the Avalanche network.
                Due to the nature of blockchain transactions, all purchases are final and non-refundable.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">5. Limitation of Liability</h2>
              <p className="text-gray-600 mb-4">
                PickWizard.io provides predictions based on available data, but we cannot guarantee
                their accuracy. We are not responsible for any losses incurred based on our predictions.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Terms;