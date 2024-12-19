const hre = require("hardhat");

async function main() {
  console.log("Starting deployment...");

  // Initial price: 1 MATIC (1 * 10^18 wei)
  const initialPrice = hre.ethers.parseEther("1");

  const PredictionPayment = await hre.ethers.getContractFactory("PredictionPayment");
  const predictionPayment = await PredictionPayment.deploy(initialPrice);

  await predictionPayment.waitForDeployment();

  console.log(
    `PredictionPayment deployed to ${await predictionPayment.getAddress()}`
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});