# Copyright 2020 Traceable, Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Node build
FROM node:12 as build
RUN mkdir /app
WORKDIR /app
COPY ./package.json /app/package.json
COPY ./package-lock.json /app/package-lock.json
RUN npm install --silent
COPY ./src /app/src
COPY ./public /app/public
RUN cp /app/src/config.js.template /app/src/config.js
RUN NODE_OPTIONS=--max_old_space_size=2048 npm run build
RUN ls /app/build

# Main Image
FROM openresty/openresty:1.17.8.2-alpine
RUN apk add gettext curl 
# React
RUN rm /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
COPY ./nginx-wrapper.sh /etc/nginx/nginx-wrapper.sh
COPY ./nginx-selfsigned.crt /etc/nginx/selfsigned.crt
COPY ./nginx-selfsigned.key /etc/nginx/selfsigned.key
COPY ./nginx.conf.template /etc/nginx/conf.d/default.conf.template

RUN echo "daemon off;" >> /usr/local/openresty/nginx/conf/nginx.conf
EXPOSE 80
EXPOSE 443

ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        curl -o wait https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait_aarch64; \
    else \
        curl -o wait https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait; \
    fi
    
RUN chmod +x /wait

CMD /wait && /etc/nginx/nginx-wrapper.sh
