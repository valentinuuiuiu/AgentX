import { ethers } from 'ethers';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002';

// Sepolia testnet config
export const SEPOLIA = {
  chainId: 11155111,
  name: 'Sepolia Testnet',
  flashArbMaster: '0x96f15Fe7Da0f32EB3a77e4eA5bf55bc2CAc29844',
  aavePoolProvider: '0x011b11C8D7A9E790114FB9F7A0e2ACF7d2B5C171',
  uniswapV2Router: '0xC532a71256731900393Bc4E2350BD5D53D2C0B6E',
  tokens: {
    WETH: '0xC558DB57039C6E8E0A6ad8A51C573a13E1C0D2A0',
    USDC: '0x94a9D9AC8415D5394D6E6f4a0d2782c3F7d13b2e',
    DAI: '0xFF34B3D4Aee8ddCd6F9AFF1e12E189D34Da9415b',
    LINK: '0xf8Fb3713D3E84F0B9727F97E3493F9e530A5e64e',
  },
};

// Fetch real prices from CoinGecko (free, no key needed)
export async function fetchRealPrices(symbols = ['bitcoin', 'ethereum', 'chainlink', 'solana', 'arbitrum', 'optimism']) {
  const idToSymbol = {
    bitcoin: 'BTC', ethereum: 'ETH', chainlink: 'LINK',
    solana: 'SOL', 'arbitrum': 'ARB', optimism: 'OP',
  };

  try {
    const res = await fetch(
      `https://api.coingecko.com/api/v3/simple/price?ids=${symbols.join(',')}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_high_24hr=true&include_low_24hr=true`
    );
    if (!res.ok) throw new Error(`CoinGecko ${res.status}`);
    const data = await res.json();

    const result = new Map();
    for (const [id, info] of Object.entries(data)) {
      const symbol = idToSymbol[id] || id.toUpperCase();
      result.set(symbol, {
        symbol,
        price: info.usd,
        change24h: info.usd * (info.usd_24h_change / 100),
        changePercent: info.usd_24h_change,
        volume: info.usd_24h_vol,
        high24h: info.usd_24h_high,
        low24h: info.usd_24h_low,
        source: 'coingecko',
        timestamp: Date.now(),
      });
    }
    return result;
  } catch (err) {
    console.error('CoinGecko fetch failed:', err);
    return null;
  }
}

// Fetch wallet token balances on Sepolia
export async function fetchSepoliaBalances(provider, walletAddress) {
  if (!provider || !walletAddress) return [];

  const ERC20_ABI = ['function balanceOf(address) view returns (uint256)', 'function decimals() view returns (uint8)', 'function symbol() view returns (string)'];
  const balances = [];

  for (const [symbol, address] of Object.entries(SEPOLIA.tokens)) {
    try {
      const contract = new ethers.Contract(address, ERC20_ABI, provider);
      const [rawBalance, decimals] = await Promise.all([
        contract.balanceOf(walletAddress),
        contract.decimals(),
      ]);
      const formatted = ethers.formatUnits(rawBalance, decimals);
      if (parseFloat(formatted) > 0) {
        balances.push({ symbol, address, balance: formatted, decimals });
      }
    } catch (e) {
      // Token might not exist or call failed
    }
  }

  // Add ETH balance
  try {
    const ethBalance = await provider.getBalance(walletAddress);
    if (ethBalance !== null && ethBalance !== undefined) {
      balances.unshift({
        symbol: 'ETH',
        address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        balance: ethers.formatEther(ethBalance),
        decimals: 18,
      });
    }
  } catch (e) {
    console.error('Error fetching ETH balance:', e);
  }

  return balances;
}

// Call FlashArbMaster.executeArbitrage on Sepolia
export async function executeFlashArbitrage(signer, asset, amount, minProfit, swapSteps) {
  const ABI = [
    'function executeArbitrage(address asset, uint256 amount, uint256 minProfit, tuple(address target, bytes data, address inputToken, uint256 inputAmount, address outputToken, uint256 minOutput)[] swapSteps) external',
    'function allowedTargets(address) view returns (bool)',
  ];

  const contract = new ethers.Contract(SEPOLIA.flashArbMaster, ABI, signer);

  // Verify allowed targets
  for (const step of swapSteps) {
    const allowed = await contract.allowedTargets(step.target);
    if (!allowed) {
      throw new Error(`Swap target ${step.target} is not allowed on FlashArbMaster. Owner must call setAllowedTarget first.`);
    }
  }

  const tx = await contract.executeArbitrage(asset, amount, minProfit, swapSteps);
  const receipt = await tx.wait();
  return {
    hash: receipt.hash,
    blockNumber: receipt.blockNumber,
    gasUsed: receipt.gasUsed.toString(),
    explorer: `https://sepolia.etherscan.io/tx/${receipt.hash}`,
  };
}

// Build a simple Uniswap V2 swap step for the FlashArbMaster
export function buildUniV2SwapStep(routerAddress, inputToken, outputToken, inputAmount, minOutput) {
  // swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline)
  const iface = new ethers.Interface([
    'function swapExactTokensForTokens(uint256,uint256,address[],address,uint256)',
  ]);
  const data = iface.encodeFunctionData('swapExactTokensForTokens', [
    inputAmount,
    minOutput,
    [inputToken, outputToken],
    SEPOLIA.flashArbMaster, // to = this contract
    Math.floor(Date.now() / 1000) + 600, // 10 min deadline
  ]);

  return {
    target: routerAddress,
    data,
    inputToken,
    inputAmount,
    outputToken,
    minOutput,
  };
}

// Fetch real price from Rehoboam API
export async function fetchAPIPrice(token) {
  try {
    const res = await fetch(`${API_BASE}/api/market/prices`);
    const data = await res.json();
    return data?.prices?.[token] || null;
  } catch {
    return null;
  }
}

// Switch MetaMask to Sepolia
export async function switchToSepolia() {
  if (!window.ethereum) throw new Error('No wallet detected');

  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: '0xaa36a7' }], // 11155111
    });
  } catch (switchError) {
    if (switchError.code === 4902) {
      await window.ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: '0xaa36a7',
          chainName: 'Sepolia Testnet',
          nativeCurrency: { name: 'SepoliaETH', symbol: 'ETH', decimals: 18 },
          rpcUrls: [`https://eth-sepolia.g.alchemy.com/v2/${import.meta.env.VITE_ALCHEMY_API_KEY || 'your-key-here'}`],
          blockExplorerUrls: ['https://sepolia.etherscan.io'],
        }],
      });
    } else {
      throw switchError;
    }
  }
}