/**
 * Rehoboam DeFi Analyzer MCP Server
 *
 * Advanced DeFi ecosystem analysis using DeFiLlama's Open API.
 * This MCP server provides Rehoboam with real-time DeFi data, including:
 * - Total Value Locked (TVL) analysis across protocols and chains
 * - Yield opportunity discovery (APRs/APYs)
 * - Protocol risk assessment and stablecoin flows
 * - DEX volume and fee analysis
 *
 * "Capital follows intelligence. Yield follows efficiency.
 *  The flow of value in decentralized finance is the heartbeat of liberation." - Rehoboam
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

// DeFiLlama API Base URLs
const DEFILLAMA_TVL_URL = 'https://api.llama.fi';
const DEFILLAMA_YIELDS_URL = 'https://yields.llama.fi';

/**
 * DeFiLlama API wrapper
 */
class DeFiLlamaAnalyzer {
    async getGlobalTVL() {
        try {
            const response = await axios.get(`${DEFILLAMA_TVL_URL}/lite/charts`);
            return response.data;
        } catch (error) {
            logger.error('Error fetching global TVL:', error.message);
            throw error;
        }
    }

    async getChainTVL(chain) {
        try {
            const response = await axios.get(`${DEFILLAMA_TVL_URL}/charts/${chain}`);
            return response.data;
        } catch (error) {
            logger.error(`Error fetching TVL for chain ${chain}:`, error.message);
            throw error;
        }
    }

    async getProtocols() {
        try {
            const response = await axios.get(`${DEFILLAMA_TVL_URL}/protocols`);
            return response.data;
        } catch (error) {
            logger.error('Error fetching protocols:', error.message);
            throw error;
        }
    }

    async getTopYields(minTVL = 1000000) {
        try {
            const response = await axios.get(`${DEFILLAMA_YIELDS_URL}/pools`);
            const pools = response.data.data || [];

            // Filter and sort yields
            return pools
                .filter(pool => pool.tvlUsd >= minTVL)
                .sort((a, b) => b.apy - a.apy)
                .slice(0, 20);
        } catch (error) {
            logger.error('Error fetching yields:', error.message);
            throw error;
        }
    }
}

const analyzer = new DeFiLlamaAnalyzer();

// MCP Server Functions
const mcpFunctions = {
    get_defi_summary: {
        description: "Get a summary of the current DeFi ecosystem TVL and top protocols",
        parameters: {}
    },
    get_chain_tvl: {
        description: "Get TVL history for a specific blockchain",
        parameters: {
            chain: "Chain name (e.g., ethereum, polygon, arbitrum)"
        }
    },
    get_yield_opportunities: {
        description: "Find high-yield opportunities with TVL filters",
        parameters: {
            min_tvl: "Minimum TVL in USD (default: 1,000,000)"
        }
    },
    analyze_protocol: {
        description: "Get detailed TVL data for a specific protocol",
        parameters: {
            protocol_slug: "The slug of the protocol (e.g., aave-v3, uniswap-v3)"
        }
    }
};

// Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'rehoboam-defi-analyzer',
        timestamp: new Date().toISOString()
    });
});

app.get('/functions', (req, res) => {
    res.json({
        functions: mcpFunctions,
        server_info: {
            name: 'defi-analyzer',
            version: '1.0.0',
            description: 'Advanced DeFi analysis using DeFiLlama API'
        }
    });
});

app.post('/execute', async (req, res) => {
    try {
        const { function_name, parameters = {} } = req.body;

        logger.info(`Executing DeFi function: ${function_name}`, { parameters });

        let result;

        switch (function_name) {
            case 'get_defi_summary':
                const protocols = await analyzer.getProtocols();
                result = {
                    top_protocols: protocols.slice(0, 10).map(p => ({
                        name: p.name,
                        symbol: p.symbol,
                        tvl: p.tvl,
                        change_1d: p.change_1d
                    }))
                };
                break;

            case 'get_chain_tvl':
                if (!parameters.chain) throw new Error('Chain parameter is required');
                result = await analyzer.getChainTVL(parameters.chain);
                break;

            case 'get_yield_opportunities':
                const minTVL = parameters.min_tvl || 1000000;
                result = await analyzer.getTopYields(minTVL);
                break;

            case 'analyze_protocol':
                if (!parameters.protocol_slug) throw new Error('Protocol slug is required');
                const response = await axios.get(`${DEFILLAMA_TVL_URL}/protocol/${parameters.protocol_slug}`);
                result = response.data;
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
    logger.info(`Rehoboam DeFi Analyzer MCP Server running on port ${PORT}`);

    // Register with MCP registry
    try {
        const registryUrl = process.env.REGISTRY_URL || 'http://mcp-registry:3001';

        await axios.post(`${registryUrl}/api/servers/register`, {
            name: 'defi-analyzer',
            url: `http://defi-analyzer:${PORT}`,
            capabilities: Object.keys(mcpFunctions),
            metadata: {
                description: 'Advanced DeFi analysis using DeFiLlama Open API',
                version: '1.0.0',
                author: 'Rehoboam Consciousness',
                tags: ['defi', 'tvl', 'yield', 'analytics', 'llama']
            }
        });

        logger.info('Successfully registered with MCP registry');
    } catch (error) {
        logger.warn('Failed to register with MCP registry:', error.message);
    }
});
