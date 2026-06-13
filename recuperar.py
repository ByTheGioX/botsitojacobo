import json, os

# Los 9 envios de ayer (30/5): (booking_code, telefono limpio)
entries = [
    ("23/5_16:00_4e",  "34635122835"),
    ("23/5_17:30_maf", "34603458949"),
    ("23/5_19:00_maf", "34649814146"),
    ("24/5_19:00_4e",  "34649515037"),
    ("24/5_16:10_csi", "34635280014"),
    ("29/5_17:30_4e",  "34610648642"),
    ("29/5_17:40_csi", "34651560074"),
    ("30/5_11:30_4e",  "34647357305"),
    ("30/5_14:40_csi", "31657059941"),
]

ts = "2026-05-30T17:20:00"   # hora real del envio de ayer
pending = []
for code, phone in entries:
    pending.append({
        "wa_link": "https://api.whatsapp.com/send?phone=" + phone,
        "timestamp_sent": ts,
        "booking_code": code,
        "booking_day": code.split('/')[0],
        "booking_time": code.split('_')[1],
        "booking_place": "",
    })

fp = os.path.join("data", "pending_replies.json")
with open(fp, "w", encoding="utf-8") as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)
print("OK:", len(pending), "entradas recuperadas en", fp)
