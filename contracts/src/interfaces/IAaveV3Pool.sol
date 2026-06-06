// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

/**
 * @title IAaveV3Pool - Aave V3 Pool interface for flash loans
 * @dev Only the functions needed for flash loan arbitrage
 */
interface IAaveV3Pool {
    struct FlashLoanParams {
        address receiverAddress;
        address[] assets;
        uint256[] amounts;
        uint256[] interestRateModes;
        address onBehalfOf;
        bytes params;
        uint16 referralCode;
    }

    /**
     * @dev Executes a flash loan
     * @param receiverAddress The contract receiving the flash loan
     * @param assets Array of asset addresses
     * @param amounts Array of asset amounts
     * @param interestRateModes Array of interest rate modes (0 = no debt)
     * @param onBehalfOf Address to incur debt
     * @param params Arbitrary data passed to callback
     * @param referralCode Referral code
     */
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata interestRateModes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

/**
 * @title IFlashLoanReceiver - Aave V3 callback interface
 */
interface IFlashLoanReceiver {
    struct FlashLoanCallbackParams {
        address[] assets;
        uint256[] amounts;
        uint256[] premiums;
        address initiator;
        bool isFlashLoan;
    }

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}