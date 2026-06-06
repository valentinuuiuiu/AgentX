#!/bin/bash

echo "=========================================="
echo "🏃 RUNNING REHOBOAM FUNCTIONAL TESTS 🏃"
echo "=========================================="

# Export test environment variables
export TESTING="true"
export JWT_SECRET="dummy_jwt_secret_for_testing_purposes_only_1234567890"
export MCP_TOKEN="dummy_mcp_token_for_testing_purposes_only_1234567890"
export API_TOKEN="dummy_api_token_for_testing_purposes_only_1234567890"

# Source the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the functional tests
pytest tests/test_functional_rehoboam.py tests/test_real_transaction_maker.py tests/test_hive_mind_core.py tests/test_conscious_trading_agent_jules.py -v

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "✅ ALL FUNCTIONAL TESTS PASSED!"
    echo "=========================================="
else
    echo "=========================================="
    echo "❌ SOME TESTS FAILED!"
    echo "=========================================="
fi

exit $EXIT_CODE
