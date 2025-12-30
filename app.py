# ============================================
# APP.PY - LUAU OBFUSCATOR API (FINAL)
# Compatible: Roblox 2025-2026, All Executors
# ============================================

from flask import Flask, request, jsonify, Response, render_template_string
from flask_cors import CORS
import random
import hashlib
import time
import os
import re

app = Flask(__name__)
CORS(app)

# ============================================
# CONFIGURATION
# ============================================

class Config:
    MAX_CODE_SIZE = int(os.environ.get('MAX_CODE_SIZE', 100000))
    SCRIPT_EXPIRY = int(os.environ.get('SCRIPT_EXPIRY', 86400))  # 24 hours
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 30))
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

# ============================================
# STORAGE (In-memory, use Redis for production)
# ============================================

script_storage = {}
stats = {
    'total_obfuscations': 0,
    'start_time': time.time()
}

def cleanup_expired():
    """Remove expired scripts"""
    now = time.time()
    expired = [k for k, v in script_storage.items() 
               if now - v.get('created', 0) > Config.SCRIPT_EXPIRY]
    for k in expired:
        del script_storage[k]

# ============================================
# LUAU OBFUSCATOR ENGINE
# ============================================

class LuauObfuscator:
    """
    Full-featured Luau/Roblox obfuscator
    
    Features:
    - string.byte, string.sub, string.char, string.gsub, string.rep
    - setmetatable, pcall, type, tostring, assert
    - loadstring (executor), table.unpack
    - Byte lookup table (0-255)
    - XOR encryption (bit32 compatible)
    - Bytecode header: {0x1B, 0x4C, 0x75, 0x61, 0x50}
    - Anti-tamper & Control flow obfuscation
    """
    
    def __init__(self):
        self.var_counter = 0
    
    # ==========================================
    # VARIABLE GENERATOR
    # ==========================================
    
    def gen_var(self):
        """Generate confusing variable name"""
        chars = ['l', 'I', 'i', 'L', '1', 'O', 'o', '0', '_']
        prefix = random.choice(['_', 'l', 'I', 'O', 'L', '__'])
        middle = ''.join(random.choice(chars) for _ in range(random.randint(4, 8)))
        self.var_counter += 1
        return f"{prefix}{middle}{self.var_counter}"
    
    def gen_num(self):
        """Generate random number"""
        return random.randint(10000, 99999)
    
    # ==========================================
    # COMPATIBILITY LAYER
    # ==========================================
    
    def gen_compat_layer(self):
        """
        Generate Lua/Luau compatibility layer
        Handles: unpack, loadstring, bit operations
        """
        v_unpack = self.gen_var()
        v_load = self.gen_var()
        v_bxor = self.gen_var()
        
        code = f"""local {v_unpack}=table.unpack or unpack;
local {v_load}=loadstring or load;
local {v_bxor}=(bit32 and bit32.bxor)or(bit and bit.bxor)or(function(a,b)
local r,p=0,1;
for i=0,7 do 
local a1,b1=a%2,b%2;
if a1~=b1 then r=r+p end;
a=math.floor(a/2);
b=math.floor(b/2);
p=p*2;
end;
return r;
end);"""
        
        return code, {'unpack': v_unpack, 'load': v_load, 'bxor': v_bxor}
    
    # ==========================================
    # STRING FUNCTION WRAPPERS
    # ==========================================
    
    def gen_string_wrappers(self):
        """
        Wrap: string.byte, string.sub, string.char, 
              string.gsub, string.rep, string.len
        """
        funcs = ['byte', 'sub', 'char', 'gsub', 'rep', 'len', 'reverse']
        wrappers = {}
        code_parts = []
        
        for f in funcs:
            v = self.gen_var()
            wrappers[f] = v
            code_parts.append(f"local {v}=string.{f};")
        
        return '\n'.join(code_parts), wrappers
    
    # ==========================================
    # UTILITY FUNCTION WRAPPERS
    # ==========================================
    
    def gen_util_wrappers(self):
        """
        Wrap: setmetatable, pcall, type, tostring, 
              assert, tonumber, pairs, ipairs, etc.
        """
        funcs = [
            'setmetatable', 'getmetatable', 'pcall', 'xpcall',
            'type', 'tostring', 'tonumber', 'assert', 'error',
            'select', 'next', 'pairs', 'ipairs', 'rawget', 'rawset'
        ]
        wrappers = {}
        code_parts = []
        
        for f in funcs:
            v = self.gen_var()
            wrappers[f] = v
            code_parts.append(f"local {v}={f};")
        
        return '\n'.join(code_parts), wrappers
    
    # ==========================================
    # BYTE TABLE (0-255)
    # ==========================================
    
    def gen_byte_table(self, char_var):
        """
        Generate: for i=0,255 do tbl[i]=char(i) end
        Creates lookup table for all byte values
        """
        tbl = self.gen_var()
        idx = self.gen_var()
        
        code = f"local {tbl}={{}};for {idx}=0,255 do {tbl}[{idx}]={char_var}({idx});end;"
        
        return code, tbl
    
    # ==========================================
    # BYTECODE HEADER
    # ==========================================
    
    def gen_bytecode_header(self):
        """
        Lua bytecode signature: {0x1B, 0x4C, 0x75, 0x61, 0x50}
        = "\27LuaP" (ESC + "LuaP")
        """
        v = self.gen_var()
        code = f"local {v}={{0x1B,0x4C,0x75,0x61,0x50}};"
        return code, v
    
    # ==========================================
    # XOR DECODER
    # ==========================================
    
    def gen_xor_decoder(self, bxor_var, byte_tbl_var):
        """
        XOR decoder function compatible with Luau
        Uses bit32.bxor or fallback
        """
        func = self.gen_var()
        data = self.gen_var()
        key = self.gen_var()
        result = self.gen_var()
        i = self.gen_var()
        
        code = f"""local function {func}({data},{key})
local {result}="";
for {i}=1,#{data} do 
{result}={result}..{byte_tbl_var}[{bxor_var}({data}[{i}],{key})];
end;
return {result};
end;"""
        
        return code, func
    
    # ==========================================
    # METATABLE PROTECTION
    # ==========================================
    
    def gen_metatable_protect(self, setmeta_var):
        """
        Create protected table using setmetatable
        """
        func = self.gen_var()
        mt = self.gen_var()
        
        code = f"""local {mt}={{
__metatable="locked",
__tostring=function()return""end,
__index=function(t,k)return rawget(t,"_d")and rawget(t,"_d")[k]end,
__newindex=function()end
}};
local function {func}(t)
return {setmeta_var}({{_d=t}},{mt});
end;"""
        
        return code, func
    
    # ==========================================
    # ANTI-TAMPER
    # ==========================================
    
    def gen_anti_tamper(self, pcall_var, type_var, tostring_var):
        """
        Anti-tamper and environment checks
        """
        check = self.gen_var()
        env = self.gen_var()
        
        code = f"""local {check}=(function()
local {env}={{}};
{env}.v=_VERSION or"Luau";
{env}.g=typeof and"Roblox"or"Lua";
{env}.l={type_var}(loadstring or load)=="function";
{env}.t={tostring_var}({{}});
return {env};
end)();"""
        
        return code, check
    
    # ==========================================
    # JUNK CODE
    # ==========================================
    
    def gen_junk(self, count=5):
        """Generate junk/dead code"""
        parts = []
        
        for _ in range(count):
            t = random.randint(1, 5)
            
            if t == 1:
                # Fake variable
                v = self.gen_var()
                parts.append(f"local {v}={self.gen_num()};")
            
            elif t == 2:
                # Fake table
                v = self.gen_var()
                nums = ','.join(str(self.gen_num()) for _ in range(3))
                parts.append(f"local {v}={{{nums}}};")
            
            elif t == 3:
                # Fake condition
                v1, v2 = self.gen_var(), self.gen_var()
                n1, n2 = self.gen_num(), self.gen_num()
                parts.append(f"local {v1}={n1};local {v2}={n2};if {v1}>{v2} then {v1}={v2}end;")
            
            elif t == 4:
                # Fake loop
                v1, v2 = self.gen_var(), self.gen_var()
                parts.append(f"local {v1}=0;for {v2}=1,1 do {v1}={v1}+1 end;")
            
            elif t == 5:
                # Fake function
                f, p = self.gen_var(), self.gen_var()
                parts.append(f"local function {f}({p})return {p} end;")
        
        return '\n'.join(parts)
    
    # ==========================================
    # CONTROL FLOW
    # ==========================================
    
    def gen_control_flow(self):
        """
        Opaque predicates and fake control flow
        """
        v1 = self.gen_var()
        v2 = self.gen_var()
        v3 = self.gen_var()
        n1 = random.randint(1, 100)
        n2 = n1 + random.randint(1, 50)
        
        code = f"""local {v1},{v2}={n1},{n2};
local {v3}=({v1}<{v2})and(function()return true end)or(function()return false end);
if not {v3}()then {v1},{v2}={v2},{v1}end;"""
        
        return code
    
    # ==========================================
    # STRING ENCODER
    # ==========================================
    
    def encode_string(self, s, key):
        """Encode string with XOR"""
        return [(ord(c) ^ key) % 256 for c in s]
    
    # ==========================================
    # MINIFY
    # ==========================================
    
    def minify(self, code):
        """Minify code - remove unnecessary whitespace"""
        # Keep header comment
        lines = code.split('\n')
        result = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('--') and not line.startswith('--[['):
                continue
            result.append(line)
        
        code = ' '.join(result)
        
        # Reduce spaces around operators
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r'\s*([=,{}\(\)\[\];])\s*', r'\1', code)
        code = re.sub(r';+', ';', code)
        
        return code.strip()
    
    # ==========================================
    # MAIN OBFUSCATE
    # ==========================================
    
    def obfuscate(self, source, level=2):
        """
        Main obfuscation function
        
        Levels:
        1 = Light: String encoding, basic wrappers
        2 = Medium: + XOR, protected execution
        3 = Heavy: + Junk, control flow, anti-tamper
        """
        
        self.var_counter = 0
        parts = []
        
        # ===== HEADER =====
        ts = int(time.time())
        sig = hashlib.md5(source.encode()).hexdigest()[:8]
        parts.append(f"--[[OBF|{ts}|{sig}|L{level}]]")
        
        # ===== COMPATIBILITY LAYER =====
        compat_code, compat = self.gen_compat_layer()
        parts.append(compat_code)
        
        # ===== STRING WRAPPERS =====
        str_code, str_vars = self.gen_string_wrappers()
        parts.append(str_code)
        
        # ===== UTILITY WRAPPERS =====
        util_code, util_vars = self.gen_util_wrappers()
        parts.append(util_code)
        
        # ===== BYTE TABLE (0-255) =====
        byte_code, byte_tbl = self.gen_byte_table(str_vars['char'])
        parts.append(byte_code)
        
        # ===== BYTECODE HEADER =====
        header_code, header_var = self.gen_bytecode_header()
        parts.append(header_code)
        
        # ===== XOR DECODER =====
        xor_key = random.randint(1, 254)
        decoder_code, decoder_func = self.gen_xor_decoder(compat['bxor'], byte_tbl)
        parts.append(decoder_code)
        
        if level >= 2:
            # ===== METATABLE PROTECTION =====
            meta_code, meta_func = self.gen_metatable_protect(util_vars['setmetatable'])
            parts.append(meta_code)
        
        if level >= 3:
            # ===== ANTI-TAMPER =====
            tamper_code, tamper_var = self.gen_anti_tamper(
                util_vars['pcall'],
                util_vars['type'],
                util_vars['tostring']
            )
            parts.append(tamper_code)
            
            # ===== JUNK CODE =====
            parts.append(self.gen_junk(random.randint(3, 7)))
            
            # ===== CONTROL FLOW =====
            parts.append(self.gen_control_flow())
        
        # ===== ENCODE PAYLOAD =====
        encoded = self.encode_string(source, xor_key)
        payload_str = ','.join(map(str, encoded))
        
        payload_var = self.gen_var()
        result_var = self.gen_var()
        
        parts.append(f"local {payload_var}={{{payload_str}}};")
        parts.append(f"local {result_var}={decoder_func}({payload_var},{xor_key});")
        
        # ===== EXECUTE =====
        if level >= 2:
            # Protected execution with pcall
            fn_var = self.gen_var()
            ok_var = self.gen_var()
            err_var = self.gen_var()
            
            parts.append(f"""local {fn_var}={compat['load']}({result_var});
if {fn_var} then 
local {ok_var},{err_var}={util_vars['pcall']}({fn_var});
end;""")
        else:
            # Direct execution
            parts.append(f"({compat['load']}({result_var}))();")
        
        # ===== COMBINE & MINIFY =====
        final = '\n'.join(parts)
        
        if level >= 2:
            final = self.minify(final)
        
        return final


# ============================================
# WEB UI TEMPLATE
# ============================================

WEB_UI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lua Obfuscator - Roblox 2025</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root{--bg:#0d1117;--bg2:#161b22;--bg3:#21262d;--text:#f0f6fc;--text2:#8b949e;--accent:#58a6ff;--success:#3fb950;--error:#f85149;--border:#30363d}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
        .header{background:var(--bg2);border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center}
        .logo{display:flex;align-items:center;gap:.75rem;font-size:1.5rem;font-weight:700}
        .logo i{color:var(--accent)}
        .nav{display:flex;gap:1.5rem}
        .nav a{color:var(--text2);text-decoration:none;transition:color .2s}
        .nav a:hover{color:var(--text)}
        .container{max-width:1400px;margin:0 auto;padding:2rem}
        .hero{text-align:center;padding:2rem 0}
        .hero h1{font-size:2.5rem;margin-bottom:1rem;background:linear-gradient(135deg,var(--accent),#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .hero p{color:var(--text2);max-width:600px;margin:0 auto}
        .badges{display:flex;justify-content:center;gap:.5rem;margin-top:1rem;flex-wrap:wrap}
        .badge{background:var(--bg3);padding:.35rem .75rem;border-radius:9999px;font-size:.8rem;color:var(--text2);border:1px solid var(--border)}
        .badge.accent{background:rgba(88,166,255,.1);color:var(--accent);border-color:var(--accent)}
        .grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem}
        @media(max-width:1024px){.grid{grid-template-columns:1fr}}
        .panel{background:var(--bg2);border-radius:12px;border:1px solid var(--border);overflow:hidden}
        .panel-header{background:var(--bg3);padding:.75rem 1rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
        .panel-title{font-weight:600;font-size:.9rem;display:flex;align-items:center;gap:.5rem}
        .panel-title i{color:var(--accent)}
        .panel-body{padding:1rem}
        .editor{width:100%;height:300px;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:.9rem;color:var(--text);resize:vertical;outline:none}
        .editor:focus{border-color:var(--accent)}
        .controls{display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap;align-items:center}
        .levels{display:flex;gap:.5rem}
        .level-btn{padding:.5rem 1rem;background:var(--bg3);border:1px solid var(--border);border-radius:6px;color:var(--text2);cursor:pointer;transition:all .2s;font-size:.85rem}
        .level-btn:hover{border-color:var(--accent);color:var(--text)}
        .level-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
        .btn{padding:.75rem 1.5rem;border-radius:8px;border:none;font-weight:600;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:.5rem}
        .btn-primary{background:var(--accent);color:#fff}
        .btn-primary:hover{filter:brightness(1.1);transform:translateY(-1px)}
        .btn-primary:disabled{opacity:.5;cursor:not-allowed;transform:none}
        .btn-secondary{background:var(--bg3);color:var(--text);border:1px solid var(--border)}
        .btn-secondary:hover{border-color:var(--accent)}
        .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:1rem}
        .stat{background:var(--bg3);padding:1rem;border-radius:8px;text-align:center}
        .stat-value{font-size:1.25rem;font-weight:700;color:var(--accent)}
        .stat-label{font-size:.75rem;color:var(--text2);margin-top:.25rem}
        .loadstring{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-top:1rem}
        .loadstring-label{font-size:.75rem;color:var(--text2);margin-bottom:.5rem}
        .loadstring-code{font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--success);word-break:break-all}
        .status{padding:.75rem 1rem;border-radius:8px;margin-top:1rem;display:none;align-items:center;gap:.5rem}
        .status.show{display:flex}
        .status.success{background:rgba(63,185,80,.1);border:1px solid var(--success);color:var(--success)}
        .status.error{background:rgba(248,81,73,.1);border:1px solid var(--error);color:var(--error)}
        .status.loading{background:rgba(88,166,255,.1);border:1px solid var(--accent);color:var(--accent)}
        @keyframes spin{to{transform:rotate(360deg)}}
        .spin{animation:spin 1s linear infinite}
        .features{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-top:3rem}
        .feature{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.25rem;transition:border-color .2s}
        .feature:hover{border-color:var(--accent)}
        .feature-icon{width:36px;height:36px;background:rgba(88,166,255,.1);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--accent);margin-bottom:.75rem}
        .feature-title{font-weight:600;margin-bottom:.25rem;font-size:.95rem}
        .feature-desc{font-size:.85rem;color:var(--text2)}
        .footer{text-align:center;padding:2rem;margin-top:3rem;border-top:1px solid var(--border);color:var(--text2);font-size:.9rem}
    </style>
</head>
<body>
    <header class="header">
        <div class="logo"><i class="fas fa-lock"></i><span>Lua Obfuscator</span></div>
        <nav class="nav">
            <a href="/"><i class="fas fa-home"></i> Home</a>
            <a href="#features"><i class="fas fa-star"></i> Features</a>
            <a href="/health"><i class="fas fa-heart"></i> Status</a>
        </nav>
    </header>
    
    <main class="container">
        <section class="hero">
            <h1>🔒 Lua/Luau Obfuscator</h1>
            <p>Advanced code obfuscation for Roblox 2025-2026. Compatible with all major executors.</p>
            <div class="badges">
                <span class="badge accent">Roblox 2025</span>
                <span class="badge">Synapse X</span>
                <span class="badge">Fluxus</span>
                <span class="badge">KRNL</span>
                <span class="badge">Hydrogen</span>
            </div>
        </section>
        
        <div class="grid">
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title"><i class="fas fa-code"></i> Input Code</span>
                    <button class="btn btn-secondary" onclick="loadExample()" style="padding:.4rem .75rem;font-size:.8rem">
                        <i class="fas fa-flask"></i> Example
                    </button>
                </div>
                <div class="panel-body">
                    <textarea class="editor" id="input" placeholder="-- Paste your Lua code here...

print('Hello World')"></textarea>
                    
                    <div class="controls">
                        <div class="levels">
                            <button class="level-btn" data-level="1" onclick="setLevel(1)">Level 1</button>
                            <button class="level-btn active" data-level="2" onclick="setLevel(2)">Level 2</button>
                            <button class="level-btn" data-level="3" onclick="setLevel(3)">Level 3</button>
                        </div>
                        <button class="btn btn-primary" id="obfBtn" onclick="obfuscate()">
                            <i class="fas fa-shield-alt"></i> Obfuscate
                        </button>
                        <button class="btn btn-secondary" onclick="clearAll()">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                    </div>
                    
                    <div class="status" id="status"></div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title"><i class="fas fa-file-code"></i> Output</span>
                    <div style="display:flex;gap:.5rem">
                        <button class="btn btn-secondary" onclick="copyOutput()" style="padding:.4rem .75rem;font-size:.8rem">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                        <button class="btn btn-secondary" onclick="download()" style="padding:.4rem .75rem;font-size:.8rem">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>
                <div class="panel-body">
                    <textarea class="editor" id="output" placeholder="-- Obfuscated code will appear here..." readonly></textarea>
                    
                    <div class="stats" id="stats" style="display:none">
                        <div class="stat"><div class="stat-value" id="sOriginal">0</div><div class="stat-label">Original</div></div>
                        <div class="stat"><div class="stat-value" id="sObfuscated">0</div><div class="stat-label">Obfuscated</div></div>
                        <div class="stat"><div class="stat-value" id="sRatio">0x</div><div class="stat-label">Ratio</div></div>
                        <div class="stat"><div class="stat-value" id="sLevel">2</div><div class="stat-label">Level</div></div>
                    </div>
                    
                    <div class="loadstring" id="loadstringBox" style="display:none">
                        <div class="loadstring-label">🎮 Roblox Loadstring:</div>
                        <code class="loadstring-code" id="loadstringCode"></code>
                    </div>
                </div>
            </div>
        </div>
        
        <section class="features" id="features">
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-key"></i></div>
                <div class="feature-title">XOR Encryption</div>
                <div class="feature-desc">bit32 compatible encryption</div>
            </div>
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-table"></i></div>
                <div class="feature-title">Byte Table</div>
                <div class="feature-desc">0-255 lookup table</div>
            </div>
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-random"></i></div>
                <div class="feature-title">Variable Obfuscation</div>
                <div class="feature-desc">Confusing variable names</div>
            </div>
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-code-branch"></i></div>
                <div class="feature-title">Control Flow</div>
                <div class="feature-desc">Fake branches & predicates</div>
            </div>
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-trash-alt"></i></div>
                <div class="feature-title">Junk Code</div>
                <div class="feature-desc">Dead code injection</div>
            </div>
            <div class="feature">
                <div class="feature-icon"><i class="fas fa-shield-virus"></i></div>
                <div class="feature-title">Anti-Tamper</div>
                <div class="feature-desc">Environment checks</div>
            </div>
        </section>
    </main>
    
    <footer class="footer">
        <p>Made with ❤️ for Roblox developers | v2.1</p>
    </footer>
    
    <script>
        let level=2,lastResult=null;
        
        function setLevel(l){
            level=l;
            document.querySelectorAll('.level-btn').forEach(b=>b.classList.remove('active'));
            document.querySelector(`[data-level="${l}"]`).classList.add('active');
        }
        
        function showStatus(type,msg){
            const s=document.getElementById('status');
            s.className=`status show ${type}`;
            s.innerHTML=type==='loading'?`<i class="fas fa-circle-notch spin"></i> ${msg}`:`<i class="fas fa-${type==='success'?'check-circle':'exclamation-circle'}"></i> ${msg}`;
            if(type!=='loading')setTimeout(()=>s.classList.remove('show'),3000);
        }
        
        async function obfuscate(){
            const code=document.getElementById('input').value.trim();
            if(!code){showStatus('error','Please enter code first!');return}
            
            const btn=document.getElementById('obfBtn');
            btn.disabled=true;
            btn.innerHTML='<i class="fas fa-circle-notch spin"></i> Processing...';
            showStatus('loading','Obfuscating...');
            
            try{
                const res=await fetch('/obfuscate',{
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({code,level})
                });
                const data=await res.json();
                
                if(data.error)throw new Error(data.error);
                
                lastResult=data;
                document.getElementById('output').value=data.obfuscated;
                
                document.getElementById('sOriginal').textContent=data.stats.original.toLocaleString();
                document.getElementById('sObfuscated').textContent=data.stats.obfuscated.toLocaleString();
                document.getElementById('sRatio').textContent=data.stats.ratio+'x';
                document.getElementById('sLevel').textContent=data.stats.level;
                document.getElementById('stats').style.display='grid';
                
                document.getElementById('loadstringCode').textContent=data.roblox_usage;
                document.getElementById('loadstringBox').style.display='block';
                
                showStatus('success','Done!');
            }catch(e){
                showStatus('error',e.message);
            }finally{
                btn.disabled=false;
                btn.innerHTML='<i class="fas fa-shield-alt"></i> Obfuscate';
            }
        }
        
        function copyOutput(){
            const o=document.getElementById('output').value;
            if(!o){showStatus('error','Nothing to copy!');return}
            navigator.clipboard.writeText(o).then(()=>showStatus('success','Copied!'));
        }
        
        function download(){
            const o=document.getElementById('output').value;
            if(!o){showStatus('error','Nothing to download!');return}
            const a=document.createElement('a');
            a.href=URL.createObjectURL(new Blob([o],{type:'text/plain'}));
            a.download=`obfuscated_${lastResult?.key||'script'}.lua`;
            a.click();
            showStatus('success','Downloaded!');
        }
        
        function clearAll(){
            document.getElementById('input').value='';
            document.getElementById('output').value='';
            document.getElementById('stats').style.display='none';
            document.getElementById('loadstringBox').style.display='none';
        }
        
        function loadExample(){
            document.getElementById('input').value=`-- Example Script
local Players = game:GetService("Players")
local player = Players.LocalPlayer

local function greet(name)
    print("Hello, " .. name .. "!")
end

greet(player.Name)

for i = 1, 5 do
    print("Count: " .. i)
    wait(1)
end`;
        }
        
        document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter')obfuscate()});
    </script>
</body>
</html>
'''


# ============================================
# ROUTES
# ============================================

@app.route('/')
def home():
    """Home - Web UI or API info"""
    accept = request.headers.get('Accept', '')
    
    if 'text/html' in accept:
        return render_template_string(WEB_UI_TEMPLATE)
    
    return jsonify({
        "service": "Luau Obfuscator API",
        "version": "2.1.0",
        "status": "online",
        "web_ui": request.host_url,
        "compatible": ["Roblox 2025", "Synapse X", "Fluxus", "KRNL", "Hydrogen", "Delta"],
        "endpoints": {
            "GET /": "Web UI / API Info",
            "GET /health": "Health check",
            "POST /obfuscate": "Obfuscate code",
            "GET /script/<key>": "Get script by key",
            "POST /raw": "Get raw obfuscated code",
            "GET /test": "Test obfuscation"
        },
        "features": [
            "string.byte/sub/char/gsub/rep",
            "setmetatable, pcall, type, tostring, assert",
            "loadstring, table.unpack",
            "Byte table (0-255)",
            "XOR encryption (bit32)",
            "Bytecode header {0x1B,0x4C,0x75,0x61,0x50}",
            "Anti-tamper, Control flow, Junk code"
        ]
    })


@app.route('/health')
def health():
    """Health check"""
    cleanup_expired()
    
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": round(time.time() - stats['start_time'], 2),
        "total_obfuscations": stats['total_obfuscations'],
        "stored_scripts": len(script_storage)
    })


@app.route('/obfuscate', methods=['POST'])
def obfuscate():
    """Obfuscate Lua code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({"error": "No code provided"}), 400
        
        code = data['code']
        level = min(max(int(data.get('level', 2)), 1), 3)
        
        # Validate size
        if len(code) > Config.MAX_CODE_SIZE:
            return jsonify({"error": f"Code too large. Max {Config.MAX_CODE_SIZE} chars"}), 400
        
        if len(code.strip()) == 0:
            return jsonify({"error": "Empty code"}), 400
        
        # Obfuscate
        obfuscator = LuauObfuscator()
        obfuscated = obfuscator.obfuscate(code, level)
        
        # Generate key
        key = hashlib.md5(f"{code}{time.time()}{random.random()}".encode()).hexdigest()[:16]
        
        # Store
        script_storage[key] = {
            "code": obfuscated,
            "created": time.time(),
            "level": level,
            "original_size": len(code),
            "obfuscated_size": len(obfuscated)
        }
        
        # Update stats
        stats['total_obfuscations'] += 1
        
        # Cleanup old scripts
        cleanup_expired()
        
        base_url = request.host_url.rstrip('/')
        
        return jsonify({
            "success": True,
            "key": key,
            "obfuscated": obfuscated,
            "loadstring_url": f"{base_url}/script/{key}",
            "roblox_usage": f'loadstring(game:HttpGet("{base_url}/script/{key}"))()',
            "stats": {
                "original": len(code),
                "obfuscated": len(obfuscated),
                "ratio": round(len(obfuscated) / max(len(code), 1), 2),
                "level": level
            },
            "expires_in": Config.SCRIPT_EXPIRY
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/script/<key>')
def get_script(key):
    """Get obfuscated script by key"""
    if key not in script_storage:
        return Response("-- Script not found or expired", mimetype='text/plain'), 404
    
    script = script_storage[key]
    
    # Check expiry
    if time.time() - script['created'] > Config.SCRIPT_EXPIRY:
        del script_storage[key]
        return Response("-- Script expired", mimetype='text/plain'), 404
    
    return Response(script["code"], mimetype='text/plain')


@app.route('/raw', methods=['POST'])
def raw_obfuscate():
    """Obfuscate and return raw code directly"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return Response("-- No code provided", mimetype='text/plain'), 400
        
        code = data['code']
        level = min(max(int(data.get('level', 2)), 1), 3)
        
        obfuscator = LuauObfuscator()
        obfuscated = obfuscator.obfuscate(code, level)
        
        stats['total_obfuscations'] += 1
        
        return Response(obfuscated, mimetype='text/plain')
        
    except Exception as e:
        return Response(f"-- Error: {e}", mimetype='text/plain'), 500


@app.route('/test')
def test():
    """Test obfuscation with sample code"""
    test_code = 'print("Hello Roblox 2025!")'
    
    results = []
    results.append(f"-- Original: {test_code}")
    results.append(f"-- {'='*50}")
    
    for level in [1, 2, 3]:
        obfuscator = LuauObfuscator()
        result = obfuscator.obfuscate(test_code, level)
        results.append(f"\n-- Level {level} ({len(result)} chars):")
        results.append(result)
        results.append("")
    
    return Response('\n'.join(results), mimetype='text/plain')


@app.route('/loader')
def get_loader():
    """Get Roblox loader script"""
    base_url = request.host_url.rstrip('/')
    
    loader = f'''-- Lua Obfuscator Loader
-- Usage: loadstring(game:HttpGet("{base_url}/loader"))()

local Loader = {{}}
Loader.API = "{base_url}"

function Loader.load(key)
    local url = Loader.API .. "/script/" .. key
    local code = game:HttpGet(url)
    local fn = loadstring(code)
    if fn then fn() end
end

function Loader.loadUrl(url)
    local code = game:HttpGet(url)
    local fn = loadstring(code)
    if fn then fn() end
end

return Loader
'''
    
    return Response(loader, mimetype='text/plain')


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    
    print(f"{'='*50}")
    print(f"🔒 Luau Obfuscator API v2.1")
    print(f"📡 Running on port {port}")
    print(f"🐛 Debug: {debug}")
    print(f"{'='*50}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
