// frontend/src/App.jsx
import { useState, useEffect } from 'react'
import { useAccount, useConnect, useReadContract, useWriteContract } from 'wagmi'
import { injected } from 'wagmi/connectors'
import { parseEther } from 'viem'
import { API_URL } from './config';

// Contract details
const CONTRACT_ADDRESS = '0xde5c1e5DdE61FF85288320434a85d73e1f0CafED'
const ABI = [
  {
    "inputs": [{"internalType": "uint256", "name": "_initialPrice", "type": "uint256"}],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "gameId", "type": "uint256"}],
    "name": "purchasePrediction",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {"internalType": "address", "name": "user", "type": "address"},
      {"internalType": "uint256", "name": "gameId", "type": "uint256"}
    ],
    "name": "canAccessPrediction",
    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "predictionPrice",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "withdraw",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  }
]

// Fuji testnet constants
const AVALANCHE_CHAIN_ID = '0xa86a'
const AVALANCHE_PARAMS = {
  chainId: AVALANCHE_CHAIN_ID,
  chainName: 'Avalanche Network',
  nativeCurrency: {
    name: 'AVAX',
    symbol: 'AVAX',
    decimals: 18
  },
  rpcUrls: ['https://api.avax.network/ext/bc/C/rpc'],
  blockExplorerUrls: ['https://snowtrace.io/']
}

function App() {
  const [error, setError] = useState(null)
  const [networkInfo, setNetworkInfo] = useState(null)
  const [networkError, setNetworkError] = useState(null)

  // game selection state
  const [games, setGames] = useState([])
  const [selectedGame, setSelectedGame] = useState(null)
  const [loading, setLoading] = useState(false)

  // Your wagmi hooks
  const { address, isConnected } = useAccount()
  const { connect } = useConnect()

  // Add these new contract hooks
  const { data: currentPrice } = useReadContract({
    address: CONTRACT_ADDRESS,
    abi: ABI,
    functionName: 'predictionPrice'
  })

  const { data: hasAccess, refetch: refetchAccess } = useReadContract({
    address: CONTRACT_ADDRESS,
    abi: ABI,
    functionName: 'canAccessPrediction',
    args: address && selectedGame ? [address, BigInt(selectedGame.id)] : undefined,
    enabled: Boolean(address && selectedGame)
  })

  const { data: contractBalance } = useReadContract({
    address: CONTRACT_ADDRESS,
    abi: [{
      "inputs": [],
      "name": "owner",
      "outputs": [{"internalType": "address", "name": "", "type": "address"}],
      "stateMutability": "view",
      "type": "function"
    }],
    functionName: 'owner'
  })

  // Add these hooks near your other hooks
  const [withdrawalStatus, setWithdrawalStatus] = useState('')
  const { writeContract } = useWriteContract()

  // new state for predictions
  const [prediction, setPrediction] = useState(null)
  const [loadingPrediction, setLoadingPrediction] = useState(false)

  // Check and handle network
  useEffect(() => {
    const checkNetwork = async () => {
      if (window.ethereum && isConnected) {
        try {
          const chainId = await window.ethereum.request({
            method: 'eth_chainId'
          })

          if (chainId !== AVALANCHE_CHAIN_ID) {
            setNetworkInfo('Wrong Network')
            setNetworkError('Please switch to Avalanche Network')
            try {
              await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: AVALANCHE_CHAIN_ID }],
              })
            } catch (switchError) {
              if (switchError.code === 4902) {
                try {
                  await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [AVALANCHE_PARAMS],
                  })
                } catch (addError) {
                  setNetworkError('Failed to add Avalanche network')
                }
              }
            }
          } else {
            setNetworkInfo('Avalanche Network')  // Updated network name
            setNetworkError(null)
          }
        } catch (err) {
          console.error('Error checking network:', err)
          setNetworkError('Error checking network')
        }
      }
    }

    checkNetwork()

    if (window.ethereum) {
      window.ethereum.on('chainChanged', checkNetwork)
      return () => window.ethereum.removeListener('chainChanged', checkNetwork)
    }
  }, [isConnected])

  // game fetching
  useEffect(() => {
    fetchGames()
  }, [])

  const fetchGames = async () => {
    try {
      setLoading(true);
      setError(null);

      const apiUrl = import.meta.env.VITE_API_URL;
      console.log('Fetching from:', apiUrl); // Debug log

      const response = await fetch(`${apiUrl}/schedule`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data); // Debug log

      if (data.success && Array.isArray(data.schedule)) {
        const sortedGames = data.schedule
          .filter(game => game.home_team && game.away_team) // Filter out games with missing teams
          .sort((a, b) => {
            const dateTimeA = new Date(`${a.date} ${a.time}`);
            const dateTimeB = new Date(`${b.date} ${b.time}`);
            return dateTimeA - dateTimeB;
          });

        console.log('Sorted games:', sortedGames); // Debug log
        setGames(sortedGames);
      } else {
        throw new Error('Invalid schedule data format');
      }
    } catch (err) {
      console.error('Error fetching games:', err);
      setError(`Failed to load games: ${err.message}`);
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  // New handleGetPrediction function
  const handleGetPrediction = async () => {
    if (!selectedGame) return
    if (!isConnected) {
      setError('Please connect your wallet first')
      return
    }

    setLoadingPrediction(true)
    setPrediction(null)
    setError(null)

    try {
      // Check if prediction has been paid for
      console.log('Checking payment status...')
      const accessResult = await refetchAccess() // Use refetchAccess instead of checkAccess
      console.log('Access status:', accessResult)

      // Only request payment if user hasn't paid
      if (!accessResult?.data) {
        // If not paid, request payment
        console.log('Payment required, requesting payment...')
        try {
          const tx = await writeContract({
            address: CONTRACT_ADDRESS,
            abi: ABI,
            functionName: 'purchasePrediction',
            args: [BigInt(selectedGame.id)], // Convert to BigInt
            value: parseEther('0.07')
          })

          // Wait for transaction confirmation
          console.log('Waiting for transaction confirmation...')
          const receipt = await tx.wait() // Wait for transaction confirmation
          if (!receipt) {
            throw new Error('Transaction failed')
          }
          console.log('Payment confirmed')
        } catch (paymentError) {
          console.error('Payment error:', paymentError)
          setError('Payment cancelled or failed. Prediction not available.')
          setLoadingPrediction(false)
          return // Exit early if payment fails
        }
      } else {
        console.log('Already paid for this prediction')
      }

      // Only proceed if payment was successful or previously paid
      const response = await fetch(`http://localhost:8000/predict/${selectedGame.id}`)
      const data = await response.json()

      if (data.success && data.prediction) {
        console.log('Setting prediction data:', data.prediction)
        setPrediction(data.prediction)
      } else {
        throw new Error(data.error || 'Failed to get prediction')
      }
    } catch (err) {
      console.error('Detailed error:', err)
      setError(err.message || 'Failed to get prediction')
    } finally {
      setLoadingPrediction(false)
    }
  }

  const handleGameSelect = (game) => {
    setSelectedGame(game)
    setError(null)
  }

  const handleConnect = async () => {
    try {
      setError(null)
      setNetworkError(null)
      await connect({ connector: injected() })
    } catch (err) {
      console.error('Connection error:', err)
      setError('Failed to connect wallet')
    }
  }

  // Add this function to handle withdrawals
  const handleWithdraw = async () => {
    try {
      setWithdrawalStatus('Initiating withdrawal...')
      setError(null)

      const result = await writeContract({
        address: CONTRACT_ADDRESS,
        abi: ABI,
        functionName: 'withdraw'
      })

      console.log('Withdrawal initiated:', result)
      setWithdrawalStatus('Waiting for confirmation...')

      // Wait for the transaction to be processed
      await new Promise(resolve => setTimeout(resolve, 5000))

      setWithdrawalStatus('Withdrawal successful!')
      setTimeout(() => setWithdrawalStatus(''), 3000) // Clear status after 3 seconds
    } catch (err) {
      console.error('Withdrawal error:', err)
      setWithdrawalStatus('Withdrawal failed: ' + err.message)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-5xl font-bold text-white">NFL Game Predictor</h1>
            {networkInfo && (
              <p className={`mt-2 ${networkInfo === 'Avalanche Fuji' ? 'text-green-400' : 'text-yellow-400'}`}>
                Network: {networkInfo}
              </p>
            )}
          </div>

          {/* Connect Wallet */}
          <div>
            {!isConnected ? (
              <button
                onClick={handleConnect}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition"
              >
                Connect Wallet
              </button>
            ) : (
              <div className="text-green-400">
                Connected: {address?.slice(0, 6)}...{address?.slice(-4)}
              </div>
            )}
          </div>
        </div>

        {/* Network Error Display */}
        {networkError && (
          <div className="mb-4 p-3 bg-yellow-100 text-yellow-700 rounded-lg">
            {networkError}
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        {/* Add Games List */}
        <div className="bg-white bg-opacity-95 rounded-xl shadow-2xl p-8 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">Upcoming Games</h2>

          {loading ? (
            <div className="text-center text-gray-600">Loading games...</div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {games.map((game) => (
                <div
                  key={game.id}
                  className={`p-6 border-2 rounded-lg cursor-pointer transition-all ${
                    selectedGame?.id === game.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
                  }`}
                  onClick={() => handleGameSelect(game)}
                >
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                    <div className="flex-1 mb-2 md:mb-0">
                      <div className="text-lg font-semibold text-gray-800">
                        <span className="text-blue-600">{game.home_team}</span>
                        <span className="mx-3 text-gray-400">vs</span>
                        <span className="text-red-600">{game.away_team}</span>
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        {game.stadium}, {game.city}
                      </div>
                    </div>
                    <div className="flex flex-col items-start md:items-end">
                      <div className="font-medium text-gray-700">
                        {game.date}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Get Prediction Button */}
          {selectedGame && isConnected && (
            <div className="text-center mt-6">
              <button
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-blue-700 transition"
                onClick={handleGetPrediction}
                disabled={loadingPrediction}
              >
                {loadingPrediction ? 'Loading...' : 'Get Prediction'}
              </button>
            </div>
          )}

          {/* Prediction Display */}
          {prediction && (
            <div className="mt-8 pt-8 border-t border-gray-200">
              <h3 className="text-2xl font-bold mb-6 text-gray-800">
                Game Analysis: {prediction.matchup}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(prediction.statistical_analysis.advantages).map(([team, advantages]) => (
                  <div key={team} className="bg-white rounded-lg border-2 border-gray-200 p-6 shadow-sm">
                    <h4 className="font-bold text-xl text-blue-600 mb-4">{team}</h4>
                    <ul className="space-y-3">
                      {advantages.map((advantage, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          <span className="text-gray-700">{advantage}</span>
                        </li>
                      ))}
                    </ul>
                    {prediction.confidence_scores && (
                      <div className="mt-6 pt-4 border-t border-gray-100">
                        <div className="text-lg">
                          <span className="font-semibold text-gray-700">Confidence Score: </span>
                          <span className="text-blue-600 font-bold">
                            {prediction.confidence_scores[team]}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {prediction.betting_recommendations && prediction.betting_recommendations.length > 0 && (
                <div className="mt-8 pt-6 border-t border-gray-200">
                  <h4 className="text-xl font-bold mb-4 text-gray-800">Betting Recommendations</h4>
                  <div className="space-y-4">
                    {prediction.betting_recommendations.map((rec, index) => (
                      <div key={index} className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="font-semibold text-gray-800 mb-2">{rec.type}</div>
                        <div className="text-gray-600">Selection: {rec.bet}</div>
                        <div className="text-gray-600">Odds: {rec.odds}</div>
                        <div className="text-gray-600">Confidence: {rec.confidence}%</div>
                        <div className="text-gray-600 mt-2">Analysis: {rec.explanation}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {/* Admin Section - Only visible to contract owner */}
          {isConnected && address?.toLowerCase() === '0x781C8EE25E31B307510F88378972040d97eEe870'.toLowerCase() && (
            <div className="mt-8 p-6 bg-gray-100 rounded-lg">
              <h2 className="text-2xl font-bold mb-4">Admin Controls</h2>
              <div className="space-y-4">
                <button
                  onClick={handleWithdraw}
                  className="bg-purple-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-purple-700 transition"
                >
                  Withdraw Funds
                </button>
                {withdrawalStatus && (
                  <div className="mt-2 text-sm font-medium text-gray-700">
                    {withdrawalStatus}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App