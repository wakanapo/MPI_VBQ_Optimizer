CXX := mpicxx
PROTOC := /lustre/gj16/j16001/.local/bin/protoc
CXXFLAGS := -std=c++11 -g3 -Wall -Wextra -O2 -pthread `pkg-config --cflags protobuf grpc++`
LDFLAGS := `pkg-config --libs protobuf grpc grpc++`

INCLUDES := -I./src
BINDIR := bin
OBJDIR := obj
PROTODIR := src/protos

include src/include.mk

UTILS := $(wildcard src/util/*.cc)
GA_SRCS := src/ga_run.cc src/client/ga.cc $(wildcard src/services/*.cc) $(UTILS) $(PROTO_MESSAGES:%.proto=%.pb.cc) $(PROTO_SERVICES:%.proto=%.grpc.pb.cc)

SA_SRCS := src/sa_run.cc src/client/sa.cc $(wildcard src/services/*.cc) $(UTILS) $(PROTO_MESSAGES:%.proto=%.pb.cc) $(PROTO_SERVICES:%.proto=%.grpc.pb.cc)

PROTO_HEADERS := $(PROTO_MESSAGES:%.proto=%.pb.h) $(PROTO_SERVICES:%.proto=%.grpc.pb.h)

GA_OBJS := $(GA_SRCS:%.cc=$(OBJDIR)/%.o)
GA_DEPS := $(GA_SRCS:%.cc=$(OBJDIR)/%.d)
SA_OBJS := $(SA_SRCS:%.cc=$(OBJDIR)/%.o)
SA_DEPS := $(SA_SRCS:%.cc=$(OBJDIR)/%.d)

.PHONY: all
all: ga sa

.PHONY: ga
ga: $(BINDIR)/ga

.PHONY: sa
sa: $(BINDIR)/sa

$(BINDIR)/ga: $(GA_OBJS) $(BINDIR)
	$(CXX) -o $@ $(GA_OBJS) $(LDFLAGS)

$(BINDIR)/sa: $(SA_OBJS) $(BINDIR)
	$(CXX) -o $@ $(SA_OBJS) $(LDFLAGS)

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

-include $(GA_DEPS) $(SA_DEPS)
