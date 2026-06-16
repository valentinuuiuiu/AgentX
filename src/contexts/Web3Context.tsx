/// <reference types="vite/client" />

import React, { createContext, useContext, useState, useEffect } from 'react';
import { ethers, BrowserProvider, JsonRpcProvider } from 'ethers';
import { useNotification } from './NotificationContext';

declare global {
  interface Window {
    ethereum?: any;
    talismanEth?: any;
  }
}

interface Web3ContextType {
  account: string | null;
  chainId: number | null;
  provider: BrowserProvider | JsonRpcProvider | null;
  infuraProvider: JsonRpcProvider | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  switchNetwork: (chainId: number) => Promise<void>;
  isConnected: boolean;
  balance: string | null;
  getGasPrice: () => Promise<bigint | null>;
}

const Web3Context = createContext<Web3ContextType>({
  account: null,
  chainId: null,
  provider: null,
  infuraProvider: null,
  connectWallet: async () => {},
  disconnectWallet: () => {},
  switchNetwork: async () => {},
  isConnected: false,
  balance: null,
  getGasPrice: async () => null
});

export function Web3ContextProvider({ children }: { children: React.ReactNode }) {
  const [account, setAccount] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [provider, setProvider] = useState<BrowserProvider | JsonRpcProvider | null>(null);
  const [infuraProvider, setInfuraProvider] = useState<JsonRpcProvider | null>(null);
  const [balance, setBalance] = useState<string | null>(null);
  const { addNotification } = useNotification();

  useEffect(() => {
    const infuraKey = import.meta.env.VITE_INFURA_API_KEY || 'ddd78bc17de648b2a89acf424fbfa8ed';
    if (infuraKey) {
      const infuraRpcProvider = new JsonRpcProvider(`https://mainnet.infura.io/v3/${infuraKey}`);
      setInfuraProvider(infuraRpcProvider);
    }
  }, []);

  const getGasPrice = async (): Promise<bigint | null> => {
    try {
      const currentProvider = provider || infuraProvider;
      if (!currentProvider) return null;
      
      const gasPrice = await currentProvider.getFeeData();
      return gasPrice.gasPrice;
    } catch (error) {
      console.error('Error fetching gas price:', error);
      return null;
    }
  };

  const updateBalance = async (address: string, currentProvider: BrowserProvider | JsonRpcProvider) => {
    try {
      const balanceWei = await currentProvider.getBalance(address);
      const balanceEth = ethers.formatEther(balanceWei);
      setBalance(balanceEth);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const connectWallet = async () => {
    const rawProvider = (window as any).ethereum || (window as any).talismanEth;
    if (!rawProvider) {
      addNotification('error', 'Please install a Web3 wallet (MetaMask, Talisman, etc)');
      return;
    }

    try {
      const browserProvider = new BrowserProvider(rawProvider);
      const accounts = await rawProvider.request({ method: 'eth_requestAccounts' });
      const network = await browserProvider.getNetwork();
      
      setProvider(browserProvider);
      setAccount(accounts[0]);
      setChainId(Number(network.chainId));
      
      await updateBalance(accounts[0], browserProvider);
      
      addNotification('success', 'Wallet connected successfully');
    } catch (error: any) {
      console.error('Failed to connect wallet:', error);
      addNotification('error', 'Failed to connect wallet');
    }
  };

  const disconnectWallet = () => {
    setAccount(null);
    setChainId(null);
    setProvider(null);
    setBalance(null);
    addNotification('info', 'Wallet disconnected');
  };

  const switchNetwork = async (targetChainId: number) => {
    const rawProvider = (window as any).ethereum || (window as any).talismanEth;
    if (!rawProvider) {
      addNotification('error', 'Web3 provider not found');
      return;
    }

    try {
      await rawProvider.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${targetChainId.toString(16)}` }],
      });
      addNotification('success', 'Network switched successfully');
    } catch (error: any) {
      console.error('Failed to switch network:', error);
      addNotification('error', 'Failed to switch network');
    }
  };

  useEffect(() => {
    const rawProvider = (window as any).ethereum || (window as any).talismanEth;
    if (rawProvider) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          disconnectWallet();
        } else {
          setAccount(accounts[0]);
          if (provider instanceof BrowserProvider) {
            updateBalance(accounts[0], provider);
          }
          addNotification('info', 'Account changed');
        }
      };

      const handleChainChanged = (chainIdStr: string) => {
        setChainId(parseInt(chainIdStr, 16));
        addNotification('info', 'Network changed');
      };

      if (rawProvider.on) {
        rawProvider.on('accountsChanged', handleAccountsChanged);
        rawProvider.on('chainChanged', handleChainChanged);
      }

      // Check if already connected
      if (rawProvider.request) {
        rawProvider.request({ method: 'eth_accounts' })
          .then((accounts: string[]) => {
            if (accounts.length > 0) {
              const browserProvider = new BrowserProvider(rawProvider);
              browserProvider.getNetwork().then(network => {
                setProvider(browserProvider);
                setAccount(accounts[0]);
                setChainId(Number(network.chainId));
                updateBalance(accounts[0], browserProvider);
              });
            }
          })
          .catch(console.error);
      }

      return () => {
        if (rawProvider.removeListener) {
          rawProvider.removeListener('accountsChanged', handleAccountsChanged);
          rawProvider.removeListener('chainChanged', handleChainChanged);
        }
      };
    }
  }, [provider]);

  return (
    <Web3Context.Provider value={{
      account,
      chainId,
      provider,
      infuraProvider,
      connectWallet,
      disconnectWallet,
      switchNetwork,
      isConnected: !!account,
      balance,
      getGasPrice
    }}>
      {children}
    </Web3Context.Provider>
  );
}

export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (!context) {
    throw new Error('useWeb3 must be used within a Web3ContextProvider');
  }
  return context;
};
