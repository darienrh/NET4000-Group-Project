#!/bin/bash
echo "Compiling eBPF C code..."
clang -O2 -target bpf -c tc.c -o tc.o
clang -O2 -target bpf -c xdp.c -o xdp.o
echo "Done. You can now run: sudo ./adaptive_switch.py"

#this is done because i need to turn the xdp and tc code into usable object files
