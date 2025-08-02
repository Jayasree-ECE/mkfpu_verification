MODULE := test_mkfpu
TOPLEVEL := mkfpu
TOPLEVEL_LANG := verilog

VERILOG_SOURCES := $(PWD)/mkfpu.v $(PWD)/mkfpu_bsvfloat.v $(PWD)/FIFO1.v

SIM := icarus

include $(shell cocotb-config --makefiles)/Makefile.sim
