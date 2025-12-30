# ============================================
# LUAU_ENGINE.PY - MODULAR OBFUSCATOR ENGINE
# Untuk kemudahan development & testing
# ============================================

import random
import re
import hashlib
import time

class VariableGenerator:
    """Generate obfuscated variable names"""
    
    def __init__(self):
        self.counter = 0
        self.used = set()
    
    def generate(self, style="confuse"):
        """
        Styles:
        - confuse: lI1O0o_
        - underscore: ___
        - short: a-z
        - hex: _x1A2B
        """
        self.counter += 1
        
        if style == "confuse":
            chars = ['l', 'I', 'i', 'L', '1', 'O', 'o', '0', '_']
            prefix = random.choice(['_', 'l', 'I', 'O'])
            name = prefix + ''.join(random.choice(chars) for _ in range(6))
            
        elif style == "underscore":
            name = '_' * random.randint(2, 5) + str(self.counter)
            
        elif style == "short":
            name = chr(97 + (self.counter % 26)) + str(self.counter // 26 or '')
            
        elif style == "hex":
            name = f"_x{self.counter:04X}"
            
        else:
            name = f"_{self.counter}"
        
        full_name = f"{name}{self.counter}"
        self.used.add(full_name)
        return full_name
    
    def reset(self):
        self.counter = 0
        self.used.clear()


class StringEncoder:
    """Encode strings dengan berbagai method"""
    
    @staticmethod
    def to_bytes(s):
        """Convert string ke byte array"""
        return [ord(c) for c in s]
    
    @staticmethod
    def from_bytes(bytes_list):
        """Convert byte array ke string"""
        return ''.join(chr(b) for b in bytes_list)
    
    @staticmethod
    def xor_encode(s, key):
        """XOR encode string"""
        return [(ord(c) ^ key) % 256 for c in s]
    
    @staticmethod
    def xor_decode(bytes_list, key):
        """XOR decode bytes"""
        return ''.join(chr((b ^ key) % 256) for b in bytes_list)
    
    @staticmethod
    def caesar_encode(s, shift):
        """Caesar cipher encode"""
        return [(ord(c) + shift) % 256 for c in s]
    
    @staticmethod
    def reverse_encode(s):
        """Reverse string then to bytes"""
        return [ord(c) for c in s[::-1]]


class JunkGenerator:
    """Generate junk/dead code"""
    
    def __init__(self, var_gen):
        self.var_gen = var_gen
    
    def fake_variable(self):
        v = self.var_gen.generate()
        n = random.randint(1000, 99999)
        return f"local {v}={n};"
    
    def fake_table(self):
        v = self.var_gen.generate()
        nums = [str(random.randint(1, 999)) for _ in range(random.randint(2, 5))]
        return f"local {v}={{{','.join(nums)}}};"
    
    def fake_condition(self):
        v1 = self.var_gen.generate()
        v2 = self.var_gen.generate()
        n1 = random.randint(1, 100)
        n2 = random.randint(101, 200)
        return f"local {v1}={n1};local {v2}={n2};if {v1}>{v2} then {v1}={v2} end;"
    
    def fake_loop(self):
        v = self.var_gen.generate()
        i = self.var_gen.generate()
        return f"local {v}=0;for {i}=1,1 do {v}={v}+1 end;"
    
    def fake_function(self):
        f = self.var_gen.generate()
        p = self.var_gen.generate()
        return f"local function {f}({p})return {p} end;"
    
    def generate_batch(self, count=5):
        funcs = [
            self.fake_variable,
            self.fake_table,
            self.fake_condition,
            self.fake_loop,
            self.fake_function
        ]
        return '\n'.join(random.choice(funcs)() for _ in range(count))


class ControlFlowObfuscator:
    """Obfuscate control flow"""
    
    def __init__(self, var_gen):
        self.var_gen = var_gen
    
    def opaque_predicate(self):
        """Generate opaque predicate (always true/false condition)"""
        v1 = self.var_gen.generate()
        v2 = self.var_gen.generate()
        n = random.randint(1, 100)
        
        # Always true: n*n >= 0
        return f"local {v1}={n};local {v2}={v1}*{v1};if {v2}>=0 then"
    
    def fake_branch(self):
        """Generate fake branch"""
        v = self.var_gen.generate()
        n1 = random.randint(1, 50)
        n2 = random.randint(51, 100)
        
        return f"""local {v}={n1};
if {v}>{n2} then
{v}={n2}
else
{v}={v}
end;"""


class LuauCodeGenerator:
    """Generate Luau-compatible code"""
    
    def __init__(self):
        self.var_gen = VariableGenerator()
    
    def compat_header(self):
        """Compatibility layer"""
        unpack = self.var_gen.generate()
        loadstr = self.var_gen.generate()
        bitxor = self.var_gen.generate()
        
        code = f"""local {unpack}=table.unpack or unpack;
local {loadstr}=loadstring or load;
local {bitxor}=(bit32 and bit32.bxor)or(bit and bit.bxor)or function(a,b)
local r,p=0,1
for i=0,7 do
local a1,b1=a%2,b%2
if a1~=b1 then r=r+p end
a=math.floor(a/2)
b=math.floor(b/2)
p=p*2
end
return r
end;"""
        return code, {'unpack': unpack, 'loadstring': loadstr, 'bitxor': bitxor}
    
    def string_wrappers(self):
        """String function wrappers"""
        wrappers = {}
        code = []
        
        for name in ['byte', 'sub', 'char', 'gsub', 'rep', 'len', 'reverse']:
            v = self.var_gen.generate()
            wrappers[name] = v
            code.append(f"local {v}=string.{name};")
        
        return '\n'.join(code), wrappers
    
    def util_wrappers(self):
        """Utility function wrappers"""
        wrappers = {}
        code = []
        
        funcs = [
            'setmetatable', 'getmetatable', 'pcall', 'xpcall',
            'type', 'tostring', 'tonumber', 'assert', 'error',
            'select', 'next', 'pairs', 'ipairs', 'rawget', 'rawset'
        ]
        
        for name in funcs:
            v = self.var_gen.generate()
            wrappers[name] = v
            code.append(f"local {v}={name};")
        
        return '\n'.join(code), wrappers
    
    def byte_table(self, char_var):
        """Generate byte lookup table (0-255)"""
        tbl = self.var_gen.generate()
        idx = self.var_gen.generate()
        
        code = f"local {tbl}={{}};for {idx}=0,255 do {tbl}[{idx}]={char_var}({idx})end;"
        return code, tbl
    
    def bytecode_header(self):
        """Lua bytecode signature"""
        v = self.var_gen.generate()
        # 0x1B, 0x4C, 0x75, 0x61, 0x50 = \27LuaP
        code = f"local {v}={{0x1B,0x4C,0x75,0x61,0x50}};"
        return code, v
    
    def xor_decoder(self, bitxor_var, bytetbl_var):
        """XOR decoder function"""
        func = self.var_gen.generate()
        data = self.var_gen.generate()
        key = self.var_gen.generate()
        result = self.var_gen.generate()
        i = self.var_gen.generate()
        
        code = f"""local function {func}({data},{key})
local {result}=""
for {i}=1,#{data} do
{result}={result}..{bytetbl_var}[{bitxor_var}({data}[{i}],{key})]
end
return {result}
end;"""
        return code, func


class LuauObfuscatorEngine:
    """Main obfuscator engine"""
    
    def __init__(self):
        self.var_gen = VariableGenerator()
        self.code_gen = LuauCodeGenerator()
        self.junk_gen = JunkGenerator(self.var_gen)
        self.cf_obf = ControlFlowObfuscator(self.var_gen)
    
    def obfuscate(self, source, level=2):
        """
        Main obfuscation entry point
        
        Level 1: Basic encoding
        Level 2: + Wrappers + XOR
        Level 3: + Junk + Control flow
        """
        
        self.var_gen.reset()
        self.code_gen.var_gen = self.var_gen
        
        parts = []
        
        # Header
        ts = int(time.time())
        parts.append(f"--[[ Obf|{ts}|L{level} ]]")
        
        # Compatibility
        compat_code, compat = self.code_gen.compat_header()
        parts.append(compat_code)
        
        # String wrappers
        str_code, str_vars = self.code_gen.string_wrappers()
        parts.append(str_code)
        
        # Util wrappers
        util_code, util_vars = self.code_gen.util_wrappers()
        parts.append(util_code)
        
        # Byte table
        byte_code, byte_tbl = self.code_gen.byte_table(str_vars['char'])
        parts.append(byte_code)
        
        # Bytecode header
        header_code, header_var = self.code_gen.bytecode_header()
        parts.append(header_code)
        
        # XOR decoder
        xor_key = random.randint(1, 254)
        decoder_code, decoder = self.code_gen.xor_decoder(compat['bitxor'], byte_tbl)
        parts.append(decoder_code)
        
        if level >= 3:
            # Junk code
            parts.append(self.junk_gen.generate_batch(random.randint(3, 6)))
            
            # Control flow
            parts.append(self.cf_obf.fake_branch())
        
        # Encode payload
        encoded = StringEncoder.xor_encode(source, xor_key)
        payload_str = ','.join(map(str, encoded))
        
        payload_var = self.var_gen.generate()
        result_var = self.var_gen.generate()
        
        parts.append(f"local {payload_var}={{{payload_str}}};")
        parts.append(f"local {result_var}={decoder}({payload_var},{xor_key});")
        
        # Execute
        if level >= 2:
            fn = self.var_gen.generate()
            ok = self.var_gen.generate()
            parts.append(f"local {fn}={compat['loadstring']}({result_var});")
            parts.append(f"if {fn} then local {ok}={util_vars['pcall']}({fn})end;")
        else:
            parts.append(f"({compat['loadstring']}({result_var}))();")
        
        # Combine
        final = '\n'.join(parts)
        
        # Minify
        if level >= 2:
            final = self.minify(final)
        
        return final
    
    def minify(self, code):
        """Minify code"""
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('--') or l.strip().startswith('--[[')]
        code = ' '.join(lines)
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r'\s*([=,{}\(\)\[\];])\s*', r'\1', code)
        return code


# ============================================
# STANDALONE TEST
# ============================================

if __name__ == '__main__':
    engine = LuauObfuscatorEngine()
    
    test_code = 'print("Hello Roblox 2025!")'
    
    print("=" * 50)
    print("LUAU OBFUSCATOR ENGINE TEST")
    print("=" * 50)
    print(f"\nOriginal: {test_code}\n")
    
    for level in [1, 2, 3]:
        print(f"\n{'='*20} LEVEL {level} {'='*20}")
        result = engine.obfuscate(test_code, level)
        print(result)
        print(f"\nSize: {len(test_code)} -> {len(result)} ({len(result)/len(test_code):.1f}x)")
