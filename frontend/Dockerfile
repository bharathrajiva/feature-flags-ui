# Stage 1: Build the frontend
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy rest of the app
COPY . .

# Build the app for production
RUN npm run build

# Stage 2: Serve with a lightweight HTTP server
FROM nginx:alpine

# Copy built assets to NGINX public folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Remove default NGINX config and replace with custom one (optional)
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

# Expose port
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
