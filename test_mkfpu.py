import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cocotb_coverage.coverage import coverage_db, CoverPoint
import random

# Functional coverage points
@CoverPoint("fpu.opcode", xf=lambda instr: (instr >> 208) & 0xF, bins=list(range(16)), at_least=1)
@CoverPoint("fpu.sign_a", xf=lambda instr: ((instr >> 207) & 0x1), bins=[0, 1], at_least=1)
@CoverPoint("fpu.sign_b", xf=lambda instr: ((instr >> 175) & 0x1), bins=[0, 1], at_least=1)
def sample_coverage(instr):
    pass

# Convert float to 32-bit unsigned int representation
def float_to_uint32(f):
    import struct
    return struct.unpack('>I', struct.pack('>f', f))[0]

@cocotb.test()
async def mkfpu_mixed_test(dut):
    """ Test mkfpu module with both fixed and randomized FP inputs and collect coverage """

    cocotb.start_soon(Clock(dut.CLK, 10, units='ns').start())
    dut.RST_N.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    fixed_inputs = [
        (0x0, float_to_uint32(1.0), float_to_uint32(2.0)),    # add
        (0x1, float_to_uint32(5.5), float_to_uint32(3.25)),   # sub
        (0x2, float_to_uint32(-4.0), float_to_uint32(2.0)),   # mul
        (0x3, float_to_uint32(6.0), float_to_uint32(3.0)),    # div
        (0x4, float_to_uint32(0.0), float_to_uint32(-1.0)),   # compare
    ]

    test_count = 0

    for opcode, a, b in fixed_inputs:
        instr = (opcode << 208) | (a << 176) | (b << 144)
        dut.fpu__start_m.value = instr
        dut.EN__start.value = 1
        await RisingEdge(dut.CLK)
        dut.EN__start.value = 0
        await RisingEdge(dut.CLK)

        sample_coverage(instr)
        cocotb.log.info(f"✅ Test {test_count}: Opcode={opcode}, A={hex(a)}, B={hex(b)}")
        test_count += 1

    # Randomized tests
    for _ in range(10):
        opcode = random.randint(0, 15)
        a = random.choice([
            float_to_uint32(random.uniform(-1000, 1000)),
            random.choice([0x00000000, 0x7F800000, 0xFF800000, 0x7FC00000])  # 0, inf, -inf, NaN
        ])
        b = random.choice([
            float_to_uint32(random.uniform(-1000, 1000)),
            random.choice([0x00000000, 0x7F800000, 0xFF800000, 0x7FC00000])
        ])

        instr = (opcode << 208) | (a << 176) | (b << 144)
        dut.fpu__start_m.value = instr
        dut.EN__start.value = 1
        await RisingEdge(dut.CLK)
        dut.EN__start.value = 0
        await RisingEdge(dut.CLK)

        sample_coverage(instr)
        cocotb.log.info(f"✅ Random Test {test_count}: Opcode={opcode}, A={hex(a)}, B={hex(b)}")
        test_count += 1

    coverage_db.export_to_yaml(filename="mkfpu_coverage.yaml")
    cocotb.log.info("📊 Functional coverage saved to mkfpu_coverage.yaml")
