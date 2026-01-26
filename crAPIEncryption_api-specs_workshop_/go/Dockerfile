# Multi-stage build for Go MCP Server
FROM golang:1.24.6-alpine AS builder

# Set working directory
WORKDIR /app

# Install git and ca-certificates for dependencies
RUN apk --no-cache add git ca-certificates

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the binary with optimizations
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o mcp-server .

# Final stage
FROM alpine:latest

# Install ca-certificates and wget for health checks
RUN apk --no-cache add ca-certificates wget

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Create app directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /app/mcp-server .

# Make binary executable
RUN chmod +x mcp-server

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port (if running in HTTP mode)
EXPOSE 8080

# Set non-sensitive environment variables
ENV PORT="8080"
ENV TRANSPORT="http"

# Run the binary
CMD ["./mcp-server"]