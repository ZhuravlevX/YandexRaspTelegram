# Dockerfile for Rust API

# Use official Rust image as builder
FROM rust:1.70 as builder

# Create a new empty shell project
RUN USER=root cargo new --bin backend
WORKDIR /backend

# Copy manifests
COPY ./Cargo.toml ./Cargo.toml

# Build dependencies only (caching)
RUN cargo build --release
RUN rm src/*.rs

# Copy source files
COPY ./src ./src

# Build for release
RUN cargo build --release

# Final stage using a slim image
FROM debian:bullseye-slim

# Install runtime dependencies if needed
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the built binary from the builder stage
COPY --from=builder /backend/target/release/backend /usr/local/bin/backend

# Environment variables (adjust as needed)
ENV RUST_LOG=info

# Expose the port the app runs on
EXPOSE 8080

# Command to run the API
CMD ["backend"]