FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# --ignore-scripts: skip the husky/git-hooks `prepare` script (no .git in the image).
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
