# Stage: Chrome-base (Bygges én gang og gjenbrukes)
FROM node:slim AS chrome-base
RUN apt-get update && apt-get install curl gnupg -y \
    && curl --location --silent https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install google-chrome-stable -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Stage: builder (Bygg appen)
FROM chrome-base AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY tsconfig.json ./
COPY src/ ./src
RUN npm run build

# Stage: runtime (Bruker chrome-base som grunnlag)
FROM chrome-base
WORKDIR /app

# Installer kun prod-avhengigheter
COPY package*.json ./
RUN npm install --only=production

# Kopierer kun nødvendige filer fra builder
COPY --from=builder /app/dist ./dist

EXPOSE 3000
CMD ["node", "dist/src/main.js"]
