; Native long conditional jumps, no toolchain macro dependency.
.macro jeq target
 bne :+
 jmp target
:
.endmacro
.macro jne target
 beq :+
 jmp target
:
.endmacro
.macro jcs target
 bcc :+
 jmp target
:
.endmacro
.macro jcc target
 bcs :+
 jmp target
:
.endmacro
.macro jmi target
 bpl :+
 jmp target
:
.endmacro
.macro jpl target
 bmi :+
 jmp target
:
.endmacro
