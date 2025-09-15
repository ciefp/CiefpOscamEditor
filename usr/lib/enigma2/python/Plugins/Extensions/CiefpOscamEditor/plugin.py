import socket
import urllib.request
import requests
import json
import re
import os
from requests.auth import HTTPBasicAuth
from Plugins.Plugin import PluginDescriptor
from Plugins.Extensions.CiefpOscamEditor.languages.en import translations as en_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sr_latn import translations as sr_latn_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sr_cyrl import translations as sr_cyrl_trans
from Plugins.Extensions.CiefpOscamEditor.languages.hr import translations as hr_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sk import translations as sk_trans
from Plugins.Extensions.CiefpOscamEditor.languages.el import translations as el_trans
from Plugins.Extensions.CiefpOscamEditor.languages.ar import translations as ar_trans
from Plugins.Extensions.CiefpOscamEditor.languages.de import translations as de_trans
from Plugins.Extensions.CiefpOscamEditor.languages.pl import translations as pl_trans
from Plugins.Extensions.CiefpOscamEditor.languages.tr import translations as tr_trans
from Plugins.Extensions.CiefpOscamEditor.languages.es import translations as es_trans
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Sources.List import List  # Ispravan import za List
from Components.MenuList import MenuList
from ServiceReference import ServiceReference
from Components.Sources.ServiceEvent import ServiceEvent
from enigma import eServiceCenter, iServiceInformation
from enigma import eListboxPythonMultiContent, gFont
from enigma import eTimer, gFont, loadPNG, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from enigma import eServiceCenter, eServiceReference, iServiceInformation, eListbox, eTimer
from enigma import eListbox, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_VALIGN_CENTER, gFont, loadPNG
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, gFont
from datetime import datetime
import urllib.parse  
import urllib.error
import urllib.request
import base64
import xml.etree.ElementTree as ET
from html import unescape
import subprocess


def restart_oscam():
    """Restart OSCam softcam-a sa full podrškom za sve Enigma2 image-ove"""
    try:
        print("[CiefpOscamEditor] Pokrećem restart OSCam-a...")

        # Prvo pokušaj sa standardnim Enigma2 načinom za moderne image-ove
        try:
            from Screens.Standby import TryQuitMainloop
            from boxbranding import getImageDistro

            image_distro = getImageDistro().lower()
            print(f"[CiefpOscamEditor] Detektovan image: {image_distro}")

            modern_images = ('openatv', 'openbh', 'openvix', 'openeight', 'openpli',
                             'egami', 'pure2', 'openhdf', 'opendroid', 'openspa')

            if image_distro in modern_images:
                try:
                    from Screens.Standby import QUIT_RESTART_SOFTCAM
                    print("[CiefpOscamEditor] Pokušavam TryQuitMainloop metod...")
                    TryQuitMainloop(QUIT_RESTART_SOFTCAM)
                    print(f"[CiefpOscamEditor] OSCam restartovan preko TryQuitMainloop za {image_distro}")
                    return True
                except ImportError:
                    print("[CiefpOscamEditor] QUIT_RESTART_SOFTCAM nije dostupan")
                    pass
        except Exception as e:
            print(f"[CiefpOscamEditor] Greška pri detekciji image-a: {str(e)}")
            image_distro = "unknown"

        # Dobij informacije o OSCam verziji
        oscam_info = get_oscam_info()
        config_dir = oscam_info.get("config_dir", "")
        print(f"[CiefpOscamEditor] Config dir: {config_dir}")

        # Odredi OSCam varijantu na osnovu config direktorijuma
        oscam_variant = "oscam"
        variant_suffix = ""
        if "oscam-emu" in config_dir:
            oscam_variant = "oscam-emu"
            variant_suffix = "emu"
        elif "oscam-master" in config_dir:
            oscam_variant = "oscam-master"
            variant_suffix = "master"
        elif "oscam-smod" in config_dir:
            oscam_variant = "oscam-smod"
            variant_suffix = "smod"
        elif "oscamicamnew" in config_dir:
            oscam_variant = "oscamicamnew"
            variant_suffix = "icamnew"

        print(f"[CiefpOscamEditor] OSCam varijanta: {oscam_variant}")

        # Image-specific restart procedure
        if image_distro == "openpli":
            print("[CiefpOscamEditor] Koristim OpenPLI metod...")
            return openpli_restart(oscam_variant, config_dir)

        elif image_distro == "pure2":
            print("[CiefpOscamEditor] Koristim Pure2 metod...")
            return pure2_restart(oscam_variant, variant_suffix)

        elif image_distro == "openvix":
            print("[CiefpOscamEditor] Koristim OpenViX metod...")
            return openvix_restart(oscam_variant, variant_suffix, config_dir)

        elif image_distro in ("openatv", "openhdf"):
            print(f"[CiefpOscamEditor] Koristim {image_distro} metod...")
            # OPENATV KORISTI INIT SKRIPTU KAO OPENVIX!
            return openvix_restart(oscam_variant, variant_suffix, config_dir)

        else:
            print("[CiefpOscamEditor] Koristim generički metod...")
            return generic_restart(oscam_variant, config_dir)

    except Exception as e:
        print(f"[CiefpOscamEditor] Critical error: {str(e)}")
        # Hitni fallback
        return emergency_restart()

def openatv_restart(oscam_variant, variant_suffix, config_dir):
    """OpenATV specific restart"""
    try:
        print(f"[CiefpOscamEditor] OpenATV restart for: {oscam_variant}")

        # OpenATV koristi iste init skripte kao OpenViX
        cam_name = "oscam-emu" if "emu" in oscam_variant.lower() else oscam_variant
        init_script = f"/etc/init.d/softcam.{cam_name}"

        if os.path.exists(init_script):
            print(f"[CiefpOscamEditor] Found OpenATV init script: {init_script}")

            # Koristi restart komandu
            result = os.system(f"{init_script} restart >/dev/null 2>&1")
            os.system("sleep 3")

            # Proveri status
            status_result = os.system(f"{init_script} status >/dev/null 2>&1")

            if status_result == 0:
                print(f"[CiefpOscamEditor] OSCam restartovan OpenATV init skriptom")
                return True

        # Fallback za OpenATV
        print(f"[CiefpOscamEditor] Using OpenATV fallback...")

        # OpenATV koristi /usr/bin/ za binarne fajlove
        binary_path = f"/usr/bin/{oscam_variant}"
        if not os.path.exists(binary_path):
            print(f"[CiefpOscamEditor] Binary not found at {binary_path}")
            return generic_restart(oscam_variant, config_dir)

        # Standardni OpenATV restart procedure
        pid_file = f"/var/tmp/{oscam_variant}.pid"

        # Stop
        os.system(f"{init_script} stop >/dev/null 2>&1" if os.path.exists(
            init_script) else f"killall {oscam_variant} 2>/dev/null")
        os.system("sleep 2")

        # Start
        config_dir_param = f"--config-dir /etc/tuxbox/config/{cam_name}" if cam_name != "oscam" else "--config-dir /etc/tuxbox/config"
        cmd = f"ulimit -s 1024 && {binary_path} {config_dir_param} --daemon --pidfile {pid_file} --restart 2 >/dev/null 2>&1"
        result = os.system(cmd)

        os.system("sleep 3")

        # Proveri da li radi
        pid_check = os.system(f"pidof {oscam_variant} >/dev/null 2>&1")

        if pid_check == 0:
            print(f"[CiefpOscamEditor] OSCam uspešno restartovan na OpenATV")
            return True
        else:
            return generic_restart(oscam_variant, config_dir)

    except Exception as e:
        print(f"[CiefpOscamEditor] OpenATV restart error: {str(e)}")
        return generic_restart(oscam_variant, config_dir)

def openvix_restart(oscam_variant, variant_suffix, config_dir):
    """OpenViX specific restart sa poboljšanom detekcijom"""
    try:
        print(f"[CiefpOscamEditor] OpenViX restart for: {oscam_variant}")

        # Prvo probaj da nađeš tačnu init skriptu
        cam_name = oscam_variant
        if "emu" in oscam_variant.lower():
            cam_name = "oscam-emu"  # Standardno ime za OpenViX

        init_script = f"/etc/init.d/softcam.{cam_name}"

        if os.path.exists(init_script):
            print(f"[CiefpOscamEditor] Found OpenViX init script: {init_script}")

            # Prvo stop pa start za čist restart
            stop_result = os.system(f"{init_script} stop >/dev/null 2>&1")
            os.system("sleep 2")

            # Očisti sve preostale procese
            os.system(f"killall {oscam_variant} {cam_name} 2>/dev/null")
            os.system("sleep 1")

            # Start
            start_result = os.system(f"{init_script} start >/dev/null 2>&1")
            os.system("sleep 3")

            # Proveri status
            status_result = os.system(f"{init_script} status >/dev/null 2>&1")

            if status_result == 0:
                print(f"[CiefpOscamEditor] OSCam restartovan OpenViX init skriptom")
                return True

        # Probaj druge init skripte
        other_scripts = [
            f"/etc/init.d/softcam.{variant_suffix}",
            f"/etc/init.d/{oscam_variant}",
            "/etc/init.d/softcam"
        ]

        for script in other_scripts:
            if os.path.exists(script):
                print(f"[CiefpOscamEditor] Trying script: {script}")
                result = os.system(f"{script} restart >/dev/null 2>&1")
                os.system("sleep 3")

                if result == 0:
                    print(f"[CiefpOscamEditor] OSCam restartovan sa: {script}")
                    return True

        # Manual restart za OpenViX
        print(f"[CiefpOscamEditor] Using manual OpenViX restart...")

        # Pronađi binarnu datoteku
        binary_paths = [
            f"/usr/softcams/{oscam_variant}",
            f"/usr/softcams/{cam_name}",
            f"/usr/bin/{oscam_variant}",
            f"/usr/bin/{cam_name}"
        ]

        oscam_bin = None
        for path in binary_paths:
            if os.path.exists(path):
                oscam_bin = path
                break

        if not oscam_bin:
            print(f"[CiefpOscamEditor] Binary not found, using fallback")
            return generic_restart(oscam_variant, config_dir)

        # Pronađi config direktorijum
        config_dirs = [
            f"/etc/tuxbox/config/{cam_name}",
            f"/etc/tuxbox/config/{oscam_variant}",
            "/etc/tuxbox/config",
            "/etc/oscam",
            config_dir
        ]

        actual_config_dir = config_dir
        for dir in config_dirs:
            if os.path.exists(dir):
                actual_config_dir = dir
                break

        # Stop sve instance
        os.system(f"killall {oscam_variant} {cam_name} 2>/dev/null")
        os.system("sleep 2")

        # Očisti PID fajlove i temp
        pid_file = f"/var/tmp/{oscam_variant}.pid"
        os.system(f"rm -f {pid_file} /var/tmp/{cam_name}.pid 2>/dev/null")
        os.system("rm -rf /tmp/.oscam /tmp/oscam* 2>/dev/null")

        # Start komanda kao u OpenViX init skripti
        cmd = f"ulimit -s 1024 && {oscam_bin} --config-dir {actual_config_dir} --daemon --pidfile {pid_file} --restart 2 >/dev/null 2>&1"
        result = os.system(cmd)

        os.system("sleep 3")

        # Proveri da li radi
        pid_check = os.system(f"pidof {oscam_variant} >/dev/null 2>&1")

        if pid_check == 0:
            print(f"[CiefpOscamEditor] OSCam uspešno restartovan manualno")
            return True
        else:
            print(f"[CiefpOscamEditor] Manual restart failed, trying generic")
            return generic_restart(oscam_variant, actual_config_dir)

    except Exception as e:
        print(f"[CiefpOscamEditor] OpenViX restart error: {str(e)}")
        return generic_restart(oscam_variant, config_dir)

def openpli_restart(oscam_variant, config_dir):
    """OpenPLI specific restart"""
    try:
        pid_file = "/tmp/oscam-emu.pid" if oscam_variant == "oscam-emu" else f"/tmp/{oscam_variant}.pid"
        config_dir_param = f"--config-dir {config_dir}" if config_dir != "Unknown" else f"--config-dir /etc/tuxbox/config/{oscam_variant}"
        
        print(f"[CiefpOscamEditor] Stopping {oscam_variant}...")
        # Stop (OpenPLI style)
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    os.system(f"kill {pid} 2>/dev/null")
                    print(f"[CiefpOscamEditor] Killed process {pid}")
            except:
                pass
        
        os.system(f"killall /usr/bin/{oscam_variant} 2>/dev/null")
        os.system("sleep 1")
        
        # Start (OpenPLI style with --wait parameter)
        print(f"[CiefpOscamEditor] Starting {oscam_variant}...")
        os.system(f"ulimit -s 1024")
        result = os.system(f"/usr/bin/{oscam_variant} --wait 60 {config_dir_param} --daemon --pidfile {pid_file} --restart 2 >/dev/null 2>&1")
        
        if result == 0:
            print(f"[CiefpOscamEditor] OSCam uspešno restartovan OpenPLI metodom")
            return True
        else:
            print(f"[CiefpOscamEditor] OpenPLI metod failed, trying fallback...")
            return generic_restart(oscam_variant, config_dir)
            
    except Exception as e:
        print(f"[CiefpOscamEditor] OpenPLI restart error: {str(e)}")
        return False


def pure2_restart(oscam_variant, variant_suffix):
    """Pure2 specific restart"""
    try:
        # Koristi Pure2 cam skriptu ako postoji
        cam_scripts = [
            f"/usr/script/cam/oscam{variant_suffix}.sh",
            "/usr/script/cam/oscamemu.sh",
            "/usr/script/cam/softcam.sh"
        ]

        for script in cam_scripts:
            if os.path.exists(script):
                print(f"[CiefpOscamEditor] Running Pure2 script: {script}")

                # Proveri da li je to oscamemu.sh i koristi pravilne parametre
                if "oscamemu" in script:
                    # Za oscamemu.sh koristimo "cam_res" parametar za restart
                    result = os.system(f"{script} cam_res >/dev/null 2>&1")
                else:
                    # Za druge skripte probaj standardni restart
                    result = os.system(f"{script} restart >/dev/null 2>&1")
                    if result != 0:
                        result = os.system(f"{script} >/dev/null 2>&1")

                if result == 0:
                    print(f"[CiefpOscamEditor] OSCam restartovan Pure2 cam skriptom: {script}")
                    return True
                else:
                    print(f"[CiefpOscamEditor] Script {script} returned error: {result}")

        # Fallback za Pure2 - koristi direktno cam_down i cam_up
        print("[CiefpOscamEditor] Using Pure2 fallback method...")

        # Prvo ugasi OSCam
        os.system(f"killall -9 {oscam_variant} 2>/dev/null")
        os.system("sleep 2")
        os.system("rm -rf /tmp/.oscam /tmp/oscam* 2>/dev/null")

        # Očisti PID-ove i temp fajlove
        os.system("rm -f /var/run/oscam* /tmp/.oscam* 2>/dev/null")
        os.system("sleep 1")

        # Pokreni OSCam ponovo
        config_dir = "/etc/tuxbox/config"

        # Proveri da li config direktorijum postoji
        if not os.path.exists(config_dir):
            config_dir = "/etc/tuxbox/config"
            if not os.path.exists(config_dir):
                config_dir = "/etc/oscam"

        # Pokreni OSCam u pozadini
        result = os.system(f"/usr/bin/cam/{oscam_variant} -S -c {config_dir} >/dev/null 2>&1 &")

        # Dodatna provera da li je proces pokrenut
        os.system("sleep 3")
        pid_check = os.system(f"pidof {oscam_variant} >/dev/null 2>&1")

        if result == 0 or pid_check == 0:
            print(f"[CiefpOscamEditor] OSCam restartovan Pure2 fallback metodom")
            return True
        else:
            print("[CiefpOscamEditor] Pure2 fallback failed, trying generic restart")
            return generic_restart(oscam_variant, config_dir)

    except Exception as e:
        print(f"[CiefpOscamEditor] Pure2 restart error: {str(e)}")
        # Fallback na generic restart
        return generic_restart(oscam_variant, "/etc/tuxbox/config")

def generic_restart(oscam_variant, config_dir):
    """Generic restart method for other images"""
    try:
        pid_file = f"/var/tmp/{oscam_variant}.pid"
        
        # Stop
        print(f"[CiefpOscamEditor] Stopping {oscam_variant}...")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    os.system(f"kill {pid} 2>/dev/null")
                    print(f"[CiefpOscamEditor] Killed process {pid}")
            except:
                pass
        
        os.system(f"killall {oscam_variant} 2>/dev/null")
        os.system("sleep 1")
        
        # Start
        config_dir_param = f"--config-dir {config_dir}" if config_dir != "Unknown" else ""
        
        # Proveri sve moguće lokacije binary fajlova
        binary_paths = [
            f"/usr/softcams/{oscam_variant}",      # OpenViX
            f"/usr/bin/{oscam_variant}",           # OpenPLI/OpenATV
            f"/usr/bin/cam/{oscam_variant}",       # Pure2
            "/usr/bin/oscam",                      # Generic
            "/usr/local/bin/oscam"                 # Alternative
        ]
        
        for binary in binary_paths:
            if os.path.exists(binary):
                print(f"[CiefpOscamEditor] Starting {oscam_variant} from {binary}...")
                os.system(f"ulimit -s 1024")
                
                if config_dir_param:
                    result = os.system(f"{binary} {config_dir_param} --daemon --pidfile {pid_file} --restart 2 >/dev/null 2>&1 &")
                else:
                    result = os.system(f"{binary} --daemon --pidfile {pid_file} --restart 2 >/dev/null 2>&1 &")
                
                os.system("sleep 0.5")
                
                if os.path.exists(pid_file):
                    print(f"[CiefpOscamEditor] OSCam restartovan generičkim metodom")
                    return True
                break
        
        # Finalni pokušaj - jednostavno pokretanje
        os.system(f"/usr/bin/{oscam_variant} -b >/dev/null 2>&1 &")
        print(f"[CiefpOscamEditor] OSCam startovan osnovnom komandom")
        return True
        
    except Exception as e:
        print(f"[CiefpOscamEditor] Generic restart error: {str(e)}")
        return False

def emergency_restart():
    """Emergency fallback restart"""
    try:
        print("[CiefpOscamEditor] Running emergency restart...")
        os.system("killall -9 oscam* oscam-emu* oscam-master* oscam-smod* oscamicamnew* 2>/dev/null")
        os.system("sleep 2")
        os.system("rm -rf /tmp/.oscam /tmp/oscam* 2>/dev/null")
        result = os.system("/usr/bin/oscam -b >/dev/null 2>&1 &")
        
        if result == 0:
            print("[CiefpOscamEditor] OSCam restartovan emergency metodom")
            return True
        else:
            print("[CiefpOscamEditor] Emergency metod failed!")
            return False
    except Exception as e:
        print(f"[CiefpOscamEditor] Emergency restart error: {str(e)}")
        return False

# Postojeći kod za prevode
TRANSLATIONS = {
    "en": en_trans,
    "sr_latn": sr_latn_trans,
    "sr_cyrl": sr_cyrl_trans,
    "hr": hr_trans,
    "sk": sk_trans,
    "el": el_trans,
    "ar": ar_trans,
    "de": de_trans,
    "pl": pl_trans,
    "tr": tr_trans,
    "es": es_trans
}

def get_translation(key):
    lang = config.plugins.CiefpOscamEditor.language.value
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    if key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]
    return key

# Konfiguracija (nakon get_translation)
config.plugins.CiefpOscamEditor = ConfigSubsection()
config.plugins.CiefpOscamEditor.dvbapi_path = ConfigSelection(
    default="/etc/tuxbox/config/oscam.dvbapi",
    choices=[
        ("/etc/tuxbox/config/oscam.dvbapi", "Default"),
        ("/etc/tuxbox/config/oscam/oscam.dvbapi", "Oscam"),
        ("/etc/tuxbox/config/oscam-emu/oscam.dvbapi", "Oscam-emu"),
        ("/etc/tuxbox/config/oscam-master/oscam.dvbapi", "Oscam-master"),
        ("/etc/tuxbox/config/oscam-smod/oscam.dvbapi", "Oscam-smod"),
        ("/etc/tuxbox/config/oscamicamnew/oscam.dvbapi", "oscamicamnew")
    ]
)

config.plugins.CiefpOscamEditor.language = ConfigSelection(
    default="en",
    choices=[
        ("en", "English"),
        ("sr_latn", "Srpski (latinica)"),
        ("sr_cyrl", "Српски (ћирилица)"),
        ("hr", "Hrvatki"),
        ("sk", "Slovak"),
        ("el", "Greek"),
        ("ar", "Arabic"),
        ("de", "German"),
        ("pl", "Polish"),
        ("tr", "Turkish"),
        ("es", "Spain")
    ]
)
config.plugins.CiefpOscamEditor.auto_version_path = ConfigSelection(
    default="yes",
    choices=[
        ("yes", "Yes"),
        ("no", "No")
    ]
)

config.plugins.CiefpOscamEditor.webif_ip = ConfigText(default="127.0.0.1", fixed_size=False)
config.plugins.CiefpOscamEditor.webif_user = ConfigText(default="", fixed_size=False)
config.plugins.CiefpOscamEditor.webif_password = ConfigText(default="", fixed_size=False)
config.plugins.CiefpOscamEditor.refresh_interval = ConfigSelection(default="5", choices=[
    ("5", get_translation("5_seconds")),
    ("10", get_translation("10_seconds")),
    ("30", get_translation("30_seconds")),
    ("60", get_translation("60_seconds"))
])



# Postojeće funkcije
VERSION_URL = "https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/refs/heads/main/version.txt"
UPDATE_COMMAND = 'wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh'
PLUGIN_VERSION = "1.2.5"

def check_for_update(session):
    try:
        print("[CiefpOscamEditor] Checking for updates...")
        current_version = PLUGIN_VERSION
        print(f"[CiefpOscamEditor] Current version: {current_version}")
        
        # Koristimo Request sa User-Agent headerom
        req = urllib.request.Request(VERSION_URL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as f:
            latest_version = f.read().decode("utf-8").strip()
            print(f"[CiefpOscamEditor] Latest version: {latest_version}")

        if latest_version != current_version:
            print("[CiefpOscamEditor] New version available!")
            def onConfirmUpdate(answer):
                if answer:
                    print("[CiefpOscamEditor] Starting update...")
                    session.open(MessageBox, get_translation("update_in_progress"), MessageBox.TYPE_INFO, timeout=5)
                    subprocess.call(UPDATE_COMMAND, shell=True)
                else:
                    print("[CiefpOscamEditor] Update cancelled")
                    session.open(MessageBox, get_translation("update_cancelled"), MessageBox.TYPE_INFO, timeout=5)

            session.openWithCallback(
                onConfirmUpdate,
                MessageBox,
                f"{get_translation('new_version_available').format(latest_version)}\n"
                f"{get_translation('current_version')}: {current_version}\n"
                f"{get_translation('update_question')}",
                MessageBox.TYPE_YESNO
            )
        else:
            print("[CiefpOscamEditor] Plugin is up to date")
            
    except urllib.error.URLError as e:
        print(f"[CiefpOscamEditor] URL Error: {e}")
    except urllib.error.HTTPError as e:
        print(f"[CiefpOscamEditor] HTTP Error: {e.code} {e.reason}")
    except Exception as e:
        print(f"[CiefpOscamEditor] Update check error: {e}")

def get_oscam_info():
    version_file = "/var/volatile/tmp/.oscam/oscam.version"
    oscam_info = {
        "version": "Unknown",
        "build_date": "Unknown",
        "start_time": "Unknown",
        "box_type": "Unknown",
        "config_dir": "Unknown",
        "webif_port": "8888",
        "features": [],
        "protocols": [],
        "readers": []
    }
    if config.plugins.CiefpOscamEditor.auto_version_path.value == "yes" and os.path.exists(version_file):
        try:
            with open(version_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Version:"):
                        oscam_info["version"] = line.split(":")[1].strip()
                    elif line.startswith("Build Date:"):
                        oscam_info["build_date"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Starttime:"):
                        oscam_info["start_time"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Box Type:"):
                        oscam_info["box_type"] = line.split(":", 1)[1].strip()
                    elif line.startswith("ConfigDir:"):
                        oscam_info["config_dir"] = line.split(":", 1)[1].strip()
                    elif line.startswith("WebifPort:"):
                        oscam_info["webif_port"] = line.split(":", 1)[1].strip()
                    elif ":" in line and "support" in line.lower():
                        feature, status = line.split(":", 1)
                        if status.strip().lower() == "yes":
                            oscam_info["features"].append(feature.strip())
                    elif ":" in line and any(proto in line.lower() for proto in ["camd", "newcamd", "cccam", "gbox", "radegast", "scam", "serial", "constant cw", "pandora", "ghttp", "streamrelay"]):
                        protocol, status = line.split(":", 1)
                        if status.strip().lower() == "yes":
                            oscam_info["protocols"].append(protocol.strip())
                    elif ":" in line and "cardreader" in line.lower():
                        reader, status = line.split(":", 1)
                        if status.strip().lower() == "yes":
                            oscam_info["readers"].append(reader.strip())
        except Exception as e:
            print(f"[CiefpOscamEditor] Error reading oscam.version: {str(e)}")
    return oscam_info

# Ažurirana funkcija read_oscam_conf
oscam_regex = {
    'httpport': re.compile(r'httpport\s*=\s*(?P<httpport>[+]?\d+)'),
    'httpuser': re.compile(r'httpuser\s*=\s*(?P<httpuser>.*)'),
    'httppwd': re.compile(r'httppwd\s*=\s*(?P<httppwd>.*)'),
}

def get_all_readers_from_config():
    """
    Vrati listu svih reader labela iz oscam.server.
    Lokacija se otkriva iz oscam.conf ili poznatih putanja.
    """
    readers = []

    # 1) pronađi oscam.conf
    conf_paths = [
        "/etc/tuxbox/config/oscam.conf",
        "/etc/tuxbox/config/oscam-emu/oscam.conf",
        "/usr/keys/oscam.conf",
        "/var/tuxbox/config/oscam.conf",
    ]
    conf_file = next((p for p in conf_paths if os.path.exists(p)), None)

    server_file = None
    if conf_file:
        with open(conf_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.match(r'^\s*serverfile\s*=\s*(.+)$', line, flags=re.IGNORECASE)
                if m:
                    server_file = m.group(1).strip()
                    break

    # 2) ako nije definisan u conf-u, probaj poznate lokacije
    if not server_file:
        possible_paths = [
            "/etc/tuxbox/config/oscam.server",
            "/etc/tuxbox/config/oscam/oscam.server",
            "/etc/tuxbox/config/oscam-emu/oscam.server",
            "/etc/tuxbox/config/oscam-master/oscam.server",
            "/etc/tuxbox/config/oscam-smod/oscam.server",
            "/etc/tuxbox/config/oscamicamnew/oscam.server",
        ]
        server_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if not server_file or not os.path.exists(server_file):
        print("[OscamStatus] oscam.server not found in any known location")
        return readers

    print(f"[OscamStatus] using oscam.server from {server_file}")

    # 3) parsiraj label-e iz oscam.server
    with open(server_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r'^\s*label\s*=\s*(.+)$', line, flags=re.IGNORECASE)
            if m:
                label = m.group(1).strip()
                if label:
                    readers.append(label)

    print(f"[OscamStatus] found readers: {readers}")
    return readers


def read_oscam_conf():
    conf = {
        "ip": config.plugins.CiefpOscamEditor.webif_ip.value,
        "port": config.plugins.CiefpOscamEditor.webif_port.value if hasattr(config.plugins.CiefpOscamEditor, 'webif_port') else "8888",
        "user": config.plugins.CiefpOscamEditor.webif_user.value,
        "pwd": config.plugins.CiefpOscamEditor.webif_password.value
    }
    # Dobij ConfigDir iz get_oscam_info
    oscam_info = get_oscam_info()
    config_dir = oscam_info.get("config_dir", "Unknown")
    webif_port = oscam_info.get("webif_port", "8888")

    possible_paths = [
        "/etc/tuxbox/config/oscam-emu/oscam.conf",
        os.path.join(config_dir, "oscam.conf") if config_dir != "Unknown" else None,
        "/etc/tuxbox/config/oscam.conf",
        "/etc/tuxbox/config/oscam-master/oscam.conf",
        "/etc/tuxbox/config/oscam-smod/oscam.conf",
        "/usr/local/etc/oscam.conf"
    ]
    possible_paths = [p for p in possible_paths if p]

    for conf_path in possible_paths:
        if os.path.isfile(conf_path):
            print(f"[CiefpOscamEditor] Pronađen oscam.conf: {conf_path}")
            try:
                with open(conf_path, "r") as f:
                    for line in f:
                        for key, rx in oscam_regex.items():
                            match = rx.search(line)
                            if match:
                                if key == "httpport":
                                    port = match.group("httpport")
                                    conf["port"] = port[1:] if port.startswith("+") else port
                                elif key == "httpuser":
                                    conf["user"] = match.group("httpuser").strip()
                                elif key == "httppwd":
                                    conf["pwd"] = match.group("httppwd").strip()
                if webif_port != "Unknown":
                    conf["port"] = webif_port
                return conf
            except Exception as e:
                print(f"[CiefpOscamEditor] Greška pri čitanju oscam.conf ({conf_path}): {e}")
    print(f"[CiefpOscamEditor] oscam.conf nije pronađen, koristim podrazumevane vrednosti")
    return conf


def get_oscam_readers(ip="127.0.0.1", port="8888", user="", pwd=""):
    """
    Dohvata OSCam čitače preko WebIf-a koristeći XML sa ?part=status.
    Radi sa verzijom OSCam 2.25.05.
    Vraća listu reader-a sa normalizovanim imenima (bez sufiksa (r)/(p)).
    """
    status_data = []
    url = f"http://{ip}:{port}/oscamapi.html?part=status"
    print(f"[CiefpOscamEditor] Pokušavam XML sa URL: {url}")

    try:
        request = urllib.request.Request(url)
        if user and pwd:
            auth_string = f"{user}:{pwd}"
            auth_encoded = base64.b64encode(auth_string.encode()).decode()
            request.add_header("Authorization", f"Basic {auth_encoded}")

        with urllib.request.urlopen(request, timeout=5) as response:
            xml_data = response.read().decode("utf-8")
            print(f"[CiefpOscamEditor] Sirovi XML odgovor: {xml_data[:500]}...")

            try:
                root = ET.fromstring(xml_data)
                # Traži sve <client> koji su čitači ili proxy (type='r' ili 'p')
                for client in root.findall(".//client[@type='r']") + root.findall(".//client[@type='p']"):
                    name = client.get("name", "Unknown").strip()
                    protocol = client.get("protocol", "Unknown").strip()
                    # Status je sadržaj <connection> taga
                    connection = client.find("connection")
                    status = connection.text.strip() if connection is not None and connection.text else "Unknown"
                    au = client.get("au", "0").strip()
                    times = client.find("times")
                    idle = times.get("idle", "0") if times is not None else "0"

                    # Normalizacija imena: ukloni sufiks (r) ili (p)
                    clean_name = name.split(" (")[0].strip()

                    status_data.append({
                        "name": clean_name,
                        "status": status,
                        "au": au,
                        "idle": idle,
                        "protocol": protocol
                    })

                print(f"[CiefpOscamEditor] XML uspešno parsiran, pronađeno {len(status_data)} čitača")
                return status_data

            except ET.ParseError as e:
                print(f"[CiefpOscamEditor] XML parsiranje nije uspelo: {e}")
                print(f"[CiefpOscamEditor] Celokupni XML odgovor: {xml_data}")

    except urllib.error.HTTPError as e:
        print(f"[CiefpOscamEditor] HTTP greška: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"[CiefpOscamEditor] Mrežna greška: {e.reason}")
    except Exception as e:
        print(f"[CiefpOscamEditor] Neočekivana greška: {e}")

    print("[CiefpOscamEditor] Nema dostupnih čitača")
    return []


class CiefpOscamStatus(Screen):
    skin = """<screen name="CiefpOscamStatus" position="center,center" size="1500,800" title="..:: OSCam Status ::..">
        <widget name="status_list" position="10,10" size="1080,740" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_status.png" position="1100,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.is_refreshing = True

        self["status_list"] = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self["status_list"].l.setItemHeight(30)
        self["status_list"].l.setFont(0, gFont("Regular", 24))

        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("refresh"))
        self["key_yellow"] = Label(get_translation("ecm_info"))
        self["key_blue"] = Label(get_translation("toggle_reader"))
        self["background"] = Pixmap()

        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.refreshStatus,
            "yellow": self.openEcmInfo,
            "blue": self.toggleReader,
            "cancel": self.close
        }, -2)

        self.timer = eTimer()
        self.timer.callback.append(self.refreshStatus)
        self.interval = int(config.plugins.CiefpOscamEditor.refresh_interval.value) * 1000
        self.timer.start(self.interval, False)
        self.refreshStatus()

    def refreshStatus(self):
        """
        Osvežava listu reader-a na ekranu sa statusom ON/OFF i informacijama.
        """
        status_data = []
        try:
            conf = read_oscam_conf()
            active_readers = get_oscam_readers(
                ip=conf["ip"],
                port=conf["port"],
                user=conf["user"],
                pwd=conf["pwd"]
            )

            # map active readers po normalizovanom imenu
            active_map = {r['name']: r for r in active_readers}

            all_readers = get_all_readers_from_config()
            if not all_readers:
                status_data.append([
                    ("", ""),
                    MultiContentEntryText(pos=(0, 0), size=(1000, 30), font=0,
                                          text=get_translation("no_readers_defined"))
                ])
            else:
                for rname in all_readers:
                    if rname in active_map:
                        reader = active_map[rname]
                        status = reader['status']  # Connected / Unknown / NeedInit
                        au = reader.get('au', '-')
                        idle = reader.get('idle', '-')
                        protocol = reader.get('protocol', '-')
                    else:
                        status = "OFF"
                        au = idle = protocol = "-"

                    # odredi ikonu
                    status_lower = status.lower()
                    if status_lower == "connected":
                        icon_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/green.png"
                    elif status_lower in ["needinit", "unknown"]:
                        icon_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/yellow.png"
                    else:
                        icon_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/red.png"

                    entry = [
                        (rname, status),
                        MultiContentEntryPixmapAlphaTest(pos=(0, 7), size=(16, 16), png=loadPNG(icon_path)),
                        MultiContentEntryText(
                            pos=(30, 0), size=(1000, 30), font=0,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=f"{get_translation('reader')}: {rname} | "
                                 f"{get_translation('status')}: {status} | "
                                 f"{get_translation('au')}: {au} | "
                                 f"{get_translation('idle_time')}: {idle} | "
                                 f"{get_translation('protocol')}: {protocol}"
                        )
                    ]
                    status_data.append(entry)

        except Exception as e:
            status_data.append([
                ("", ""),
                MultiContentEntryText(pos=(0, 0), size=(1000, 30), font=0,
                                      text=get_translation("connection_error").format(str(e)))
            ])

        self["status_list"].setList(status_data)

    # --- ostale funkcije ostaju iste ---
    def toggleReader(self):
        current = self["status_list"].getCurrent()
        if not current:
            self.session.open(MessageBox, get_translation("no_reader_selected"), MessageBox.TYPE_ERROR, timeout=5)
            return

        data = current[0] if isinstance(current, (list, tuple)) and len(current) > 0 else None
        if not (isinstance(data, (list, tuple)) and len(data) >= 2):
            self.session.open(MessageBox, get_translation("no_reader_selected"), MessageBox.TYPE_ERROR, timeout=5)
            return

        reader_name, current_status = data[0], data[1]
        if not reader_name:
            self.session.open(MessageBox, get_translation("no_reader_selected"), MessageBox.TYPE_ERROR, timeout=5)
            return

        clean_name = reader_name.split(" (")[0]
        status_lower = (current_status or "").strip().lower()
        should_enable = status_lower in ("off", "error", "disabled", "down", "stopped", "unknown", "needinit")
        action = "enable" if should_enable else "disable"

        try:
            conf = read_oscam_conf()
            encoded_reader_name = urllib.parse.quote(clean_name)
            url = f"http://{conf['ip']}:{conf['port']}/readers.html?label={encoded_reader_name}&action={action}"

            req = urllib.request.Request(url)
            if conf.get("user") and conf.get("pwd"):
                auth_bytes = f"{conf['user']}:{conf['pwd']}".encode("utf-8")
                req.add_header("Authorization", f"Basic {base64.b64encode(auth_bytes).decode('ascii')}")

            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.getcode() == 200:
                    msg = f"Reader '{clean_name}' is {'ON' if action == 'enable' else 'OFF'}."
                    self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=3)
                    self.refreshStatus()
                else:
                    raise Exception(f"HTTP {resp.getcode()}")

        except Exception as e:
            self.session.open(MessageBox, f"Error when changing the state of the reader: {e}", MessageBox.TYPE_ERROR, timeout=5)

    def openEcmInfo(self):
        self.session.open(CiefpOscamEcmInfo)

    def close(self):
        self.timer.stop()
        Screen.close(self)

class CiefpOscamConfPreview(Screen):
    skin = """<screen name="CiefpOscamConfPreview" position="center,center" size="1400,800" title="..:: oscam.conf Preview ::..">
        <widget name="file_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_conf_preview.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session, filepath):
        Screen.__init__(self, session)
        self.filepath = filepath
        self.setTitle(get_translation("title_oscam_conf_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("edit"))  # opcionalno
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.editFile,
            "cancel": self.close
        }, -2)
        self.loadFile()

    def loadFile(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r") as f:
                    lines = [line.rstrip() for line in f if line.strip()]
                self["file_list"].setList(lines)
            else:
                self["file_list"].setList([get_translation("file_not_exist")])
        except Exception as e:
            self["file_list"].setList([get_translation("file_read_error").format(str(e))])

    def editFile(self):
        # Kasnije možeš dodati uređivanje
        pass

class CiefpOscamConfEditor(Screen, ConfigListScreen):
    skin = """<screen name="CiefpOscamConfEditor" position="center,center" size="1400,800" title="..:: OSCam Conf ::..">
        <widget name="config" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_conf_editor.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_oscam_conf"))
        self._rebuild_pending = False

        # --- [global] ---
        self.disablelog = ConfigSelection(default="1", choices=[("1", get_translation("on")), ("0", get_translation("off"))])
        self.logfile = ConfigText(default="/dev/tty", fixed_size=False)
        self.clienttimeout = ConfigText(default="5000", fixed_size=False)
        self.clientmaxidle = ConfigText(default="180", fixed_size=False)
        self.netprio = ConfigText(default="1", fixed_size=False)
        self.nice = ConfigText(default="-1", fixed_size=False)
        self.maxlogsize = ConfigText(default="1000", fixed_size=False)
        self.waitforcards = ConfigSelection(default="0", choices=[("0", "0"), ("1", "1")])
        self.preferlocalcards = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.dropdups = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.disablecrccws_only_for = ConfigText(
            default="0E00:000000 1811:003311,023311,003315,003341,00331B,000007,000107;0500:030B00,032830,041950,042800,042820,050F00;1817:000000,00006A;1818:000000,00006C,000007;1819:00006D,000007;098C:000000;09C4:000000;098D:000000;0E00:000000;1830:000000;1810:000000",
            fixed_size=False
        )
        self.cccam_cfg_reconnect_delay = ConfigText(default="90", fixed_size=False)
        self.cccam_cfg_reconnect_attempts = ConfigText(default="6", fixed_size=False)
        self.cccam_cfg_save = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])

        # --- [streamrelay] ---
        self.stream_relay_buffer_opt = ConfigSelection(default="0", choices=[("0", "0"), ("1", "1")])
        self.stream_relay_buffer_time = ConfigText(default="600", fixed_size=False)
        self.stream_relay_ctab = ConfigText(default="09C4,098C,098D", fixed_size=False)
        self.stream_ecm_delay = ConfigText(default="0", fixed_size=False)

        # --- [dvbapi] ---
        self.dvbapi_au = ConfigSelection(default="1", choices=[("1", get_translation("on")), ("0", get_translation("off"))])
        self.dvbapi_pmt_mode = ConfigSelection(default="0", choices=[("0", "0"), ("1", "1"), ("2", "2")])
        self.dvbapi_request_mode = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.dvbapi_delayer = ConfigText(default="60", fixed_size=False)
        self.dvbapi_user = ConfigText(default="dvbapiau", fixed_size=False)
        self.dvbapi_read_sdt = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.dvbapi_write_sdt_prov = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.dvbapi_extended_cw_api = ConfigSelection(default="2", choices=[("0", "0"), ("1", "1"), ("2", "2")])
        self.dvbapi_boxtype = ConfigSelection(default="vuplus", choices=[
            ("dreambox", "dreambox"), ("vuplus", "vuplus"), ("zgemma", "zgemma"),
            ("octagon", "octagon"), ("abpuls", "abpuls"), ("ipbox", "ipbox")
        ])

        # --- [webif] ---
        self.httpport = ConfigText(default="8888", fixed_size=False)
        self.httpshowmeminfo = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.httpshowuserinfo = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.httpshowcacheexinfo = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.httpshowecminfo = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.httpshowloadinfo = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.httpallowed = ConfigText(default="127.0.0.1,192.1.0.0-192.168.255.255", fixed_size=False)
        self.httpuser_enabled = ConfigSelection(default="0", choices=[("0", get_translation("off")), ("1", get_translation("on"))])
        self.httpuser = ConfigText(default="", fixed_size=False)
        self.httppwd = ConfigText(default="", fixed_size=False)

        # --- [newcamd] ---
        self.newcamd_enabled = ConfigSelection(default="0", choices=[("1", get_translation("on")), ("0", get_translation("off"))])
        self.newcamd_port = ConfigText(default="15001@0963:000000", fixed_size=False)
        self.newcamd_key = ConfigText(default="0123456789ABCDEF0123456789ABCDEF", fixed_size=False)
        self.newcamd_allowed = ConfigText(default="0.0.0.0-255.255.255.255", fixed_size=False)

        # --- [cccam] ---
        self.cccam_enabled = ConfigSelection(default="0", choices=[("1", get_translation("on")), ("0", get_translation("off"))])
        self.cccam_port = ConfigText(default="16001", fixed_size=False)
        self.cccam_version = ConfigText(default="2.3.0", fixed_size=False)
        self.cccam_reshare = ConfigText(default="1", fixed_size=False)

        # GUI
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("preview"))
        self["key_blue"] = Label(get_translation("oscam_user"))
        self["background"] = Pixmap()  
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.saveConfig,
            "yellow": self.previewFile,
            "blue": self.openUserEditor,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)

        self.createSetup()
        self["config"].onSelectionChanged.append(self.onSelectionChanged)

    def onSelectionChanged(self):
        current = self["config"].getCurrent()
        if not current:
            return

        # Proveri da li je trenutni unos "enable" tipa
        key = current[0].lower()
        if not any(x in key for x in ["on", "off", "enable", "auth", "newcamd", "cccam"]):
            return

        # Ako je vrednost već obrađena, izbegni rekurziju
        if hasattr(self, "_rebuild_pending") and self._rebuild_pending:
            return

        try:
            self._rebuild_pending = True
            self["config"].blockInputHelpers = True  # Blokira eventove
            self.createSetup()
        finally:
            self._rebuild_pending = False
            self["config"].blockInputHelpers = False

    def createSetup(self):
        self.list = []

        # === [global] ===
        self.list.append(getConfigListEntry("=== [global] ===", ConfigText(default="", fixed_size=True)))
        self.list.extend([
            getConfigListEntry(get_translation("disablelog"), self.disablelog),
            getConfigListEntry(get_translation("logfile"), self.logfile),
            getConfigListEntry(get_translation("clienttimeout"), self.clienttimeout),
            getConfigListEntry(get_translation("clientmaxidle"), self.clientmaxidle),
            getConfigListEntry(get_translation("netprio"), self.netprio),
            getConfigListEntry(get_translation("nice"), self.nice),
            getConfigListEntry(get_translation("maxlogsize"), self.maxlogsize),
            getConfigListEntry(get_translation("waitforcards"), self.waitforcards),
            getConfigListEntry(get_translation("preferlocalcards"), self.preferlocalcards),
            getConfigListEntry(get_translation("dropdups"), self.dropdups),
            getConfigListEntry(get_translation("disablecrccws_only_for"), self.disablecrccws_only_for),
            getConfigListEntry(get_translation("cccam_cfg_reconnect_delay"), self.cccam_cfg_reconnect_delay),
            getConfigListEntry(get_translation("cccam_cfg_reconnect_attempts"), self.cccam_cfg_reconnect_attempts),
            getConfigListEntry(get_translation("cccam_cfg_save"), self.cccam_cfg_save),
        ])

        # === [streamrelay] ===
        self.list.append(getConfigListEntry("=== [streamrelay] ===", ConfigText(default="", fixed_size=True)))
        self.list.extend([
            getConfigListEntry("stream_relay_enabled = 1", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("stream_relay_buffer_opt"), self.stream_relay_buffer_opt),
            getConfigListEntry(get_translation("stream_relay_buffer_time"), self.stream_relay_buffer_time),
            getConfigListEntry(get_translation("stream_relay_ctab"), self.stream_relay_ctab),
            getConfigListEntry(get_translation("stream_ecm_delay"), self.stream_ecm_delay),
        ])

        # === [dvbapi] ===
        self.list.append(getConfigListEntry("=== [dvbapi] ===", ConfigText(default="", fixed_size=True)))
        self.list.extend([
            getConfigListEntry("enabled = 1", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("au"), self.dvbapi_au),
            getConfigListEntry(get_translation("pmt_mode"), self.dvbapi_pmt_mode),
            getConfigListEntry(get_translation("request_mode"), self.dvbapi_request_mode),
            getConfigListEntry(get_translation("delayer"), self.dvbapi_delayer),
            getConfigListEntry(get_translation("user"), self.dvbapi_user),
            getConfigListEntry(get_translation("read_sdt"), self.dvbapi_read_sdt),
            getConfigListEntry(get_translation("write_sdt_prov"), self.dvbapi_write_sdt_prov),
            getConfigListEntry(get_translation("extended_cw_api"), self.dvbapi_extended_cw_api),
            getConfigListEntry(get_translation("boxtype"), self.dvbapi_boxtype),
        ])

        # === [webif] ===
        self.list.append(getConfigListEntry("=== [webif] ===", ConfigText(default="", fixed_size=True)))
        self.list.extend([
            getConfigListEntry(get_translation("httpport"), self.httpport),
            getConfigListEntry(get_translation("httpshowmeminfo"), self.httpshowmeminfo),
            getConfigListEntry(get_translation("httpshowuserinfo"), self.httpshowuserinfo),
            getConfigListEntry(get_translation("httpshowcacheexinfo"), self.httpshowcacheexinfo),
            getConfigListEntry(get_translation("httpshowecminfo"), self.httpshowecminfo),
            getConfigListEntry(get_translation("httpshowloadinfo"), self.httpshowloadinfo),
            getConfigListEntry(get_translation("httpallowed"), self.httpallowed),
            getConfigListEntry(get_translation("enable_http_auth"), self.httpuser_enabled),
        ])
        if self.httpuser_enabled.value == "1":
            self.list.extend([
                getConfigListEntry(get_translation("httpuser"), self.httpuser),
                getConfigListEntry(get_translation("httppwd"), self.httppwd),
            ])

        # === [newcamd] ===
        self.list.append(getConfigListEntry("=== [newcamd] ===", self.newcamd_enabled))
        if self.newcamd_enabled.value == "1":
            self.list.extend([
                getConfigListEntry(get_translation("port"), self.newcamd_port),
                getConfigListEntry(get_translation("key"), self.newcamd_key),
                getConfigListEntry(get_translation("allowed"), self.newcamd_allowed),
            ])

        # === [cccam] ===
        self.list.append(getConfigListEntry("=== [cccam] ===", self.cccam_enabled))
        if self.cccam_enabled.value == "1":
            self.list.extend([
                getConfigListEntry(get_translation("port"), self.cccam_port),
                getConfigListEntry(get_translation("version"), self.cccam_version),
                getConfigListEntry(get_translation("reshare"), self.cccam_reshare),
            ])

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def saveConfig(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        conf_path = dvbapi_path.replace("oscam.dvbapi", "oscam.conf")

        try:
            lines = []

            if not os.path.exists(conf_path):
                lines.append("## Created by CiefpOscamEditor ##")
                lines.append("## ..:: CiefpSettings ::.. ##")
                lines.append("")

            # [global]
            lines.append("[global]")
            lines.append(f"disablelog                    = {self.disablelog.value}")
            lines.append(f"logfile                       = {self.logfile.value}")
            lines.append(f"clienttimeout                 = {self.clienttimeout.value}")
            lines.append(f"clientmaxidle                 = {self.clientmaxidle.value}")
            lines.append(f"netprio                       = {self.netprio.value}")
            lines.append(f"nice                          = {self.nice.value}")
            lines.append(f"maxlogsize                    = {self.maxlogsize.value}")
            lines.append(f"waitforcards                  = {self.waitforcards.value}")
            lines.append(f"preferlocalcards              = {self.preferlocalcards.value}")
            lines.append(f"dropdups                      = {self.dropdups.value}")
            lines.append(f"disablecrccws_only_for        = {self.disablecrccws_only_for.value}")
            lines.append(f"cccam_cfg_reconnect_delay     = {self.cccam_cfg_reconnect_delay.value}")
            lines.append(f"cccam_cfg_reconnect_attempts  = {self.cccam_cfg_reconnect_attempts.value}")
            lines.append(f"cccam_cfg_save                = {self.cccam_cfg_save.value}")
            lines.append("")

            # [streamrelay]
            lines.append("[streamrelay]")
            lines.append("stream_relay_enabled          = 1")
            lines.append(f"stream_relay_buffer_opt       = {self.stream_relay_buffer_opt.value}")
            lines.append(f"stream_relay_buffer_time      = {self.stream_relay_buffer_time.value}")
            lines.append(f"stream_relay_ctab             = {self.stream_relay_ctab.value}")
            lines.append(f"stream_ecm_delay              = {self.stream_ecm_delay.value}")
            lines.append("")

            # [dvbapi]
            lines.append("[dvbapi]")
            lines.append("enabled                       = 1")
            lines.append(f"au                            = {self.dvbapi_au.value}")
            lines.append(f"pmt_mode                      = {self.dvbapi_pmt_mode.value}")
            lines.append(f"request_mode                  = {self.dvbapi_request_mode.value}")
            lines.append(f"delayer                       = {self.dvbapi_delayer.value}")
            lines.append(f"user                          = {self.dvbapi_user.value}")
            lines.append(f"read_sdt                      = {self.dvbapi_read_sdt.value}")
            lines.append(f"write_sdt_prov                = {self.dvbapi_write_sdt_prov.value}")
            lines.append(f"extended_cw_api               = {self.dvbapi_extended_cw_api.value}")
            lines.append(f"boxtype                       = {self.dvbapi_boxtype.value}")
            lines.append("")

            # [webif]
            lines.append("[webif]")
            lines.append(f"httpport                      = {self.httpport.value}")
            lines.append(f"httpshowmeminfo               = {self.httpshowmeminfo.value}")
            lines.append(f"httpshowuserinfo              = {self.httpshowuserinfo.value}")
            lines.append(f"httpshowcacheexinfo           = {self.httpshowcacheexinfo.value}")
            lines.append(f"httpshowecminfo               = {self.httpshowecminfo.value}")
            lines.append(f"httpshowloadinfo              = {self.httpshowloadinfo.value}")
            lines.append(f"httpallowed                   = {self.httpallowed.value}")
            if self.httpuser_enabled.value == "1":
                lines.append(f"httpuser                      = {self.httpuser.value}")
                lines.append(f"httppwd                       = {self.httppwd.value}")
            lines.append("")

            # [newcamd]
            if self.newcamd_enabled.value == "1":
                lines.append("[newcamd]")
                lines.append(f"port                          = {self.newcamd_port.value}")
                lines.append(f"key                           = {self.newcamd_key.value}")
                lines.append(f"allowed                       = {self.newcamd_allowed.value}")
                lines.append("")

            # [cccam]
            if self.cccam_enabled.value == "1":
                lines.append("[cccam]")
                lines.append(f"port                          = {self.cccam_port.value}")
                lines.append(f"version                       = {self.cccam_version.value}")
                lines.append(f"reshare                       = {self.cccam_reshare.value}")
                lines.append("")

            # Snimi fajl
            os.makedirs(os.path.dirname(conf_path), exist_ok=True)
            with open(conf_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.session.open(MessageBox, get_translation("conf_saved").format(conf_path), MessageBox.TYPE_INFO, timeout=5)

        except Exception as e:
            self.session.open(MessageBox, get_translation("write_error").format(conf_path, str(e)), MessageBox.TYPE_ERROR)
    
    def openUserEditor(self):
        self.session.open(CiefpOscamUserEditor)        

    def previewFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        conf_path = dvbapi_path.replace("oscam.dvbapi", "oscam.conf")
        self.session.open(CiefpOscamConfPreview, conf_path)

    def resetToDefault(self):
        self.session.open(MessageBox, get_translation("reset_not_impl"), MessageBox.TYPE_INFO, timeout=5)

    def moveUp(self):
        self["config"].instance.moveSelection(self["config"].instance.moveUp)

    def moveDown(self):
        self["config"].instance.moveSelection(self["config"].instance.moveDown)


class CiefpOscamEditorMain(Screen):
    skin = """
    <screen name="CiefpOscamEditorMain" position="center,center" size="1400,800" title="..:: Ciefp Oscam Editor ::..">
        <widget name="channel_info" position="10,10" size="980,650" font="Regular;26" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_editor_main.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        oscam_info = get_oscam_info()
        self.setTitle(f"{get_translation('title_main')} (OSCam: {oscam_info['version']})")
        self["channel_info"] = Label()

        # Odložena provera verzije
        self.updateTimer = eTimer()
        self.updateTimer.callback.append(lambda: check_for_update(self.session))
        self.updateTimer.start(500, True)

        # Labele
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("functions"))
        self["key_yellow"] = Label(get_translation("settings"))
        self["key_blue"] = Label(get_translation("free_cccam"))
        self["background"] = Pixmap()

        # Action map
        self["actions"] = ActionMap(["ColorActions"], {
            "red": self.close,
            "green": self.openChoiceBox,
            "yellow": self.openSettings,
            "blue": self.addFreeReader,
        }, -2)

        self["cancel_action"] = ActionMap(["SetupActions"], {
            "cancel": self.close
        }, -2)

        self.current_provider_id = "000000"
        self.updateChannelInfo()

    def getSID(self):
        """Dobija SID iz trenutnog servisa"""
        service = self.session.nav.getCurrentlyPlayingServiceReference()
        if service:
            try:
                service_string = service.toString()
                parts = service_string.split(':')
                if len(parts) >= 4:
                    sid_hex = parts[3]
                    sid_decimal = int(sid_hex, 16)
                    return f"{sid_decimal:04X}"
            except:
                pass
        return "0001"

    def getVPID(self):
        """Dobija Video PID iz trenutnog servisa"""
        try:
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    vpid = info.getInfo(iServiceInformation.sVideoPID)
                    if vpid > 0:
                        return f"{vpid:04X}"
        except:
            pass
        return "0021"

    def getChannelName(self):
        """Dobija ime trenutnog kanala"""
        try:
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    name = info.getName()
                    if name:
                        return name
        except:
            pass
        return "Current Channel"

    def openChoiceBox(self):
        choices = [
            (get_translation("oscam_info_button"), "info"),
            (get_translation("oscam_status"), "status"),
            (get_translation("ecm_info"), "ecm_info"),

            (get_translation("oscam_server"), "server_preview"),
            (get_translation("add_reader"), "server_add"),
            (get_translation("add_emulator"), "server_emulator"),
            (get_translation("select_reader"), "server_reader_select"),

            (get_translation("softcam_key_preview"), "softcam_key_preview"),
            (get_translation("add_biss_key"), "add_biss_key"),

            (get_translation("add_dvbapi"), "dvbapi_add"),
            (get_translation("preview_dvbapi"), "dvbapi_preview"),

            (get_translation("oscam_conf_editor"), "conf_editor"),
            (get_translation("oscam_conf_preview"), "conf_preview"),

            (get_translation("oscam_user_preview"), "user_preview"),
            (get_translation("oscam_user"), "user_editor"),
        ]
        self.session.openWithCallback(self.choiceBoxCallback, ChoiceBox,
                                      title=get_translation("select_function"),
                                      list=choices)

    def choiceBoxCallback(self, choice):
        if choice is None:
            return
        selection = choice[1]

        if selection == "info":
            self.session.open(CiefpOscamInfo)
        elif selection == "status":
            self.session.open(CiefpOscamStatus)
        elif selection == "ecm_info":
            self.session.open(CiefpOscamEcmInfo)

        elif selection == "server_preview":
            self.session.open(CiefpOscamServerPreview)
        elif selection == "server_add":
            self.session.open(CiefpOscamServerAdd)
        elif selection == "server_emulator":
            self.session.open(CiefpOscamEmulatorAdd)
        elif selection == "server_reader_select":
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")
            lines = []
            try:
                if os.path.exists(server_path):
                    with open(server_path, "r", encoding="utf-8") as f:
                        lines = [line.rstrip() for line in f]
                else:
                    lines = [get_translation("file_not_exist")]
                self.session.open(CiefpOscamServerReaderSelect, lines)
            except Exception as e:
                self.session.open(MessageBox, get_translation("file_read_error").format(str(e)), MessageBox.TYPE_ERROR,
                                  timeout=5)

        elif selection == "softcam_key_preview":
            self.session.open(CiefpOscamSoftCamKeyPreview)
        elif selection == "add_biss_key":
            self.addBissKey()

        elif selection == "dvbapi_add":
            self.session.open(CiefpOscamEditorAdd, default_provider=self.current_provider_id)
        elif selection == "dvbapi_preview":
            self.session.open(CiefpOscamEditorPreview)

        elif selection == "conf_editor":
            self.session.open(CiefpOscamConfEditor)
        elif selection == "conf_preview":
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            conf_path = dvbapi_path.replace("oscam.dvbapi", "oscam.conf")
            self.session.open(CiefpOscamConfPreview, conf_path)

        elif selection == "user_preview":
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            user_path = dvbapi_path.replace("oscam.dvbapi", "oscam.user")
            self.session.open(CiefpOscamUserPreview, user_path)
        elif selection == "user_editor":
            self.session.open(CiefpOscamUserEditor)

    def addFreeReader(self):
        def onSourceSelected(selected):
            if not selected or not selected[1]:
                return
            selected_url, selected_name = selected[1], selected[0]
            label_name = selected_name.replace(" ", "_").lower()

            try:
                # Preuzmi C-line sa izabrane web stranice
                html = urllib.request.urlopen(selected_url, timeout=5).read().decode("utf-8", errors="ignore")
                match = re.search(r'C:\s*([\w\.-]+)\s+(\d+)\s+(\w+)\s+([^<\s]+)', html)
                if not match:
                    self.session.open(MessageBox, "C-line nije pronađena!", MessageBox.TYPE_ERROR, timeout=5)
                    return

                server, port, user, password = match.groups()
                password = re.sub(r'<.*?>', '', password)
                password = unescape(password).strip()

                # Kreiraj linije za novi reader
                reader_lines = [
                    "[reader]",
                    f"label                         = {label_name}",
                    "protocol                      = cccam",
                    f"device                        = {server},{port}",
                    f"user                          = {user}",
                    f"password                      = {password}",
                    "inactivitytimeout             = -1",
                    "cacheex                       = 1",
                    "group                         = 2",
                    "emmcache                      = 1,3,2,0",
                    "disablecrccws                 = 0",
                    "disablecrccws_only_for        = 0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000",
                    "cccversion                    = 2.0.11",
                    "cccmaxhops                    = 2",
                    "ccckeepalive                  = 1"
                ]

                # Odredi putanju oscam.server iz podešene dvbapi putanje
                dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
                server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")

                os.makedirs(os.path.dirname(server_path), exist_ok=True)
                with open(server_path, "a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(reader_lines) + "\n")

                # Restartuj OSCam
                restart_oscam()

                # ⚡ Osveži listu readera odmah, da se novi reader prikaže
                self.session.open(CiefpOscamStatus)

                # Prikaži poruku o uspehu
                self.session.open(
                    MessageBox,
                    f"Reader '{label_name}' dodat iz '{selected_name}', Oscam reloadovan.",
                    MessageBox.TYPE_INFO,
                    timeout=5
                )

            except Exception as e:
                self.session.open(MessageBox, f"Greška: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

        # Lista izvora sa kojih se mogu preuzeti free readeri
        choices = [
            (get_translation("cccamia_free"), "https://cccamia.com/cccam-free"),
            (get_translation("cccam_premium"), "https://cccam-premium.pro/free-cccam"),
            (get_translation("cccamiptv_free"), "https://cccamiptv.tv/cccamfree/#page-content"),
            (get_translation("cccamgalaxy_free"), "https://cccamgalaxy.com/"),
            (get_translation("cccam_net_free"), "https://cccam.net/freecccam"),
            (get_translation("cccamsate_free"), "https://cccamsate.com/free")
        ]

        # Otvori ChoiceBox za izbor izvora
        self.session.openWithCallback(
            onSourceSelected,
            ChoiceBox,
            title=get_translation("select_source"),
            list=choices
        )

    def get_ecm_info(self):
        ecm_path = "/tmp/ecm.info"
        ecm_data = {
            "caid": "N/A",
            "pid": "N/A",
            "prov": "000000",
            "chid": "N/A",
            "reader": "N/A",
            "from": "N/A",
            "protocol": "N/A",
            "hops": "N/A",
            "ecm_time": "N/A",
            "cw0": "N/A",
            "cw1": "N/A"
        }
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if ":" not in line:
                            continue
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == "caid":
                            ecm_data["caid"] = value.replace("0x", "").upper()
                        elif key == "pid":
                            ecm_data["pid"] = value
                        elif key == "prov":
                            ecm_data["prov"] = value
                        elif key == "chid":
                            ecm_data["chid"] = value
                        elif key == "reader":
                            ecm_data["reader"] = value
                        elif key == "from":
                            ecm_data["from"] = value
                        elif key == "protocol":
                            ecm_data["protocol"] = value
                        elif key == "hops":
                            ecm_data["hops"] = value
                        elif key == "ecm time":
                            ecm_data["ecm_time"] = value
                        elif key == "cw0":
                            ecm_data["cw0"] = value
                        elif key == "cw1":
                            ecm_data["cw1"] = value
            except Exception as e:
                print(f"Error reading ecm.info: {str(e)}")
        return ecm_data

    def updateChannelInfo(self):
        service = self.session.nav.getCurrentService()
        if service:
            info = service.info()
            name = info.getName()
            service_id = info.getInfo(iServiceInformation.sSID)
            service_id = f"{service_id:04X}" if service_id is not None else "N/A"
            caids = info.getInfoObject(iServiceInformation.sCAIDs) or []
            provider_name = info.getInfoString(iServiceInformation.sProvider) or "N/A"

            service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
            print(f"Service Reference: {service_ref and service_ref.toString() or 'None'}")
            print(f"Service ID from sSID: {service_id}")

            ecm_data = self.get_ecm_info()
            self.current_provider_id = ecm_data["prov"]

            active_caid = ecm_data["caid"]
            caids_str_list = []
            for caid in caids:
                caid_str = hex(caid)[2:].zfill(4).upper()
                if active_caid != "N/A" and caid_str == active_caid:
                    caids_str_list.append(f"{caid_str} (Active)")
                else:
                    caids_str_list.append(caid_str)
            caids_str = ", ".join(caids_str_list)

            pids = info.getInfoObject(iServiceInformation.sDVBState) or {}
            ecm_pid = pids.get("ecm_pid", "N/A")

            text = (
                f"{get_translation('channel')}: {name}\n"
                f"{get_translation('service_id')}: {service_id}\n"
                f"{get_translation('caids')}: {caids_str}\n"
                f"{get_translation('ecm_pid')}: {ecm_pid}\n"
                f"{get_translation('provider')}: {provider_name} ({ecm_data['prov']})\n"
                f"{get_translation('chid')}: {ecm_data['chid']}\n"
                f"{get_translation('reader')}: {ecm_data['reader']}\n"
                f"{get_translation('from')}: {ecm_data['from']}\n"
                f"{get_translation('protocol')}: {ecm_data['protocol']}\n"
                f"{get_translation('hops')}: {ecm_data['hops']}\n"
                f"{get_translation('ecm_time')}: {ecm_data['ecm_time']}"
            )
            self["channel_info"].setText(text)
        else:
            self["channel_info"].setText(get_translation("no_channel_info"))

    def addBissKey(self):
        """Dodaje BISS ključ za trenutni kanal sa automatskim SID i VPID"""
        # Dohvati informacije o trenutnom kanalu
        service = self.session.nav.getCurrentService()
        if not service:
            self.session.open(MessageBox, get_translation("no_channel_selected"), MessageBox.TYPE_ERROR, timeout=3)
            return

        # Dobij SID, VPID i ime kanala
        sid = self.getSID()
        vpid = self.getVPID()
        channel_name = self.getChannelName()

        # Prikaži informacije korisniku
        info_text = f"{channel_name} (SID:{sid}/VPID:{vpid}) Enter BISS Key:"

        # Pokreni VirtualKeyBoard za unos BISS ključa
        self.session.openWithCallback(
            lambda key: self.bissKeyCallback(key, sid, vpid, channel_name),
            VirtualKeyBoard,
            title=info_text,
            text=""
        )

    def bissKeyCallback(self, biss_key, sid, vpid, channel_name):
        """Callback nakon unosa BISS ključa"""
        if not biss_key:
            return

        formatted_key = biss_key.replace(" ", "").upper()

        if len(formatted_key) not in [8, 16]:
            self.session.open(
                MessageBox,
                get_translation("invalid_key_length"),
                MessageBox.TYPE_ERROR,
                timeout=3
            )
            return

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # FORMAT KOJI VAŠ OSCAM ZAHTEVA: SID + VPID
        sid_vpid = f"{sid}{vpid}"
        line = f"F {sid_vpid} 00 {formatted_key} ; {channel_name} - {current_time}\n"

        try:
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            base_dir = os.path.dirname(dvbapi_path)

            # Upis u softcam.key fajlove
            for filename in ["SoftCam.Key", "softcam.key"]:
                softcam_path = os.path.join(base_dir, filename)
                self._writeToFile(softcam_path, line, f"F {sid_vpid} 00")

            restart_oscam()

            self.session.open(
                MessageBox,
                get_translation("biss_key_added").format(channel_name),
                MessageBox.TYPE_INFO,
                timeout=3
            )

        except Exception as e:
            self.session.open(
                MessageBox,
                get_translation("biss_key_error").format(str(e)),
                MessageBox.TYPE_ERROR,
                timeout=3
            )

    def _writeToFile(self, file_path, new_line, search_pattern):
        """Upis bez duplikata"""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line for line in f if search_pattern not in line]
        else:
            lines = []

        lines.append(new_line)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def openSettings(self):
        self.session.open(CiefpOscamEditorSettings)

    def openAddDvbapi(self):
        self.session.open(CiefpOscamEditorAdd, default_provider=self.current_provider_id)

    def openServerPreview(self):
        self.session.open(CiefpOscamServerPreview)

class CiefpOscamInfo(Screen):
    skin = """
    <screen name="CiefpOscamInfo" position="center,center" size="1400,800" title="..:: OSCam Info ::..">
        <widget name="info_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_info.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self["info_list"] = MenuList([], enableWrapAround=True)
        self["info_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("status"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.openStatus,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        self.displayOscamInfo()

    def openStatus(self):
        self.session.open(CiefpOscamStatus)

    def displayOscamInfo(self):
        oscam_info = get_oscam_info()
        info_lines = [
            f"{get_translation('oscam_version')}: {oscam_info['version']}",
            f"{get_translation('build_date')}: {oscam_info['build_date']}",
            f"{get_translation('start_time')}: {oscam_info['start_time']}",
            f"{get_translation('box_type')}: {oscam_info['box_type']}",
            f"{get_translation('config_dir')}: {oscam_info['config_dir']}",
            f"{get_translation('webif_port')}: {oscam_info['webif_port']}",
            "",
            f"{get_translation('supported_features')}:",
            *[f"- {feature}" for feature in oscam_info['features']],
            "",
            f"{get_translation('supported_protocols')}:",
            *[f"- {protocol}" for protocol in oscam_info['protocols']],
            "",
            f"{get_translation('supported_readers')}:",
            *[f"- {reader}" for reader in oscam_info['readers']]
        ]
        self["info_list"].setList(info_lines)

    def moveUp(self):
        self["info_list"].up()

    def moveDown(self):
        self["info_list"].down()

class CiefpOscamEditorAdd(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamEditorAdd" position="center,center" size="1400,800" title="..:: Add dvbapi Line ::..">
        <widget name="config" position="10,10" size="980,650" scrollbarMode="showOnDemand" itemHeight="40" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/add_dvbapi.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session, default_provider="000000"):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_add_dvbapi"))
        self["key_green"] = Label(get_translation("add"))
        self["key_red"] = Label(get_translation("cancel"))
        self["key_yellow"] = Label(get_translation("preview"))
        self["key_blue"] = Label(get_translation("oscam_info_button"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.addLine,
            "red": self.close,
            "yellow": self.openPreview,
            "blue": self.openOscamInfo,
            "cancel": self.close
        }, -2)

        self.line_type = ConfigSelection(default="P:", choices=[
            ("P:", get_translation("Priority [ P: ]")),
            ("I:", get_translation("Ignore [ I: ]")),
            ("J:", get_translation("Join [ J: ]")),
            ("M:", get_translation("Map [ M: ]")),
            ("A:", get_translation("Add [ A: ]"))
        ])

        service = self.session.nav.getCurrentService()
        caid_choices = [("", get_translation("custom_caid"))]
        if service:
            caids = service.info().getInfoObject(iServiceInformation.sCAIDs) or []
            caid_choices.extend([(hex(x)[2:].zfill(4).upper(), hex(x)[2:].zfill(4).upper()) for x in caids])
        self.caid = ConfigSelection(default="", choices=caid_choices)
        self.caid2 = ConfigSelection(default="", choices=caid_choices)
        self.custom_caid = ConfigText(default="", fixed_size=False)
        self.custom_caid2 = ConfigText(default="", fixed_size=False)

        clean_provider = default_provider.lower().replace("0x", "").upper()
        self.provider = ConfigText(default=clean_provider, fixed_size=False)
        self.provider2 = ConfigText(default="000000", fixed_size=False)
        self.stari_prov = ConfigText(default="000000", fixed_size=False)
        self.novi_prov = ConfigText(default="000000", fixed_size=False)

        self.ns = ConfigText(default="", fixed_size=False)
        self.sid = ConfigText(default="", fixed_size=False)
        self.sid2 = ConfigText(default="", fixed_size=False)
        self.ecmpid = ConfigText(default="", fixed_size=False)
        self.ecmpid2 = ConfigText(default="", fixed_size=False)

        self.channel_specific = ConfigSelection(default="no", choices=[
            ("no", get_translation("no")),
            ("yes", get_translation("yes"))
        ])
        self.add_comment = ConfigSelection(default="no", choices=[
            ("no", get_translation("no")),
            ("yes", get_translation("yes"))
        ])

        self.caid.addNotifier(self.caidChanged, initial_call=False)
        self.caid2.addNotifier(self.caidChanged, initial_call=False)
        self.line_type.addNotifier(self.lineTypeChanged, initial_call=False)

        self.createSetup()

    def caidChanged(self, configElement):
        self.createSetup()

    def lineTypeChanged(self, configElement):
        self.createSetup()

    def createSetup(self):
        self.list = [getConfigListEntry(get_translation("line_type"), self.line_type)]
        
        if self.line_type.value in ["P:", "I:"]:
            self.list.extend([
                getConfigListEntry(get_translation("caid"), self.caid),
                getConfigListEntry(get_translation("custom_caid"), self.custom_caid) if self.caid.value == "" else None,
                getConfigListEntry(get_translation("provider"), self.provider),
                getConfigListEntry(get_translation("channel_specific"), self.channel_specific),
                getConfigListEntry(get_translation("add_comment"), self.add_comment)
            ])
        elif self.line_type.value == "A:":
            self.list.extend([
                getConfigListEntry(get_translation("ns"), self.ns),
                getConfigListEntry(get_translation("sid"), self.sid),
                getConfigListEntry(get_translation("ecmpid"), self.ecmpid),
                getConfigListEntry(get_translation("caid"), self.caid),
                getConfigListEntry(get_translation("custom_caid"), self.custom_caid) if self.caid.value == "" else None,
                getConfigListEntry(get_translation("provider"), self.provider),
                getConfigListEntry(get_translation("add_comment"), self.add_comment)
            ])
        elif self.line_type.value == "J:":
            self.list.extend([
                getConfigListEntry(get_translation("caid1"), self.caid),
                getConfigListEntry(get_translation("custom_caid"), self.custom_caid) if self.caid.value == "" else None,
                getConfigListEntry(get_translation("provider1"), self.provider),
                getConfigListEntry(get_translation("sid"), self.sid),
                getConfigListEntry(get_translation("ecmpid1"), self.ecmpid),
                getConfigListEntry(get_translation("caid2"), self.caid2),
                getConfigListEntry(get_translation("custom_caid2"), self.custom_caid2) if self.caid2.value == "" else None,
                getConfigListEntry(get_translation("provider2"), self.provider2),
                getConfigListEntry(get_translation("ecmpid2"), self.ecmpid2),
                getConfigListEntry(get_translation("add_comment"), self.add_comment)
            ])
        elif self.line_type.value == "M:":
            self.list.extend([
                getConfigListEntry(get_translation("caid"), self.caid),
                getConfigListEntry(get_translation("custom_caid"), self.custom_caid) if self.caid.value == "" else None,
                getConfigListEntry(get_translation("old_provider"), self.stari_prov),
                getConfigListEntry(get_translation("sid"), self.sid),
                getConfigListEntry(get_translation("caid2"), self.caid2),
                getConfigListEntry(get_translation("custom_caid2"), self.custom_caid2) if self.caid2.value == "" else None,
                getConfigListEntry(get_translation("new_provider"), self.novi_prov),
                getConfigListEntry(get_translation("sid2"), self.sid2),
                getConfigListEntry(get_translation("add_comment"), self.add_comment)
            ])

        self.list = [entry for entry in self.list if entry is not None]
        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def addLine(self):
        line_type = self.line_type.value
        caid = self.custom_caid.value.lower().replace("0x", "").upper() if self.caid.value == "" else self.caid.value.lower().replace("0x", "").upper()
        provider = self.provider.value.lower().replace("0x", "").upper()
        channel_specific = self.channel_specific.value == "yes"
        add_comment = self.add_comment.value == "yes"
        service = self.session.nav.getCurrentService()
        service_id = service and service.info().getInfo(iServiceInformation.sSID) or ""
        channel_name = service and service.info().getName() or "Unknown"

        if line_type in ["P:", "I:"]:
            line = f"{line_type} {caid}:{provider}"
            if channel_specific and service_id:
                line += f":{service_id:04X}"
        elif line_type == "A:":
            ns = self.ns.value.strip().lower().replace("0x", "").upper()
            sid = self.sid.value.strip().lower().replace("0x", "").upper()
            ecmpid = self.ecmpid.value.strip().lower().replace("0x", "").upper()
            ns_field = ns if ns else ""
            sid_field = sid if sid else ""
            ecmpid_field = ecmpid if ecmpid else ""
            line = f"{line_type} ::{sid_field}:{ecmpid_field}:: {caid}:{provider}:1FFF"
        elif line_type == "J:":
            caid2 = self.custom_caid2.value.lower().replace("0x", "").upper() if self.caid2.value == "" else self.caid2.value.lower().replace("0x", "").upper()
            provider2 = self.provider2.value.lower().replace("0x", "").upper()
            sid = self.sid.value.lower().replace("0x", "").upper()
            ecmpid = self.ecmpid.value.lower().replace("0x", "").upper()
            ecmpid2 = self.ecmpid2.value.lower().replace("0x", "").upper()
            line = f"{line_type} {caid}:{provider}:{sid}:{ecmpid} {caid2}:{provider2}:{ecmpid2}"
        elif line_type == "M:":
            stari_prov = self.stari_prov.value.lower().replace("0x", "").upper()
            caid2 = self.custom_caid2.value.lower().replace("0x", "").upper() if self.caid2.value == "" else self.caid2.value.lower().replace("0x", "").upper()
            novi_prov = self.novi_prov.value.lower().replace("0x", "").upper()
            sid = self.sid.value.lower().replace("0x", "").upper()
            sid2 = self.sid2.value.lower().replace("0x", "").upper()
            line = f"{line_type} {caid}:{stari_prov}:{sid} {caid2}:{novi_prov}:{sid2}"

        if add_comment and line_type in ["P:", "I:", "A:", "J:", "M:"]:
            line += f" # {channel_name}"

        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        try:
            if not os.path.exists(dvbapi_path):
                os.makedirs(os.path.dirname(dvbapi_path), exist_ok=True)
                with open(dvbapi_path, "w") as f:
                    f.write("## Created by CiefpOscamEditor ##\n")
                    f.write("## ..:: CiefpSettings ::.. ##\n\n")

            with open(dvbapi_path, "a") as f:
                f.write(line + "\n")
            self.session.open(MessageBox, get_translation("line_added").format(dvbapi_path, line), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        except Exception as e:
            self.session.open(MessageBox, get_translation("write_error").format(dvbapi_path, str(e)), MessageBox.TYPE_ERROR)

    def openPreview(self):
        self.session.open(CiefpOscamEditorPreview)

    def openOscamInfo(self):
        self.session.open(CiefpOscamInfo)

class CiefpOscamEditorPreview(Screen):
    skin = """
    <screen name="CiefpOscamEditorPreview" position="center,center" size="1400,800" title="..:: oscam.dvbapi Preview ::..">
        <widget name="file_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_blue" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_dvbapi_preview.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(get_translation("title_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_blue"] = Label(get_translation("delete"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.saveFile,
            "blue": self.deleteLine,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        self.lines = []
        self.loadFile()

    def loadFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        self.lines = []
        try:
            if os.path.exists(dvbapi_path):
                with open(dvbapi_path, "r", encoding="utf-8") as f:
                    self.lines = [line.strip() for line in f if line.strip()]
            else:
                self.lines = [get_translation("file_not_exist")]
            self["file_list"].setList(self.lines)
        except Exception as e:
            self["file_list"].setList([get_translation("file_read_error").format(str(e))])

    def saveFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        try:
            with open(dvbapi_path, "w", encoding="utf-8") as f:
                for line in self.lines:
                    f.write(line + "\n")
            self.session.open(MessageBox, get_translation("file_saved").format(dvbapi_path), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        except Exception as e:
            self.session.open(MessageBox, get_translation("file_save_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

    def deleteLine(self):
        current_index = self["file_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.lines):
            line = self.lines[current_index]
            self.session.openWithCallback(
                lambda confirmed: self.deleteLineConfirmed(confirmed, current_index),
                MessageBox,
                get_translation("delete_line_confirm").format(line),
                MessageBox.TYPE_YESNO
            )

    def deleteLineConfirmed(self, confirmed, index):
        if confirmed:
            del self.lines[index]
            self["file_list"].setList(self.lines)

    def moveUp(self):
        self["file_list"].up()

    def moveDown(self):
        self["file_list"].down()

class CiefpOscamServerPreview(Screen):
    skin = """
    <screen name="CiefpOscamServerPreview" position="center,center" size="1400,800" title="..:: oscam.server Preview ::..">
        <widget name="file_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_server_preview.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(get_translation("title_server_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("free_cccam"))
        self["key_yellow"] = Label(get_translation("add_reader"))
        self["key_blue"] = Label(get_translation("delete"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.addFreeReader,
            "yellow": self.addReader,
            "blue": self.deleteReader,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        self.lines = []
        self.loadFile()

    def loadFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")
        self.lines = []
        try:
            if os.path.exists(server_path):
                with open(server_path, "r", encoding="utf-8") as f:
                    self.lines = [line.strip() for line in f if line.strip()]
            else:
                self.lines = [get_translation("file_not_exist")]
            self["file_list"].setList(self.lines)
        except Exception as e:
            self["file_list"].setList([get_translation("file_read_error").format(str(e))])

    def addReader(self):
        self.session.open(CiefpOscamServerAdd)

    def deleteReader(self):
        self.session.openWithCallback(self.updateLines, CiefpOscamServerReaderSelect, self.lines)


    def addFreeReader(self):
        def onSourceSelected(selected):
            if not selected or not selected[1]:
                return
            selected_url, selected_name = selected[1], selected[0]
            label_name = selected_name.replace(" ", "_").lower()

            try:
                # Preuzmi C-line sa izabrane web stranice
                html = urllib.request.urlopen(selected_url, timeout=5).read().decode("utf-8", errors="ignore")
                match = re.search(r'C:\s*([\w\.-]+)\s+(\d+)\s+(\w+)\s+([^<\s]+)', html)
                if not match:
                    self.session.open(MessageBox, "C-line nije pronađena!", MessageBox.TYPE_ERROR, timeout=5)
                    return

                server, port, user, password = match.groups()
                password = re.sub(r'<.*?>', '', password)
                password = unescape(password).strip()

                # Kreiraj linije za novi reader
                reader_lines = [
                    "[reader]",
                    f"label                         = {label_name}",
                    "protocol                      = cccam",
                    f"device                        = {server},{port}",
                    f"user                          = {user}",
                    f"password                      = {password}",
                    "inactivitytimeout             = -1",
                    "cacheex                       = 1",
                    "group                         = 2",
                    "emmcache                      = 1,3,2,0",
                    "disablecrccws                 = 0",
                    "disablecrccws_only_for        = 0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000",
                    "cccversion                    = 2.0.11",
                    "cccmaxhops                    = 2",
                    "ccckeepalive                  = 1"
                ]

                # Odredi putanju oscam.server iz podešene dvbapi putanje
                dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
                server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")

                os.makedirs(os.path.dirname(server_path), exist_ok=True)
                with open(server_path, "a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(reader_lines) + "\n")

                # Restartuj OSCam
                restart_oscam()

                # ⚡ Osveži listu readera odmah, da se novi reader prikaže
                self.session.open(CiefpOscamStatus)

                # Prikaži poruku o uspehu
                self.session.open(
                    MessageBox,
                    f"Reader '{label_name}' dodat iz '{selected_name}', Oscam reloadovan.",
                    MessageBox.TYPE_INFO,
                    timeout=5
                )

            except Exception as e:
                self.session.open(MessageBox, f"Greška: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

        # Lista izvora sa kojih se mogu preuzeti free readeri
        choices = [
            (get_translation("cccamia_free"), "https://cccamia.com/cccam-free"),
            (get_translation("cccam_premium"), "https://cccam-premium.pro/free-cccam"),
            (get_translation("cccamiptv_free"), "https://cccamiptv.tv/cccamfree/#page-content"),
            (get_translation("cccamgalaxy_free"), "https://cccamgalaxy.com/"),
            (get_translation("cccam_net_free"), "https://cccam.net/freecccam"),
            (get_translation("cccamsate_free"), "https://cccamsate.com/free")
        ]

        # Otvori ChoiceBox za izbor izvora
        self.session.openWithCallback(
            onSourceSelected,
            ChoiceBox,
            title=get_translation("select_source"),
            list=choices
        )

    def updateLines(self, updated_lines):
        if updated_lines:
            self.lines = updated_lines
            self["file_list"].setList(self.lines)

    def moveUp(self):
        self["file_list"].up()

    def moveDown(self):
        self["file_list"].down()
        
class CiefpOscamEmulatorAdd(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamEmulatorAdd" position="center,center" size="1400,800" title="..:: Add Emulator  ::..">
        <widget name="config" position="10,10" size="980,650" scrollbarMode="showOnDemand" itemHeight="40" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />"
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08500" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/add_emulator.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_add_emulator"))
        
        # Dugmici
        self["key_red"] = Label(get_translation("cancel"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("key_source"))
        self["background"] = Pixmap()
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.save,
            "yellow": self.changeKeySource,
            "cancel": self.close
        }, -2)

        # Konfiguracione varijable za Emulator
        self.label = ConfigText(default="emulator", fixed_size=False)
        self.enable = ConfigSelection(default="1", choices=[("1", get_translation("enabled")), ("0", get_translation("disabled"))])
        self.key_source = ConfigSelection(default="online", choices=[
            ("online", get_translation("online_source")),
            ("local", get_translation("local_source"))
        ])
        self.caid = ConfigText(default="0500,0E00,1010,2600", fixed_size=False)
        self.ident = ConfigText(default="0500:021110;0E00:000000;1010:000000;2600:000000", fixed_size=False)
        self.group = ConfigSelection(default="1", choices=[str(i) for i in range(1, 11)])
        self.emmcache = ConfigSelection(default="2,1,2,1", choices=["2,1,2,1", "1,3,2,0", "1,5,2,0"])
        self.emu_auproviders = ConfigText(default="0E00:000000;1010:000000", fixed_size=False)
        self.detect = ConfigSelection(default="cd", choices=[("cd", "cd"), ("ff", "ff")])

        # Parametri za ConstantCW reader (sakriveni ako je isključen)
        self.enable_constantcw = ConfigYesNo(default=False)
        self.constantcw_label = ConfigText(default="myconstantcw", fixed_size=False)
        self.constantcw_path = ConfigText(default="/etc/tuxbox/config/oscam-emu/constant.cw", fixed_size=False)
        self.constantcw_caid = ConfigText(default="0D00,0D02,090F,0500,1801,0604,2600,FFFF,0E00,4AE1,1010", fixed_size=False)
        self.constantcw_group = ConfigSelection(default="2", choices=[str(i) for i in range(1, 11)])

        # Postavi notifier za dinamičko ažuriranje
        self.enable_constantcw.addNotifier(self.configChanged)
        self.createSetup()

    def configChanged(self, configElement):
        """Callback kada se promeni enable_constantcw"""
        self.createSetup()

    def createSetup(self):
        self.list = [
            getConfigListEntry("=== Emulator Reader ===", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("label") + ":", self.label),
            getConfigListEntry(get_translation("enable") + ":", self.enable),
            getConfigListEntry(get_translation("key_source") + ":", self.key_source),
            getConfigListEntry(get_translation("caid") + ":", self.caid),
            getConfigListEntry(get_translation("ident") + ":", self.ident),
            getConfigListEntry(get_translation("detect") + ":", self.detect),
            getConfigListEntry(get_translation("group") + ":", self.group),
            getConfigListEntry(get_translation("emmcache") + ":", self.emmcache),
            getConfigListEntry(get_translation("emu_auproviders") + ":", self.emu_auproviders),
            
            getConfigListEntry("=== ConstantCW Reader ===", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("enable_constantcw") + ":", self.enable_constantcw)
        ]

        # Prikaži ConstantCW opcije samo ako je omogućen
        if self.enable_constantcw.value:
            self.list.extend([
                getConfigListEntry(get_translation("label") + ":", self.constantcw_label),
                getConfigListEntry(get_translation("constantcw_path") + ":", self.constantcw_path),
                getConfigListEntry(get_translation("caid") + ":", self.constantcw_caid),
                getConfigListEntry(get_translation("group") + ":", self.constantcw_group)
            ])

        self["config"].list = self.list
    

    def changeKeySource(self):
        self.key_source.value = "online" if self.key_source.value == "local" else "local"
        self.createSetup()

    def save(self):
        reader_lines = []

        # Emulator reader
        if self.enable.value == "1":
            oscam_info = get_oscam_info()
            config_dir = oscam_info.get("config_dir", "/etc/tuxbox/config")

            online_url = "https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/main/SoftCam.Key"

            reader_lines.extend([
                "[reader]",
                f"label                         = {self.label.value}",
                f"enable                        = {self.enable.value}",
                f"protocol                      = emu",
                f"device                        = emulator"
            ])

            # Ako je online izvor → dodaj URL u device
            if self.key_source.value == "online":
                reader_lines.append(
                    f"device                        = {online_url}  # online softcamkey"
                )
            else:
                # Ako je lokalni izvor → pobrini se da postoje oba fajla (SoftCam.Key i softcam.key)
                dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
                base_dir = os.path.dirname(dvbapi_path)
                path1 = os.path.join(base_dir, "SoftCam.Key")
                path2 = os.path.join(base_dir, "softcam.key")

                for path in [path1, path2]:
                    if not os.path.exists(path):
                        try:
                            os.makedirs(os.path.dirname(path), exist_ok=True)
                            with open(path, "w", encoding="utf-8") as f:
                                f.write("## Created by CiefpOscamEditor ##\n")
                        except Exception as e:
                            print(f"[CiefpOscamEditor] Greška pri kreiranju {path}: {e}")

            reader_lines.extend([
                f"caid                          = {self.caid.value}",
                f"detect                        = {self.detect.value}",
                f"ident                         = {self.ident.value}",
                f"group                         = {self.group.value}",
                f"emmcache                      = {self.emmcache.value}",
                f"emu_auproviders               = {self.emu_auproviders.value}",
                ""  # Prazan red na kraju reader-a
            ])

        # ConstantCW reader (samo ako je omogućen)
        if self.enable_constantcw.value:
            reader_lines.extend([
                "[reader]",
                f"label                         = {self.constantcw_label.value}",
                f"protocol                      = constcw",
                f"device                        = {self.constantcw_path.value}",
                f"caid                          = {self.constantcw_caid.value}",
                f"group                         = {self.constantcw_group.value}",
                ""  # Prazan red na kraju reader-a
            ])

        # Snimanje u oscam.server
        if reader_lines:
            server_path = config.plugins.CiefpOscamEditor.dvbapi_path.value.replace("oscam.dvbapi", "oscam.server")
            try:
                os.makedirs(os.path.dirname(server_path), exist_ok=True)

                # Proveri da li fajl već postoji i da li ima sadržaja
                file_exists = os.path.exists(server_path) and os.path.getsize(server_path) > 0

                with open(server_path, "a", encoding="utf-8") as f:
                    if file_exists and reader_lines:
                        f.write("\n")
                    f.write("\n".join(reader_lines))

                self.session.open(MessageBox, "Čitač uspešno dodat!", MessageBox.TYPE_INFO, timeout=5)
                self.close()
            except Exception as e:
                self.session.open(MessageBox, f"Greška: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

class CiefpOscamServerAdd(Screen, ConfigListScreen):
    skin = """<screen name="CiefpOscamServerAdd" position="center,center" size="1400,800" title="..:: Add Reader ::..">
        <widget name="config" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/add_reader.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("add_reader_title"))

        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("add_emulator"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.save,
            "yellow": self.addEmulator,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)

        #Ispravljeno: sid umjesto caid
        self.sid = ConfigText(default="0001", fixed_size=False)
        self.provid = ConfigText(default="00", fixed_size=False)
        self.channel_name = ConfigText(default="", fixed_size=False)

        self.emulator_name = ConfigText(default="new_emulator", fixed_size=False)

        # Osnovne postavke čitača
        self.label = ConfigText(default="", fixed_size=False)
        self.protocol = ConfigSelection(default="cccam", choices=[
            ("cccam", get_translation("protocol") + ": cccam"),
            ("cccam_mcs", get_translation("protocol") + ": cccam_mcs"),
            ("mgcamd", get_translation("protocol") + ": mgcamd")
        ])
        self.device = ConfigText(default="", fixed_size=False)
        self.user = ConfigText(default="", fixed_size=False)
        self.password = ConfigText(default="", fixed_size=False)

        # Mgcamd specifične postavke
        self.deskey = ConfigText(default="01 02 03 04 05 06 07 08 09 10 11 12 13 14", fixed_size=False)

        # CCCam specifične postavke
        self.cccversion = ConfigSelection(default="2.3.0", choices=[
            ("2.0.11", "2.0.11"), ("2.1.1", "2.1.1"), ("2.1.2", "2.1.2"),
            ("2.1.3", "2.1.3"), ("2.1.4", "2.1.4"), ("2.2.0", "2.2.0"),
            ("2.2.1", "2.2.1"), ("2.3.0", "2.3.0"), ("2.3.1", "2.3.1"),
            ("2.3.2", "2.3.2")
        ])
        self.cccmaxhops = ConfigSelection(default="2", choices=[
            ("1", "1"), ("2", "2"), ("3", "3")
        ])
        self.ccckeepalive = ConfigSelection(default="1", choices=[
            ("0", "0"), ("1", "1")
        ])

        # Napredne postavke
        self.inactivitytimeout = ConfigSelection(default="-1", choices=[
            ("-1", "-1"), ("0", "0"), ("30", "30"), ("60", "60")
        ])
        self.group = ConfigSelection(default="1", choices=[
            ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
            ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10")
        ])
        self.cacheex = ConfigSelection(default="1", choices=[
            ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")
        ])
        self.emmcache = ConfigSelection(default="1,3,2,0", choices=[
            ("1,3,2,0", "1,3,2,0"),
            ("1,5,2,0", "1,5,2,0"),
            ("1,1,2,0", "1,1,2,0")
        ])
        self.disablecrccws = ConfigSelection(default="0", choices=[
            ("0", "0"), ("1", "1")
        ])
        self.disablecrccws_only_for = ConfigText(
            default="0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000",
            fixed_size=False
        )

        self.autoPopulateFromCurrentService()
        self.protocol.addNotifier(self.protocolChanged, initial_call=True)
        self.createSetup()
        self["config"].onSelectionChanged.append(self.onSelectionChanged)

    def autoPopulateFromCurrentService(self):
        service = self.session.nav.getCurrentService()
        if not service:
            return

        info = service.info()
        if not info:
            return

        #Ispravno: dohvati pravi SID
        sid = info.getInfo(iServiceInformation.sSID)
        if sid != -1:
            self.sid.value = "%04X" % sid  # → npr. 0001
        else:
            self.sid.value = "0001"

        # Naziv kanala
        channel_name = info.getName() or "Unknown Channel"
        try:
            channel_name = channel_name.encode('utf-8', 'ignore').decode('utf-8')
        except:
            pass
        self.channel_name.value = f"{channel_name} at 7.0E"

        # PROVID = 00 za BISS
        self.provid.value = "00"

    def addEmulator(self):
        self.session.open(CiefpOscamEmulatorAdd)

    def protocolChanged(self, configElement):
        self.createSetup()

    def createSetup(self):
        self.list = [
            getConfigListEntry(get_translation("label") + ":", self.label),
            getConfigListEntry(get_translation("protocol") + ":", self.protocol),
            getConfigListEntry(get_translation("device") + ":", self.device),
        ]

        if self.protocol.value == "mgcamd":
            self.list.append(getConfigListEntry(get_translation("deskey") + ":", self.deskey))

        self.list.extend([
            getConfigListEntry(get_translation("user") + ":", self.user),
            getConfigListEntry(get_translation("password") + ":", self.password),
        ])

        self.list.extend([
            getConfigListEntry(get_translation("inactivity_timeout") + ":", self.inactivitytimeout),
            getConfigListEntry(get_translation("group") + ":", self.group),
            getConfigListEntry(get_translation("cacheex") + ":", self.cacheex),
            getConfigListEntry(get_translation("emm_cache") + ":", self.emmcache),
            getConfigListEntry(get_translation("disable_crc_cws") + ":", self.disablecrccws),
            getConfigListEntry(get_translation("disable_crc_cws_only_for") + ":", self.disablecrccws_only_for)
        ])

        if self.protocol.value in ["cccam", "cccam_mcs"]:
            self.list.extend([
                getConfigListEntry(get_translation("ccc_version") + ":", self.cccversion),
                getConfigListEntry(get_translation("ccc_max_hops") + ":", self.cccmaxhops),
                getConfigListEntry(get_translation("ccc_keep_alive") + ":", self.ccckeepalive),
            ])


        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def save(self):
        reader_lines = [
            "[reader]",
            f"label                         = {self.label.value}",
            f"protocol                      = {self.protocol.value}",
            f"device                        = {self.device.value}",
        ]

        if self.protocol.value == "mgcamd":
            reader_lines.append(f"deskey                        = {self.deskey.value.strip()}")

        reader_lines.extend([
            f"user                          = {self.user.value}",
            f"password                      = {self.password.value}",
        ])

        reader_lines.extend([
            f"inactivitytimeout             = {self.inactivitytimeout.value}",
            f"group                         = {self.group.value}",
            f"cacheex                       = {self.cacheex.value}",
            f"emmcache                      = {self.emmcache.value}",
            f"disablecrccws                 = {self.disablecrccws.value}",
            f"disablecrccws_only_for        = {self.disablecrccws_only_for.value}"
        ])

        if self.protocol.value in ["cccam", "cccam_mcs"]:
            reader_lines.extend([
                f"cccversion                    = {self.cccversion.value}",
                f"cccmaxhops                    = {self.cccmaxhops.value}",
                f"ccckeepalive                  = {self.ccckeepalive.value}",
            ])

        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")
        try:
            os.makedirs(os.path.dirname(server_path), exist_ok=True)
            with open(server_path, "a", encoding="utf-8") as f:
                f.write("\n")
                for line in reader_lines:
                    f.write(line + "\n")
            print(f"Reader added to {server_path}")
            self.session.open(MessageBox, get_translation("reader_added").format(server_path), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        except Exception as e:
            print(f"Error saving reader: {str(e)}")
            self.session.open(MessageBox, get_translation("reader_add_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

    def moveUp(self):
        self["config"].instance.moveSelection(self["config"].instance.moveUp)

    def moveDown(self):
        self["config"].instance.moveSelection(self["config"].instance.moveDown)

    def onSelectionChanged(self):
        current = self["config"].getCurrent()
        if not current:
            return

class CiefpOscamServerReaderSelect(Screen):
    skin = """
    <screen name="CiefpOscamServerReaderSelect" position="center,center" size="1400,800" title="..:: Delete Reader ::..">
        <widget name="reader_list" position="10,10" size="980,650" font="Regular;26" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08500" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/delete_reader.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session, lines):
        Screen.__init__(self, session)
        self.session = session
        self.lines = lines[:]
        self.readers = []
        self.setTitle(get_translation("title_reader_select"))
        self["reader_list"] = MenuList([], enableWrapAround=True)
        self["reader_list"].l.setItemHeight(35)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("delete"))
        self["key_blue"] = Label(get_translation("edit"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["ColorActions", "SetupActions"], {
            "red": self.closeWithCallback,
            "green": self.saveFile,
            "yellow": self.deleteReader,
            "blue": self.editReader,
            "cancel": self.closeWithCallback,
            "ok": self.selectReader,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        print("DEBUG: ActionMap initialized with contexts: ['ColorActions', 'SetupActions']")
        print("DEBUG: ActionMap bindings: red=closeWithCallback, green=saveFile, yellow=deleteReader, blue=editReader, cancel=closeWithCallback, ok=selectReader, up=moveUp, down=moveDown")
        self.loadReaders()

    def loadReaders(self):
        self.readers = []
        try:
            current_reader = None
            start_index = None
            for i, line in enumerate(self.lines):
                line = line.strip()
                if line.startswith("[reader]"):
                    if current_reader is not None:
                        self.readers.append((current_reader, start_index, i))
                    current_reader = None
                    start_index = i
                elif line.startswith("label") and "=" in line:
                    current_reader = line.split("=", 1)[1].strip()
            if current_reader is not None:
                self.readers.append((current_reader, start_index, len(self.lines)))
            reader_labels = [reader[0] for reader in self.readers if reader[0]]
            if not reader_labels:
                reader_labels = [get_translation("no_readers")]
            self["reader_list"].setList(reader_labels)
            print(f"Loaded readers: {reader_labels}")
            print(f"Reader boundaries: {self.readers}")
        except Exception as e:
            self["reader_list"].setList([get_translation("file_read_error").format(str(e))])
            print(f"Error loading readers: {str(e)}")

    def moveUp(self):
        self["reader_list"].up()

    def moveDown(self):
        self["reader_list"].down()

    def selectReader(self):
        print("DEBUG: selectReader called")
        pass

    def deleteReader(self):
        print("DEBUG: deleteReader called")
        current_index = self["reader_list"].getSelectionIndex()
        print(f"DEBUG: Current index: {current_index}, Readers: {len(self.readers)}")
        if current_index >= 0 and current_index < len(self.readers) and self.readers[current_index][0]:
            reader_label, start_index, end_index = self.readers[current_index]
            print(f"DEBUG: Selected reader: '{reader_label}', start_index: {start_index}, end_index: {end_index}")
            print(f"DEBUG: Lines to delete: {self.lines[start_index:end_index]}")
            self.session.openWithCallback(
                lambda confirmed: self.deleteReaderConfirmed(confirmed, current_index, reader_label, start_index, end_index),
                MessageBox,
                get_translation("delete_reader_confirm").format(reader_label),
                MessageBox.TYPE_YESNO
            )
        else:
            print("DEBUG: Invalid selection or no readers available")
            self.session.open(MessageBox, get_translation("no_readers"), MessageBox.TYPE_ERROR, timeout=5)

    def deleteReaderConfirmed(self, confirmed, index, reader_label, start_index, end_index):
        print(f"DEBUG: deleteReaderConfirmed called with confirmed={confirmed}, index={index}, reader_label='{reader_label}'")
        if confirmed:
            print(f"DEBUG: Before deletion: {len(self.lines)} lines, {len(self.readers)} readers")
            del self.lines[start_index:end_index]
            del self.readers[index]
            print(f"DEBUG: After deletion: {len(self.lines)} lines, {len(self.readers)} readers")
            reader_labels = [reader[0] for reader in self.readers if reader[0]]
            if not reader_labels:
                reader_labels = [get_translation("no_readers")]
            self["reader_list"].setList(reader_labels)
            print(f"DEBUG: Updated reader labels: {reader_labels}")
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")
            try:
                os.makedirs(os.path.dirname(server_path), exist_ok=True)
                with open(server_path, "w", encoding="utf-8") as f:
                    for line in self.lines:
                        f.write(line + "\n")
                print(f"DEBUG: Reader '{reader_label}' deleted and saved to {server_path}")
                self.session.open(MessageBox, get_translation("reader_deleted").format(reader_label), MessageBox.TYPE_INFO, timeout=5)
            except Exception as e:
                print(f"DEBUG: Error saving file: {str(e)}")
                self.session.open(MessageBox, get_translation("file_save_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)
        else:
            print(f"DEBUG: Deletion of reader '{reader_label}' cancelled")

    def editReader(self):
        print("DEBUG: editReader called")
        current_index = self["reader_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.readers) and self.readers[current_index][0]:
            reader_label, start_index, end_index = self.readers[current_index]
            reader_lines = self.lines[start_index:end_index]
            self.session.openWithCallback(
                self.updateReaderCallback,
                CiefpOscamServerEdit,
                reader_lines,
                start_index,
                end_index
            )
        else:
            self.session.open(MessageBox, get_translation("no_reader_selected"), MessageBox.TYPE_ERROR, timeout=5)

    def updateReaderCallback(self, result):
        if result:
            start_index, end_index, new_lines = result
            self.lines[start_index:end_index] = new_lines
            self.loadReaders()
            self.session.open(MessageBox, get_translation("reader_updated"), MessageBox.TYPE_INFO, timeout=5)

    def saveFile(self):
        print("DEBUG: saveFile called")
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")
        try:
            os.makedirs(os.path.dirname(server_path), exist_ok=True)
            with open(server_path, "w", encoding="utf-8") as f:
                for line in self.lines:
                    f.write(line + "\n")
            print(f"DEBUG: File saved: {server_path} with {len(self.lines)} lines")
            self.session.open(MessageBox, get_translation("file_saved").format(server_path), MessageBox.TYPE_INFO, timeout=5)
            self.closeWithCallback()
        except Exception as e:
            print(f"DEBUG: Error saving file: {str(e)}")
            self.session.open(MessageBox, get_translation("file_save_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

    def closeWithCallback(self):
        print("DEBUG: closeWithCallback called")
        self.close(self.lines)

class CiefpOscamServerEdit(Screen, ConfigListScreen):
    skin = """<screen name="CiefpOscamServerEdit" position="center,center" size="1400,800" title="..:: Edit Reader ::..">
        <widget name="config" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/edit_reader.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session, reader_lines, start_index, end_index):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.reader_lines = reader_lines
        self.start_index = start_index
        self.end_index = end_index
        self.setTitle(get_translation("edit_reader_title"))

        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("add_reader"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.cancel,
            "green": self.save,
            "yellow": self.addReader,
            "cancel": self.cancel,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)

        # Osnovne postavke čitača
        self.label = ConfigText(default="", fixed_size=False)
        self.protocol = ConfigSelection(default="cccam", choices=[
            ("cccam", get_translation("protocol") + ": cccam"),
            ("cccam_mcs", get_translation("protocol") + ": cccam_mcs"),
            ("mgcamd", get_translation("protocol") + ": mgcamd")
        ])
        self.device = ConfigText(default="", fixed_size=False)
        self.user = ConfigText(default="", fixed_size=False)
        self.password = ConfigText(default="", fixed_size=False)

        # Mgcamd specifične postavke
        self.deskey = ConfigText(default="01 02 03 04 05 06 07 08 09 10 11 12 13 14", fixed_size=False)

        # CCCam specifične postavke
        self.cccversion = ConfigSelection(default="2.3.0", choices=[
            ("2.0.11", "2.0.11"), ("2.1.1", "2.1.1"), ("2.1.2", "2.1.2"),
            ("2.1.3", "2.1.3"), ("2.1.4", "2.1.4"), ("2.2.0", "2.2.0"),
            ("2.2.1", "2.2.1"), ("2.3.0", "2.3.0"), ("2.3.1", "2.3.1"),
            ("2.3.2", "2.3.2")
        ])
        self.cccmaxhops = ConfigSelection(default="2", choices=[
            ("1", "1"), ("2", "2"), ("3", "3")
        ])
        self.ccckeepalive = ConfigSelection(default="1", choices=[
            ("0", "0"), ("1", "1")
        ])

        # Napredne postavke
        self.inactivitytimeout = ConfigSelection(default="-1", choices=[
            ("-1", "-1"), ("0", "0"), ("30", "30"), ("60", "60")
        ])
        self.group = ConfigSelection(default="1", choices=[
            ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
            ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10")
        ])
        self.cacheex = ConfigSelection(default="1", choices=[
            ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")
        ])
        self.emmcache = ConfigSelection(default="1,3,2,0", choices=[
            ("1,3,2,0", "1,3,2,0"),
            ("1,5,2,0", "1,5,2,0"),
            ("1,1,2,0", "1,1,2,0")
        ])
        self.disablecrccws = ConfigSelection(default="0", choices=[
            ("0", "0"), ("1", "1")
        ])
        self.disablecrccws_only_for = ConfigText(
            default="0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000",
            fixed_size=False
        )

        self.protocol.addNotifier(self.protocolChanged, initial_call=True)
        self.parseReaderLines()
        self.createSetup()
        self["config"].onSelectionChanged.append(self.onSelectionChanged)

    def parseReaderLines(self):
        for line in self.reader_lines:
            line = line.strip()
            if "=" in line:
                key, value = [part.strip() for part in line.split("=", 1)]
                key_lower = key.lower()
                if key_lower == "label":
                    self.label.value = value
                elif key_lower == "protocol":
                    self.protocol.value = value
                elif key_lower == "device":
                    self.device.value = value
                elif key_lower == "user":
                    self.user.value = value
                elif key_lower == "password":
                    self.password.value = value
                elif key_lower == "deskey":
                    self.deskey.value = value
                elif key_lower == "cccversion":
                    self.cccversion.value = value
                elif key_lower == "cccmaxhops":
                    self.cccmaxhops.value = value
                elif key_lower == "ccckeepalive":
                    self.ccckeepalive.value = value
                elif key_lower == "inactivitytimeout":
                    self.inactivitytimeout.value = value
                elif key_lower == "group":
                    self.group.value = value
                elif key_lower == "cacheex":
                    self.cacheex.value = value
                elif key_lower == "emmcache":
                    self.emmcache.value = value
                elif key_lower == "disablecrccws":
                    self.disablecrccws.value = value
                elif key_lower == "disablecrccws_only_for":
                    self.disablecrccws_only_for.value = value

    def addReader(self):
        self.session.open(CiefpOscamServerAdd)

    def protocolChanged(self, configElement):
        self.createSetup()

    def createSetup(self):
        self.list = [
            getConfigListEntry(get_translation("label") + ":", self.label),
            getConfigListEntry(get_translation("protocol") + ":", self.protocol),
            getConfigListEntry(get_translation("device") + ":", self.device),
        ]

        if self.protocol.value == "mgcamd":
            self.list.append(getConfigListEntry(get_translation("deskey") + ":", self.deskey))

        self.list.extend([
            getConfigListEntry(get_translation("user") + ":", self.user),
            getConfigListEntry(get_translation("password") + ":", self.password),
        ])

        self.list.extend([
            getConfigListEntry(get_translation("inactivity_timeout") + ":", self.inactivitytimeout),
            getConfigListEntry(get_translation("group") + ":", self.group),
            getConfigListEntry(get_translation("cacheex") + ":", self.cacheex),
            getConfigListEntry(get_translation("emm_cache") + ":", self.emmcache),
            getConfigListEntry(get_translation("disable_crc_cws") + ":", self.disablecrccws),
            getConfigListEntry(get_translation("disable_crc_cws_only_for") + ":", self.disablecrccws_only_for)
        ])

        if self.protocol.value in ["cccam", "cccam_mcs"]:
            self.list.extend([
                getConfigListEntry(get_translation("ccc_version") + ":", self.cccversion),
                getConfigListEntry(get_translation("ccc_max_hops") + ":", self.cccmaxhops),
                getConfigListEntry(get_translation("ccc_keep_alive") + ":", self.ccckeepalive),
            ])

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def save(self):
        new_lines = [
            "[reader]",
            f"label                         = {self.label.value}",
            f"protocol                      = {self.protocol.value}",
            f"device                        = {self.device.value}",
        ]

        if self.protocol.value == "mgcamd":
            new_lines.append(f"deskey                        = {self.deskey.value.strip()}")

        new_lines.extend([
            f"user                          = {self.user.value}",
            f"password                      = {self.password.value}",
        ])

        new_lines.extend([
            f"inactivitytimeout             = {self.inactivitytimeout.value}",
            f"group                         = {self.group.value}",
            f"cacheex                       = {self.cacheex.value}",
            f"emmcache                      = {self.emmcache.value}",
            f"disablecrccws                 = {self.disablecrccws.value}",
            f"disablecrccws_only_for        = {self.disablecrccws_only_for.value}"
        ])

        if self.protocol.value in ["cccam", "cccam_mcs"]:
            new_lines.extend([
                f"cccversion                    = {self.cccversion.value}",
                f"cccmaxhops                    = {self.cccmaxhops.value}",
                f"ccckeepalive                  = {self.ccckeepalive.value}",
            ])

        self.close((self.start_index, self.end_index, new_lines))

    def cancel(self):
        self.close(None)

    def moveUp(self):
        self["config"].instance.moveSelection(self["config"].instance.moveUp)

    def moveDown(self):
        self["config"].instance.moveSelection(self["config"].instance.moveDown)

    def onSelectionChanged(self):
        current = self["config"].getCurrent()
        if not current:
            return
            
class CiefpOscamEditorSettings(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamEditorSettings" position="center,center" size="1400,800" title="..:: Oscam Editor Settings ::..">
        <widget name="config" position="10,10" size="980,650" scrollbarMode="showOnDemand" itemHeight="40" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/settings.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_settings"))
        self["key_green"] = Label(get_translation("save"))
        self["key_red"] = Label(get_translation("cancel"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.save,
            "red": self.close,
            "cancel": self.close
        }, -2)
        self.list = [
            getConfigListEntry(get_translation("dvbapi_path") + ":", config.plugins.CiefpOscamEditor.dvbapi_path),
            getConfigListEntry(get_translation("language") + ":", config.plugins.CiefpOscamEditor.language),
            getConfigListEntry(get_translation("auto_version_detection") + ":", config.plugins.CiefpOscamEditor.auto_version_path),
            getConfigListEntry(get_translation("webif_ip") + ":", config.plugins.CiefpOscamEditor.webif_ip),
            getConfigListEntry(get_translation("webif_user") + ":", config.plugins.CiefpOscamEditor.webif_user),
            getConfigListEntry(get_translation("webif_password") + ":", config.plugins.CiefpOscamEditor.webif_password),
            getConfigListEntry(get_translation("refresh_interval") + ":", config.plugins.CiefpOscamEditor.refresh_interval)
        ]
        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def save(self):
        config.plugins.CiefpOscamEditor.dvbapi_path.save()
        config.plugins.CiefpOscamEditor.language.save()
        config.plugins.CiefpOscamEditor.auto_version_path.save()
        config.plugins.CiefpOscamEditor.webif_ip.save()
        config.plugins.CiefpOscamEditor.webif_user.save()
        config.plugins.CiefpOscamEditor.webif_password.save()
        config.plugins.CiefpOscamEditor.refresh_interval.save()
        self.session.open(MessageBox, get_translation("settings_saved"), MessageBox.TYPE_INFO, timeout=5)
        self.close()
        
class CiefpOscamEcmInfo(Screen):
    skin = """
    <screen name="CiefpOscamEcmInfo" position="center,center" size="1400,800" title="..:: ECM Info ::..">
        <widget name="info_list" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/ecm_info.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(get_translation("title_ecm_info"))
        self["info_list"] = MenuList([], enableWrapAround=True)
        self["info_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("refresh"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.refresh,
            "cancel": self.close
        }, -2)
        self.refresh()

    def refresh(self):
        info = self.get_ecm_info()
        info_lines = [
            f"{get_translation('caid')}: {info['caid']}",
            f"{get_translation('pid')}: {info['pid']}",
            f"{get_translation('prov')}: {info['prov']}",
            f"{get_translation('chid')}: {info['chid']}",
            f"{get_translation('reader')}: {info['reader']}",
            f"{get_translation('from')}: {info['from']}",
            f"{get_translation('protocol')}: {info['protocol']}",
            f"{get_translation('hops')}: {info['hops']}",
            f"{get_translation('ecm_time')}: {info['ecm_time']}"
        ]
        self["info_list"].setList(info_lines)

    def get_ecm_info(self):
        ecm_path = "/tmp/ecm.info"
        ecm_data = {
            "caid": "N/A",
            "pid": "N/A",
            "prov": "000000",
            "chid": "N/A",
            "reader": "N/A",
            "from": "N/A",
            "protocol": "N/A",
            "hops": "N/A",
            "ecm_time": "N/A",
            "cw0": "N/A",
            "cw1": "N/A"
        }
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if ":" not in line:
                            continue
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == "caid":
                            ecm_data["caid"] = value.replace("0x", "").upper()
                        elif key == "pid":
                            ecm_data["pid"] = value
                        elif key == "prov":
                            ecm_data["prov"] = value
                        elif key == "chid":
                            ecm_data["chid"] = value
                        elif key == "reader":
                            ecm_data["reader"] = value
                        elif key == "from":
                            ecm_data["from"] = value
                        elif key == "protocol":
                            ecm_data["protocol"] = value
                        elif key == "hops":
                            ecm_data["hops"] = value
                        elif key == "ecm time":
                            ecm_data["ecm_time"] = value
                        elif key == "cw0":
                            ecm_data["cw0"] = value
                        elif key == "cw1":
                            ecm_data["cw1"] = value
            except Exception as e:
                print(f"Error reading ecm.info: {str(e)}")
        return ecm_data

class CiefpOscamUserEditor(Screen, ConfigListScreen):
    skin = """<screen name="CiefpOscamUserEditor" position="center,center" size="1400,800" title="..:: OSCam User Editor ::..">
        <widget name="config" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_user_editor.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_oscam_user_editor"))
        self._rebuild_pending = False

        # Default account - dvbapiau
        self.dvbapiau_user = ConfigText(default="dvbapiau", fixed_size=False)
        self.dvbapiau_description = ConfigText(default="DVB API User for Enigma2 with AU", fixed_size=False)
        self.dvbapiau_pwd = ConfigText(default="dvbapiau", fixed_size=False)
        self.dvbapiau_monlevel = ConfigSelection(default="4", choices=[("0", "0"), ("1", "1"), ("2", "2"), ("4", "4")])
        self.dvbapiau_au = ConfigSelection(default="1", choices=[("0", get_translation("off")), ("1", get_translation("on"))])
        self.dvbapiau_group = ConfigSelection(default="1,2,3,4,5,6,7,8,9,10", choices=[
            ("1", "1"),
            ("1,2", "1,2"),
            ("1,2,3", "1,2,3"),
            ("1,2,3,4,5,6", "1,2,3,4,5,6"),
            ("1,2,3,4,5,6,7,8,9,10", "1,2,3,4,5,6,7,8,9,10")
        ])
        self.dvbapiau_services = ConfigSelection(default="!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8,!blocked-9,!blocked-10,!blocked-11,!blocked-12,!blocked-13,!blocked-14,!blocked-15", choices=[
            ("0", "0"),
            ("!blocked-1,!blocked-2", "!blocked-1,!blocked-2"),
            ("!blocked-1,!blocked-2,!blocked-3,!blocked-4", "!blocked-1,!blocked-2,!blocked-3,!blocked-4"),
            ("!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6", "!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6"),
            ("!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8", "!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8"),
            ("!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8,!blocked-9,!blocked-10", "!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8,!blocked-9,!blocked-10"),
            ("!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8,!blocked-9,!blocked-10,!blocked-11,!blocked-12,!blocked-13,!blocked-14,!blocked-15", "!blocked-1,!blocked-2,!blocked-3,!blocked-4,!blocked-5,!blocked-6,!blocked-7,!blocked-8,!blocked-9,!blocked-10,!blocked-11,!blocked-12,!blocked-13,!blocked-14,!blocked-15")
        ])
        self.dvbapiau_cccmaxhops = ConfigText(default="2", fixed_size=False)
        self.dvbapiau_cccreshare = ConfigSelection(default="0", choices=[("0", "0"), ("1", "1")])
        self.dvbapiau_caid = ConfigText(default="09C4, 098C, 098D", fixed_size=False)
        self.dvbapiau_keepalive = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.dvbapiau_disabled = ConfigSelection(default="0", choices=[("0", get_translation("off")), ("1", get_translation("on"))])

        # Default account - anonymous
        self.anonymous_user = ConfigText(default="anonymous", fixed_size=False)
        self.anonymous_group = ConfigText(default="1", fixed_size=False)
        self.anonymous_disabled = ConfigSelection(default="1", choices=[("0", get_translation("off")), ("1", get_translation("on"))])

        # CacheEx opcija
        self.enable_cacheex = ConfigYesNo(default=False)
        self.enable_cacheex.addNotifier(self.cacheexChanged, initial_call=False)  # Callback za promenu
        self.cacheex_user = ConfigText(default="cacheex123", fixed_size=False)
        self.cacheex_pwd = ConfigText(default="cacheex123", fixed_size=False)
        self.cacheex_description = ConfigText(default="CacheEx User", fixed_size=False)
        self.cacheex_monlevel = ConfigSelection(default="4", choices=[("0", "0"), ("1", "1"), ("2", "2"), ("4", "4")])
        self.cacheex_au = ConfigSelection(default="1", choices=[("0", get_translation("off")), ("1", get_translation("on"))])
        self.cacheex_group = ConfigText(default="1", fixed_size=False)
        self.cacheex_services = ConfigText(default="0", fixed_size=False)
        self.cacheex_cccmaxhops = ConfigText(default="1", fixed_size=False)
        self.cacheex_cccreshare = ConfigSelection(default="0", choices=[("0", "0"), ("1", "1")])
        self.cacheex_caid = ConfigText(default="09C4,098C,098D", fixed_size=False)
        self.cacheex_keepalive = ConfigSelection(default="1", choices=[("0", "0"), ("1", "1")])
        self.cacheex_disabled = ConfigSelection(default="0", choices=[("0", get_translation("off")), ("1", get_translation("on"))])

        # GUI
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("preview"))
        self["key_blue"] = Label(get_translation("placeholder"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.saveConfig,
            "yellow": self.previewFile,
            "blue": self.close,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)

        self.createSetup()
        self["config"].onSelectionChanged.append(self.onSelectionChanged)

    def cacheexChanged(self, configElement):
        """Callback kada se enable_cacheex promeni."""
        self.createSetup()

    def onSelectionChanged(self):
        current = self["config"].getCurrent()
        if not current:
            return
        key = current[0].lower()
        if not any(x in key for x in ["au", "cccreshare", "keepalive", "disabled"]):
            return
        if hasattr(self, "_rebuild_pending") and self._rebuild_pending:
            return
        try:
            self._rebuild_pending = True
            self["config"].blockInputHelpers = True
            self.createSetup()
        finally:
            self._rebuild_pending = False
            self["config"].blockInputHelpers = False

    def createSetup(self):
        self.list = [
            getConfigListEntry("=== [account] dvbapiau ===", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("user"), self.dvbapiau_user),
            getConfigListEntry(get_translation("description"), self.dvbapiau_description),
            getConfigListEntry(get_translation("pwd"), self.dvbapiau_pwd),
            getConfigListEntry(get_translation("monlevel"), self.dvbapiau_monlevel),
            getConfigListEntry(get_translation("au"), self.dvbapiau_au),
            getConfigListEntry(get_translation("group"), self.dvbapiau_group),
            getConfigListEntry(get_translation("services"), self.dvbapiau_services),
            getConfigListEntry(get_translation("cccmaxhops"), self.dvbapiau_cccmaxhops),
            getConfigListEntry(get_translation("cccreshare"), self.dvbapiau_cccreshare),
            getConfigListEntry(get_translation("caid"), self.dvbapiau_caid),
            getConfigListEntry(get_translation("keepalive"), self.dvbapiau_keepalive),
            getConfigListEntry(get_translation("disabled"), self.dvbapiau_disabled),
            getConfigListEntry("=== [account] anonymous ===", ConfigText(default="", fixed_size=True)),
            getConfigListEntry(get_translation("user"), self.anonymous_user),
            getConfigListEntry(get_translation("group"), self.anonymous_group),
            getConfigListEntry(get_translation("disabled"), self.anonymous_disabled),
            getConfigListEntry(get_translation("enable_cacheex"), self.enable_cacheex)
        ]
        if self.enable_cacheex.value:
            self.list.append(getConfigListEntry("=== [account] cacheex123 ===", ConfigText(default="", fixed_size=True)))
            self.list.append(getConfigListEntry(get_translation("user"), self.cacheex_user))
            self.list.append(getConfigListEntry(get_translation("description"), self.cacheex_description))
            self.list.append(getConfigListEntry(get_translation("pwd"), self.cacheex_pwd))
            self.list.append(getConfigListEntry(get_translation("monlevel"), self.cacheex_monlevel))
            self.list.append(getConfigListEntry(get_translation("au"), self.cacheex_au))
            self.list.append(getConfigListEntry(get_translation("group"), self.cacheex_group))
            self.list.append(getConfigListEntry(get_translation("services"), self.cacheex_services))
            self.list.append(getConfigListEntry(get_translation("cccmaxhops"), self.cacheex_cccmaxhops))
            self.list.append(getConfigListEntry(get_translation("cccreshare"), self.cacheex_cccreshare))
            self.list.append(getConfigListEntry(get_translation("caid"), self.cacheex_caid))
            self.list.append(getConfigListEntry(get_translation("keepalive"), self.cacheex_keepalive))
            self.list.append(getConfigListEntry(get_translation("disabled"), self.cacheex_disabled))
        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def saveConfig(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        user_path = dvbapi_path.replace("oscam.dvbapi", "oscam.user")

        try:
            lines = []
            if not os.path.exists(user_path):
                lines.append("## Created by CiefpOscamEditor ##")
                lines.append("## ..:: CiefpSettings ::.. ##")
                lines.append("")

            # dvbapiau
            lines.append("[account]")
            lines.append(f"user                          = {self.dvbapiau_user.value}")
            lines.append(f"pwd                           = {self.dvbapiau_pwd.value}")
            lines.append(f"description                   = {self.dvbapiau_description.value}")
            lines.append(f"monlevel                      = {self.dvbapiau_monlevel.value}")
            lines.append(f"au                            = {self.dvbapiau_au.value}")
            lines.append(f"group                         = {self.dvbapiau_group.value}")
            if self.dvbapiau_services.value != "0":
                lines.append(f"services                      = {self.dvbapiau_services.value}")
            lines.append(f"cccmaxhops                    = {self.dvbapiau_cccmaxhops.value}")
            lines.append(f"cccreshare                    = {self.dvbapiau_cccreshare.value}")
            lines.append(f"caid                          = {self.dvbapiau_caid.value}")
            lines.append(f"keepalive                      = {self.dvbapiau_keepalive.value}")
            lines.append(f"disabled                      = {self.dvbapiau_disabled.value}")
            lines.append("")

            # anonymous
            lines.append("[account]")
            lines.append(f"user                          = {self.anonymous_user.value}")
            lines.append(f"group                         = {self.anonymous_group.value}")
            lines.append(f"disabled                      = {self.anonymous_disabled.value}")
            lines.append("")

            # cacheex123 (samo ako je enabled)
            if self.enable_cacheex.value:
                lines.append("[account]")
                lines.append(f"user                          = {self.cacheex_user.value}")
                lines.append(f"pwd                           = {self.cacheex_pwd.value}")
                lines.append(f"description                   = {self.cacheex_description.value}")
                lines.append(f"monlevel                      = {self.cacheex_monlevel.value}")
                lines.append(f"au                            = {self.cacheex_au.value}")
                lines.append(f"group                         = {self.cacheex_group.value}")
                if self.cacheex_services.value != "0":
                    lines.append(f"services                      = {self.cacheex_services.value}")
                lines.append(f"cccmaxhops                    = {self.cacheex_cccmaxhops.value}")
                lines.append(f"cccreshare                    = {self.cacheex_cccreshare.value}")
                lines.append(f"caid                          = {self.cacheex_caid.value}")
                lines.append(f"keepalive                      = {self.cacheex_keepalive.value}")
                lines.append(f"disabled                      = {self.cacheex_disabled.value}")
                lines.append("")

            os.makedirs(os.path.dirname(user_path), exist_ok=True)
            with open(user_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines))

            restart_oscam()

            self.session.open(MessageBox, get_translation("user_saved").format(user_path), MessageBox.TYPE_INFO,
                              timeout=5)
        except Exception as e:
            self.session.open(MessageBox, get_translation("write_error").format(user_path, str(e)),
                              MessageBox.TYPE_ERROR)

    def previewFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        user_path = dvbapi_path.replace("oscam.dvbapi", "oscam.user")
        self.session.open(CiefpOscamUserPreview, user_path)

    def moveUp(self):
        self["config"].instance.moveSelection(self["config"].instance.moveUp)

    def moveDown(self):
        self["config"].instance.moveSelection(self["config"].instance.moveDown)

class CiefpOscamUserPreview(Screen):
    skin = """<screen name="CiefpOscamUserPreview" position="center,center" size="1400,800" title="..:: oscam.user Preview ::..">
        <widget name="file_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/oscam_user_preview.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session, filepath):
        Screen.__init__(self, session)
        self.filepath = filepath
        self.setTitle(get_translation("title_oscam_user_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "cancel": self.close
        }, -2)
        self.loadFile()

    def loadFile(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    lines = [line.rstrip() for line in f if line.strip()]
                self["file_list"].setList(lines)
            else:
                self["file_list"].setList([get_translation("file_not_exist")])
        except Exception as e:
            self["file_list"].setList([get_translation("file_read_error").format(str(e))])


class CiefpOscamSoftCamKeyPreview(Screen):
    skin = """
    <screen name="CiefpOscamSoftCamKeyPreview" position="center,center" size="1400,800" title="..:: SoftCam.key Preview ::..">
        <widget name="file_list" position="10,10" size="980,720" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="260,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="510,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="key_blue" position="760,750" size="240,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/softcamkey_preview.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(get_translation("title_softcam_key_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("save"))
        self["key_yellow"] = Label(get_translation("delete"))
        self["key_blue"] = Label("ADD KEY")
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
            "red": self.close,
            "green": self.saveFile,
            "yellow": self.deleteKey,
            "blue": self.addBissKey,
            "cancel": self.close,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        self.lines = []
        self.loadFile()

        # Dobij informacije o trenutnom kanalu
        self.current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        self.sid = self.getSID()
        self.vpid = self.getVPID()
        self.channel_name = self.getChannelName()

    def getSID(self):
        """Dobija SID iz trenutnog servisa"""
        if self.current_service:
            try:
                # Service reference format: 1:0:1:1234:567:2:0:0:0:0:
                service_string = self.current_service.toString()
                parts = service_string.split(':')
                if len(parts) >= 4:
                    sid_hex = parts[3]  # SID je četvrti deo
                    # Konvertuj hex u decimalni i onda u 4-cifreni hex
                    sid_decimal = int(sid_hex, 16)
                    return f"{sid_decimal:04X}"  # 4-cifreni hex
            except:
                pass
        return "0001"  # Default

    def getVPID(self):
        """Dobija Video PID iz trenutnog servisa"""
        try:
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    vpid = info.getInfo(iServiceInformation.sVideoPID)
                    if vpid > 0:
                        return f"{vpid:04X}"  # 4-cifreni hex
        except:
            pass
        return "0021"  # Default

    def getChannelName(self):
        """Dobija ime trenutnog kanala"""
        try:
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    name = info.getName()
                    if name:
                        return name
        except:
            pass
        return "Current Channel"

    def loadFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        softcam_path = dvbapi_path.replace("oscam.dvbapi", "SoftCam.Key")
        self.softcam_path = softcam_path
        self.lines = []
        try:
            if os.path.exists(softcam_path):
                with open(softcam_path, "r", encoding="utf-8") as f:
                    self.lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            else:
                self.lines = [get_translation("file_not_exist")]
            self["file_list"].setList(self.lines)
        except Exception as e:
            self["file_list"].setList([get_translation("file_read_error").format(str(e))])

    def addBissKey(self):
        """Pokreće dijalog za unos BISS ključa sa automatskim parametrima"""
        title = f"Enter BISS Key for {self.channel_name} (SID:{self.sid}, VPID:{self.vpid})"
        self.session.openWithCallback(
            self.bissKeyCallback,
            VirtualKeyBoard,
            title=title,
            text=""
        )

    def bissKeyCallback(self, biss_key):
        """Callback za unos BISS ključa"""
        if not biss_key:
            return

        formatted_key = biss_key.replace(" ", "").upper()

        if len(formatted_key) not in [8, 16]:
            self.session.open(
                MessageBox,
                get_translation("invalid_key_length"),
                MessageBox.TYPE_ERROR,
                timeout=3
            )
            return

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # FORMAT KOJI VAŠ OSCAM ZAHTEVA: SID + VPID
        sid_vpid = f"{self.sid}{self.vpid}"
        line = f"F {sid_vpid} 00 {formatted_key} ; {self.channel_name} - {current_time}\n"

        try:
            dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
            base_dir = os.path.dirname(dvbapi_path)

            # Upis u softcam.key fajlove
            for filename in ["SoftCam.Key", "softcam.key"]:
                softcam_path = os.path.join(base_dir, filename)
                self._writeToFile(softcam_path, line, f"F {sid_vpid} 00")

            # Dodaj u prikaz
            self.lines.append(line.strip())
            self["file_list"].setList(self.lines)

            restart_oscam()

            self.session.open(
                MessageBox,
                get_translation("biss_key_added").format(self.channel_name),
                MessageBox.TYPE_INFO,
                timeout=3
            )

        except Exception as e:
            print(f"Greška pri upisu BISS ključa: {e}")
            self.session.open(
                MessageBox,
                f"Error: {str(e)}",
                MessageBox.TYPE_ERROR,
                timeout=3
            )

    def _writeToFile(self, file_path, new_line, search_pattern):
        """Upis bez duplikata"""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line for line in f if search_pattern not in line]
        else:
            lines = []

        lines.append(new_line)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def deleteKey(self):
        current = self["file_list"].getCurrent()
        if current and current != get_translation("file_not_exist") and not current.startswith(
                get_translation("file_read_error")):
            index = self["file_list"].getSelectedIndex()
            self.session.openWithCallback(
                lambda result: self.confirmDelete(index) if result else None,
                MessageBox,
                get_translation("confirm_delete_key"),
                MessageBox.TYPE_YESNO
            )
        else:
            self.session.open(MessageBox, get_translation("no_key_selected"), MessageBox.TYPE_ERROR, timeout=3)

    def confirmDelete(self, index):
        try:
            del self.lines[index]
            self["file_list"].setList(self.lines)

            # Ažuriraj fajl
            with open(self.softcam_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines) + "\n")

            restart_oscam()

            self.session.open(MessageBox, get_translation("key_deleted"), MessageBox.TYPE_INFO, timeout=3)
        except Exception as e:
            self.session.open(MessageBox, get_translation("delete_error").format(str(e)), MessageBox.TYPE_ERROR,
                              timeout=3)

    def saveFile(self):
        try:
            with open(self.softcam_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines) + "\n")

            restart_oscam()

            self.session.open(MessageBox, get_translation("file_saved").format(self.softcam_path), MessageBox.TYPE_INFO,
                              timeout=3)
            self.close()
        except Exception as e:
            self.session.open(MessageBox, get_translation("write_error").format(self.softcam_path, str(e)),
                              MessageBox.TYPE_ERROR, timeout=3)

    def moveUp(self):
        self["file_list"].up()

    def moveDown(self):
        self["file_list"].down()
        
def main(session, **kwargs):
    session.open(CiefpOscamEditorMain)

def Plugins(**kwargs):
    return [PluginDescriptor(
        name="Ciefp Oscam Editor",
        description=f"Edit Oscam files from Enigma2 (Version {PLUGIN_VERSION})",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="plugin.png",
        fnc=main
    )]