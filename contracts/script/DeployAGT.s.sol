// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Script.sol";
import "../src/AGT.sol";

/**
 * @title DeployAGT
 * @dev Deploy Antigravity Token to Sepolia
 */
contract DeployAGT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("SEPOLIA_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        console.log("Deploying AGT from:", deployer);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy AGT with 1,000,000 initial supply
        AgentToken agt = new AgentToken(1000000);
        console.log("Agent Token (AGT) deployed at:", address(agt));
        
        vm.stopBroadcast();
    }
}
