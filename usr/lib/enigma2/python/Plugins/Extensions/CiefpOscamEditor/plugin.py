import requests
import json
import re
import os
from requests.auth import HTTPBasicAuth
from Plugins.Plugin import PluginDescriptor
from Plugins.Extensions.CiefpOscamEditor.languages.en import translations as en_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sr import translations as sr_trans
from Plugins.Extensions.CiefpOscamEditor.languages.el import translations as el_trans
from Plugins.Extensions.CiefpOscamEditor.languages.ar import translations as ar_trans
from Plugins.Extensions.CiefpOscamEditor.languages.de import translations as de_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sk import translations as sk_trans
from Plugins.Extensions.CiefpOscamEditor.languages.pl import translations as pl_trans
from Plugins.Extensions.CiefpOscamEditor.languages.tr import translations as tr_trans
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, getConfigListEntry
from Components.MenuList import MenuList
from enigma import eServiceCenter, eServiceReference, iServiceInformation, eListbox, eTimer
import urllib.request
import urllib.error
import base64
import xml.etree.ElementTree as ET
from html import unescape
import subprocess

# Postojeći kod za prevode
TRANSLATIONS = {
    "en": en_trans,
    "sr": sr_trans,
    "el": el_trans,
    "ar": ar_trans,
    "de": de_trans,
    "sk": sk_trans,
    "pl": pl_trans,
    "tr": tr_trans
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
        ("sr", "Srpski"),
        ("el", "Greek"),
        ("ar", "Arabic"),
        ("de", "German"),
        ("sk", "Slovak"),
        ("pl", "Polish"),
        ("tr", "Turkish")
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
PLUGIN_VERSION = "1.1.5"

def check_for_update(session):
    try:
        current_version = PLUGIN_VERSION
        with urllib.request.urlopen(VERSION_URL, timeout=5) as f:
            latest_version = f.read().decode("utf-8").strip()

        if latest_version != current_version:
            def onConfirmUpdate(answer):
                if answer:
                    session.open(MessageBox, get_translation("update_in_progress"), MessageBox.TYPE_INFO, timeout=5)
                    subprocess.call(UPDATE_COMMAND, shell=True)
                else:
                    session.open(MessageBox, get_translation("update_cancelled"), MessageBox.TYPE_INFO, timeout=5)

            session.openWithCallback(
                onConfirmUpdate,
                MessageBox,
                f"{get_translation('new_version_available').format(latest_version)}\n"
                f"{get_translation('current_version')}: {current_version}\n"
                f"{get_translation('update_question')}",
                MessageBox.TYPE_YESNO
            )
    except Exception as e:
        session.open(MessageBox, get_translation("update_check_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

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
    Radi sa tvojom verzijom OSCam-a 2.25.05.
    Prikazuje sve čitače (type='r', 'p') i koristi ispravne metode za status, au, idle.
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
                    name = client.get("name", "Unknown")
                    protocol = client.get("protocol", "Unknown")
                    # Ukloni verziju iz protokola ako postoji
                    if " (" in protocol:
                        protocol = protocol.split(" (")[0]

                    # Status je sadržaj <connection> taga
                    connection = client.find("connection")
                    status = connection.text.strip() if connection is not None and connection.text else "Unknown"

                    # AU je atribut
                    au = client.get("au", "0")

                    # Idle vreme je u <times idle="...">, ali u tvojoj verziji ga nema
                    # Koristi idle iz atributa <times> ako postoji, inače "0"
                    times = client.find("times")
                    idle = times.get("idle", "0") if times is not None else "0"

                    # Dodaj tip za jasnoću (opciono)
                    client_type = client.get("type", "Unknown")
                    display_name = f"{name} ({client_type})"

                    status_data.append({
                        "name": display_name,
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


# Ažurirana klasa CiefpOscamStatus
class CiefpOscamStatus(Screen):
    skin = """<screen name="CiefpOscamStatus" position="center,center" size="1400,800" title="..:: OSCam Status ::..">
        <widget name="status_list" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#A08000" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background6.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.is_refreshing = True
        self["status_list"] = MenuList([], enableWrapAround=True)
        self["status_list"].l.setItemHeight(30)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("refresh"))
        self["key_yellow"] = Label(get_translation("ecm_info"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.refreshStatus,
            "yellow": self.openEcmInfo,
            "cancel": self.close
        }, -2)
        self.timer = eTimer()
        self.timer.callback.append(self.refreshStatus)
        self.interval = int(config.plugins.CiefpOscamEditor.refresh_interval.value) * 1000
        self.timer.start(self.interval, False)
        self.refreshStatus()

    def toggleRefresh(self):
        if self.is_refreshing:
            self.timer.stop()
            self.is_refreshing = False
            self["key_green"].setText(get_translation("start_refresh"))
        else:
            self.timer.start(self.interval, False)
            self.is_refreshing = True
            self["key_green"].setText(get_translation("refresh"))
        self.refreshStatus()

    def refreshStatus(self):
        status_data = []
        try:
            # Čitaj config iz oscam.conf bez prosleđivanja putanje
            conf = read_oscam_conf()
            print(f"[CiefpOscamStatus] Konfiguracija: IP={conf['ip']}, Port={conf['port']}, User={conf['user']}")

            # Dohvati čitače
            readers = get_oscam_readers(
                ip=conf["ip"],
                port=conf["port"],
                user=conf["user"],
                pwd=conf["pwd"]
            )

            if readers:
                for reader in readers:
                    status_data.append(
                        f"{get_translation('reader')}: {reader['name']} | "
                        f"{get_translation('status')}: {reader['status']} | "
                        f"{get_translation('au')}: {reader['au']} | "
                        f"{get_translation('idle_time')}: {reader['idle']} | "
                        f"{get_translation('protocol')}: {reader['protocol']}"
                    )
            else:
                status_data.append(get_translation("no_status_data"))
                print("[CiefpOscamStatus] Nema čitača ili greška u komunikaciji")

        except Exception as e:
            status_data.append(get_translation("connection_error").format(f"{str(e)}"))
            print(f"[CiefpOscamStatus] Error: {str(e)}")

        self["status_list"].setList(status_data)

    def openEcmInfo(self):
        self.session.open(CiefpOscamEcmInfo)

    def close(self):
        self.timer.stop()
        Screen.close(self)

# Ostale klase (CiefpOscamEditorMain, CiefpOscamInfo, itd.) ostaju nepromenjene
# ... (dodaj ostatak originalnog koda ovde)

class CiefpOscamEditorMain(Screen):
    skin = """
    <screen name="CiefpOscamEditorMain" position="center,center" size="1400,800" title="..:: Ciefp Oscam Editor ::..">
        <widget name="channel_info" position="10,10" size="980,650" font="Regular;26" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="640,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        oscam_info = get_oscam_info()
        self.setTitle(f"{get_translation('title_main')} (OSCam: {oscam_info['version']})")
        self["channel_info"] = Label()
        self["key_green"] = Label(get_translation("add_dvbapi"))
        self["key_yellow"] = Label(get_translation("settings"))
        self["key_red"] = Label(get_translation("exit"))
        self["key_blue"] = Label(get_translation("oscam_server"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.openAddDvbapi,
            "yellow": self.openSettings,
            "red": self.close,
            "blue": self.openServerPreview,
            "cancel": self.close
        }, -2)
        self.current_provider_id = "000000"
        self.updateChannelInfo()

        # Odložena provera verzije da bi se ekran prvo inicijalizovao
        self.updateTimer = eTimer()
        self.updateTimer.callback.append(lambda: check_for_update(self.session))
        self.updateTimer.start(500, True)

        # Dinamički podešavanje dvbapi_path na osnovu ConfigDir
        if config.plugins.CiefpOscamEditor.auto_version_path.value == "yes" and oscam_info["config_dir"] != "Unknown":
            config_dir = oscam_info["config_dir"]
            if config_dir.endswith("/"):
                config_dir = config_dir[:-1]
            new_dvbapi_path = f"{config_dir}/oscam.dvbapi"
            if new_dvbapi_path not in [x[0] for x in config.plugins.CiefpOscamEditor.dvbapi_path.choices.choices]:
                config.plugins.CiefpOscamEditor.dvbapi_path.choices.choices.append((new_dvbapi_path, f"Custom ({config_dir})"))
            config.plugins.CiefpOscamEditor.dvbapi_path.setValue(new_dvbapi_path)

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
            "ecm_time": "N/A"
        }
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.lower().startswith("caid:"):
                            caid = line.split(":")[1].strip()
                            caid = caid.replace("0x", "").upper()
                            ecm_data["caid"] = caid
                        elif line.lower().startswith("pid:"):
                            ecm_data["pid"] = line.split(":")[1].strip()
                        elif line.lower().startswith("prov:"):
                            ecm_data["prov"] = line.split(":")[1].strip()
                        elif line.lower().startswith("chid:"):
                            ecm_data["chid"] = line.split(":")[1].strip()
                        elif line.lower().startswith("reader:"):
                            ecm_data["reader"] = line.split(":")[1].strip()
                        elif line.lower().startswith("from:"):
                            ecm_data["from"] = line.split(":")[1].strip()
                        elif line.lower().startswith("protocol:"):
                            ecm_data["protocol"] = line.split(":")[1].strip()
                        elif line.lower().startswith("hops:"):
                            ecm_data["hops"] = line.split(":")[1].strip()
                        elif line.lower().startswith("ecm time:"):
                            ecm_data["ecm_time"] = line.split(":")[1].strip()
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

    def openAddDvbapi(self):
        self.session.open(CiefpOscamEditorAdd, default_provider=self.current_provider_id)

    def openSettings(self):
        self.session.open(CiefpOscamEditorSettings)

    def openServerPreview(self):
        self.session.open(CiefpOscamServerPreview)

class CiefpOscamInfo(Screen):
    skin = """
    <screen name="CiefpOscamInfo" position="center,center" size="1400,800" title="..:: OSCam Info ::..">
        <widget name="info_list" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" itemHeight="30" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background5.png" position="1000,0" size="400,800" />
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
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="640,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background2.png" position="1000,0" size="400,800" />
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
        <widget name="file_list" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_blue" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background3.png" position="1000,0" size="400,800" />
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
    <screen name="CiefpOscamServerPreview" position="center,center" size="1400,800" title="..:: oscam.server Pregled ::..">
        <widget name="file_list" position="10,10" size="980,740" font="Regular;24" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="640,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background3.png" position="1000,0" size="400,800" />
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
                html = urllib.request.urlopen(selected_url, timeout=5).read().decode("utf-8", errors="ignore")
                match = re.search(r'C:\s*([\w\.-]+)\s+(\d+)\s+(\w+)\s+([^<\s]+)', html)
                if not match:
                    self.session.open(MessageBox, "C-line nije pronađena!", MessageBox.TYPE_ERROR, timeout=5)
                    return

                server, port, user, password = match.groups()
                password = re.sub(r'<.*?>', '', password)
                password = unescape(password).strip()

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

                dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
                server_path = dvbapi_path.replace("oscam.dvbapi", "oscam.server")

                os.makedirs(os.path.dirname(server_path), exist_ok=True)
                with open(server_path, "a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(reader_lines) + "\n")

                os.system("killall -HUP oscam")
                self.session.open(
                    MessageBox,
                    f"Reader '{label_name}' dodat iz '{selected_name}', Oscam reloadovan.",
                    MessageBox.TYPE_INFO,
                    timeout=5
                )

            except Exception as e:
                self.session.open(MessageBox, f"Greška: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

        choices = [
            (get_translation("cccamia_free"), "https://cccamia.com/cccam-free"),
            (get_translation("cccam_premium"), "https://cccam-premium.pro/free-cccam"),
            (get_translation("cccamiptv_free"), "https://cccamiptv.tv/cccamfree/#page-content")
        ]

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

class CiefpOscamServerAdd(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamServerAdd" position="center,center" size="900,800" title="..:: Dodaj čitač u oscam.server ::..">
        <widget name="config" position="10,10" size="880,650" scrollbarMode="showOnDemand" itemHeight="40" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_add_reader"))
        self["key_red"] = Label(get_translation("cancel"))
        self["key_green"] = Label(get_translation("save"))
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.save,
            "cancel": self.close
        }, -2)

        self.label = ConfigText(default="", fixed_size=False)
        self.protocol = ConfigSelection(default="cccam", choices=[
            ("cccam", get_translation("protocol") + ": cccam"),
            ("cccam_mcs", get_translation("protocol") + ": cccam_mcs")
        ])
        self.device = ConfigText(default="", fixed_size=False)
        self.user = ConfigText(default="", fixed_size=False)
        self.password = ConfigText(default="", fixed_size=False)
        self.inactivitytimeout = ConfigSelection(default="-1", choices=[
            ("-1", "-1"),
            ("0", "0"),
            ("30", "30"),
            ("60", "60")
        ])
        self.cacheex = ConfigSelection(default="1", choices=[
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3")
        ])
        self.group = ConfigSelection(default="2", choices=[
            ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
            ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10")
        ])
        self.emmcache = ConfigSelection(default="1,3,2,0", choices=[
            ("1,3,2,0", "1,3,2,0"),
            ("1,5,2,0", "1,5,2,0"),
            ("1,1,2,0", "1,1,2,0")
        ])
        self.disablecrccws = ConfigSelection(default="0", choices=[
            ("0", "0"),
            ("1", "1")
        ])
        self.disablecrccws_only_for = ConfigSelection(default="0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000", choices=[
            ("0", "0"),
            ("0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000", 
             "0E00:000000;0500:050F00,030B00;09C4:000000;098C:000000;098D:000000;091F:000000")
        ])
        self.cccversion = ConfigSelection(default="2.0.11", choices=[
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

        self.createSetup()

    def createSetup(self):
        self.list = [
            getConfigListEntry(get_translation("label") + ":", self.label),
            getConfigListEntry(get_translation("protocol") + ":", self.protocol),
            getConfigListEntry(get_translation("device") + ":", self.device),
            getConfigListEntry(get_translation("user") + ":", self.user),
            getConfigListEntry(get_translation("password") + ":", self.password),
            getConfigListEntry(get_translation("inactivity_timeout") + ":", self.inactivitytimeout),
            getConfigListEntry(get_translation("cacheex") + ":", self.cacheex),
            getConfigListEntry(get_translation("group") + ":", self.group),
            getConfigListEntry(get_translation("emm_cache") + ":", self.emmcache),
            getConfigListEntry(get_translation("disable_crc_cws") + ":", self.disablecrccws),
            getConfigListEntry(get_translation("disable_crc_cws_only_for") + ":", self.disablecrccws_only_for),
            getConfigListEntry(get_translation("ccc_version") + ":", self.cccversion),
            getConfigListEntry(get_translation("ccc_max_hops") + ":", self.cccmaxhops),
            getConfigListEntry(get_translation("ccc_keep_alive") + ":", self.ccckeepalive)
        ]
        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def save(self):
        reader_lines = [
            "[reader]",
            f"label                         = {self.label.value}",
            f"protocol                      = {self.protocol.value}",
            f"device                        = {self.device.value}",
            f"user                          = {self.user.value}",
            f"password                      = {self.password.value}",
            f"inactivitytimeout             = {self.inactivitytimeout.value}",
            f"cacheex                       = {self.cacheex.value}",
            f"group                         = {self.group.value}",
            f"emmcache                      = {self.emmcache.value}",
            f"disablecrccws                 = {self.disablecrccws.value}",
            f"disablecrccws_only_for        = {self.disablecrccws_only_for.value}",
            f"cccversion                    = {self.cccversion.value}",
            f"cccmaxhops                    = {self.cccmaxhops.value}",
            f"ccckeepalive                  = {self.ccckeepalive.value}"
        ]

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

class CiefpOscamServerReaderSelect(Screen):
    skin = """
    <screen name="CiefpOscamServerReaderSelect" position="center,center" size="900,800" title="..:: Izaberi čitač za brisanje ::..">
        <widget name="reader_list" position="10,10" size="880,650" font="Regular;26" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
    </screen>"""

    def __init__(self, session, lines):
        Screen.__init__(self, session)
        self.session = session
        self.lines = lines[:]
        self.readers = []
        self.setTitle(get_translation("title_reader_select"))
        self["reader_list"] = MenuList([], enableWrapAround=True)
        self["reader_list"].l.setItemHeight(35)
        self["key_red"] = Label(get_translation("delete"))
        self["key_green"] = Label(get_translation("save"))
        self["actions"] = ActionMap(["ColorActions", "SetupActions"], {
            "red": self.deleteReader,
            "green": self.saveFile,
            "cancel": self.closeWithCallback,
            "ok": self.selectReader,
            "up": self.moveUp,
            "down": self.moveDown
        }, -2)
        print("DEBUG: ActionMap initialized with contexts: ['ColorActions', 'SetupActions']")
        print("DEBUG: ActionMap bindings: red=deleteReader, green=saveFile, cancel=closeWithCallback, ok=selectReader, up=moveUp, down=moveDown")
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
        
class CiefpOscamEditorSettings(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamEditorSettings" position="center,center" size="900,800" title="..:: Ciefp Oscam Editor Settings ::..">
        <widget name="config" position="10,10" size="880,650" scrollbarMode="showOnDemand" itemHeight="40" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="220,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [])
        self.session = session
        self.setTitle(get_translation("title_settings"))
        self["key_green"] = Label(get_translation("save"))
        self["key_red"] = Label(get_translation("cancel"))
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
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background7.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
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
        info = {
            "caid": "N/A",
            "pid": "N/A",
            "prov": "000000",
            "chid": "N/A",
            "reader": "N/A",
            "from": "N/A",
            "protocol": "N/A",
            "hops": "N/A",
            "ecm_time": "N/A"
        }
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.lower().startswith("caid:"):
                            caid = line.split(":", 1)[1].strip().replace("0x", "").upper()
                            info["caid"] = caid
                        elif line.lower().startswith("pid:"):
                            info["pid"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("prov:"):
                            info["prov"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("chid:"):
                            info["chid"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("reader:"):
                            info["reader"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("from:"):
                            info["from"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("protocol:"):
                            info["protocol"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("hops:"):
                            info["hops"] = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("ecm time:"):
                            info["ecm_time"] = line.split(":", 1)[1].strip()
            except Exception as e:
                print(f"[CiefpOscamEditor] Greška pri čitanju ecm.info: {str(e)}")
        return info

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