// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Script.sol";
import "../src/FlashLoanArbitrage.sol";
import "../src/TradeExecutor.sol";

/**
 * @title DeploySepolia
 * @dev Deploy Rehoboam contracts to Sepolia testnet
 */
contract DeploySepolia is Script {
    // Sepolia addresses
    address constant AAVE_V3_POOL = 0x6Ae43d3271ff6888e7Fc43Fd7321a503104E31D7;
    address constant WETH = 0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14;
    address constant USDC = 0x94a9D9AC8415D5394D6E6f4a0d2782c3F7d13b2e;
    address constant DAI = 0xFF34B3D4Aee8ddCd6F9AFF1e12E189D34Da9415b;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("SEPOLIA_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        console.log("Deploying from:", deployer);
        console.log("Deployer balance:", deployer.balance);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy FlashLoanArbitrage
        FlashLoanArbitrage arb = new FlashLoanArbitrage(
            AAVE_V3_POOL,
            deployer,  // fee recipient
            1000,       // 10% profit fee
            0.001 ether, // min profit
            100         // 1% max slippage
        );
        console.log("FlashLoanArbitrage deployed at:", address(arb));
        
        // Deploy TradeExecutor
        TradeExecutor executor = new TradeExecutor();
        console.log("TradeExecutor deployed at:", address(executor));
        
        // Approve tokens for arbitrage
        arb.approveToken(WETH);
        arb.approveToken(USDC);
        arb.approveToken(DAI);
        console.log("Tokens approved for arbitrage");
        
        vm.stopBroadcast();
        
        // Log deployment info
        console.log("\n=== DEPLOYMENT SUMMARY ===");
        console.log("FlashLoanArbitrage:", address(arb));
        console.log("TradeExecutor:", address(executor));
        console.log("==========================");
    }
}
