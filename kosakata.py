"""Aturan leksikal dari notebook analisis, bagian 3 dan 7."""
import re

EXTRA_SW = set("""
ai video youtube channel komen komentar nya banget bgt sih deh dong kok kan tuh nih aja saja gak ga nggak ngga iya ya yah
udah sudah bang pak bu mas kak bro om min admin pas jadi bisa kalau kalo kayak seperti lagi masih sama juga cuma cuman emang
memang terus soalnya karena kita kami kamu saya aku gue gw lu orang banyak sangat lebih tapi tetap dalam akan harus lalu
bukan hanya yg dg dgn tidak dan yang untuk dengan dari ini itu ada apa mau kasih lihat bikin udh klo krn
""".split())

SLANG = {
    "yg": "yang", "gak": "tidak", "ga": "tidak", "nggak": "tidak", "ngga": "tidak", "gk": "tidak", "tdk": "tidak",
    "dgn": "dengan", "dg": "dengan", "utk": "untuk", "krn": "karena", "karna": "karena", "sdh": "sudah",
    "udh": "sudah", "udah": "sudah", "blm": "belum", "jg": "juga", "jd": "jadi", "bgt": "banget", "aja": "saja",
    "sy": "saya", "gw": "saya", "gue": "saya", "lu": "kamu", "dr": "dari", "org": "orang", "klo": "kalau",
    "kalo": "kalau", "tp": "tapi", "bs": "bisa", "pake": "pakai", "emg": "memang", "emang": "memang",
    "mnrt": "menurut", "hrs": "harus", "kyk": "seperti", "kayak": "seperti", "pd": "pada", "sm": "sama",
    "bkn": "bukan", "tau": "tahu", "bikin": "membuat", "trus": "terus", "dlm": "dalam", "skrg": "sekarang",
    "pekerjaaan": "pekerjaan", "kerjaan": "pekerjaan", "kerja2": "kerja",
}

LAUGH_RE   = re.compile(r"^(wk)+a?$|^(ha)+h?$|^(he)+h?$|^(xi)+$|^(wa)+$")

PERCEPTION_LEXICON = {
    "Ancaman": ["ganti", "gantikan", "menggantikan", "pengangguran", "phk", "bahaya", "berbahaya", "takut", "ancam", "ancaman",
                "hilang", "kehilangan", "punah", "bohong", "dibohongi", "hoax", "hoaks", "kiamat", "tersingkir", "miskin", "ngeri",
                "seram", "mengerikan", "khawatir", "cemas", "waspada", "rusak", "merusak", "menyesatkan", "malas", "bodoh",
                "dibodohi", "dikuasai", "menguasai", "mengambil alih", "lapangan kerja hilang"],
    "Peluang": ["peluang", "kesempatan", "cuan", "income", "pendapatan", "penghasilan", "bisnis", "usaha", "karir", "karier",
                "skill", "keahlian", "belajar", "berkembang", "maju", "inovasi", "masa depan", "tumbuh", "untung", "manfaat",
                "lapangan kerja", "adaptasi", "beradaptasi", "upgrade", "naik level", "kesempatan emas"],
    "Alat Bantu": ["alat", "membantu", "bantu", "tools", "tool", "asisten", "produktif", "produktivitas", "efisien", "efisiensi",
                   "mempermudah", "memudahkan", "praktis", "dimanfaatkan", "manfaatkan", "pendukung", "kolaborasi", "partner", "copilot"],
}
