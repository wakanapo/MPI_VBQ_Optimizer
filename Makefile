CXX := g++
PROTOC := protoc
CXXFLAGS := -std=c++11 -g3 -Wall -Wextra -O2 -pthread `pkg-config --cflags protobuf grpc++`
LDFLAGS := `pkg-config --libs protobuf grpc grpc++`

INCLUDES := -I./src
BINDIR := bin
OBJDIR := obj
PROTODIR := src/protos

include src/include.mk

UTILS := $(wildcard src/util/*.cc)
SRCS := $(wildcard src/client/*.cc) $(UTILS) $(PROTO_MESSAGES:%.proto=%.pb.cc) $(PROTO_SERVICES:%.proto=%.grpc.pb.cc)

PROTO_HEADERS := $(PROTO_MESSAGES:%.proto=%.pb.h) $(PROTO_SERVICES:%.proto=%.grpc.pb.h)

OBJS := $(SRCS:%.cc=$(OBJDIR)/%.o)
DEPS := $(SRCS:%.cc=$(OBJDIR)/%.d)

.PHONY: all
all: client

.PHONY: client
client: $(BINDIR)/client

$(BINDIR)/client: $(OBJS) $(BINDIR)
	$(CXX) -o $@ $(OBJS) $(LDFLAGS)

$(OBJDIR)/%.o: %.cc $(PROTO_HEADERS)
	@if [ ! -e `dirname $@` ]; then mkdir -p `dirname $@`; fi
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c -o $@ -MMD $<

.SECONDARY:
%.grpc.pb.cc %.grpc.pb.h: %.proto
	$(PROTOC) -I=$(PROTODIR) --grpc_out=$(PROTODIR) --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` $<

.SECONDARY:
%.pb.cc %.pb.h: %.proto
	$(PROTOC) -I=$(PROTODIR) --cpp_out=$(PROTODIR) $<

$(BINDIR):
	mkdir -p $(BINDIR)

.PHONY: clean
clean:
	rm -rf $(BINDIR) $(OBJDIR) $(PROTODIR)/*.pb.*

-include $(DEPS)
