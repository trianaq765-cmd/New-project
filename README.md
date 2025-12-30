# 🔒 Lua/Luau Obfuscator

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Advanced Lua/Luau obfuscator dengan dukungan penuh untuk **Roblox Executor 2025-2026**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 XOR Encryption | Encrypt payload dengan XOR (bit32 compatible) |
| 📦 String Encoding | Convert strings ke byte arrays |
| 🎭 Variable Obfuscation | Rename variables ke nama yang confusing |
| 🗑️ Junk Code Injection | Inject fake code untuk confusion |
| 🌀 Control Flow | Opaque predicates & fake branches |
| 🛡️ Anti-Tamper | Environment & integrity checks |
| 📊 Byte Table (0-255) | Lookup table untuk fast decoding |
| 🔗 Loadstring URL | Direct URL untuk Roblox executor |

## 🎮 Supported Executors

| Executor | Status | Tested |
|----------|--------|--------|
| Synapse X | ✅ Full Support | ✅ |
| Script-Ware | ✅ Full Support | ✅ |
| Fluxus | ✅ Full Support | ✅ |
| KRNL | ✅ Full Support | ✅ |
| Hydrogen | ✅ Full Support | ✅ |
| Delta | ✅ Full Support | ✅ |
| Arceus X | ✅ Full Support | ✅ |
| JJSploit | ⚠️ Limited | ✅ |

## 🚀 Quick Start

### Deploy ke Render.com

1. Fork repository ini
2. Buat akun di [Render.com](https://render.com)
3. Connect GitHub repository
4. Create **Web Service** untuk API
5. Create **Background Worker** untuk Discord Bot
6. Set environment variables

### Environment Variables

```bash
# Discord Bot
DISCORD_TOKEN=your_bot_token

# API URL (otomatis dari Render)
API_URL=https://your-app.onrender.com
