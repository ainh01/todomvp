# Frontend Dockerfile - Multi-stage build (Fly.io Compatible)
# Stage 1: Build the React application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application
FROM node:18-alpine AS runner

# Set working directory
WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Use existing node user (already exists in node:alpine image)
# or create user with different UID/GID
RUN if ! getent group appgroup > /dev/null 2>&1; then \
        addgroup -g 1001 appgroup; \
    fi && \
    if ! id -u appuser > /dev/null 2>&1; then \
        adduser -D -u 1001 -G appgroup appuser; \
    fi

# Copy built files from builder stage
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist

# Switch to non-root user
USER appuser

# Expose frontend port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the application
CMD ["serve", "-s", "dist", "-l", "3000"]
