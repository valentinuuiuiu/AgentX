// SPDX-License-Identifier: MIT
// VSR Registry — On-Chain Audit Verification
// Vetal Shabar Raksha — वेताल शाबर रक्षा

pragma solidity ^0.8.20;

/// @title VSRRegistry
/// @notice On-chain registry for VSR security audits
/// @dev Stores audit hashes, levels, and timestamps for smart contract verification
contract VSRRegistry {
    
    // ============ Events ============
    event AuditRegistered(
        address indexed contractAddress,
        bytes32 indexed reportHash,
        uint8 level,
        uint256 timestamp,
        address indexed auditor
    );
    
    event AuditorAdded(address indexed auditor);
    event AuditorRemoved(address indexed auditor);
    
    // ============ Errors ============
    error NotAuditor();
    error AlreadyAudited();
    error InvalidLevel();
    error ZeroAddress();
    
    // ============ State ============
    address public owner;
    mapping(address => bool) public isAuditor;
    
    struct Audit {
        bytes32 reportHash;
        uint8 level;      // 0=None, 1=Bronze, 2=Silver, 3=Gold, 4=Platinum
        uint256 timestamp;
        address auditor;
        bool exists;
    }
    
    mapping(address => Audit) public audits;
    mapping(bytes32 => address) public hashToContract;
    
    uint256 public totalAudits;
    
    // ============ Modifiers ============
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier onlyAuditor() {
        if (!isAuditor[msg.sender]) revert NotAuditor();
        _;
    }
    
    // ============ Constructor ============
    constructor() {
        owner = msg.sender;
        isAuditor[msg.sender] = true;
    }
    
    // ============ Admin Functions ============
    
    function addAuditor(address _auditor) external onlyOwner {
        isAuditor[_auditor] = true;
        emit AuditorAdded(_auditor);
    }
    
    function removeAuditor(address _auditor) external onlyOwner {
        isAuditor[_auditor] = false;
        emit AuditorRemoved(_auditor);
    }
    
    function transferOwnership(address _newOwner) external onlyOwner {
        if (_newOwner == address(0)) revert ZeroAddress();
        owner = _newOwner;
    }
    
    // ============ Core Functions ============
    
    /// @notice Register a new audit for a contract
    /// @param _contract The audited contract address
    /// @param _reportHash SHA-256 hash of the audit report
    /// @param _level Audit level: 1=Bronze, 2=Silver, 3=Gold, 4=Platinum
    function registerAudit(
        address _contract,
        bytes32 _reportHash,
        uint8 _level
    ) external onlyAuditor {
        if (_level == 0 || _level > 4) revert InvalidLevel();
        if (audits[_contract].exists) revert AlreadyAudited();
        if (_contract == address(0)) revert ZeroAddress();
        
        audits[_contract] = Audit({
            reportHash: _reportHash,
            level: _level,
            timestamp: block.timestamp,
            auditor: msg.sender,
            exists: true
        });
        
        hashToContract[_reportHash] = _contract;
        totalAudits++;
        
        emit AuditRegistered(_contract, _reportHash, _level, block.timestamp, msg.sender);
    }
    
    // ============ View Functions ============
    
    /// @notice Check if a contract has been audited
    /// @param _contract The contract to check
    /// @return isAudited Whether the contract has an audit
    /// @return level The audit level (0 if not audited)
    /// @return timestamp When the audit was registered
    /// @return auditor Who performed the audit
    function getAudit(address _contract)
        external
        view
        returns (bool isAudited, uint8 level, uint256 timestamp, address auditor)
    {
        Audit memory a = audits[_contract];
        return (a.exists, a.level, a.timestamp, a.auditor);
    }
    
    /// @notice Check audit level by report hash
    function getAuditByHash(bytes32 _hash)
        external
        view
        returns (address contractAddr, uint8 level, uint256 timestamp)
    {
        address addr = hashToContract[_hash];
        Audit memory a = audits[addr];
        return (addr, a.level, a.timestamp);
    }
    
    /// @notice Get human-readable level name
    function getLevelName(uint8 _level) external pure returns (string memory) {
        if (_level == 1) return "VSR-Bronze";
        if (_level == 2) return "VSR-Silver";
        if (_level == 3) return "VSR-Gold";
        if (_level == 4) return "VSR-Platinum";
        return "None";
    }
    
    /// @notice Get all audits by an auditor
    function getAuditsByAuditor(address _auditor)
        external
        view
        returns (address[] memory)
    {
        // Note: In production, use an enumerable mapping or off-chain indexer
        // This is a simplified version
        address[] memory result = new address[](totalAudits);
        uint256 count = 0;
        // This is a placeholder — real implementation needs EnumerableSet
        return result;
    }
}
