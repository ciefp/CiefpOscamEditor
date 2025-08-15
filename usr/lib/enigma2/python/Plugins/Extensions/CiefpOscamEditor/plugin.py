from Plugins.Plugin import PluginDescriptor
from Plugins.Extensions.CiefpOscamEditor.languages.en import translations as en_trans
from Plugins.Extensions.CiefpOscamEditor.languages.sr import translations as sr_trans
from Plugins.Extensions.CiefpOscamEditor.languages.el import translations as el_trans
from Plugins.Extensions.CiefpOscamEditor.languages.ar import translations as ar_trans
from Plugins.Extensions.CiefpOscamEditor.languages.de import translations as de_trans
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, getConfigListEntry
from Components.MenuList import MenuList
from enigma import eServiceCenter, eServiceReference, iServiceInformation, eListbox
import os
import re
import requests
import urllib.request
from html import unescape
from enigma import eTimer

# --- Provera i instalacija bs4 ---
try:
    from bs4 import BeautifulSoup
except ImportError:
    import os
    try:
        os.system("opkg update")
        # pokušaj za python3, ako ne uspe probaj python2 paket
        if os.system("opkg install python3-beautifulsoup4") != 0:
            os.system("opkg install python-beautifulsoup4")
        from bs4 import BeautifulSoup
    except Exception as e:
        try:
            from Screens.MessageBox import MessageBox
            session.open(MessageBox,
                         "Nedostaje modul 'bs4' (BeautifulSoup4)\nMolimo instalirajte ga ručno:\n"
                         "opkg update && opkg install python3-beautifulsoup4",
                         MessageBox.TYPE_ERROR, timeout=10)
        except:
            print(f"[CiefpOscamEditor] Upozorenje: Modul 'bs4' nije dostupan ({e})")
        BeautifulSoup = None
# --- Kraj provere bs4 ---

from Screens.ChoiceBox import ChoiceBox
import urllib.request
import subprocess

VERSION_URL = "https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/refs/heads/main/version.txt"
UPDATE_COMMAND = 'wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh'
PLUGIN_VERSION = "1.1.3"

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

# Konfiguracija za putanju i jezik
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
    default="sr",
    choices=[
        ("en", "English"),
        ("sr", "Srpski"),
        ("el", "Greek"),
        ("ar", "Arabic"),
        ("de", "German")
    ]
)

# Rečnik za prevode
TRANSLATIONS = {
    "en": en_trans,
    "sr": sr_trans,
    "el": el_trans,
    "ar": ar_trans,
    "de": de_trans
}

def get_translation(key):
    lang = config.plugins.CiefpOscamEditor.language.value
    # prvo pokušaj odabrani jezik
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    # ako nema, probaj engleski
    if key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]
    # ako nema ni u engleskom, vrati sam ključ
    return key

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
        self.setTitle(get_translation("title_main"))
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
        self.updateTimer.start(500, True)  # pokreni za 0.5 sekundi

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
        self["key_blue"] = Label(get_translation("future"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.addLine,
            "red": self.close,
            "yellow": self.openPreview,
            "blue": self.futureFunction,
            "cancel": self.close
        }, -2)

        # Ispravljene opcije za ConfigSelection bez dupliranja ključa prevoda
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
        caid = self.custom_caid.value.lower().replace("0x",
                                                      "").upper() if self.caid.value == "" else self.caid.value.lower().replace(
            "0x", "").upper()
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
            # Polja iz GUI-ja
            ns = self.ns.value.strip().lower().replace("0x", "").upper()
            sid = self.sid.value.strip().lower().replace("0x", "").upper()
            ecmpid = self.ecmpid.value.strip().lower().replace("0x", "").upper()

            # Ako je neko polje prazno, ostaje prazno, ali dvotačke se zadržavaju
            # Format: A: ::SID:ECMPID:: CAID:PROVIDER:1FFF
            ns_field = ns if ns else ""
            sid_field = sid if sid else ""
            ecmpid_field = ecmpid if ecmpid else ""

            # Formiramo string sa praznim poljima ako nisu popunjena
            line = f"{line_type} ::{sid_field}:{ecmpid_field}:: {caid}:{provider}:1FFF"
        elif line_type == "J:":
            caid2 = self.custom_caid2.value.lower().replace("0x",
                                                            "").upper() if self.caid2.value == "" else self.caid2.value.lower().replace(
                "0x", "").upper()
            provider2 = self.provider2.value.lower().replace("0x", "").upper()
            sid = self.sid.value.lower().replace("0x", "").upper()
            ecmpid = self.ecmpid.value.lower().replace("0x", "").upper()
            ecmpid2 = self.ecmpid2.value.lower().replace("0x", "").upper()
            line = f"{line_type} {caid}:{provider}:{sid}:{ecmpid} {caid2}:{provider2}:{ecmpid2}"
        elif line_type == "M:":
            stari_prov = self.stari_prov.value.lower().replace("0x", "").upper()
            caid2 = self.custom_caid2.value.lower().replace("0x",
                                                            "").upper() if self.caid2.value == "" else self.caid2.value.lower().replace(
                "0x", "").upper()
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
            self.session.open(MessageBox, get_translation("line_added").format(dvbapi_path, line), MessageBox.TYPE_INFO,
                              timeout=5)
            self.close()
        except Exception as e:
            self.session.open(MessageBox, get_translation("write_error").format(dvbapi_path, str(e)),
                              MessageBox.TYPE_ERROR)

    def openPreview(self):
        self.session.open(CiefpOscamEditorPreview)

    def futureFunction(self):
        self.session.open(MessageBox, get_translation("future_function"), MessageBox.TYPE_INFO, timeout=5)

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
            print(f"Loaded lines: {self.lines}")
            print(f"Setting MenuList with: {self.lines}")
            self["file_list"].setList(self.lines)
        except Exception as e:
            self.lines = [get_translation("file_read_error").format(str(e))]
            print(f"Setting MenuList with error: {self.lines}")
            self["file_list"].setList(self.lines)

    def moveUp(self):
        self["file_list"].up()

    def moveDown(self):
        self["file_list"].down()

    def deleteLine(self):
        current_index = self["file_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.lines):
            selected_line = self.lines[current_index]
            self.session.openWithCallback(
                lambda confirmed: self.deleteLineConfirmed(confirmed, current_index),
                MessageBox,
                get_translation("delete_confirm").format(selected_line),
                MessageBox.TYPE_YESNO
            )
        else:
            self.session.open(MessageBox, get_translation("no_line_selected"), MessageBox.TYPE_ERROR, timeout=5)

    def deleteLineConfirmed(self, confirmed, index):
        if confirmed and index < len(self.lines):
            deleted_line = self.lines.pop(index)
            print(f"Deleted line: {deleted_line}")
            print(f"Updated lines: {self.lines}")
            self["file_list"].setList(self.lines)
            self.session.open(MessageBox, get_translation("line_deleted").format(deleted_line), MessageBox.TYPE_INFO, timeout=5)

    def saveFile(self):
        dvbapi_path = config.plugins.CiefpOscamEditor.dvbapi_path.value
        try:
            os.makedirs(os.path.dirname(dvbapi_path), exist_ok=True)
            with open(dvbapi_path, "w", encoding="utf-8") as f:
                for line in self.lines:
                    f.write(line + "\n")
            print(f"File saved: {dvbapi_path} with {len(self.lines)} lines")
            self.session.open(MessageBox, get_translation("file_saved").format(dvbapi_path), MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            self.session.open(MessageBox, get_translation("file_save_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

class CiefpOscamServerPreview(Screen):
    skin = """
    <screen name="CiefpOscamServerPreview" position="center,center" size="1400,800" title="..:: oscam.server Preview ::..">
        <widget name="file_list" position="10,10" size="980,740" font="Regular;22" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="220,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="430,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="key_blue" position="640,750" size="200,40" font="Bold;20" halign="center" valign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpOscamEditor/background4.png" position="1000,0" size="400,800" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle(get_translation("title_server_preview"))
        self["file_list"] = MenuList([], enableWrapAround=True)
        self["file_list"].l.setItemHeight(26)
        self["key_red"] = Label(get_translation("exit"))
        self["key_green"] = Label(get_translation("FreeCCcam"))
        self["key_yellow"] = Label(get_translation("add_reader"))
        self["key_blue"] = Label(get_translation("delete"))
        self["background"] = Pixmap()
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": self.fetchFreeCCcam,
            "yellow": self.openAddReader,
            "blue": self.openReaderSelect,
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
                    self.lines = [line.rstrip('\n') for line in f]
            else:
                self.lines = [get_translation("file_not_exist").replace("oscam.dvbapi", "oscam.server")]
            print(f"Loaded lines from {server_path}: {self.lines}")
            print(f"Setting MenuList with: {self.lines}")
            self["file_list"].setList(self.lines)
        except Exception as e:
            self.lines = [get_translation("file_read_error").format(str(e))]
            print(f"Setting MenuList with error: {self.lines}")
            self["file_list"].setList(self.lines)

    def moveUp(self):
        self["file_list"].up()

    def moveDown(self):
        self["file_list"].down()

    def openReaderSelect(self):
        self.session.openWithCallback(self.updateLines, CiefpOscamServerReaderSelect, self.lines)

    def openAddReader(self):
        self.session.open(CiefpOscamServerAdd)

    def updateLines(self, updated_lines):
        if updated_lines is not None:
            self.lines = updated_lines
            print(f"Updated lines in CiefpOscamServerPreview: {self.lines}")
            self["file_list"].setList(self.lines)

    def fetch_cccamia_free_cccam():
        url = "https://cccamia.com/cccam-free"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Pronađite sve C linije na stranici - ovo zavisi od HTML strukture stranice
                c_lines = []
                # Pretpostavka da su C linije u <pre> tagu ili nekom sličnom elementu
                for pre_tag in soup.find_all('pre'):
                    text = pre_tag.get_text()
                    # Pronađite sve C linije u tekstu
                    matches = re.findall(r'C:\s*[\w\.-]+\s+\d+\s+\w+\s+[\w\.-]+', text)
                    c_lines.extend(matches)
                return c_lines
            else:
                print(f"Error: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching from cccamia.com: {str(e)}")
            return []

    def fetchFreeCCcam(self):
        def onSourceSelected(choice):
            if choice is None:
                return

            selected_name = choice[0]  # Prikazano ime
            selected_url = choice[1]  # URL

            # Odredi label prema izvoru
            if "cccam-premium.pro" in selected_url:
                label_name = "FreeCCcam_Premium"
            elif "cccamia.com" in selected_url:
                label_name = "CCCamIA_Free"
            elif "cccamiptv.tv" in selected_url:
                label_name = "CCcamIPTV_Free"
            else:
                label_name = "FreeCCcam"

            # Posebna obrada za CCCamIPTV Free
            if "cccamiptv.tv" in selected_url:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Referer": "https://cccamiptv.tv/"
                    }
                    response = requests.get(selected_url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        c_lines = []

                        # Parsiranje specifično za CCCamIPTV - tražimo u div-u sa id="page-content"
                        content_div = soup.find('div', {'id': 'page-content'})
                        if content_div:
                            # Tražimo sve C linije u tekstu
                            matches = re.findall(r'C:\s*[\w\.-]+\s+\d+\s+\w+\s+[\w\.-]+', content_div.get_text())
                            c_lines.extend(matches)

                        if not c_lines:
                            self.session.open(MessageBox, get_translation("no_lines_found").format(get_translation("cccamiptv_free")), MessageBox.TYPE_ERROR, timeout=5)
                            return

                        # Pripremi listu za ChoiceBox
                        choice_list = [(line, line) for line in c_lines]

                        # Prikaži korisniku da izabere liniju
                        self.session.openWithCallback(
                            lambda selected_line: self.addCCcamReader(selected_line, label_name),
                            ChoiceBox,
                            title=f"Izaberite C liniju sa {selected_name}",
                            list=choice_list
                        )
                    else:
                        self.session.open(MessageBox, get_translation("connection_error").format(get_translation("cccamiptv_free"), f"HTTP {response.status_code}"), MessageBox.TYPE_ERROR, timeout=5)
                except Exception as e:
                    self.session.open(MessageBox, f"Greška pri dobijanju C linija sa CCCamIPTV Free: {str(e)}",
                                      MessageBox.TYPE_ERROR, timeout=5)
                return

            # Posebna obrada za CCCamIA Free
            if "cccamia.com" in selected_url:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(selected_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        c_lines = []

                        # Parsiranje specifično za CCCamIA Free
                        for pre_tag in soup.find_all('pre'):
                            text = pre_tag.get_text()
                            matches = re.findall(r'C:\s*[\w\.-]+\s+\d+\s+\w+\s+[\w\.-]+', text)
                            c_lines.extend(matches)

                        if not c_lines:
                            self.session.open(MessageBox, "Nema dostupnih C linija na CCCamIA Free!",
                                              MessageBox.TYPE_ERROR, timeout=5)
                            return

                        # Pripremi listu za ChoiceBox
                        choice_list = [(line, line) for line in c_lines]

                        # Prikaži korisniku da izabere liniju
                        self.session.openWithCallback(
                            lambda selected_line: self.addCCcamReader(selected_line, label_name),
                            ChoiceBox,
                            title=f"Izaberite C liniju sa {selected_name}",
                            list=choice_list
                        )
                    else:
                        self.session.open(MessageBox, f"Greška pri pristupu CCCamIA Free: HTTP {response.status_code}",
                                          MessageBox.TYPE_ERROR, timeout=5)
                except Exception as e:
                    self.session.open(MessageBox, f"Greška pri dobijanju C linija sa CCCamIA Free: {str(e)}",
                                      MessageBox.TYPE_ERROR, timeout=5)
                return

            # Obrada za CCcam Premium
            try:
                html = urllib.request.urlopen(selected_url, timeout=5).read().decode("utf-8", errors="ignore")

                # Traži C: liniju
                match = re.search(r'C:\s*([\w\.-]+)\s+(\d+)\s+(\w+)\s+([^<\s]+)', html)
                if not match:
                    self.session.open(MessageBox, "C-line nije pronađena!", MessageBox.TYPE_ERROR, timeout=5)
                    return

                server, port, user, password = match.groups()

                # ukloni HTML tagove i dekodiraj entitete (ako postoje)
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

        # Lista izvora
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

    def addCCcamReader(self, c_line, label_prefix):
        if not c_line:
            return

        # Parsiraj C liniju
        try:
            # Proveri da li je c_line tuple (ako je došlo iz ChoiceBox-a)
            if isinstance(c_line, tuple):
                c_line = c_line[1]  # Uzmi stvarnu vrednost iz tuple-a

            parts = c_line.split()
            if len(parts) < 4:
                raise ValueError(get_translation("invalid_c_line"))

            server = parts[1]
            port = parts[2]
            user = parts[3]
            password = parts[4] if len(parts) > 4 else "no_password"

            reader_lines = [
                "[reader]",
                f"label                         = {label_prefix}_{user}",
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
            self.session.open(MessageBox, get_translation("reader_added_from").format(f"{label_prefix}_{user}", get_translation("cccamiptv_free")), MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, get_translation("parsing_error").format(str(e)), MessageBox.TYPE_ERROR, timeout=5)

class CiefpOscamServerAdd(ConfigListScreen, Screen):
    skin = """
    <screen name="CiefpOscamServerAdd" position="center,center" size="900,800" title="..:: Add Reader to oscam.server ::..">
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
    <screen name="CiefpOscamServerReaderSelect" position="center,center" size="900,800" title="..:: Select Reader to Delete ::..">
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
            getConfigListEntry(get_translation("language") + ":", config.plugins.CiefpOscamEditor.language)
        ]
        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def save(self):
        config.plugins.CiefpOscamEditor.dvbapi_path.save()
        config.plugins.CiefpOscamEditor.language.save()
        self.session.open(MessageBox, get_translation("settings_saved"), MessageBox.TYPE_INFO, timeout=5)
        self.close()

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