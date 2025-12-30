# ============================================
# OBFUSCATOR PACKAGE
# ============================================

"""
Luau Obfuscator Package
Compatible with Roblox 2025-2026

Features:
- string.byte, string.sub, string.char, string.gsub, string.rep
- setmetatable, pcall, type, tostring, assert
- loadstring, table.unpack
- Byte lookup table (0-255)
- XOR encryption (bit32 compatible)
- Bytecode header {0x1B, 0x4C, 0x75, 0x61, 0x50}
- Anti-tamper & Control flow obfuscation
"""

__version__ = "2.1.0"
__author__ = "Lua Obfuscator"

from .luau_engine import (
    LuauObfuscatorEngine,
    VariableGenerator,
    StringEncoder,
    JunkGenerator,
    ControlFlowObfuscator,
    LuauCodeGenerator
)

__all__ = [
    'LuauObfuscatorEngine',
    'VariableGenerator',
    'StringEncoder',
    'JunkGenerator',
    'ControlFlowObfuscator',
    'LuauCodeGenerator'
]


def obfuscate(code: str, level: int = 2) -> str:
    """
    Quick obfuscate function
    
    Args:
        code: Lua source code
        level: Obfuscation level (1-3)
    
    Returns:
        Obfuscated code
    """
    engine = LuauObfuscatorEngine()
    return engine.obfuscate(code, level)


def create_obfuscator():
    """Create new obfuscator instance"""
    return LuauObfuscatorEngine()
