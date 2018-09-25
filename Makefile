CXX := mpic++
PROTOC := protoc
CXXFLAGS := -std=c++11 -g3 -Wall -Wextra -O2 -pthread `pkg-config --cflags protobuf grpc++`
LDFLAGS := `pkg-config --libs protobuf grpc grpc++`

INCLUDES := -I./src
BINDIR := bin
OBJDIR := obj
PROTODIR := src/protos

include src/include.mk

UTILS := $(wildcard src/util/*.cc)
C_SRCS := $(wildcard src/client/*.cc) $(UTILS) $(PROTO_MESSAGES:%.proto=%.pb.cc) $(PROTO_SERVICES:%.proto=%.grpc.pb.cc)
S_SRCS := $(wildcard src/services/*.cc) $(UTILS) $(PROTO_MESSAGES:%.proto=%.pb.cc) $(PROTO_SERVICES:%.proto=%.grpc.pb.cc)

PROTO_HEADERS := $(PROTO_MESSAGES:%.proto=%.pb.h) $(PROTO_SERVICES:%.proto=%.grpc.pb.h)

C_OBJS := $(C_SRCS:%.cc=$(OBJDIR)/%.o)
C_DEPS := $(C_SRCS:%.cc=$(OBJDIR)/%.d)
S_OBJS := $(S_SRCS:%.cc=$(OBJDIR)/%.o)
S_DEPS := $(S_SRCS:%.cc=$(OBJDIR)/%.d)

.PHONY: all
all: client server

.PHONY: client
client: $(BINDIR)/client

.PHONY: server
server: $(BINDIR)/server

$(BINDIR)/client: $(C_OBJS) $(BINDIR)
	$(CXX) -o $@ $(C_OBJS) $(LDFLAGS)

$(BINDIR)/server: $(S_OBJS) $(BINDIR)
	$(CXX) -o $@ $(S_OBJS) $(LDFLAGS)

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

-include $(C_DEPS) $(S_DEPS)
