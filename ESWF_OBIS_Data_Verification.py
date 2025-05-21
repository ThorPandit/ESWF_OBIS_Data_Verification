import re
from tkinter import filedialog, messagebox, Tk
from datetime import datetime
import csv

from Tools.scripts.mailerdaemon import emparse_list_from

# === ESWF BIT MEANINGS ===
ESWF_MEANINGS = {
    3: "Over Voltage", 4: "Low Voltage", 11: "Over current in any phase",
    51: "Earth Loading", 61: "Module cover restore", 62: "Single wire restore",
    81: "Magnet Influence", 82: "Neutral disturbance", 83: "Meter cover open",
    84: "Load disconnected/connected", 85: "Last Gasp - Power Outage",
    86: "First Breath - Power Restore", 87: "Billing Counter Increment",
    90: "LRCF Availed", 91: "NIC Firmware Upgrade", 92: "Module Firmware Upgrade",
    93: "Firmware Upgrade", 103: "RTC battery - Low", 119: "Main battery - Low"
}

# === File Selection ===
root = Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select gurux.txt",
    filetypes=[("Text files", "*.txt")]
)
if not file_path:
    messagebox.showwarning("No file selected", "You must select a file.")
    exit()

# === Load file content ===
with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# === OBIS Push Event Counts ===
obis_counts = {
    "Self Registration": content.count("0.130.25.9.0.255"),
    "Load Survey Push": content.count("0.5.25.9.0.255"),
    "Instant Push": content.count("0.0.25.9.0.255"),
    "Daily Energy": content.count("0.6.25.9.0.255"),
    "Tamper Push": content.count("0.134.25.9.0.255"),
    "Bill Push": content.count("0.132.25.9.0.255"),
    "Outage Push": content.count("0.4.25.9.0.255")
}

# === Regex for OBIS 0.4.25.9.0.255 + ESWF BitString ===
pattern = re.compile(
    r'<Structure Qty="04".*?<String Value="(.*?)".*?'
    r'<OctetString Value="(0004190900FF)".*?'
    r'<OctetString Value="([0-9A-F]{24})".*?'
    r'<BitString Value="([01]{128})"',
    re.DOTALL
)

matches = pattern.findall(content)
results = []
outage_count = restore_count = alert_count =Billing_Counter_Increment_count =Low_Voltage_count= Mainbattery_Low_count=RTCbattery_Low_count=FWUpgrade_count=ModuleFW_upgrade_count=NICFW_upgrade_count=LRCF_count=Load_disconnected_connected_count=Meter_cover_open_count=Neutral_disturbance_count=Magnet_Influence_count=Single_wire_restore_count=Module_cover_restore_count=Earth_loading_count=Over_current_count=Over_Voltage_count=alert_count= 0

def parse_dlms_datetime(hex_str):
    year = int(hex_str[0:4], 16)
    month = int(hex_str[4:6], 16)
    day = int(hex_str[6:8], 16)
    hour = int(hex_str[10:12], 16)
    minute = int(hex_str[12:14], 16)
    second = int(hex_str[14:16], 16)
    return datetime(year, month, day, hour, minute, second)

# === Parse each matched entry ===
for meter, obis, dt_hex, bitstring in matches:
    dt = parse_dlms_datetime(dt_hex)
    bits = [i for i, b in enumerate(bitstring) if b == '1']
    meanings = [ESWF_MEANINGS.get(i) for i in bits if i in ESWF_MEANINGS]

    if 85 in bits:
        event_type = "Power Outage"
        outage_count += 1
    elif 86 in bits:
        event_type = "Power Restore"
        restore_count += 1
    elif 3 in bits:
        event_type = "Over Voltage"
        Over_Voltage_count += 1
    elif 4 in bits:
        event_type ="Low Voltage"
        Low_Voltage_count += 1
    elif 11 in bits:
        event_type ="Over current in any phase"
        Over_current_count+=1
    elif 51 in bits:
        event_type="Earth Loading"
        Earth_loading_count+=1
    elif 61 in bits:
        event_type="Module cover restore"
        Module_cover_restore_count+=1
    elif 62 in bits:
        event_type="Single wire restore"
        Single_wire_restore_count+=1
    elif 81 in bits:
        event_type="Magnet Influence"
        Magnet_Influence_count+=1
    elif 82 in bits:
        event_type="Neutral disturbance"
        Neutral_disturbance_count+=1
    elif 83 in bits:
        event_type="Meter cover open"
        Meter_cover_open_count+=1
    elif 84 in bits:
        event_type="Load disconnected/connected"
        Load_disconnected_connected_count+=1
    elif 87 in bits:
        event_type="Billing Counter Increment"
        Billing_Counter_Increment_count+=1
    elif 90 in bits:
        event_type="LRCF Availed"
        LRCF_count+=1
    elif 91 in bits:
        event_type="NIC Firmware Upgrade"
        NICFW_upgrade_count+=1
    elif 92 in bits:
        event_type="Module Firmware Upgrade"
        ModuleFW_upgrade_count+=1
    elif 93 in bits:
        event_type="Firmware Upgrade"
        FWUpgrade_count+=1
    elif 103 in bits:
        event_type="RTC battery - Low"
        RTCbattery_Low_count+=1
    elif 119 in bits:
        event_type="Main battery - Low"
        Mainbattery_Low_count+=1
    elif meanings:
        event_type = "Alert"
        alert_count += 1
    else:
        event_type = "Unknown"

    results.append({
        "Timestamp": dt,
        "Meter": meter,
        "Event Type": event_type,
        "Meaning": "; ".join(m for m in meanings if m),
        "Bits Set": ", ".join(str(b) for b in bits)
    })

# === Save Events to CSV ===
output_csv = file_path.replace(".txt", "_eswf_results.csv")
with open(output_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Timestamp", "Meter", "Event Type", "Meaning", "Bits Set"])
    writer.writeheader()
    writer.writerows(results)

# === Save OBIS push counts to .txt file ===
output_log = file_path.replace(".txt", "_obis_counts.txt")
with open(output_log, "w") as f:
    f.write("OBIS Push Event Counts:\n")
    for k, v in obis_counts.items():
        f.write(f"{k}: {v}\n")

# === Summary Popup ===
summary = f"""
==================================================================
ESWF Event Analysis Completed, Total Parsed Events: {len(results)}
3:   Over Voltage: {Over_Voltage_count}
4:   Low Voltage: {Low_Voltage_count}
11:  Over current in any phase:{Over_current_count}
51:  Earth Loading:{Earth_loading_count}
61:  Module cover restore:{Module_cover_restore_count}
62:  Single wire restore:{Single_wire_restore_count}
81:  Magnet Influence:{Magnet_Influence_count}
82:  Neutral disturbance:{Neutral_disturbance_count}
83:  Meter cover open:{Meter_cover_open_count}
84:  Load disconnected/connected: {Load_disconnected_connected_count}
85:  Last Gasp - Power Outages: {outage_count}
86:  First Breath - Power Restore: : {restore_count}
87:  Billing Counter Increment: {Billing_Counter_Increment_count}
90:  LRCF Availed:{LRCF_count}
91:  NIC Firmware Upgrade:{NICFW_upgrade_count}
92:  Module Firmware Upgrade: {ModuleFW_upgrade_count}
93:  Firmware Upgrade: {FWUpgrade_count}
103: RTC battery - Low: {RTCbattery_Low_count}
119: Main battery - Low: {Mainbattery_Low_count}
Alerts: {alert_count}
-

--- OBIS Push Event Counts ---
Self Registration: {obis_counts['Self Registration']}
Load Survey Push: {obis_counts['Load Survey Push']}
Instant Push: {obis_counts['Instant Push']}
Daily Energy: {obis_counts['Daily Energy']}
Tamper Push: {obis_counts['Tamper Push']}
Bill Push: {obis_counts['Bill Push']}
Alert Push: {obis_counts['Outage Push']}

Results saved to:
- {output_csv}
- {output_log}

For any issue Contact to : Shubham Kumar Bhardwaj
"""
messagebox.showinfo("ESWF Summary", summary)
