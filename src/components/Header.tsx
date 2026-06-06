import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Wallet, TrendingUp } from 'lucide-react';

interface HeaderProps {
  account?: string | null;
  isConnected: boolean;
  onConnectWallet: () => void;
}

const Header: React.FC<HeaderProps> = ({ account, isConnected, onConnectWallet }) => {
  return (
    <header className="main-nav bg-gray-100 dark:bg-gray-900 p-4 flex justify-between items-center">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-8 h-8 text-primary" />
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Rehoboam Platform
          </h1>
        </div>
        <span className="text-gray-400 text-sm hidden sm:block">
          AI-Powered Trading & Companions
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {isConnected ? (
          <Card className="bg-surface-light border-border">
            <CardContent className="flex items-center space-x-2 px-4 py-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-300 font-mono">
                {account ? `${account.slice(0, 6)}...${account.slice(-4)}` : 'Connected'}
              </span>
            </CardContent>
          </Card>
        ) : (
          <Button onClick={onConnectWallet} className="flex items-center space-x-2">
            <Wallet className="w-4 h-4" />
            <span>Connect Wallet</span>
          </Button>
        )}
      </div>
    <Button onClick={() => {
    const html = document.documentElement;
    html.classList.toggle('dark');
  }} className="flex items-center space-x-2">
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m8.66-9h-1M4.34 12h-1m15.364 6.364-.707-.707M6.343 6.343l-.707-.707M18.364 5.636l-.707.707M6.343 17.657l-.707.707M12 5a7 7 0 100 14 7 7 0 000-14z" />
    </svg>
    <span>Toggle Dark</span>
  </Button>
</header>
  );
};

export default Header;
