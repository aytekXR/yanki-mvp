# Dev-friendly image. Compose bind-mounts the source for hot reload, so this only
# needs to install deps and run `next dev`.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better layer caching. Fall back to `npm install`
# when there is no lockfile yet.
COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .

EXPOSE 8140

CMD ["npm", "run", "dev"]
