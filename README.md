# Ciefp Plugins Panel

**Version:** `2.5`  
**Author:** [@ciefp](https://github.com/ciefp)  
**License:** Free for personal use  
**Supported Languages:** English, Srpski, Slovenčina, Русский, Deutsch, Ελληνικά

---

## 📖 Description

**Ciefp Plugins Panel** is a powerful and user-friendly Enigma2 plugin that serves as a central hub for installing and managing a collection of popular **Ciefp** utilities and tools. Designed for satellite receiver users (OpenPLi, OpenATV, VTI, etc.), this panel simplifies the installation of advanced features like EPG importers, IPTV bouquet managers, satellite editors, and more — all with a single click.

---

## ✨ Features

- **One-click installation** of 25+ Ciefp plugins
- **Multilingual interface** (6 languages)
- **Plugin descriptions** with localized text
- **Image viewer** for plugin screenshots
- **Auto-update system** with version checking
- **Installed plugins tracking**
- **Clean, modern GUI** with icons and scrollable descriptions
- **Safe backup & restore** of installed plugins list during updates

---

## 🛠️ Supported Plugins (Examples)

| Plugin Name | Function |
|------------|---------|
| Ciefpsettings Motor | Motorized dish configuration |
| Ciefp IPTV Bouquets | IPTV channel list management |
| Ciefp EPGshare | EPG sharing between devices |
| Ciefp OscamEditor | OSCam configuration editor |
| Ciefp Satellite Analyzer | Signal analysis & transponder scanning |
| Ciefp TvProgramSBB | TV guide for SBB (Serbia) |

> Full list available in the plugin interface.

---

## 🌍 Supported Languages

The plugin automatically detects and loads descriptions in the selected language. Available languages:

| Code | Language |
|------|----------|
| `en` | English |
| `sr` | Srpski |
| `sk` | Slovenčina |
| `ru` | Русский |
| `de` | Deutsch |
| `el` | Ελληνικά |

> Language files are located in:  
> `/usr/lib/enigma2/python/Plugins/Extensions/CiefpPlugins/descriptions/<lang>/`

---

## 📥 Installation

The plugin is installed via its own **installer script** from GitHub:

```bash
wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpPlugins/main/installer.sh -O - | /bin/sh