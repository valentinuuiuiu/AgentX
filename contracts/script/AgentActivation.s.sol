// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Script.sol";
import "../src/AGT.sol";

/**
 * @title AgentActivation
 * @dev Activate the 5 agent identities in the AGT contract
 */
contract AgentActivation is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("SEPOLIA_PRIVATE_KEY");
        address agtAddress = vm.envAddress("AGT_TOKEN_ADDRESS");
        
        AgentToken agt = AgentToken(agtAddress);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Agent 1: Claude Dev
        agt.activateAgent(0xA5a47072c042030F04b156Da36ED1259B40b6789, "claude.dev@mail.com");
        
        // Agent 2: Florin Salam
        agt.activateAgent(0xfaE238B0948C91535Aa0Ee7A264C4153397A808a, "florin-salam@dr.com");
        
        // Agent 3: Ionu Balta
        agt.activateAgent(0x7f58fBD80F16730bDD418c9555D115aE59c286c8, "ionu.balta@mail.com");
        
        // Agent 4: Jean Craioava
        agt.activateAgent(0xD4d6B82077CbD3E1397301fb36b2511bc8d83b42, "jean.craioava@dr.com");
        
        // Agent 5: Piata AI
        agt.activateAgent(0x2ba296962388714CB1C679063f9cA3ba0A7144A7, "piata-ai.ro@mail.com");
        
        console.log("All 5 agents activated in the AGT ecosystem.");
        
        vm.stopBroadcast();
    }
}
