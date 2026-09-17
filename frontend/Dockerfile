# Immagine Alpine per server Node.js ottimizzato e leggero
FROM node:20-alpine AS builder

WORKDIR /app

# (Placeholder) Copia i manifesti del pacchetto
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copia il sorgente
COPY . .

# Genera la build per produzione (assumendo sveltekit con adapter-node)
RUN npm run build

# Stage di produzione
FROM node:20-alpine

WORKDIR /app

# Copia solo la build e i nodemodules compilati
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

EXPOSE 3000

ENV NODE_ENV=production
# Comando per avviare il Node server (adapter-node)
CMD ["node", "build"]
