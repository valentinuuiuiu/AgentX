// Model Context Protocol (MCP) Server simulation for S&P 500
// This acts as a specialized tool provider for the Eliza agents

export const sp500McpServer = {
  async handleRequest(payload: any) {
    // In a real MCP, this would parse JSON-RPC and route to tools/resources
    // Here we simulate fetching S&P 500 data and returning it in MCP format
    
    const basePrice = 5165.20;
    const volatility = 15;
    
    // Generate some realistic-looking intraday data
    const mockSp500Data = [
      { time: '09:30', price: basePrice - 45 },
      { time: '10:30', price: basePrice - 30 },
      { time: '11:30', price: basePrice - 37 },
      { time: '12:30', price: basePrice - 23 },
      { time: '13:30', price: basePrice - 15 },
      { time: '14:30', price: basePrice - 20 },
      { time: '15:30', price: basePrice - 5 },
      { time: '16:00', price: basePrice + (Math.random() * volatility - (volatility / 2)) },
    ];

    return {
      jsonrpc: "2.0",
      id: payload?.id || "req-1",
      result: {
        data: mockSp500Data,
        currentPrice: mockSp500Data[mockSp500Data.length - 1].price,
        changePercent: 1.2 + (Math.random() * 0.2 - 0.1),
        status: "success",
        source: "MCP_SP500_ORACLE",
        timestamp: new Date().toISOString()
      }
    };
  }
};
