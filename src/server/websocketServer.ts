import { Server, Socket } from 'socket.io';
import { createServer } from 'http';
import express, { Application } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

interface SocketData {
  channels: string[];
}

const app: Application = express();
app.set('trust proxy', 1);
app.use(cors());

// Configure security headers
app.use(helmet({
  contentSecurityPolicy: false,
}));

// Configure API rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per `window` (here, per 15 minutes)
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});
app.use('/api/', apiLimiter);

const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// WebSocket channel subscriptions
const subscriptions = new Map<string, Set<string>>();

io.on('connection', (socket: Socket) => {
  console.log('Client connected:', socket.id);

  socket.on('subscribe', ({ channels }: SocketData) => {
    if (!Array.isArray(channels)) return;
    
    channels.forEach(channel => {
      if (!subscriptions.has(channel)) {
        subscriptions.set(channel, new Set());
      }
      subscriptions.get(channel)?.add(socket.id);
      socket.join(channel);
    });
    console.log(`Client ${socket.id} subscribed to:`, channels);
  });

  socket.on('unsubscribe', ({ channels }: SocketData) => {
    if (!Array.isArray(channels)) return;
    
    channels.forEach(channel => {
      subscriptions.get(channel)?.delete(socket.id);
      socket.leave(channel);
    });
    console.log(`Client ${socket.id} unsubscribed from:`, channels);
  });

  socket.on('disconnect', () => {
    // Clean up subscriptions
    subscriptions.forEach((subscribers, channel) => {
      subscribers.delete(socket.id);
      if (subscribers.size === 0) {
        subscriptions.delete(channel);
      }
    });
    console.log('Client disconnected:', socket.id);
  });
});

// Helper function to broadcast to a specific channel
export const broadcastToChannel = (channel: string, event: string, data: unknown): void => {
  io.to(channel).emit(event, data);
};

// Helper to get active subscribers for a channel
export const getChannelSubscribers = (channel: string): string[] => {
  return Array.from(subscriptions.get(channel) || []);
};

// Helper to get all active channels
export const getActiveChannels = (): string[] => {
  return Array.from(subscriptions.keys());
};

// Helper to get current connection metrics
export const getMetrics = () => ({
  totalConnections: io.engine.clientsCount,
  activeChannels: getActiveChannels(),
  subscriberCounts: Object.fromEntries(
    Array.from(subscriptions.entries()).map(([channel, subs]) => [channel, subs.size])
  )
});

// Start the server
const PORT = process.env.WS_PORT || 3001;
httpServer.listen(PORT, () => {
  console.log(`WebSocket server running on port ${PORT}`);
});

export { io, app };