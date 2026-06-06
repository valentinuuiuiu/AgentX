// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Test.sol";
import "../src/FlashLoanArbitrage.sol";
import "../src/interfaces/IAaveV3Pool.sol";
import "../src/interfaces/IDexRouter.sol";

// ============================================================
// MOCK CONTRACTS
// ============================================================

contract MockERC20 is IERC20 {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public override totalSupply;
    mapping(address => uint256) public override balanceOf;
    mapping(address => mapping(address => uint256)) public override allowance;

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function mint(address to, uint256 amount) external {
        totalSupply += amount;
        balanceOf[to] += amount;
    }

    function burn(address from, uint256 amount) external {
        totalSupply -= amount;
        balanceOf[from] -= amount;
    }

    function transfer(address to, uint256 amount) external override returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function approve(address spender, uint256 amount) external override returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract MockAavePool is IAaveV3Pool {
    uint256 public feeBps = 5;

    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata interestRateModes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external {
        MockERC20 token = MockERC20(assets[0]);
        uint256 amount = amounts[0];
        uint256 fee = (amount * feeBps) / 10000;

        token.mint(receiverAddress, amount);

        uint256[] memory premiums = new uint256[](1);
        premiums[0] = fee;

        IFlashLoanReceiver(receiverAddress).executeOperation(
            assets, amounts, premiums, address(this), params
        );

        uint256 requiredRepayment = amount + fee;
        uint256 balance = token.balanceOf(receiverAddress);
        require(balance >= requiredRepayment, "Flash loan not repaid");

        token.burn(receiverAddress, requiredRepayment);
    }
}

contract MockDexV2Router is IUniswapV2Router02 {
    uint256 public buyPrice;
    uint256 public sellPrice;
    MockERC20 public inputToken;
    MockERC20 public outputToken;

    constructor(MockERC20 _inputToken, MockERC20 _outputToken, uint256 _buyPrice, uint256 _sellPrice) {
        inputToken = _inputToken;
        outputToken = _outputToken;
        buyPrice = _buyPrice;
        sellPrice = _sellPrice;
    }

    function setPrices(uint256 _buyPrice, uint256 _sellPrice) external {
        buyPrice = _buyPrice;
        sellPrice = _sellPrice;
    }

    function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256) external override returns (uint256[] memory amounts) {
        uint256 price = (path[0] == address(inputToken)) ? buyPrice : sellPrice;
        uint256 amountOut = (amountIn * price) / 1e18;
        require(amountOut >= amountOutMin, "Insufficient output");
        MockERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        MockERC20(path[path.length - 1]).mint(to, amountOut);
        amounts = new uint256[](2);
        amounts[0] = amountIn;
        amounts[1] = amountOut;
    }

    function swapTokensForExactTokens(uint256, uint256, address[] calldata, address, uint256) external pure override returns (uint256[] memory) {
        return new uint256[](0);
    }

    function getAmountsOut(uint256 amountIn, address[] calldata path) external view override returns (uint256[] memory amounts) {
        uint256 price = (path[0] == address(inputToken)) ? buyPrice : sellPrice;
        uint256 amountOut = (amountIn * price) / 1e18;
        amounts = new uint256[](2);
        amounts[0] = amountIn;
        amounts[1] = amountOut;
    }

    function getAmountsIn(uint256, address[] calldata) external pure override returns (uint256[] memory) {
        return new uint256[](0);
    }
}

// ============================================================
// TEST CONTRACT
// ============================================================

contract FlashLoanArbitrageTest is Test {
    FlashLoanArbitrage public arb;
    MockAavePool public aavePool;
    MockERC20 public usdc;
    MockERC20 public weth;
    MockDexV2Router public buyDex;
    MockDexV2Router public sellDex;

    address public owner;
    address public feeRecipient;
    address public caller;
    address public attacker;

    uint256 constant FLASH_LOAN_AMOUNT = 100_000e18;

    function setUp() public {
        owner = address(this);
        feeRecipient = makeAddr("feeRecipient");
        caller = makeAddr("caller");
        attacker = makeAddr("attacker");

        usdc = new MockERC20("USDC", "USDC");
        weth = new MockERC20("WETH", "WETH");
        aavePool = new MockAavePool();

        arb = new FlashLoanArbitrage(
            address(aavePool),
            feeRecipient,
            1000,
            1e15,
            100
        );

        arb.approveToken(address(usdc));
        buyDex = new MockDexV2Router(usdc, weth, 0.5e18, 2e18);
        sellDex = new MockDexV2Router(weth, usdc, 2.1e18, 0.48e18);
        arb.addTrustedDexV2(address(buyDex));
        arb.addTrustedDexV2(address(sellDex));

        usdc.mint(address(buyDex), 1_000_000e18);
        weth.mint(address(sellDex), 1_000_000e18);
    }

    // ============================================================
    // DEPLOYMENT TESTS
    // ============================================================

    function test_Deployment_SetsParameters() public view {
        assertEq(arb.feeRecipient(), feeRecipient);
        assertEq(arb.profitFeeBps(), 1000);
        assertEq(arb.minProfitWei(), 1e15);
        assertEq(arb.maxSlippageBps(), 100);
        assertFalse(arb.paused());
    }

    function test_Deployment_RevertZeroPool() public {
        vm.expectRevert("Aave pool cannot be zero");
        new FlashLoanArbitrage(address(0), feeRecipient, 1000, 1e15, 100);
    }

    function test_Deployment_RevertZeroFeeRecipient() public {
        vm.expectRevert("Fee recipient cannot be zero");
        new FlashLoanArbitrage(address(aavePool), address(0), 1000, 1e15, 100);
    }

    // ============================================================
    // ADMIN TESTS
    // ============================================================

    function test_AddRemoveTrustedDexV2() public {
        address newDex = makeAddr("newDex");
        arb.addTrustedDexV2(newDex);
        assertTrue(arb.trustedDexV2(newDex));
        arb.removeTrustedDexV2(newDex);
        assertFalse(arb.trustedDexV2(newDex));
    }

    function test_AddTrustedDexV2_OnlyOwner() public {
        vm.prank(attacker);
        vm.expectRevert();
        arb.addTrustedDexV2(makeAddr("fake"));
    }

    function test_ApproveDisapproveToken() public {
        address newToken = makeAddr("newToken");
        arb.approveToken(newToken);
        assertTrue(arb.approvedTokens(newToken));
        arb.disapproveToken(newToken);
        assertFalse(arb.approvedTokens(newToken));
    }

    function test_SetFeeRecipient() public {
        address newRecipient = makeAddr("newRecipient");
        arb.setFeeRecipient(newRecipient);
        assertEq(arb.feeRecipient(), newRecipient);
    }

    function test_SetFeeRecipient_RevertZero() public {
        vm.expectRevert("Zero address");
        arb.setFeeRecipient(address(0));
    }

    function test_SetProfitFeeBps() public {
        arb.setProfitFeeBps(500);
        assertEq(arb.profitFeeBps(), 500);
    }

    function test_SetProfitFeeBps_RevertOver100() public {
        vm.expectRevert("Fee cannot exceed 100%");
        arb.setProfitFeeBps(10001);
    }

    function test_SetMinProfitWei() public {
        arb.setMinProfitWei(2e15);
        assertEq(arb.minProfitWei(), 2e15);
    }

    function test_PauseUnpause() public {
        arb.pause();
        assertTrue(arb.paused());
        arb.unpause();
        assertFalse(arb.paused());
    }

    function test_Pause_OnlyOwner() public {
        vm.prank(attacker);
        vm.expectRevert();
        arb.pause();
    }

    // ============================================================
    // FUZZ TESTS
    // ============================================================

    function testFuzz_SetProfitFeeBps(uint256 bps) public {
        vm.assume(bps <= 10000);
        arb.setProfitFeeBps(bps);
        assertEq(arb.profitFeeBps(), bps);
    }

    function testFuzz_SetMinProfitWei(uint256 minProfit) public {
        arb.setMinProfitWei(minProfit);
        assertEq(arb.minProfitWei(), minProfit);
    }

    function testFuzz_SlippageBpsValidRange(uint256 bps) public {
        if (bps <= 1000) {
            arb.setMaxSlippageBps(bps);
            assertEq(arb.maxSlippageBps(), bps);
        } else {
            vm.expectRevert("Slippage cannot exceed 10%");
            arb.setMaxSlippageBps(bps);
        }
    }

    function testFuzz_TokenApproval(address token) public {
        vm.assume(token != address(0));
        arb.approveToken(token);
        assertTrue(arb.approvedTokens(token));
        arb.disapproveToken(token);
        assertFalse(arb.approvedTokens(token));
    }

    function testFuzz_EmergencyWithdraw(uint256 mintAmount) public {
        vm.assume(mintAmount > 0);
        vm.assume(mintAmount < type(uint128).max);
        MockERC20 fuzzToken = new MockERC20("Fuzz", "FUZZ");
        fuzzToken.mint(address(arb), mintAmount);
        uint256 ownerBalBefore = fuzzToken.balanceOf(owner);
        arb.emergencyWithdraw(address(fuzzToken), mintAmount);
        assertEq(fuzzToken.balanceOf(owner), ownerBalBefore + mintAmount);
    }

    function testFuzz_ProfitDistributionConservation(uint256 profit, uint256 feeBps) public pure {
        vm.assume(profit > 0);
        vm.assume(profit < type(uint128).max);
        vm.assume(feeBps <= 10000);
        uint256 feeShare = (profit * feeBps) / 10000;
        uint256 callerShare = profit - feeShare;
        assert(feeShare + callerShare == profit);
    }

    function testFuzz_AaveFlashLoanFeeCalculation(uint256 amount) public pure {
        vm.assume(amount > 0);
        vm.assume(amount < type(uint128).max);
        uint256 fee = (amount * 5) / 10000;
        uint256 repayment = amount + fee;
        assertGt(fee, 0);
        assertLt(fee, amount);
        assertGt(repayment, amount);
    }

    // ============================================================
    // INVARIANT TESTS
    // ============================================================

    function testInvariant_SlippageNeverExceedsMax() public {
        vm.expectRevert("Slippage cannot exceed 10%");
        arb.setMaxSlippageBps(1001);
    }

    function testInvariant_ProfitFeeNeverExceeds100() public {
        vm.expectRevert("Fee cannot exceed 100%");
        arb.setProfitFeeBps(10001);
    }

    function testInvariant_ZeroAddressCannotBeFeeRecipient() public {
        vm.expectRevert("Zero address");
        arb.setFeeRecipient(address(0));
    }

    function testInvariant_PausedContractRejectsArbitrage() public {
        arb.pause();
        address[] memory buyPath = new address[](2);
        buyPath[0] = address(usdc);
        buyPath[1] = address(weth);
        address[] memory sellPath = new address[](2);
        sellPath[0] = address(weth);
        sellPath[1] = address(usdc);

        vm.expectRevert("Contract is paused");
        arb.executeV2Arbitrage(address(usdc), FLASH_LOAN_AMOUNT, address(buyDex), address(sellDex), buyPath, sellPath, 1e15);
    }

    function testInvariant_UnapprovedTokensReject() public {
        MockERC20 newToken = new MockERC20("NEW", "NEW");
        address[] memory buyPath = new address[](2);
        buyPath[0] = address(newToken);
        buyPath[1] = address(weth);
        address[] memory sellPath = new address[](2);
        sellPath[0] = address(weth);
        sellPath[1] = address(newToken);

        vm.expectRevert("Token not approved for arbitrage");
        arb.executeV2Arbitrage(address(newToken), FLASH_LOAN_AMOUNT, address(buyDex), address(sellDex), buyPath, sellPath, 1e15);
    }

    function testInvariant_UntrustedDexRejects() public {
        address fakeDex = makeAddr("fakeDex");
        address[] memory buyPath = new address[](2);
        buyPath[0] = address(usdc);
        buyPath[1] = address(weth);
        address[] memory sellPath = new address[](2);
        sellPath[0] = address(weth);
        sellPath[1] = address(usdc);

        vm.expectRevert("Buy DEX not trusted");
        arb.executeV2Arbitrage(address(usdc), FLASH_LOAN_AMOUNT, fakeDex, address(sellDex), buyPath, sellPath, 1e15);

        vm.expectRevert("Sell DEX not trusted");
        arb.executeV2Arbitrage(address(usdc), FLASH_LOAN_AMOUNT, address(buyDex), fakeDex, buyPath, sellPath, 1e15);
    }

    function testInvariant_ZeroAmountRejects() public {
        address[] memory buyPath = new address[](2);
        buyPath[0] = address(usdc);
        buyPath[1] = address(weth);
        address[] memory sellPath = new address[](2);
        sellPath[0] = address(weth);
        sellPath[1] = address(usdc);

        vm.expectRevert("Amount must be > 0");
        arb.executeV2Arbitrage(address(usdc), 0, address(buyDex), address(sellDex), buyPath, sellPath, 1e15);
    }

    // ============================================================
    // EDGE CASES
    // ============================================================

    function test_EdgeCase_100PercentFee() public {
        arb.setProfitFeeBps(10000);
        assertEq(arb.profitFeeBps(), 10000);
    }

    function test_EdgeCase_ZeroFee() public {
        arb.setProfitFeeBps(0);
        assertEq(arb.profitFeeBps(), 0);
    }

    function test_EdgeCase_MaxSlippageBoundary() public {
        arb.setMaxSlippageBps(1000);
        assertEq(arb.maxSlippageBps(), 1000);
    }

    function test_EdgeCase_ReceiveETH() public {
        (bool success,) = address(arb).call{value: 1 ether}("");
        assertTrue(success);
        assertEq(address(arb).balance, 1 ether);
    }

    function test_EdgeCase_EmergencyWithdrawETH() public {
        (bool success,) = address(arb).call{value: 2 ether}("");
        assertTrue(success);
        uint256 ownerBalBefore = owner.balance;
        arb.emergencyWithdrawETH();
        assertEq(owner.balance, ownerBalBefore + 2 ether);
        assertEq(address(arb).balance, 0);
    }
}