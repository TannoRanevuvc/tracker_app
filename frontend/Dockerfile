FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .
RUN npm run build

FROM alpine:3.19
COPY --from=builder /app/dist /static
CMD ["sh", "-c", "cp -rf /static/. /app/dist/ && tail -f /dev/null"]
