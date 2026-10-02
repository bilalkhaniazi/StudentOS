FROM node:22-alpine AS deps
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /web
COPY --from=deps /web/node_modules ./node_modules
COPY web/ ./
ARG API_INTERNAL_URL=http://api:43124
ENV API_INTERNAL_URL=${API_INTERNAL_URL}
ARG NEXT_PUBLIC_DEV_LOGIN=false
ENV NEXT_PUBLIC_DEV_LOGIN=${NEXT_PUBLIC_DEV_LOGIN}
RUN npm run build

FROM node:22-alpine
WORKDIR /web
ENV NODE_ENV=production
ENV API_INTERNAL_URL=http://api:43124
ENV AUTH_TRUST_HOST=true
ENV AUTH_URL=http://127.0.0.1:43123
COPY --from=build /web ./
EXPOSE 43123
CMD ["npm", "run", "start", "--", "-p", "43123", "-H", "0.0.0.0"]
