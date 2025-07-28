async function main() {
    const contractAddress = '0x0675BeE5EED206D771FaFB9D9C6905bB09A1d492';
    
    // Get the contract factory
    const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
    
    // Attach to the deployed contract
    const simpleStorage = SimpleStorage.attach(contractAddress);
    
    // Get the current value
    const currentValue = await simpleStorage.getValue();
    console.log("Current value:", currentValue.toString());
    
    // Set a new value
    console.log("Setting new value to 42...");
    const tx = await simpleStorage.setValue(42);
    await tx.wait();
    
    // Get the updated value
    const newValue = await simpleStorage.getValue();
    console.log("New value:", newValue.toString());
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
