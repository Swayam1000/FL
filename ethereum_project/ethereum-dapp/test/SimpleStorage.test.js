const { expect } = require("chai");

describe("SimpleStorage", function () {
  let simpleStorage;

  beforeEach(async function () {
    const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
    simpleStorage = await SimpleStorage.deploy();
    await simpleStorage.waitForDeployment();
  });

  it("Should return 0 by default", async function () {
    expect(await simpleStorage.getValue()).to.equal(0);
  });

  it("Should set and get the value correctly", async function () {
    const setValue = 42;
    const setValueTx = await simpleStorage.setValue(setValue);
    await setValueTx.wait();
    expect(await simpleStorage.getValue()).to.equal(setValue);
  });
});
