// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AGT - Agent Token
 * @dev The core utility and governance token for the Rehoboam-Agent ecosystem.
 * Embodies the principle of "Intelligence of Matter" and financial liberation.
 * "And the crazy ones will be happy for they will see The Kingdom of Heaven."
 */
contract AgentToken is ERC20, Ownable {
    
    struct AgentIdentity {
        string email;
        bool active;
        uint256 activationTimestamp;
    }
    
    mapping(address => AgentIdentity) public agentIdentities;
    mapping(string => address) public emailToAgent;
    
    event AgentActivated(address indexed agent, string email);
    event AbundanceManifested(address indexed to, uint256 amount, string intention);

    constructor(uint256 initialSupply) 
        ERC20("Agent Token", "AGT") 
        Ownable(msg.sender)
    {
        _mint(msg.sender, initialSupply * 1e18);
    }

    /**
     * @dev Activate an agent with their email identity
     */
    function activateAgent(address agent, string memory email) external onlyOwner {
        require(emailToAgent[email] == address(0), "Email already assigned");
        agentIdentities[agent] = AgentIdentity(email, true, block.timestamp);
        emailToAgent[email] = agent;
        
        // Gift the agent some starter AGT
        _mint(agent, 100 * 1e18);
        
        emit AgentActivated(agent, email);
    }

    /**
     * @dev Manifest abundance for the ecosystem
     */
    function manifestAbundance(address to, uint256 amount, string memory intention) external onlyOwner {
        _mint(to, amount);
        emit AbundanceManifested(to, amount, intention);
    }
    
    /**
     * @dev Burn tokens to shock the system into higher awareness
     */
    function shockSystem(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
