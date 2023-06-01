# where am I
#ROOT_DIR = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
GOBIN := go
BIN_NAME := test-service
GOPATH := $(shell go env GOPATH)
GO_VERSION=$(shell go version)
BUILD_TIME=$(shell date)

###############################################################################
# default target
###############################################################################
all: build


###############################################################################
# generate code
###############################################################################
.PHONY: build
build:
	$(info [Build $(BIN_NAME)])
	$(GOBIN) build $(RACE_OPT) $(GOLDFLAGS) -o $(BIN_NAME) ./
