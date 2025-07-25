# Build stage
FROM node:16 AS builder
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

# Nginx stage
FROM nginx:latest
COPY --from=builder /app/dist /usr/share/nginx/html