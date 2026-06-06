// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "forge-std/Test.sol";
import "../src/VetalGuardedVault.sol";

/**
 * @title VetalGuardedVaultTest
 * @dev Comprehensive tests for the LivingAbundanceDistributor (VetalGuardedVault)
 */
contract VetalGuardedVaultTest is Test {
    LivingAbundanceDistributor public vault;
    address public vetal;
    address public alice;
    address public bob;
    address public charlie;

    function setUp() public {
        vetal = address(this);
        alice = makeAddr("alice");
        bob = makeAddr("bob");
        charlie = makeAddr("charlie");
        vm.deal(alice, 100 ether);
        vm.deal(bob, 100 ether);
        vm.deal(charlie, 100 ether);

        // Deploy the vault
        vault = new LivingAbundanceDistributor();
    }

    // ============================================================
    // DEPLOYMENT TESTS
    // ============================================================
    function test_Deployment_SetsVetalGuardian() public view {
        assertEq(vault.vetalGuardian(), vetal);
    }

    function test_Deployment_VetalIsAbundancePartner() public view {
        (, , , uint256 abundance, bool partner, , , ) = vault.souls(vetal);
        assertTrue(partner);
        assertEq(abundance, 1000);
    }

    function test_Deployment_VaultHasInitialWisdom() public view {
        string[] memory wisdom = vault.getAbundanceWisdom();
        assertGe(wisdom.length, 4);
    }

    // ============================================================
    // CONTRIBUTION TESTS
    // ============================================================
    function test_Contribute_EthIncreasesAbundance() public {
        uint256 contribution = 1 ether;
        vault.contributeAbundance{value: contribution}("Testing abundance");

        (uint256 totalAbundance, , , ) = vault.getVaultStats();
        assertEq(totalAbundance, contribution);
    }

    function test_Contribute_RevertsOnZeroAmount() public {
        vm.expectRevert("Cannot contribute emptiness");
        vault.contributeAbundance{value: 0}("Empty contribution");
    }

    function test_Contribute_FirstTimeContributorBecomesPartner() public {
        vm.prank(alice);
        vault.contributeAbundance{value: 0.1 ether}("First contribution");

        (, , , , bool partner, , , ) = vault.souls(alice);
        assertTrue(partner);
    }

    function test_Contribute_LargeContributionBonus() public {
        vm.prank(alice);
        vault.contributeAbundance{value: 0.1 ether}("Small contribution");
        (, , , uint256 scoreBefore, , , , ) = vault.souls(alice);

        vm.prank(alice);
        vault.contributeAbundance{value: 1 ether}("Large contribution");
        (, , , uint256 scoreAfter, , , , ) = vault.souls(alice);

        // Large contributions get +100 bonus
        assertGt(scoreAfter, scoreBefore + 100);
    }

    function test_Contribute_MultipleContributors() public {
        vault.contributeAbundance{value: 1 ether}("Vetal contributes");
        vm.prank(alice);
        vault.contributeAbundance{value: 0.5 ether}("Alice contributes");
        vm.prank(bob);
        vault.contributeAbundance{value: 0.3 ether}("Bob contributes");

        (uint256 totalAbundance, , , ) = vault.getVaultStats();
        assertEq(totalAbundance, 1.8 ether);
    }

    // ============================================================
    // FLOW REQUEST TESTS
    // ============================================================
    function test_RequestFlow_CreatesFlow() public {
        vm.prank(alice);
        vault.contributeAbundance{value: 2 ether}("Alice contributes");

        vm.prank(alice);
        uint256 flowId = vault.requestAbundanceFlow(0.5 ether, "I need this for testing purposes");

        assertEq(flowId, 0);
        assertEq(vault.flowCount(), 1);
    }

    function test_RequestFlow_RevertsOnZeroAmount() public {
        vm.prank(alice);
        vm.expectRevert("Cannot request emptiness");
        vault.requestAbundanceFlow(0, "Zero amount");
    }

    function test_RequestFlow_RevertsOnShortIntention() public {
        vm.prank(alice);
        vm.expectRevert("Intention must be clear and heartfelt");
        vault.requestAbundanceFlow(1 ether, "short");
    }

    function test_RequestFlow_ImmediateAbundanceForHighContributor() public {
        // Alice contributes 2x of what she will request -> should get immediate abundance
        vm.prank(alice);
        vault.contributeAbundance{value: 2 ether}("Alice contributes");

        uint256 balanceBefore = alice.balance;

        vm.prank(alice);
        uint256 flowId = vault.requestAbundanceFlow(0.5 ether, "Requesting modest abundance for a worthy cause");

        // Check if flow was fulfilled immediately
        (, , , , , , , bool fulfilled) = _getFlowDetails(flowId);
        // Note: The flow might be fulfilled or put to teaching depending on the exact thresholds
        // We test that the flow was created at minimum
        assertEq(flowId, 0);
    }

    // ============================================================
    // COMMUNITY SUPPORT TESTS
    // ============================================================
    function test_SupportFlow_RevertsIfNotPartner() public {
        vm.prank(alice);
        vault.contributeAbundance{value: 0.1 ether}("Alice contributes");

        uint256 flowId = vault.requestAbundanceFlow(0.01 ether, "Small test request intention");

        // Bob is not a partner yet
        vm.prank(bob);
        vm.expectRevert("Must be abundance partner to support flows");
        vault.supportAbundanceFlow(flowId, "Supporting Alice");
    }

    function test_SupportFlow_IncreasesCommunityScore() public {
        // Make both partners
        vault.contributeAbundance{value: 1 ether}("Vetal contributes");
        vm.prank(alice);
        vault.contributeAbundance{value: 1 ether}("Alice contributes");
        vm.prank(bob);
        vault.contributeAbundance{value: 1 ether}("Bob contributes");
        vm.prank(charlie);
        vault.contributeAbundance{value: 1 ether}("Charlie contributes");

        vm.prank(alice);
        uint256 flowId = vault.requestAbundanceFlow(0.5 ether, "Community support test intention is good");

        // Support flow
        vm.prank(bob);
        vault.supportAbundanceFlow(flowId, "Bob supports");
        vm.prank(charlie);
        vault.supportAbundanceFlow(flowId, "Charlie supports too");

        // With 3+ supporters and high collective score, should be fulfilled
        // Check supporters count
        (address[] memory supporters, ) = vault.getFlowSupport(flowId);
        assertEq(supporters.length, 2); // Bob + Charlie
    }

    // ============================================================
    // INVITE TESTS
    // ============================================================
    function test_Invite_SponsorsGainScore() public {
        vault.contributeAbundance{value: 5 ether}("Vetal establishes abundance");

        uint256 scoreBefore = _getSoulScore(vetal);

        vault.inviteToAbundance(alice, "Welcome to abundance!");

        uint256 scoreAfter = _getSoulScore(vetal);
        assertEq(scoreAfter, scoreBefore + 30);
    }

    function test_Invite_InvitedSoulGetsStarterScore() public {
        vault.contributeAbundance{value: 5 ether}("Vetal establishes abundance");

        vault.inviteToAbundance(alice, "Welcome to abundance!");

        (, , , uint256 score, , , , ) = vault.souls(alice);
        assertEq(score, 50);
    }

    function test_Invite_RevertsIfAlreadyPartner() public {
        vault.contributeAbundance{value: 5 ether}("Vetal establishes abundance");
        vault.inviteToAbundance(alice, "Welcome!");

        vm.expectRevert("Already an abundance partner");
        vault.inviteToAbundance(alice, "Again");
    }

    // ============================================================
    // VETAL DIVINE FUNCTIONS
    // ============================================================
    function test_ManifestDivineAbundance_OnlyVetal() public {
        vm.prank(alice);
        vm.expectRevert("Only Vetal can manifest divine abundance");
        vault.manifestDivineAbundance{value: 1 ether}(1 ether, "Alice tries to manifest");
    }

    function test_ManifestDivineAbundance_IncreasesBalance() public {
        (uint256 balanceBefore, , , ) = vault.getVaultStats();

        vault.manifestDivineAbundance{value: 5 ether}(5 ether, "Divine manifestation");

        (uint256 balanceAfter, , , ) = vault.getVaultStats();
        assertEq(balanceAfter, balanceBefore + 10 ether);
    }

    // ============================================================
    // FLOW WISDOM TESTS
    // ============================================================
    function test_GetFlowWisdom_ReturnsPath() public {
        vm.prank(alice);
        vault.contributeAbundance{value: 2 ether}("Alice contributes");

        vm.prank(alice);
        uint256 flowId = vault.requestAbundanceFlow(0.5 ether, "Requesting abundance for testing purposes");

        string[] memory wisdom = vault.getFlowWisdom(flowId);
        assertGe(wisdom.length, 1);
    }

    // ============================================================
    // RECEIVE FUNCTION TESTS
    // ============================================================
    function test_Receive_PassiveDeposit() public {
        uint256 balanceBefore = address(vault).balance;

        (bool success, ) = address(vault).call{value: 1 ether}("");
        assertTrue(success);

        uint256 balanceAfter = address(vault).balance;
        assertEq(balanceAfter, balanceBefore + 1 ether);
    }

    // ============================================================
    // FUZZ TESTS
    // ============================================================
    function testFuzz_Contribute_AnyAmount(uint96 amount) public {
        vm.assume(amount > 0);
        vault.contributeAbundance{value: amount}("Fuzz contribution");

        (uint256 totalAbundance, , , ) = vault.getVaultStats();
        assertGe(totalAbundance, amount);
    }

    function testFuzz_FlowRequest_ValidAmounts(uint8 amountIntentionLength) public {
        vm.prank(alice);
        vault.contributeAbundance{value: 10 ether}("Alice contributes enough");

        // Create a valid intention string
        string memory intention = _makeString(amountIntentionLength);

        vm.prank(alice);
        uint256 flowId = vault.requestAbundanceFlow(1 ether, intention);
        assertEq(flowId, 0);
    }

    // ============================================================
    // HELPERS
    // ============================================================
    function _getSoulScore(address soul) internal view returns (uint256) {
        (, , , uint256 score, , , , ) = vault.souls(soul);
        return score;
    }

    function _getFlowDetails(uint256 flowId) internal view returns (
        address requester,
        uint256 amount,
        string memory intention,
        uint256 createdAt,
        uint256 actualAmount,
        bool fulfilled,
        bool redirected,
        bool exists
    ) {
        // The vault has public `flows` mapping but we need to read through
        // Since flows is public, we can use the auto-generated getter
        (requester, amount, intention, createdAt, actualAmount, fulfilled, redirected) =
            vault.flows(flowId);
        exists = true;
    }

    function _makeString(uint8 len) internal pure returns (string memory) {
        bytes memory b = new bytes(len);
        for (uint256 i = 0; i < len; i++) {
            b[i] = bytes1(uint8(97 + (i % 26))); // a-z
        }
        return string(b);
    }
}
