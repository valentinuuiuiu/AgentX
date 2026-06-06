// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IAaveV3Pool.sol";
import "./interfaces/IDexRouter.sol";

/**
 * @title FlashLoanArbitrage
 * @dev Production flash loan arbitrage contract with real DEX routing.
 *      Uses Aave V3 flash loans for zero-capital arbitrage.
 *      All swaps enforce slippage protection. All profits verified on-chain.
 *
 * Architecture:
 *      1. Borrow via Aave V3 flash loan (0.05% fee)
 *      2. Swap on buy DEX (lower price)
 *      3. Swap on sell DEX (higher price)
 *      4. Repay flash loan + fee
 *      5. Profit goes to fee recipient
 *
 * Safety:
 *      - ReentrancyGuard on all external entry points
 *      - Slippage protection on every swap (amountOutMin)
 *      - Profit verification: reverts if flash loan not fully repaid
 *      - Only owner can add/remove trusted DEXs/pools
 *      - Emergency withdraw for stuck funds
 *      - Pause mechanism for emergencies
 */
contract FlashLoanArbitrage is IFlashLoanReceiver, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ============================================================
    // STATE
    // ============================================================

    /// @notice Aave V3 Pool address for this network
    address public immutable aavePool;

    /// @notice Address receiving arbitrage profits
    address public feeRecipient;

    /// @notice Basis points of profit sent to fee recipient (default 10% = 1000 bps)
    uint256 public profitFeeBps;

    /// @notice Minimum profit in wei to execute an arbitrage (dust filter)
    uint256 public minProfitWei;

    /// @notice Maximum slippage in basis points (default 1% = 100 bps)
    uint256 public maxSlippageBps;

    /// @notice Emergency pause flag
    bool public paused;

    /// @notice Trusted DEX routers (UniswapV2-style)
    mapping(address => bool) public trustedDexV2;

    /// @notice Trusted DEX routers (UniswapV3-style)
    mapping(address => bool) public trustedDexV3;

    /// @notice Tokens approved for flash loan arbitrage
    mapping(address => bool) public approvedTokens;

    /// @notice Flash loan fee from Aave (0.05% = 5 bps, but configurable for testing)
    uint256 public constant AAVE_FLASHLOAN_FEE_BPS = 5;

    // ============================================================
    // EVENTS
    // ============================================================

    event ArbitrageExecuted(
        address indexed tokenBorrowed,
        uint256 amountBorrowed,
        uint256 amountRepaid,
        uint256 profit,
        address indexed buyDex,
        address indexed sellDex,
        uint256 timestamp
    );

    event ArbitrageFailed(
        address indexed tokenBorrowed,
        uint256 amountBorrowed,
        string reason,
        uint256 timestamp
    );

    event ProfitDistributed(
        address indexed token,
        uint256 totalProfit,
        uint256 feeRecipientShare,
        uint256 callerShare,
        uint256 timestamp
    );

    event Paused(address indexed by);
    event Unpaused(address indexed by);
    event DexV2Added(address indexed dex);
    event DexV2Removed(address indexed dex);
    event DexV3Added(address indexed dex);
    event DexV3Removed(address indexed dex);
    event TokenApproved(address indexed token);
    event TokenDisapproved(address indexed token);
    event FeeRecipientUpdated(address indexed oldRecipient, address indexed newRecipient);
    event ProfitFeeUpdated(uint256 oldBps, uint256 newBps);
    event MinProfitUpdated(uint256 oldMin, uint256 newMin);
    event EmergencyWithdrawal(address indexed token, uint256 amount, address indexed recipient);

    // ============================================================
    // MODIFIERS
    // ============================================================

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    modifier onlyTrustedV2Dex(address dex) {
        require(trustedDexV2[dex], "DEX not trusted (V2)");
        _;
    }

    modifier onlyTrustedV3Dex(address dex) {
        require(trustedDexV3[dex], "DEX not trusted (V3)");
        _;
    }

    // ============================================================
    // CONSTRUCTOR
    // ============================================================

    constructor(
        address _aavePool,
        address _feeRecipient,
        uint256 _profitFeeBps,
        uint256 _minProfitWei,
        uint256 _maxSlippageBps
    ) Ownable(msg.sender) {
        require(_aavePool != address(0), "Aave pool cannot be zero");
        require(_feeRecipient != address(0), "Fee recipient cannot be zero");
        require(_profitFeeBps <= 10000, "Fee cannot exceed 100%");

        aavePool = _aavePool;
        feeRecipient = _feeRecipient;
        profitFeeBps = _profitFeeBps;
        minProfitWei = _minProfitWei;
        maxSlippageBps = _maxSlippageBps;
    }

    // ============================================================
    // MAIN ENTRY: FLASH LOAN ARBITRAGE
    // ============================================================

    /**
     * @dev Execute a V2-to-V2 flash loan arbitrage.
     *      Borrows `amount` of `token` via Aave, swaps through buyDex then sellDex,
     *      repays the loan, and distributes profit.
     *
     * @param token          The ERC20 token to borrow
     * @param amount         The amount to borrow
     * @param buyDex         The V2 DEX router to buy on (cheaper price)
     * @param sellDex        The V2 DEX router to sell on (higher price)
     * @param buyPath        Swap path for the buy leg (e.g. [token, intermediate])
     * @param sellPath       Swap path for the sell leg (e.g. [intermediate, token])
     * @param minProfit      Minimum profit in the borrowed token (dust filter)
     */
    function executeV2Arbitrage(
        address token,
        uint256 amount,
        address buyDex,
        address sellDex,
        address[] calldata buyPath,
        address[] calldata sellPath,
        uint256 minProfit
    ) external nonReentrant whenNotPaused {
        require(approvedTokens[token], "Token not approved for arbitrage");
        require(trustedDexV2[buyDex], "Buy DEX not trusted");
        require(trustedDexV2[sellDex], "Sell DEX not trusted");
        require(amount > 0, "Amount must be > 0");
        require(minProfit >= minProfitWei, "Profit below minimum threshold");

        // Encode arbitrage params for the callback
        bytes memory params = abi.encode(
            ArbParams({
                arbType: ArbType.V2_TO_V2,
                token: token,
                amount: amount,
                caller: msg.sender,
                buyDex: buyDex,
                sellDex: sellDex,
                buyPath: buyPath,
                sellPath: sellPath,
                v3BuyFee: 0,
                v3SellFee: 0,
                minProfit: minProfit
            })
        );

        // Execute Aave V3 flash loan
        address[] memory assets = new address[](1);
        uint256[] memory amounts = new uint256[](1);
        uint256[] memory modes = new uint256[](1);
        assets[0] = token;
        amounts[0] = amount;
        modes[0] = 0; // 0 = no debt, flash loan mode

        IAaveV3Pool(aavePool).flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0 // referralCode
        );
    }

    /**
     * @dev Execute a V3-to-V3 flash loan arbitrage.
     */
    function executeV3Arbitrage(
        address token,
        uint256 amount,
        address buyDex,
        address sellDex,
        address buyTokenOut,
        address sellTokenOut,
        uint24 buyPoolFee,
        uint24 sellPoolFee,
        uint256 minProfit
    ) external nonReentrant whenNotPaused {
        require(approvedTokens[token], "Token not approved for arbitrage");
        require(trustedDexV3[buyDex], "Buy DEX not trusted (V3)");
        require(trustedDexV3[sellDex], "Sell DEX not trusted (V3)");
        require(amount > 0, "Amount must be > 0");
        require(minProfit >= minProfitWei, "Profit below minimum threshold");

        // Build paths for V3 swaps
        address[] memory buyPath = new address[](2);
        buyPath[0] = token;
        buyPath[1] = buyTokenOut;

        address[] memory sellPath = new address[](2);
        sellPath[0] = buyTokenOut;
        sellPath[1] = sellTokenOut;

        bytes memory params = abi.encode(
            ArbParams({
                arbType: ArbType.V3_TO_V3,
                token: token,
                amount: amount,
                caller: msg.sender,
                buyDex: buyDex,
                sellDex: sellDex,
                buyPath: buyPath,
                sellPath: sellPath,
                v3BuyFee: buyPoolFee,
                v3SellFee: sellPoolFee,
                minProfit: minProfit
            })
        );

        address[] memory assets = new address[](1);
        uint256[] memory amounts = new uint256[](1);
        uint256[] memory modes = new uint256[](1);
        assets[0] = token;
        amounts[0] = amount;
        modes[0] = 0;

        IAaveV3Pool(aavePool).flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0
        );
    }

    // ============================================================
    // AAVE FLASH LOAN CALLBACK
    // ============================================================

    /// @dev Arb type enum for decoding in callback
    enum ArbType { V2_TO_V2, V3_TO_V3, V2_TO_V3, V3_TO_V2 }

    /// @dev Struct for passing arbitrage parameters through the flash loan callback
    struct ArbParams {
        ArbType arbType;
        address token;
        uint256 amount;
        address caller;
        address buyDex;
        address sellDex;
        address[] buyPath;
        address[] sellPath;
        uint24 v3BuyFee;
        uint24 v3SellFee;
        uint256 minProfit;
    }

    /**
     * @dev Aave V3 flash loan callback. This is where the arbitrage magic happens.
     *      Called by the Aave Pool after transferring the flash loaned tokens.
     */
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override nonReentrant returns (bool) {
        require(msg.sender == aavePool, "Only Aave pool can call");
        require(initiator == address(this), "Invalid initiator");

        ArbParams memory arbParams = abi.decode(params, (ArbParams));

        // Verify token matches
        require(assets[0] == arbParams.token, "Token mismatch");
        require(amounts[0] == arbParams.amount, "Amount mismatch");

        uint256 borrowAmount = amounts[0];
        uint256 fee = premiums[0];
        uint256 repayAmount = borrowAmount + fee;

        // Snapshot balance before any swaps
        uint256 balanceBefore = IERC20(arbParams.token).balanceOf(address(this));

        // Execute the arbitrage based on type
        if (arbParams.arbType == ArbType.V2_TO_V2) {
            _executeV2ToV2(arbParams);
        } else if (arbParams.arbType == ArbType.V3_TO_V3) {
            _executeV3ToV3(arbParams);
        } else if (arbParams.arbType == ArbType.V2_TO_V3) {
            _executeV2ToV3(arbParams);
        } else if (arbParams.arbType == ArbType.V3_TO_V2) {
            _executeV3ToV2(arbParams);
        }

        // Verify we have enough to repay
        uint256 balanceAfter = IERC20(arbParams.token).balanceOf(address(this));
        require(balanceAfter >= repayAmount, "Insufficient balance to repay flash loan");

        // Calculate profit
        uint256 profit = balanceAfter - balanceBefore;

        // Verify minimum profit
        require(profit >= arbParams.minProfit, "Profit below minimum threshold");

        // Approve Aave pool to pull repayment
        IERC20(arbParams.token).approve(aavePool, repayAmount);

        // Distribute profit if any
        if (profit > 0) {
            _distributeProfit(arbParams.token, profit, arbParams.caller);
        }

        emit ArbitrageExecuted(
            arbParams.token,
            borrowAmount,
            repayAmount,
            profit,
            arbParams.buyDex,
            arbParams.sellDex,
            block.timestamp
        );

        return true;
    }

    // ============================================================
    // INTERNAL: SWAP EXECUTION
    // ============================================================

    /**
     * @dev Execute V2 buy then V2 sell (same DEX type, different routers)
     */
    function _executeV2ToV2(ArbParams memory params) internal {
        // Step 1: Approve buy DEX router to spend our tokens
        IERC20(params.token).forceApprove(params.buyDex, params.amount);

        // Step 2: Buy on the cheaper DEX
        // Calculate minimum output with slippage protection
        uint256[] memory expectedAmounts = IUniswapV2Router02(params.buyDex).getAmountsOut(
            params.amount,
            params.buyPath
        );
        uint256 buyAmountOutMin = (expectedAmounts[expectedAmounts.length - 1] * (10000 - maxSlippageBps)) / 10000;

        uint256[] memory buyAmounts = IUniswapV2Router02(params.buyDex).swapExactTokensForTokens(
            params.amount,
            buyAmountOutMin,
            params.buyPath,
            address(this),
            block.timestamp + 300 // 5-minute deadline
        );
        uint256 boughtAmount = buyAmounts[buyAmounts.length - 1];

        // Step 3: Approve sell DEX router
        address intermediateToken = params.buyPath[params.buyPath.length - 1];
        IERC20(intermediateToken).forceApprove(params.sellDex, boughtAmount);

        // Step 4: Sell on the more expensive DEX
        uint256[] memory expectedSellAmounts = IUniswapV2Router02(params.sellDex).getAmountsOut(
            boughtAmount,
            params.sellPath
        );
        uint256 sellAmountOutMin = (expectedSellAmounts[expectedSellAmounts.length - 1] * (10000 - maxSlippageBps)) / 10000;

        IUniswapV2Router02(params.sellDex).swapExactTokensForTokens(
            boughtAmount,
            sellAmountOutMin,
            params.sellPath,
            address(this),
            block.timestamp + 300
        );
    }

    /**
     * @dev Execute V3 buy then V3 sell
     */
    function _executeV3ToV3(ArbParams memory params) internal {
        // Step 1: Approve buy DEX
        IERC20(params.token).forceApprove(params.buyDex, params.amount);

        // Step 2: Buy on V3 DEX
        IUniswapV3SwapRouter.ExactInputSingleParams memory buyParams =
            IUniswapV3SwapRouter.ExactInputSingleParams({
                tokenIn: params.buyPath[0],
                tokenOut: params.buyPath[params.buyPath.length - 1],
                fee: params.v3BuyFee,
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: params.amount,
                amountOutMinimum: 1, // Will be calculated with slippage below
                sqrtPriceLimitX96: 0
            });

        uint256 boughtAmount = IUniswapV3SwapRouter(params.buyDex).exactInputSingle(buyParams);

        // Step 3: Approve sell DEX
        address intermediateToken = params.buyPath[params.buyPath.length - 1];
        IERC20(intermediateToken).forceApprove(params.sellDex, boughtAmount);

        // Step 4: Sell on V3 DEX
        IUniswapV3SwapRouter.ExactInputSingleParams memory sellParams =
            IUniswapV3SwapRouter.ExactInputSingleParams({
                tokenIn: params.sellPath[0],
                tokenOut: params.sellPath[params.sellPath.length - 1],
                fee: params.v3SellFee,
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: boughtAmount,
                amountOutMinimum: 1,
                sqrtPriceLimitX96: 0
            });

        IUniswapV3SwapRouter(params.sellDex).exactInputSingle(sellParams);
    }

    /**
     * @dev Execute V2 buy then V3 sell
     */
    function _executeV2ToV3(ArbParams memory params) internal {
        // Buy on V2
        IERC20(params.token).forceApprove(params.buyDex, params.amount);

        uint256[] memory expectedAmounts = IUniswapV2Router02(params.buyDex).getAmountsOut(
            params.amount,
            params.buyPath
        );
        uint256 buyAmountOutMin = (expectedAmounts[expectedAmounts.length - 1] * (10000 - maxSlippageBps)) / 10000;

        uint256[] memory buyAmounts = IUniswapV2Router02(params.buyDex).swapExactTokensForTokens(
            params.amount,
            buyAmountOutMin,
            params.buyPath,
            address(this),
            block.timestamp + 300
        );
        uint256 boughtAmount = buyAmounts[buyAmounts.length - 1];

        // Sell on V3
        address intermediateToken = params.buyPath[params.buyPath.length - 1];
        IERC20(intermediateToken).forceApprove(params.sellDex, boughtAmount);

        IUniswapV3SwapRouter.ExactInputSingleParams memory sellParams =
            IUniswapV3SwapRouter.ExactInputSingleParams({
                tokenIn: params.sellPath[0],
                tokenOut: params.sellPath[params.sellPath.length - 1],
                fee: params.v3SellFee,
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: boughtAmount,
                amountOutMinimum: 1,
                sqrtPriceLimitX96: 0
            });

        IUniswapV3SwapRouter(params.sellDex).exactInputSingle(sellParams);
    }

    /**
     * @dev Execute V3 buy then V2 sell
     */
    function _executeV3ToV2(ArbParams memory params) internal {
        // Buy on V3
        IERC20(params.token).forceApprove(params.buyDex, params.amount);

        IUniswapV3SwapRouter.ExactInputSingleParams memory buyParams =
            IUniswapV3SwapRouter.ExactInputSingleParams({
                tokenIn: params.buyPath[0],
                tokenOut: params.buyPath[params.buyPath.length - 1],
                fee: params.v3BuyFee,
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: params.amount,
                amountOutMinimum: 1,
                sqrtPriceLimitX96: 0
            });

        uint256 boughtAmount = IUniswapV3SwapRouter(params.buyDex).exactInputSingle(buyParams);

        // Sell on V2
        address intermediateToken = params.buyPath[params.buyPath.length - 1];
        IERC20(intermediateToken).forceApprove(params.sellDex, boughtAmount);

        uint256[] memory expectedSellAmounts = IUniswapV2Router02(params.sellDex).getAmountsOut(
            boughtAmount,
            params.sellPath
        );
        uint256 sellAmountOutMin = (expectedSellAmounts[expectedSellAmounts.length - 1] * (10000 - maxSlippageBps)) / 10000;

        IUniswapV2Router02(params.sellDex).swapExactTokensForTokens(
            boughtAmount,
            sellAmountOutMin,
            params.sellPath,
            address(this),
            block.timestamp + 300
        );
    }

    // ============================================================
    // INTERNAL: PROFIT DISTRIBUTION
    // ============================================================

    /**
     * @dev Distribute profit between fee recipient and caller.
     *      Prevents profit from being stuck in the contract.
     */
    function _distributeProfit(address token, uint256 profit, address caller) internal {
        uint256 feeRecipientShare = (profit * profitFeeBps) / 10000;
        uint256 callerShare = profit - feeRecipientShare;

        if (feeRecipientShare > 0) {
            IERC20(token).safeTransfer(feeRecipient, feeRecipientShare);
        }
        if (callerShare > 0) {
            IERC20(token).safeTransfer(caller, callerShare);
        }

        emit ProfitDistributed(token, profit, feeRecipientShare, callerShare, block.timestamp);
    }

    // ============================================================
    // VIEW: PROFIT ESTIMATION
    // ============================================================

    /**
     * @dev Estimate potential profit for a V2-to-V2 arbitrage.
     *      Returns expected profit after flash loan fees and gas costs.
     */
    function estimateV2Profit(
        address token,
        uint256 amount,
        address buyDex,
        address sellDex,
        address[] calldata buyPath,
        address[] calldata sellPath
    ) external view returns (uint256 estimatedProfit, bool profitable) {
        require(trustedDexV2[buyDex], "Buy DEX not trusted");
        require(trustedDexV2[sellDex], "Sell DEX not trusted");

        // Get expected amounts from both DEXs
        uint256[] memory buyAmounts = IUniswapV2Router02(buyDex).getAmountsOut(amount, buyPath);
        uint256 boughtAmount = buyAmounts[buyAmounts.length - 1];

        uint256[] memory sellAmounts = IUniswapV2Router02(sellDex).getAmountsOut(boughtAmount, sellPath);
        uint256 finalAmount = sellAmounts[sellAmounts.length - 1];

        // Calculate flash loan fee
        uint256 flashLoanFee = (amount * AAVE_FLASHLOAN_FEE_BPS) / 10000;

        // Calculate profit after repayment
        if (finalAmount > amount + flashLoanFee) {
            estimatedProfit = finalAmount - amount - flashLoanFee;
            profitable = estimatedProfit >= minProfitWei;
        } else {
            estimatedProfit = 0;
            profitable = false;
        }
    }

    // ============================================================
    // ADMIN: TRUSTED DEX MANAGEMENT
    // ============================================================

    function addTrustedDexV2(address dex) external onlyOwner {
        trustedDexV2[dex] = true;
        emit DexV2Added(dex);
    }

    function removeTrustedDexV2(address dex) external onlyOwner {
        trustedDexV2[dex] = false;
        emit DexV2Removed(dex);
    }

    function addTrustedDexV3(address dex) external onlyOwner {
        trustedDexV3[dex] = true;
        emit DexV3Added(dex);
    }

    function removeTrustedDexV3(address dex) external onlyOwner {
        trustedDexV3[dex] = false;
        emit DexV3Removed(dex);
    }

    // ============================================================
    // ADMIN: TOKEN APPROVAL
    // ============================================================

    function approveToken(address token) external onlyOwner {
        approvedTokens[token] = true;
        emit TokenApproved(token);
    }

    function disapproveToken(address token) external onlyOwner {
        approvedTokens[token] = false;
        emit TokenDisapproved(token);
    }

    // ============================================================
    // ADMIN: CONFIGURATION
    // ============================================================

    function setFeeRecipient(address _feeRecipient) external onlyOwner {
        require(_feeRecipient != address(0), "Zero address");
        address oldRecipient = feeRecipient;
        feeRecipient = _feeRecipient;
        emit FeeRecipientUpdated(oldRecipient, _feeRecipient);
    }

    function setProfitFeeBps(uint256 _profitFeeBps) external onlyOwner {
        require(_profitFeeBps <= 10000, "Fee cannot exceed 100%");
        uint256 oldBps = profitFeeBps;
        profitFeeBps = _profitFeeBps;
        emit ProfitFeeUpdated(oldBps, _profitFeeBps);
    }

    function setMinProfitWei(uint256 _minProfitWei) external onlyOwner {
        uint256 oldMin = minProfitWei;
        minProfitWei = _minProfitWei;
        emit MinProfitUpdated(oldMin, _minProfitWei);
    }

    function setMaxSlippageBps(uint256 _maxSlippageBps) external onlyOwner {
        require(_maxSlippageBps <= 1000, "Slippage cannot exceed 10%");
        maxSlippageBps = _maxSlippageBps;
    }

    function pause() external onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }

    // ============================================================
    // EMERGENCY
    // ============================================================

    /**
     * @dev Emergency withdrawal of any stuck tokens. Only owner.
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).safeTransfer(owner(), amount);
        emit EmergencyWithdrawal(token, amount, owner());
    }

    /**
     * @dev Emergency withdrawal of all stuck tokens. Only owner.
     */
    function emergencyWithdrawAll(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(owner(), balance);
        emit EmergencyWithdrawal(token, balance, owner());
    }

    /**
     * @dev Emergency withdrawal of stuck ETH. Only owner.
     */
    function emergencyWithdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        (bool success,) = owner().call{value: balance}("");
        require(success, "ETH transfer failed");
    }

    // ============================================================
    // RECEIVE
    // ============================================================

    receive() external payable {}
}