<div align="center">

# Ciefp Oscam Editor

**Advanced OSCam configuration editor for Enigma2 receivers**

![Version](https://img.shields.io/badge/Version-1.2.5-blue.svg?style=for-the-badge)
![Enigma2](https://img.shields.io/badge/Enigma2-Compatible-green.svg?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-11-yellow.svg?style=for-the-badge)

<img src="https://github.com/ciefp/CiefpOscamEditor/blob/main/logo.jpg" width="200" alt="Ciefp Logo"/>

**Edit `oscam.user`, `oscam.dvbapi`, `SoftCam.Key`, monitor WebIF, and manage BISS keys — all from your remote!**

[🇬🇧 English](#english) | [🇷🇸 Srpski](#srpski) | [🇭🇷 Hrvatski](#hrvatski) | [🇸🇰 Slovenčina](#slovenčina) | [🇬🇷 Ελληνικά](#ελληνικά) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski) | [🇹🇷 Türkçe](#türkçe) | [🇪🇸 Español](#español) | [🇦🇪 العربية](#العربية) | [🇷🇸 Српски (ћирилица)](#српски-ћирилица)

</div>

---

## English **Overview**

**Ciefp Oscam Editor** is a powerful, user-friendly Enigma2 plugin designed for satellite receiver users who run **OSCam** (softcam). It allows full configuration editing directly from the TV screen using your remote control — no telnet or FTP required.

---

## English **Key Features**

| Feature | Description |
|--------|-------------|
| **Multi-Language UI** | 11 languages with full translation support |
| **Config File Editors** | Edit `oscam.user`, `oscam.dvbapi`, `oscam.server` |
| **SoftCam.Key Manager** | Add, delete, preview BISS keys |
| **Auto Channel Detection** | SID & VPID auto-filled when adding BISS keys |
| **WebIF Monitoring** | Live view of readers, users, entitlements |
| **Smart Restart** | Image-specific OSCam restart (OpenATV, OpenPLi, Pure2, OpenViX, etc.) |
| **Auto-Update** | Checks GitHub for new versions |
| **Safe Path Handling** | Supports all common OSCam config locations |
| **Preview Before Save** | See changes before applying |

---

## English **Supported Languages**

| Language | Code | Script |
|--------|------|--------|
| English | `en` | Latin |
| Srpski (latinica) | `sr_latn` | Latin |
| Српски (ћирилица) | `sr_cyrl` | Cyrillic |
| Hrvatski | `hr` | Latin |
| Slovenčina | `sk` | Latin |
| Ελληνικά | `el` | Greek |
| العربية | `ar` | Arabic |
| Deutsch | `de` | Latin |
| Polski | `pl` | Latin |
| Türkçe | `tr` | Latin |
| Español | `es` | Latin |

> Translation files:  
> `/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/languages/<code>.py`

---

## English **Installation**

```bash
wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh
```

> After installation:  
> **Restart GUI**: `init 4 && sleep 5 && init 3`  
> or **reboot the receiver**

---

## English **Usage Guide**

1. **Open Plugin** → Plugins Menu → **Ciefp Oscam Editor**
2. **Navigate** using arrow keys
3. **Edit Configs**:
   - `oscam.user` → Manage accounts (`dvbapiau`, `anonymous`, `cacheex`)
   - `oscam.dvbapi` → CAID, services, AU settings
   - `SoftCam.Key` → Add BISS keys for current channel
4. **WebIF Monitor** → View live OSCam status
5. **Save** → Green button → OSCam restarts automatically
6. **Update** → Checked on startup → prompt to install

---

## English **BISS Key Auto-Add**

- Press **Blue** → "ADD KEY"
- Enter BISS key (8 or 16 hex digits)
- Plugin auto-detects:
  - **Channel Name**
  - **SID** (Service ID)
  - **VPID** (Video PID)
- Key saved to `SoftCam.Key` in correct format:
  ```
  F 1A2B0021 00 1122334455667788 ; Channel Name - 2025-11-10 16:52:00
  ```

---

## English **OSCam Restart Engine**

Fully supports **all major Enigma2 images**:

| Image | Restart Method |
|------|----------------|
| OpenATV / OpenHDF | `softcam.oscam*` init script |
| OpenViX | `softcam.oscam-emu` or manual binary |
| OpenPLi | `--wait 60` + PID file |
| Pure2 | `cam_res` script or fallback |
| Others | Generic `killall` + direct start |

> No more "OSCam not restarting" issues!

---

## English **Auto-Update System**

- Checks: `https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/version.txt`
- If new version → **Yes/No** dialog
- Runs `installer.sh` → full update

---

## English **File Paths (Auto-Detected)**

| File | Common Locations |
|------|------------------|
| `oscam.user` | `/etc/tuxbox/config/oscam.user` |
| `oscam.dvbapi` | `/etc/tuxbox/config/oscam.dvbapi` |
| `SoftCam.Key` | Same folder as `oscam.dvbapi` |
| `oscam.server` | Auto-detected from running OSCam |

---

## English **Screenshots**

![Main Menu](https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/screenshot1.jpg)
![Functions](https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/screenshot2.jpg)
![ADD Emulator](https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/screenshot3.jpg)
![ADD DVB API](https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/screenshot4.jpg)


```markdown
![Main Menu](.github/screenshots/main.png)
![User Editor](.github/screenshots/user_editor.png)
![BISS Key Add](.github/screenshots/biss_add.png)
![WebIF Monitor](.github/screenshots/webif.png)
```

---

## English **Contributing**

Want to help?

1. Fork: [github.com/ciefp/CiefpOscamEditor](https://github.com/ciefp/CiefpOscamEditor)
2. Add translation → `languages/your_lang.py`
3. Improve restart logic for your image
4. Submit Pull Request

---

## English **Support**

- **GitHub Issues**: Report bugs or request features
- **X (Twitter)**: [@ciefp](https://x.com/ciefp)
- **Community**: Share configs, tips, feedback

---

<div align="center">


**Made with ❤️ by @ciefp — Serbia, 2025**

[![GitHub](https://img.shields.io/badge/GitHub-ciefp-black.svg?style=for-the-badge&logo=github)](https://github.com/ciefp)
[![X](https://img.shields.io/badge/X-@ciefp-blue.svg?style=for-the-badge&logo=x)](https://x.com/ciefp)

**⭐ Star this repo if you find it useful!**
