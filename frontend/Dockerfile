# Multi-stage: Node build → nginx static serve.
# `target builder` is used by the dev / e2e compose services so
# Playwright can run against `npm run dev` inside the container; the
# final `runtime` stage is the local-prod static serve.

FROM node:20-alpine AS builder
WORKDIR /work/frontend

# Reproducible install — `npm ci` requires package-lock.json. The
# lockfile is committed alongside package.json so the same versions
# install across local / CI / Docker (13.6 cleanup §2-§3).
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# App source.
COPY tsconfig.json vite.config.ts index.html ./
COPY .eslintrc.cjs ./
COPY src ./src
COPY public ./public
COPY playwright.config.ts ./
COPY e2e ./e2e

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

EXPOSE 5173
CMD ["npm", "run", "dev"]


FROM nginx:1.27-alpine AS runtime
COPY --from=builder /work/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
