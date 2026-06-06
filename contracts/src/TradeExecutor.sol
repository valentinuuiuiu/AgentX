// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

// Import OpenZeppelin contracts via standard Remappings
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TradeExecutor - Unified Execution Layer for Rehoboam
 * @notice Executes token swaps and arbitrage paths determined by the AI Agent.
 * @dev Integrates with VetalGuardedVault for funding and DivineMultiSig for approvals.
 */
contract TradeExecutor is Ownable, ReentrancyGuard {
    
    // Mapping of AI-analyzed strategies
    struct Strategy {
        bool active;
        uint256 minProfitThreshold; // in basis points (e.g., 50 = 0.5%)
        uint256 maxGasPrice;
        address executor; // The address authorized to execute this specific strategy type
    }
    
    // State variables
    mapping(bytes32 => Strategy) public strategies; // strategyId => Strategy
    mapping(address => bool) public authorizedTraders; // AI Agents / Bots allowed to trigger
    
    // Events for Tenderly / Sentio tracking
    event TradeExecuted(
        address indexed trader,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 profit,
        string strategyName
    );
    
    event TradeFailed(
        address indexed trader,
        string reason,
        uint256 timestamp
    );
    
    constructor() Ownable(msg.sender) {
        // Initial setup
    }
    
    /**
     * @notice Register a new trading strategy
     * @param strategyId Unique identifier for the strategy
     * @param minProfitBps Minimum profit percentage required to attempt trade
     * @param executor Address allowed to execute trades for this strategy
     */
    function registerStrategy(
        bytes32 strategyId,
        uint256 minProfitBps,
        address executor
    ) external onlyOwner {
        require(!strategies[strategyId].active, "Strategy already active");
        
        strategies[strategyId] = Strategy({
            active: true,
            minProfitThreshold: minProfitBps,
            maxGasPrice: 50 gwei, // Default safety cap
            executor: executor
        });
    }
    
    /**
     * @notice Add an authorized trader (AI Agent / Bot)
     * @param trader The address to authorize
     */
    function authorizeTrader(address trader) external onlyOwner {
        authorizedTraders[trader] = true;
    }
    
    /**
     * @notice Remove an authorized trader
     * @param trader The address to revoke
     */
    function revokeTrader(address trader) external onlyOwner {
        authorizedTraders[trader] = false;
    }
    
    /**
     * @notice Execute a standard swap/arbitrage
     * @param strategyId The active strategy to follow
     * @param tokenIn Address of input token
     * @param tokenOut Address of output token
     * @param amountIn Amount of tokens to swap
     * @param minAmountOut Minimum expected output (slippage protection)
     */
    function executeTrade(
        bytes32 strategyId,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external nonReentrant {
        require(authorizedTraders[msg.sender], "Unauthorized trader");
        require(strategies[strategyId].active, "Strategy not active");
        
        // Transfer tokens from sender to this contract for execution
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        
        uint256 balanceBefore = IERC20(tokenOut).balanceOf(address(this));
        
        // --- EXECUTION PLACEHOLDER ---
        // This is where the DEX router calls (Uniswap, SushiSwap, etc.) happen.
        // The Vetal Shabar Forge script will deploy a Router or call external DEXs.
        _performSwap(tokenIn, tokenOut, amountIn, minAmountOut);
        // -----------------------------
        
        uint256 balanceAfter = IERC20(tokenOut).balanceOf(address(this));
        uint256 actualOut = balanceAfter - balanceBefore;
        
        require(actualOut >= minAmountOut, "Insufficient output amount");
        
        // Return tokens to sender
        IERC20(tokenOut).transfer(msg.sender, actualOut);
        
        emit TradeExecuted(
            msg.sender,
            tokenIn,
            tokenOut,
            amountIn,
            actualOut,
            actualOut > balanceBefore ? actualOut - balanceBefore : 0,
            "Standard Execution"
        );
    }
    
    /**
     * @notice Internal swap logic (can be replaced with DEX aggregator logic)
     */
    function _performSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) internal {
        // Placeholder: In a real deployment, this interacts with the Uniswap V2/V3 Router
        // or a custom Aggregator. For now, we assume the tokens are already moved
        // or handled by a higher-level arbitrage logic. 
        // To simulate a successful mock trade for testing:
        // IERC20(tokenOut).transfer(address(this), minAmountOut); 
        
        // Real implementation example:
        // IUniswapV2Router(router).swapExactTokensForTokens(...);
    }
    
    /**
     * @notice Rescue stuck tokens (Safety fallback)
     */
    function rescueTokens(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }
    
    /**
     * @notice Receive Ether
     */
    receive() external payable {}
}
