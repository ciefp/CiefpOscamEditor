<div align="center">

# Ciefp Oscam Editor

**Editor za OSCam konfiguraciju u Enigma2 okruženju**

![Version](https://img.shields.io/badge/Version-1.2.5-blue.svg?style=for-the-badge)
![Enigma2](https://img.shields.io/badge/Enigma2-Compatible-green.svg?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-11-yellow.svg?style=for-the-badge)

<img src="https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/.github/logo.png" width="200" alt="Ciefp Logo"/>

**Jednostavan editor za OSCam fajlove: user, dvbapi, softcam.key, webif monitoring i više**

[🇬🇧 English](#english) | [🇷🇸 Srpski](#srpski) | [🇭🇷 Hrvatski](#hrvatski) | [🇸🇰 Slovenčina](#slovenčina) | [🇬🇷 Ελληνικά](#ελληνικά) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski) | [🇹🇷 Türkçe](#türkçe) | [🇪🇸 Español](#español) | [🇦🇪 العربية](#عربي) | [🇷🇸 Српски (ћирилица)](#српски-ћирилица)

</div>

---

## English **Features**

| Feature | Description |
|---------|-------------|
| **Multi-Language Support** | 11 languages with automatic translations |
| **OSCam File Editors** | Edit oscam.user, oscam.dvbapi, SoftCam.Key |
| **WebIF Monitoring** | Real-time status, readers, users via WebIF |
| **Auto-Update** | Check and install new versions from GitHub |
| **BISS Key Management** | Add, delete, preview keys for current channel |
| **Restart OSCam** | Full support for all Enigma2 images (OpenATV, OpenPLi, Pure2, etc.) |
| **Configurable Paths** | Custom paths for config files |
| **Preview & Save** | Preview changes before saving |

---

## English **Installation**

```bash
wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh
```

> Restart GUI: `init 4 && sleep 5 && init 3` or reboot the receiver.

---

## English **Supported Languages**

| Language | Code | Script |
|----------|------|--------|
| English | `en` | Latin |
| Srpski (latinica) | `sr_latn` | Latin |
| Српски (ћирилица) | `sr_cyrl` | Cyrillic |
| Hrvatski | `hr` | Latin |
| Slovak | `sk` | Latin |
| Greek | `el` | Greek |
| Arabic | `ar` | Arabic |
| German | `de` | Latin |
| Polish | `pl` | Latin |
| Turkish | `tr` | Latin |
| Spanish | `es` | Latin |

> Language files: `/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/languages/<lang>.py`

---

## English **Usage**

- **Main Menu**: Access editors for user, dvbapi, softcam.key
- **WebIF**: Monitor OSCam status (IP, user, password configurable)
- **BISS Keys**: Add keys for current channel (SID, VPID auto-detected)
- **Restart**: Automatic OSCam restart after changes
- **Update**: Checks `https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/version.txt`

---

## English **Screenshots**

(Add screenshots here or link to images in repo)

---

## English **Logging & Debugging**

- Logs: Printed to console (telnet/SSH: `cat /tmp/oscam.log` if configured)
- Errors: Handled with MessageBox popups

---

## English **Auto-Update**

- Current Version: 1.2.5
- Update Command: Runs installer.sh on confirmation

---

<div align="center">

## Srpski **Ciefp Oscam Editor**

**Editor za OSCam fajlove u Enigma2**

</div>

---

## Srpski **Šta nudi?**

- Podrška za 11 jezika  
- Editovanje oscam.user, dvbapi, SoftCam.Key  
- Monitoring preko WebIF  
- Dodavanje BISS ključeva za trenutni kanal  
- Restart OSCam-a za sve image-ove  
- Automatsko ažuriranje sa GitHub-a  

---

## Srpski **Instalacija**

```bash
wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh
```

> Restartuj GUI ili risiver.

---

## Srpski **Podržani jezici**

- Srpski (latinica i ćirilica)  
- English, Hrvatski, Slovak, Greek, Arabic, German, Polish, Turkish, Spanish

---

## Srpski **Kako koristiti?**

- Glavni meni: Odaberi editor  
- Dodaj BISS: Automatski SID/VPID  
- Sačuvaj i restartuj  

---

<div align="center">

## Hrvatski | Slovenčina | Ελληνικά | Deutsch | Polski | Türkçe | Español | العربية | Српски (ћирилица)

> Prevedi i dodaj sekcije ako je potrebno. Pošalji Pull Request za nove jezike!

</div>

---

<div align="center">

## English **Thanks for using Ciefp Oscam Editor!**

**@ciefp** • Serbia • 2025

[![GitHub](https://img.shields.io/badge/GitHub-ciefp-black.svg?style=for-the-badge&logo=github)](https://github.com/ciefp/CiefpOscamEditor)
[![X](https://img.shields.io/badge/X-@ciefp-blue.svg?style=for-the-badge&logo=x)](https://x.com/ciefp)

**Star the repo if you like it!**

</div>

---