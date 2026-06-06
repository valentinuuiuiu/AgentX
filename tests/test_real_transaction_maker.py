import pytest
from unittest.mock import patch, MagicMock
from real_transaction_maker import RealTransactionMaker
import os

@pytest.fixture
def transaction_maker():
    with patch('real_transaction_maker.Web3') as mock_web3:
        # Create a mock web3 instance
        mock_w3_instance = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.block_number = 12345678
        mock_web3.return_value = mock_w3_instance
        
        # We also need to patch HTTPProvider so it doesn't try to make real requests
        with patch('real_transaction_maker.Web3.HTTPProvider'):
            # Instantiate with mocked Web3
            maker = RealTransactionMaker()
            maker.w3 = mock_w3_instance
            return maker

def test_check_wallet_status_with_funds(transaction_maker):
    """Test wallet status when wallet has funds."""
    # Mock balance and nonce
    transaction_maker.w3.eth.get_balance.return_value = int(1.5 * 10**18)  # 1.5 ETH in wei
    transaction_maker.w3.from_wei.return_value = 1.5
    transaction_maker.w3.eth.get_transaction_count.return_value = 5
    
    status = transaction_maker.check_wallet_status()
    
    assert status is not None
    assert status['balance_eth'] == 1.5
    assert status['balance_usd'] == 1.5 * 3000
    assert status['nonce'] == 5
    assert status['has_funds'] is True

def test_check_wallet_status_empty(transaction_maker):
    """Test wallet status when wallet is empty."""
    transaction_maker.w3.eth.get_balance.return_value = 0
    transaction_maker.w3.from_wei.return_value = 0.0
    transaction_maker.w3.eth.get_transaction_count.return_value = 0
    
    status = transaction_maker.check_wallet_status()
    
    assert status is not None
    assert status['balance_eth'] == 0.0
    assert status['nonce'] == 0
    assert status['has_funds'] is False

@patch('os.getenv')
def test_create_test_transaction_no_private_key(mock_getenv, transaction_maker):
    """Test transaction creation aborts if no private key."""
    mock_getenv.return_value = None
    
    result = transaction_maker.create_test_transaction()
    
    assert result is False

@patch('os.getenv')
@patch('builtins.input', return_value='NO')
@patch('eth_account.Account.from_key')
def test_create_test_transaction_insufficient_funds(mock_from_key, mock_input, mock_getenv, transaction_maker):
    """Test transaction creation aborts if insufficient funds."""
    mock_getenv.return_value = '0x1234567890abcdef'
    
    # Mock account
    mock_account = MagicMock()
    mock_account.address = transaction_maker.your_wallet
    mock_from_key.return_value = mock_account
    
    # Mock balance to be very low
    transaction_maker.w3.eth.get_balance.return_value = 1000
    transaction_maker.w3.from_wei.return_value = 0.0001
    
    result = transaction_maker.create_test_transaction()
    
    assert result is False
