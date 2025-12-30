# ============================================
# APP.PY - LUAU OBFUSCATOR API
# Fixed Port Binding untuk Render.com
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
    SCRIPT_EXPIRY = int(os.environ.get('SCRIPT_EXPIRY', 86400))
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

# ============================================
# STORAGE
# ============================================

script_storage = {}
stats = {
    'total_obfuscations': 0,
    'start_time': time.time()
}

def cleanup_expired():
    now = time.time()
    expired = [k for k, v in script_storage.items() 
               if now - v.get('created', 0) > Config.SCRIPT_EXPIRY]
    for k in expired:
        del script_storage[k]

# ============================================
# OBFUSCATOR ENGINE
# ============================================

class LuauObfuscator:
    def __init__(self):
        self.var_counter = 0
    
    def gen_var(self):
        chars = ['l', 'I', 'i', 'L', '1', 'O', 'o', '0', '_']
        prefix = random.choice(['_', 'l', 'I', 'O', 'L', '__'])
        middle = ''.join(random.choice(chars) for _ in range(random.randint(4, 8)))
        self.var_counter += 1
        return f"{prefix}{middle}{self.var_counter}"
    
    def gen_num(self):
        return random.randint(10000, 99999)
    
    def gen_compat_layer(self):
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
    
    def gen_string_wrappers(self):
        funcs = ['byte', 'sub', 'char', 'gsub', 'rep', 'len', 'reverse']
        wrappers = {}
        code_parts = []
        
        for f in funcs:
            v = self.gen_var()
            wrappers[f] = v
            code_parts.append(f"local {v}=string.{f};")
        
        return '\n'.join(code_parts), wrappers
    
    def gen_util_wrappers(self):
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
    
    def gen_byte_table(self, char_var):
        tbl = self.gen_var()
        idx = self.gen_var()
        code = f"local {tbl}={{}};for {idx}=0,255 do {tbl}[{idx}]={char_var}({idx});end;"
        return code, tbl
    
    def gen_bytecode_header(self):
        v = self.gen_var()
        code = f"local {v}={{0x1B,0x4C,0x75,0x61,0x50}};"
        return code, v
    
    def gen_xor_decoder(self, bxor_var, byte_tbl_var):
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
    
    def gen_junk(self, count=5):
        parts = []
        for _ in range(count):
            t = random.randint(1, 4)
            if t == 1:
                v = self.gen_var()
                parts.append(f"local {v}={self.gen_num()};")
            elif t == 2:
                v = self.gen_var()
                nums = ','.join(str(self.gen_num()) for _ in range(3))
                parts.append(f"local {v}={{{nums}}};")
            elif t == 3:
                v1, v2 = self.gen_var(), self.gen_var()
                parts.append(f"local {v1}={self.gen_num()};local {v2}={self.gen_num()};")
            else:
                f, p = self.gen_var(), self.gen_var()
                parts.append(f"local function {f}({p})return {p} end;")
        return '\n'.join(parts)
    
    def encode_string(self, s, key):
        return [(ord(c) ^ key) % 256 for c in s]
    
    def minify(self, code):
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
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r'\s*([=,{}\(\)\[\];])\s*', r'\1', code)
        code = re.sub(r';+', ';', code)
        return code.strip()
    
    def obfuscate(self, source, level=2):
        self.var_counter = 0
        parts = []
        
        ts = int(time.time())
        sig = hashlib.md5(source.encode()).hexdigest()[:8]
        parts.append(f"--[[OBF|{ts}|{sig}|L{level}]]")
        
        compat_code, compat = self.gen_compat_layer()
        parts.append(compat_code)
        
        str_code, str_vars = self.gen_string_wrappers()
        parts.append(str_code)
        
        util_code, util_vars = self.gen_util_wrappers()
        parts.append(util_code)
        
        byte_code, byte_tbl = self.gen_byte_table(str_vars['char'])
        parts.append(byte_code)
        
        header_code, header_var = self.gen_bytecode_header()
        parts.append(header_code)
        
        xor_key = random.randint(1, 254)
        decoder_code, decoder_func = self.gen_xor_decoder(compat['bxor'], byte_tbl)
        parts.append(decoder_code)
        
        if level >= 3:
            parts.append(self.gen_junk(random.randint(3, 7)))
        
        encoded = self.encode_string(source, xor_key)
        payload_str = ','.join(map(str, encoded))
        
        payload_var = self.gen_var()
        result_var = self.gen_var()
        
        parts.append(f"local {payload_var}={{{payload_str}}};")
        parts.append(f"local {result_var}={decoder_func}({payload_var},{xor_key});")
        
        if level >= 2:
            fn_var = self.gen_var()
            ok_var = self.gen_var()
            parts.append(f"local {fn_var}={compat['load']}({result_var});if {fn_var} then local {ok_var}={util_vars['pcall']}({fn_var});end;")
        else:
            parts.append(f"({compat['load']}({result_var}))();")
        
        final = '\n'.join(parts)
        if level >= 2:
            final = self.minify(final)
        
        return final

# ============================================
# WEB UI
# ============================================

WEB_UI = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lua Obfuscator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#f0f6fc;min-height:100vh;padding:20px}
.container{max-width:1200px;margin:0 auto}
h1{text-align:center;margin-bottom:20px;color:#58a6ff}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.panel{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:15px}
.panel h3{margin-bottom:10px;color:#58a6ff}
textarea{width:100%;height:250px;background:#0d1117;border:1px solid #30363d;border-radius:5px;padding:10px;color:#f0f6fc;font-family:monospace;resize:vertical}
.controls{margin-top:10px;display:flex;gap:10px;flex-wrap:wrap}
button{padding:10px 20px;border:none;border-radius:5px;cursor:pointer;font-weight:bold}
.btn-primary{background:#58a6ff;color:#fff}
.btn-primary:hover{background:#79b8ff}
.btn-secondary{background:#30363d;color:#f0f6fc}
.levels{display:flex;gap:5px}
.level-btn{padding:8px 15px;background:#30363d;border:1px solid #484f58;border-radius:5px;color:#8b949e;cursor:pointer}
.level-btn.active{background:#58a6ff;color:#fff;border-color:#58a6ff}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:15px}
.stat{background:#21262d;padding:10px;border-radius:5px;text-align:center}
.stat-value{font-size:1.2em;color:#58a6ff;font-weight:bold}
.stat-label{font-size:0.8em;color:#8b949e}
.loadstring{background:#0d1117;border:1px solid #30363d;border-radius:5px;padding:10px;margin-top:15px;font-family:monospace;font-size:0.85em;color:#3fb950;word-break:break-all}
.status{padding:10px;border-radius:5px;margin-top:10px;display:none}
.status.show{display:block}
.status.success{background:rgba(63,185,80,0.1);border:1px solid #3fb950;color:#3fb950}
.status.error{background:rgba(248,81,73,0.1);border:1px solid #f85149;color:#f85149}
</style></head>
<body>
<div class="container">
<h1>🔒 Lua Obfuscator</h1>
<p style="text-align:center;color:#8b949e;margin-bottom:20px">Roblox 2025 Compatible</p>
<div class="grid">
<div class="panel">
<h3>📝 Input</h3>
<textarea id="input" placeholder="-- Paste Lua code here..."></textarea>
<div class="controls">
<div class="levels">
<button class="level-btn" onclick="setLevel(1)">L1</button>
<button class="level-btn active" onclick="setLevel(2)">L2</button>
<button class="level-btn" onclick="setLevel(3)">L3</button>
</div>
<button class="btn-primary" onclick="obfuscate()">🔒 Obfuscate</button>
<button class="btn-secondary" onclick="document.getElementById('input').value=''">Clear</button>
</div>
<div class="status" id="status"></div>
</div>
<div class="panel">
<h3>📤 Output</h3>
<textarea id="output" readonly placeholder="-- Obfuscated code..."></textarea>
<div class="controls">
<button class="btn-secondary" onclick="copy()">📋 Copy</button>
<button class="btn-secondary" onclick="download()">💾 Download</button>
</div>
<div class="stats" id="stats" style="display:none">
<div class="stat"><div class="stat-value" id="s1">0</div><div class="stat-label">Original</div></div>
<div class="stat"><div class="stat-value" id="s2">0</div><div class="stat-label">Obfuscated</div></div>
<div class="stat"><div class="stat-value" id="s3">0x</div><div class="stat-label">Ratio</div></div>
<div class="stat"><div class="stat-value" id="s4">2</div><div class="stat-label">Level</div></div>
</div>
<div class="loadstring" id="ls" style="display:none"></div>
</div>
</div>
</div>
<script>
let level=2,result=null;
function setLevel(l){level=l;document.querySelectorAll('.level-btn').forEach((b,i)=>b.classList.toggle('active',i+1===l))}
function showStatus(t,m){const s=document.getElementById('status');s.className='status show '+t;s.textContent=m;if(t!=='loading')setTimeout(()=>s.classList.remove('show'),3000)}
async function obfuscate(){
const code=document.getElementById('input').value;
if(!code){showStatus('error','Enter code first!');return}
showStatus('loading','Processing...');
try{
const r=await fetch('/obfuscate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,level})});
const d=await r.json();
if(d.error)throw new Error(d.error);
result=d;
document.getElementById('output').value=d.obfuscated;
document.getElementById('s1').textContent=d.stats.original;
document.getElementById('s2').textContent=d.stats.obfuscated;
document.getElementById('s3').textContent=d.stats.ratio+'x';
document.getElementById('s4').textContent=d.stats.level;
document.getElementById('stats').style.display='grid';
document.getElementById('ls').textContent=d.roblox_usage;
document.getElementById('ls').style.display='block';
showStatus('success','Done!');
}catch(e){showStatus('error',e.message)}
}
function copy(){const o=document.getElementById('output').value;if(o)navigator.clipboard.writeText(o).then(()=>showStatus('success','Copied!'))}
function download(){const o=document.getElementById('output').value;if(!o)return;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([o]));a.download='obfuscated.lua';a.click()}
</script>
</body></html>'''

# ============================================
# ROUTES
# ============================================

@app.route('/')
def home():
    if 'text/html' in request.headers.get('Accept', ''):
        return render_template_string(WEB_UI)
    return jsonify({
        "service": "Luau Obfuscator API",
        "version": "2.1.0",
        "status": "online",
        "endpoints": {
            "GET /": "Web UI",
            "GET /health": "Health check",
            "POST /obfuscate": "Obfuscate code",
            "GET /script/<key>": "Get script"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": round(time.time() - stats['start_time'], 2)
    })

@app.route('/obfuscate', methods=['POST'])
def obfuscate():
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({"error": "No code provided"}), 400
        
        code = data['code']
        level = min(max(int(data.get('level', 2)), 1), 3)
        
        if len(code) > Config.MAX_CODE_SIZE:
            return jsonify({"error": "Code too large"}), 400
        
        obfuscator = LuauObfuscator()
        obfuscated = obfuscator.obfuscate(code, level)
        
        key = hashlib.md5(f"{code}{time.time()}{random.random()}".encode()).hexdigest()[:16]
        
        script_storage[key] = {
            "code": obfuscated,
            "created": time.time(),
            "level": level
        }
        
        stats['total_obfuscations'] += 1
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
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/script/<key>')
def get_script(key):
    if key not in script_storage:
        return Response("-- Script not found", mimetype='text/plain'), 404
    return Response(script_storage[key]["code"], mimetype='text/plain')

@app.route('/raw', methods=['POST'])
def raw():
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return Response("-- No code", mimetype='text/plain'), 400
        
        obfuscator = LuauObfuscator()
        result = obfuscator.obfuscate(data['code'], data.get('level', 2))
        return Response(result, mimetype='text/plain')
    except Exception as e:
        return Response(f"-- Error: {e}", mimetype='text/plain'), 500

@app.route('/test')
def test():
    obfuscator = LuauObfuscator()
    result = obfuscator.obfuscate('print("Hello World")', 2)
    return Response(f"-- Test:\n{result}", mimetype='text/plain')

@app.route('/loader')
def loader():
    base = request.host_url.rstrip('/')
    code = f'''local L={{}}
L.API="{base}"
function L.load(k)local c=game:HttpGet(L.API.."/script/"..k)local f=loadstring(c)if f then f()end end
return L'''
    return Response(code, mimetype='text/plain')

# ============================================
# RUN - PENTING: PORT BINDING
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
