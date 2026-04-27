FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port (Internal cloud-run/VPS port)
EXPOSE 3000

# Start the server using tsx in production mode
ENV NODE_ENV=production
CMD ["npm", "run", "dev"]
