<div align="center">

# Ciefp Oscam Editor

**Advanced OSCam configuration editor for Enigma2 receivers**

![Version](https://img.shields.io/badge/Version-1.2.5-blue.svg?style=for-the-badge)
![Enigma2](https://img.shields.io/badge/Enigma2-Compatible-green.svg?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-11-yellow.svg?style=for-the-badge)

<img src="https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/.github/logo.png" width="180" alt="Ciefp Oscam Editor Logo"/>

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