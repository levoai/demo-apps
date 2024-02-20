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


# GoLang Build
FROM golang:alpine AS builder
ARG TARGETARCH
ARG TARGETOS
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    GOOS=$TARGETOS \
    GOARCH=$TARGETARCH
WORKDIR /build
COPY ./go.mod .
COPY ./go.sum .
RUN go mod download
COPY ./main.go ./main.go
COPY ./api ./api
RUN go mod vendor
RUN ls -al
RUN go build -o main .
WORKDIR /dist
RUN cp /build/main .

# Main Image
FROM alpine:3

# go
RUN mkdir /app
RUN apk update && apk add --no-cache curl
COPY --from=builder /dist/main /app/main
RUN ls -al /app
EXPOSE 8087

ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        wget -o wait https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait_aarch64 \
    else \
        wget -o wait https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait \
    fi
    
RUN chmod +x /wait

CMD /wait && /app/main
