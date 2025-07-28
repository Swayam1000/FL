const hre = require("hardhat");

async function main() {
  const MetadataStorage = await hre.ethers.getContractFactory("MetadataStorage");
  const metadataStorage = await MetadataStorage.deploy();

  await metadataStorage.waitForDeployment();

  console.log("MetadataStorage deployed to:", await metadataStorage.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
