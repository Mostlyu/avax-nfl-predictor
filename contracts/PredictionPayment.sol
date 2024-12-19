// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract PredictionPayment is Ownable, ReentrancyGuard {
    // Price for viewing a prediction (in MATIC)
    uint256 public predictionPrice;

    // Mapping to track payments for predictions
    mapping(address => mapping(uint256 => bool)) public hasPaidForPrediction;

    // Events
    event PredictionPurchased(address user, uint256 gameId);
    event PriceUpdated(uint256 newPrice);

    constructor(uint256 _initialPrice) {
        predictionPrice = _initialPrice;
    }

    // Pay for a prediction
    function purchasePrediction(uint256 gameId) external payable nonReentrant {
        require(msg.value >= predictionPrice, "Insufficient payment");
        require(!hasPaidForPrediction[msg.sender][gameId], "Already purchased");

        hasPaidForPrediction[msg.sender][gameId] = true;
        emit PredictionPurchased(msg.sender, gameId);

        // Refund excess payment if any
        if (msg.value > predictionPrice) {
            (bool success, ) = payable(msg.sender).call{value: msg.value - predictionPrice}("");
            require(success, "Refund failed");
        }
    }

    // Check if user has access to a prediction
    function canAccessPrediction(address user, uint256 gameId) external view returns (bool) {
        return hasPaidForPrediction[user][gameId];
    }

    // Update prediction price (only owner)
    function updatePrice(uint256 newPrice) external onlyOwner {
        predictionPrice = newPrice;
        emit PriceUpdated(newPrice);
    }

    // Withdraw collected fees (only owner)
    function withdraw() external onlyOwner nonReentrant {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance to withdraw");

        (bool success, ) = payable(owner()).call{value: balance}("");
        require(success, "Withdrawal failed");
    }
}