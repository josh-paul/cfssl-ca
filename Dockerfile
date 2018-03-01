FROM alpine:3.7

RUN apk update && \
    apk add go git gcc libc-dev libltdl libtool libgcc && \
    export GOPATH=/go && \
    go get -u github.com/cloudflare/cfssl/cmd/... && \
    apk del go git gcc libc-dev libtool libgcc && \
    mv /go/bin/* /bin/ && \
    rm -rf /go && \
    unset GOPATH

VOLUME [ "/etc/cfssl" ]
WORKDIR /etc/cfssl
EXPOSE 8888
ENTRYPOINT ["/bin/cfssl"]