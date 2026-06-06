// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Test.sol";
import "../src/TradeExecutor.sol";

/**
 * @title TradeExecutorTest
 * @dev Tests for the TradeExecutor contract
 */
contract TradeExecutorTest is Test {
    TradeExecutor public executor;
    address public owner;
    address public aiAgent;
    address public unauthorized;

    bytes32 public constant STRATEGY_001 = keccak256("STRATEGY_001");

    function setUp() public {
        owner = address(this);
        aiAgent = makeAddr("aiAgent");
        unauthorized = makeAddr("unauthorized");

        executor = new TradeExecutor();
        executor.authorizeTrader(aiAgent);

        // Register a strategy
        executor.registerStrategy(STRATEGY_001, 50, aiAgent);
    }

    // ============================================================
    // DEPLOYMENT TESTS
    // ============================================================
    function test_Deployment_OwnerIsCreator() public view {
        assertEq(executor.owner(), owner);
    }

    function test_Deployment_NoInitialStrategies() public view {
        // Strategy should be inactive by default
        (bool active, , , ) = executor.strategies(keccak256("nonexistent"));
        assertFalse(active);
    }

    // ============================================================
    // STRATEGY MANAGEMENT TESTS
    // ============================================================
    function test_RegisterStrategy_SetsActiveStrategy() public view {
        (bool active, uint256 minProfit, uint256 maxGas, address exec) = executor.strategies(STRATEGY_001);
        assertTrue(active);
        assertEq(minProfit, 50);
        assertEq(exec, aiAgent);
    }

    function test_RegisterStrategy_RevertsIfDuplicate() public {
        bytes32 existing = STRATEGY_001;
        vm.expectRevert("Strategy already active");
        executor.registerStrategy(existing, 100, aiAgent);
    }

    function test_RegisterStrategy_OnlyOwner() public {
        vm.prank(unauthorized);
        vm.expectRevert();
        executor.registerStrategy(keccak256("new_strategy"), 100, unauthorized);
    }

    // ============================================================
    // TRADER AUTHORIZATION TESTS
    // ============================================================
    function test_AuthorizeTrader_AddsTrader() public {
        address newTrader = makeAddr("newTrader");
        executor.authorizeTrader(newTrader);
        assertTrue(executor.authorizedTraders(newTrader));
    }

    function test_RevokeTrader_RemovesTrader() public {
        executor.revokeTrader(aiAgent);
        assertFalse(executor.authorizedTraders(aiAgent));
    }

    function test_AuthorizeTrader_OnlyOwner() public {
        vm.prank(unauthorized);
        vm.expectRevert();
        executor.authorizeTrader(unauthorized);
    }

    // ============================================================
    // EXECUTION TESTS
    // ============================================================
    function test_ExecuteTrade_UnauthorizedReverts() public {
        vm.prank(unauthorized);
        vm.expectRevert("Unauthorized trader");
        executor.executeTrade(
            STRATEGY_001,
            address(0xdead),
            address(0xbeef),
            1 ether,
            0.9 ether
        );
    }

    function test_ExecuteTrade_InactiveStrategyReverts() public {
        bytes32 inactive = keccak256("inactive_strategy");
        vm.prank(aiAgent);
        vm.expectRevert("Strategy not active");
        executor.executeTrade(
            inactive,
            address(0xdead),
            address(0xbeef),
            1 ether,
            0.9 ether
        );
    }

    // ============================================================
    // SAFETY TESTS
    // ============================================================
    function test_RescueTokens_OnlyOwner() public {
        vm.prank(unauthorized);
        vm.expectRevert();
        executor.rescueTokens(address(0xdead), 1 ether);
    }

    // ============================================================
    // RECEIVE FUNCTION
    // ============================================================
    function test_Receive_AcceptsEth() public {
        uint256 balanceBefore = address(executor).balance;
        (bool success, ) = address(executor).call{value: 1 ether}("");
        assertTrue(success);
        assertEq(address(executor).balance, balanceBefore + 1 ether);
    }
}
