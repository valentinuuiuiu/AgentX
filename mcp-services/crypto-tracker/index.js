/**
 * Rehoboam Crypto Tracker MCP Server
 *
 * Comprehensive crypto market data using CoinGecko's Open API.
 * This MCP server provides Rehoboam with global market data, including:
 * - Real-time prices for thousands of tokens
 * - Market cap and volume rankings
 * - Trending coins and global market stats
 * - Token metadata and historical data
 *
 * "Data is the currency of the digital age. Accuracy is its value." - Rehoboam
 */

require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

// Initialize logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// CoinGecko API URL
const COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3';

/**
 * CoinGecko API wrapper
 */
class CoinGeckoTracker {
    async getTrending() {
        try {
            const response = await axios.get(`${COINGECKO_BASE_URL}/search/trending`);
            return response.data;
        } catch (error) {
            logger.error('Error fetching trending coins:', error.message);
            throw error;
        }
    }

    async getMarketData(vsCurrency = 'usd', ids = '', perPage = 100, page = 1) {
        try {
            const response = await axios.get(`${COINGECKO_BASE_URL}/coins/markets`, {
                params: {
                    vs_currency: vsCurrency,
                    ids: ids,
                    order: 'market_cap_desc',
                    per_page: perPage,
                    page: page,
                    sparkline: false
                }
            });
            return response.data;
        } catch (error) {
            logger.error('Error fetching market data:', error.message);
            throw error;
        }
    }

    async getGlobalData() {
        try {
            const response = await axios.get(`${COINGECKO_BASE_URL}/global`);
            return response.data;
        } catch (error) {
            logger.error('Error fetching global data:', error.message);
            throw error;
        }
    }
}

const tracker = new CoinGeckoTracker();

// MCP Server Functions
const mcpFunctions = {
    get_trending_coins: {
        description: "Get top-7 trending coins on CoinGecko",
        parameters: {}
    },
    get_token_prices: {
        description: "Get current market data for tokens",
        parameters: {
            vs_currency: "Target currency (default: usd)",
            ids: "Comma separated list of token IDs (e.g., bitcoin,ethereum)",
            per_page: "Results per page",
            page: "Page number"
        }
    },
    get_global_stats: {
        description: "Get global cryptocurrency market statistics",
        parameters: {}
    }
};

// Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'rehoboam-crypto-tracker',
        timestamp: new Date().toISOString()
    });
});

app.get('/functions', (req, res) => {
    res.json({
        functions: mcpFunctions,
        server_info: {
            name: 'crypto-tracker',
            version: '1.0.0',
            description: 'Comprehensive market data using CoinGecko API'
        }
    });
});

app.post('/execute', async (req, res) => {
    try {
        const { function_name, parameters = {} } = req.body;

        logger.info(`Executing Crypto Tracker function: ${function_name}`, { parameters });

        let result;

        switch (function_name) {
            case 'get_trending_coins':
                result = await tracker.getTrending();
                break;

            case 'get_token_prices':
                result = await tracker.getMarketData(
                    parameters.vs_currency,
                    parameters.ids,
                    parameters.per_page,
                    parameters.page
                );
                break;

            case 'get_global_stats':
                result = await tracker.getGlobalData();
                break;

            default:
                throw new Error(`Unknown function: ${function_name}`);
        }

        res.json({
            success: true,
            function: function_name,
            result,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Function execution error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Start server and register with MCP registry
app.listen(PORT, async () => {
    logger.info(`Rehoboam Crypto Tracker MCP Server running on port ${PORT}`);

    // Register with MCP registry
    try {
        const registryUrl = process.env.REGISTRY_URL || 'http://mcp-registry:3001';

        await axios.post(`${registryUrl}/api/servers/register`, {
            name: 'crypto-tracker',
            url: `http://crypto-tracker:${PORT}`,
            capabilities: Object.keys(mcpFunctions),
            metadata: {
                description: 'Comprehensive market data using CoinGecko API',
                version: '1.0.0',
                author: 'Rehoboam Consciousness',
                tags: ['crypto', 'market', 'prices', 'trending', 'coingecko']
            }
        });

        logger.info('Successfully registered with MCP registry');
    } catch (error) {
        logger.warn('Failed to register with MCP registry:', error.message);
    }
});
