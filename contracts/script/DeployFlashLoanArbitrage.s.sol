// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Script.sol";
import "../src/FlashLoanArbitrage.sol";

/**
 * @title DeployFlashLoanArbitrage
 * @dev Deployment script for FlashLoanArbitrage on multiple networks.
 *
 * Usage:
 *   forge script script/DeployFlashLoanArbitrage.s.sol --rpc-url <RPC_URL> --broadcast
 *
 * Environment variables needed:
 *   - AAVE_POOL_ADDRESS: Aave V3 Pool address for the target network
 *   - FEE_RECIPIENT: Address receiving profit fees
 *   - PRIVATE_KEY: Deployer private key
 *
 * Networks:
 *   - Ethereum Mainnet:  Aave Pool 0x87870bCa4f8e1a9F26b5b4B4c4bb2e6f7b3e6040
 *   - Arbitrum:          Aave Pool 0x794a61358D6845594F94dc1DB02A252b5b4814aD
 *   - Optimism:          Aave Pool 0x794a61358D6845594F94dc1DB02A252b5b4814aD
 *   - Polygon:           Aave Pool 0x794a61358D6845594F94dc1DB02A252b5b4814aD
 *   - Base:              Aave Pool 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5
 */
contract DeployFlashLoanArbitrage is Script {
    // Aave V3 Pool addresses per network
    address constant AAVE_POOL_ETHEREUM = 0x87870bCa4f8e1a9F26b5b4B4c4bb2e6f7b3e6040;
    address constant AAVE_POOL_ARBITRUM = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address constant AAVE_POOL_OPTIMISM = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address constant AAVE_POOL_POLYGON = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address constant AAVE_POOL_BASE = 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5;

    // Uniswap V2 Router addresses
    address constant UNISWAP_V2_ROUTER_ETHEREUM = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address constant SUSHISWAP_ROUTER_ETHEREUM = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    // Uniswap V3 Router addresses
    address constant UNISWAP_V3_ROUTER_ETHEREUM = 0x68b3465833fb72A70ecDF485E0b4fAA6d2910F47;

    // Common tokens
    address constant WETH_ETHEREUM = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC_ETHEREUM = 0xa0b86a33e6441Cb59b3Ac4d2a9da2b8ec55b3dE5;
    address constant USDT_ETHEREUM = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant LINK_ETHEREUM = 0x514910771AF9Ca656af840dff83E8264EcF986CA;
    address constant AAVE_ETHEREUM = 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9;

    // Default config
    uint256 constant DEFAULT_PROFIT_FEE_BPS = 1000;  // 10% to fee recipient
    uint256 constant DEFAULT_MIN_PROFIT_WEI = 1e15;  // 0.001 tokens minimum profit
    uint256 constant DEFAULT_MAX_SLIPPAGE_BPS = 100; // 1% max slippage

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address feeRecipient = vm.envOr("FEE_RECIPIENT", address(0));

        // Get Aave Pool based on chain
        address aavePool = getAavePool();

        if (feeRecipient == address(0)) {
            feeRecipient = vm.addr(deployerPrivateKey);
        }

        console.log("=== Deploying FlashLoanArbitrage ===");
        console.log("Chain ID:", block.chainid);
        console.log("Aave Pool:", aavePool);
        console.log("Fee Recipient:", feeRecipient);
        console.log("Profit Fee BPS:", DEFAULT_PROFIT_FEE_BPS);
        console.log("Min Profit Wei:", DEFAULT_MIN_PROFIT_WEI);
        console.log("Max Slippage BPS:", DEFAULT_MAX_SLIPPAGE_BPS);

        vm.startBroadcast(deployerPrivateKey);

        // Deploy the contract
        FlashLoanArbitrage arb = new FlashLoanArbitrage(
            aavePool,
            feeRecipient,
            DEFAULT_PROFIT_FEE_BPS,
            DEFAULT_MIN_PROFIT_WEI,
            DEFAULT_MAX_SLIPPAGE_BPS
        );

        console.log("FlashLoanArbitrage deployed at:", address(arb));

        // Configure trusted DEXs based on network
        _configureDexs(arb);

        // Approve common tokens
        _approveTokens(arb);

        vm.stopBroadcast();

        console.log("=== Deployment Complete ===");
        console.log("Contract:", address(arb));
        console.log("Owner:", arb.owner());
        console.log("Fee Recipient:", arb.feeRecipient());
    }

    function getAavePool() internal view returns (address) {
        address pool = vm.envOr("AAVE_POOL_ADDRESS", address(0));

        if (pool != address(0)) {
            return pool;
        }

        // Fallback to known addresses
        if (block.chainid == 1) return AAVE_POOL_ETHEREUM;        // Ethereum
        if (block.chainid == 42161) return AAVE_POOL_ARBITRUM;    // Arbitrum
        if (block.chainid == 10) return AAVE_POOL_OPTIMISM;       // Optimism
        if (block.chainid == 137) return AAVE_POOL_POLYGON;        // Polygon
        if (block.chainid == 8453) return AAVE_POOL_BASE;          // Base

        revert("Unknown chain - set AAVE_POOL_ADDRESS env var");
    }

    function _configureDexs(FlashLoanArbitrage arb) internal {
        if (block.chainid == 1) {
            // Ethereum Mainnet DEXs
            arb.addTrustedDexV2(UNISWAP_V2_ROUTER_ETHEREUM);
            arb.addTrustedDexV2(SUSHISWAP_ROUTER_ETHEREUM);
            arb.addTrustedDexV3(UNISWAP_V3_ROUTER_ETHEREUM);
            console.log("Added Ethereum Mainnet DEXs");
        } else if (block.chainid == 42161) {
            // Arbitrum DEXs
            arb.addTrustedDexV2(0x68b3465833fb72A70ecDF485E0b4fAA6d2910F47); // Uniswap V2 on Arbitrum
            arb.addTrustedDexV3(0x68b3465833fb72A70ecDF485E0b4fAA6d2910F47); // Uniswap V3 on Arbitrum
            console.log("Added Arbitrum DEXs");
        } else if (block.chainid == 10) {
            // Optimism DEXs
            arb.addTrustedDexV2(0xa062aE8aFb06e435780890Bbe3830DDC4105313B); // SushiSwap on Optimism
            arb.addTrustedDexV3(0x68b3465833fb72A70ecDF485E0b4fAA6d2910F47); // Uniswap V3 on Optimism
            console.log("Added Optimism DEXs");
        } else if (block.chainid == 137) {
            // Polygon DEXs
            arb.addTrustedDexV2(0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff); // QuickSwap on Polygon
            arb.addTrustedDexV2(0x1b02dA8Cb0d097eB8DfAe1c41b2D8848404F4173); // SushiSwap on Polygon
            arb.addTrustedDexV3(0x68b3465833fb72A70ecDF485E0b4fAA6d2910F47); // Uniswap V3 on Polygon
            console.log("Added Polygon DEXs");
        } else if (block.chainid == 8453) {
            // Base DEXs
            arb.addTrustedDexV2(0x8cFe327CEc23b6E4e2832Cc39e7EbDA10DA8C622); // Uniswap V2 on Base
            arb.addTrustedDexV3(0x2626664c2603331E17A476e16F6DC2D7f860B247); // Uniswap V3 on Base
            console.log("Added Base DEXs");
        } else {
            console.log("WARNING: No known DEXs for this chain - configure manually");
        }
    }

    function _approveTokens(FlashLoanArbitrage arb) internal {
        if (block.chainid == 1) {
            // Ethereum Mainnet tokens
            arb.approveToken(WETH_ETHEREUM);
            arb.approveToken(USDC_ETHEREUM);
            arb.approveToken(USDT_ETHEREUM);
            arb.approveToken(LINK_ETHEREUM);
            arb.approveToken(AAVE_ETHEREUM);
            console.log("Approved Ethereum Mainnet tokens");
        } else {
            console.log("WARNING: No known tokens for this chain - approve manually");
        }
    }
}