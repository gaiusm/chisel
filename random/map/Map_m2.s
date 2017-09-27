	.file	"Map_m2.cpp"
	.text
.Ltext0:
	.type	_ZL4initiPPc, @function
_ZL4initiPPc:
.LFB0:
	.file 1 "Map_m2.cpp"
	.loc 1 72 0
	.cfi_startproc
	.cfi_personality 0x3,__gxx_personality_v0
	.cfi_lsda 0x3,.LLSDA0
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%rbx
	subq	$24, %rsp
	.cfi_offset 3, -24
	movl	%edi, -20(%rbp)
	movq	%rsi, -32(%rbp)
	.loc 1 74 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
.LEHB0:
	call	_M2_Storage_init
	.loc 1 75 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_SYSTEM_init
	.loc 1 76 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_M2RTS_init
	.loc 1 77 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_RTExceptions_init
	.loc 1 78 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_NumberIO_init
	.loc 1 79 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_StrLib_init
	.loc 1 80 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_ASCII_init
	.loc 1 81 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Indexing_init
	.loc 1 82 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_errno_init
	.loc 1 83 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_termios_init
	.loc 1 84 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_FIO_init
	.loc 1 85 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_IO_init
	.loc 1 86 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_UnixArgs_init
	.loc 1 87 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_StdIO_init
	.loc 1 88 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Args_init
	.loc 1 89 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Chance_init
	.loc 1 90 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Debug_init
	.loc 1 91 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_StrIO_init
	.loc 1 92 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_StoreCoords_init
	.loc 1 93 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Assertion_init
	.loc 1 94 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Geometry_init
	.loc 1 95 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_MakeBoxes_init
	.loc 1 96 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_SysStorage_init
	.loc 1 97 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_MapOptions_init
	.loc 1 98 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_SysExceptions_init
	.loc 1 99 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_M2EXCEPTION_init
	.loc 1 100 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_BoxMap_init
	.loc 1 101 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Break_init
	.loc 1 102 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_RoomMap_init
	.loc 1 103 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_WriteMap_init
	.loc 1 104 0
	call	M2RTS_ExecuteInitialProcedures
	.loc 1 105 0
	movq	-32(%rbp), %rdx
	movl	-20(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_M2_Map_init
.LEHE0:
	.loc 1 110 0
	jmp	.L1
.L5:
	.loc 1 107 0
	movq	%rax, %rdi
	call	__cxa_begin_catch
.LEHB1:
	.loc 1 108 0
	call	RTExceptions_DefaultErrorCatch
.LEHE1:
.LEHB2:
	.loc 1 107 0
	call	__cxa_end_catch
.LEHE2:
	.loc 1 110 0
	jmp	.L1
.L6:
	movq	%rax, %rbx
	.loc 1 107 0
	call	__cxa_end_catch
	movq	%rbx, %rax
	movq	%rax, %rdi
.LEHB3:
	call	_Unwind_Resume
.LEHE3:
.L1:
	.loc 1 110 0
	addq	$24, %rsp
	popq	%rbx
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.globl	__gxx_personality_v0
	.section	.gcc_except_table,"a",@progbits
	.align 4
.LLSDA0:
	.byte	0xff
	.byte	0x3
	.uleb128 .LLSDATT0-.LLSDATTD0
.LLSDATTD0:
	.byte	0x1
	.uleb128 .LLSDACSE0-.LLSDACSB0
.LLSDACSB0:
	.uleb128 .LEHB0-.LFB0
	.uleb128 .LEHE0-.LEHB0
	.uleb128 .L5-.LFB0
	.uleb128 0x1
	.uleb128 .LEHB1-.LFB0
	.uleb128 .LEHE1-.LEHB1
	.uleb128 .L6-.LFB0
	.uleb128 0
	.uleb128 .LEHB2-.LFB0
	.uleb128 .LEHE2-.LEHB2
	.uleb128 0
	.uleb128 0
	.uleb128 .LEHB3-.LFB0
	.uleb128 .LEHE3-.LEHB3
	.uleb128 0
	.uleb128 0
.LLSDACSE0:
	.byte	0x1
	.byte	0
	.align 4
	.long	0

.LLSDATT0:
	.text
	.size	_ZL4initiPPc, .-_ZL4initiPPc
	.type	_ZL6finishv, @function
_ZL6finishv:
.LFB1:
	.loc 1 113 0
	.cfi_startproc
	.cfi_personality 0x3,__gxx_personality_v0
	.cfi_lsda 0x3,.LLSDA1
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	pushq	%rbx
	subq	$8, %rsp
	.cfi_offset 3, -24
.LEHB4:
	.loc 1 115 0
	call	M2RTS_ExecuteTerminationProcedures
	.loc 1 116 0
	call	_M2_Map_finish
	.loc 1 117 0
	call	_M2_WriteMap_finish
	.loc 1 118 0
	call	_M2_RoomMap_finish
	.loc 1 119 0
	call	_M2_Break_finish
	.loc 1 120 0
	call	_M2_BoxMap_finish
	.loc 1 121 0
	call	_M2_M2EXCEPTION_finish
	.loc 1 122 0
	call	_M2_SysExceptions_finish
	.loc 1 123 0
	call	_M2_MapOptions_finish
	.loc 1 124 0
	call	_M2_SysStorage_finish
	.loc 1 125 0
	call	_M2_MakeBoxes_finish
	.loc 1 126 0
	call	_M2_Geometry_finish
	.loc 1 127 0
	call	_M2_Assertion_finish
	.loc 1 128 0
	call	_M2_StoreCoords_finish
	.loc 1 129 0
	call	_M2_StrIO_finish
	.loc 1 130 0
	call	_M2_Debug_finish
	.loc 1 131 0
	call	_M2_Chance_finish
	.loc 1 132 0
	call	_M2_Args_finish
	.loc 1 133 0
	call	_M2_StdIO_finish
	.loc 1 134 0
	call	_M2_UnixArgs_finish
	.loc 1 135 0
	call	_M2_IO_finish
	.loc 1 136 0
	call	_M2_FIO_finish
	.loc 1 137 0
	call	_M2_termios_finish
	.loc 1 138 0
	call	_M2_errno_finish
	.loc 1 139 0
	call	_M2_Indexing_finish
	.loc 1 140 0
	call	_M2_ASCII_finish
	.loc 1 141 0
	call	_M2_StrLib_finish
	.loc 1 142 0
	call	_M2_NumberIO_finish
	.loc 1 143 0
	call	_M2_RTExceptions_finish
	.loc 1 144 0
	call	_M2_M2RTS_finish
	.loc 1 145 0
	call	_M2_SYSTEM_finish
	.loc 1 146 0
	call	_M2_Storage_finish
.LEHE4:
	.loc 1 147 0
	movl	$0, %edi
	call	exit
.L10:
	.loc 1 149 0
	movq	%rax, %rdi
	call	__cxa_begin_catch
.LEHB5:
	.loc 1 150 0
	call	RTExceptions_DefaultErrorCatch
.LEHE5:
.LEHB6:
	.loc 1 149 0
	call	__cxa_end_catch
.LEHE6:
	.loc 1 152 0
	jmp	.L12
.L11:
	movq	%rax, %rbx
	.loc 1 149 0
	call	__cxa_end_catch
	movq	%rbx, %rax
	movq	%rax, %rdi
.LEHB7:
	call	_Unwind_Resume
.LEHE7:
.L12:
	.loc 1 152 0
	addq	$8, %rsp
	popq	%rbx
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE1:
	.section	.gcc_except_table
	.align 4
.LLSDA1:
	.byte	0xff
	.byte	0x3
	.uleb128 .LLSDATT1-.LLSDATTD1
.LLSDATTD1:
	.byte	0x1
	.uleb128 .LLSDACSE1-.LLSDACSB1
.LLSDACSB1:
	.uleb128 .LEHB4-.LFB1
	.uleb128 .LEHE4-.LEHB4
	.uleb128 .L10-.LFB1
	.uleb128 0x1
	.uleb128 .LEHB5-.LFB1
	.uleb128 .LEHE5-.LEHB5
	.uleb128 .L11-.LFB1
	.uleb128 0
	.uleb128 .LEHB6-.LFB1
	.uleb128 .LEHE6-.LEHB6
	.uleb128 0
	.uleb128 0
	.uleb128 .LEHB7-.LFB1
	.uleb128 .LEHE7-.LEHB7
	.uleb128 0
	.uleb128 0
.LLSDACSE1:
	.byte	0x1
	.byte	0
	.align 4
	.long	0

.LLSDATT1:
	.text
	.size	_ZL6finishv, .-_ZL6finishv
	.globl	main
	.type	main, @function
main:
.LFB2:
	.loc 1 155 0
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	subq	$16, %rsp
	movl	%edi, -4(%rbp)
	movq	%rsi, -16(%rbp)
	.loc 1 156 0
	movq	-16(%rbp), %rdx
	movl	-4(%rbp), %eax
	movq	%rdx, %rsi
	movl	%eax, %edi
	call	_ZL4initiPPc
	.loc 1 157 0
	call	_ZL6finishv
	.loc 1 158 0
	movl	$0, %eax
	.loc 1 159 0
	leave
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE2:
	.size	main, .-main
.Letext0:
	.section	.debug_info,"",@progbits
.Ldebug_info0:
	.long	0xd1
	.value	0x4
	.long	.Ldebug_abbrev0
	.byte	0x8
	.uleb128 0x1
	.long	.LASF3
	.byte	0x4
	.long	.LASF4
	.long	.LASF5
	.quad	.Ltext0
	.quad	.Letext0-.Ltext0
	.long	.Ldebug_line0
	.uleb128 0x2
	.long	.LASF6
	.byte	0x1
	.byte	0x47
	.quad	.LFB0
	.quad	.LFE0-.LFB0
	.uleb128 0x1
	.byte	0x9c
	.long	0x67
	.uleb128 0x3
	.long	.LASF0
	.byte	0x1
	.byte	0x47
	.long	0x67
	.uleb128 0x2
	.byte	0x91
	.sleb128 -36
	.uleb128 0x3
	.long	.LASF1
	.byte	0x1
	.byte	0x47
	.long	0x6e
	.uleb128 0x2
	.byte	0x91
	.sleb128 -48
	.byte	0
	.uleb128 0x4
	.byte	0x4
	.byte	0x5
	.string	"int"
	.uleb128 0x5
	.byte	0x8
	.long	0x74
	.uleb128 0x5
	.byte	0x8
	.long	0x7a
	.uleb128 0x6
	.byte	0x1
	.byte	0x6
	.long	.LASF2
	.uleb128 0x7
	.long	.LASF7
	.byte	0x1
	.byte	0x70
	.quad	.LFB1
	.quad	.LFE1-.LFB1
	.uleb128 0x1
	.byte	0x9c
	.uleb128 0x8
	.long	.LASF8
	.byte	0x1
	.byte	0x9a
	.long	0x67
	.quad	.LFB2
	.quad	.LFE2-.LFB2
	.uleb128 0x1
	.byte	0x9c
	.uleb128 0x3
	.long	.LASF0
	.byte	0x1
	.byte	0x9a
	.long	0x67
	.uleb128 0x2
	.byte	0x91
	.sleb128 -20
	.uleb128 0x3
	.long	.LASF1
	.byte	0x1
	.byte	0x9a
	.long	0x6e
	.uleb128 0x2
	.byte	0x91
	.sleb128 -32
	.byte	0
	.byte	0
	.section	.debug_abbrev,"",@progbits
.Ldebug_abbrev0:
	.uleb128 0x1
	.uleb128 0x11
	.byte	0x1
	.uleb128 0x25
	.uleb128 0xe
	.uleb128 0x13
	.uleb128 0xb
	.uleb128 0x3
	.uleb128 0xe
	.uleb128 0x1b
	.uleb128 0xe
	.uleb128 0x11
	.uleb128 0x1
	.uleb128 0x12
	.uleb128 0x7
	.uleb128 0x10
	.uleb128 0x17
	.byte	0
	.byte	0
	.uleb128 0x2
	.uleb128 0x2e
	.byte	0x1
	.uleb128 0x3
	.uleb128 0xe
	.uleb128 0x3a
	.uleb128 0xb
	.uleb128 0x3b
	.uleb128 0xb
	.uleb128 0x11
	.uleb128 0x1
	.uleb128 0x12
	.uleb128 0x7
	.uleb128 0x40
	.uleb128 0x18
	.uleb128 0x2116
	.uleb128 0x19
	.uleb128 0x1
	.uleb128 0x13
	.byte	0
	.byte	0
	.uleb128 0x3
	.uleb128 0x5
	.byte	0
	.uleb128 0x3
	.uleb128 0xe
	.uleb128 0x3a
	.uleb128 0xb
	.uleb128 0x3b
	.uleb128 0xb
	.uleb128 0x49
	.uleb128 0x13
	.uleb128 0x2
	.uleb128 0x18
	.byte	0
	.byte	0
	.uleb128 0x4
	.uleb128 0x24
	.byte	0
	.uleb128 0xb
	.uleb128 0xb
	.uleb128 0x3e
	.uleb128 0xb
	.uleb128 0x3
	.uleb128 0x8
	.byte	0
	.byte	0
	.uleb128 0x5
	.uleb128 0xf
	.byte	0
	.uleb128 0xb
	.uleb128 0xb
	.uleb128 0x49
	.uleb128 0x13
	.byte	0
	.byte	0
	.uleb128 0x6
	.uleb128 0x24
	.byte	0
	.uleb128 0xb
	.uleb128 0xb
	.uleb128 0x3e
	.uleb128 0xb
	.uleb128 0x3
	.uleb128 0xe
	.byte	0
	.byte	0
	.uleb128 0x7
	.uleb128 0x2e
	.byte	0
	.uleb128 0x3
	.uleb128 0xe
	.uleb128 0x3a
	.uleb128 0xb
	.uleb128 0x3b
	.uleb128 0xb
	.uleb128 0x11
	.uleb128 0x1
	.uleb128 0x12
	.uleb128 0x7
	.uleb128 0x40
	.uleb128 0x18
	.uleb128 0x2116
	.uleb128 0x19
	.byte	0
	.byte	0
	.uleb128 0x8
	.uleb128 0x2e
	.byte	0x1
	.uleb128 0x3f
	.uleb128 0x19
	.uleb128 0x3
	.uleb128 0xe
	.uleb128 0x3a
	.uleb128 0xb
	.uleb128 0x3b
	.uleb128 0xb
	.uleb128 0x49
	.uleb128 0x13
	.uleb128 0x11
	.uleb128 0x1
	.uleb128 0x12
	.uleb128 0x7
	.uleb128 0x40
	.uleb128 0x18
	.uleb128 0x2116
	.uleb128 0x19
	.byte	0
	.byte	0
	.byte	0
	.section	.debug_aranges,"",@progbits
	.long	0x2c
	.value	0x2
	.long	.Ldebug_info0
	.byte	0x8
	.byte	0
	.value	0
	.value	0
	.quad	.Ltext0
	.quad	.Letext0-.Ltext0
	.quad	0
	.quad	0
	.section	.debug_line,"",@progbits
.Ldebug_line0:
	.section	.debug_str,"MS",@progbits,1
.LASF5:
	.string	"/home/gaius/Sandpit/chisel/random/map"
.LASF6:
	.string	"init"
.LASF0:
	.string	"argc"
.LASF4:
	.string	"Map_m2.cpp"
.LASF8:
	.string	"main"
.LASF3:
	.string	"GNU C++ 5.2.0 -mtune=generic -march=x86-64 -g"
.LASF7:
	.string	"finish"
.LASF2:
	.string	"char"
.LASF1:
	.string	"argv"
	.ident	"GCC: (GNU) 5.2.0"
	.section	.note.GNU-stack,"",@progbits
