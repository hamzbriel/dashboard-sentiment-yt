"""Dashboard penelitian komentar YouTube, dijalankan dengan Streamlit."""
from collections import Counter
from pathlib import Path
import re

import emoji
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import chi2_contingency
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from kosakata import EXTRA_SW, LAUGH_RE, PERCEPTION_LEXICON, SLANG

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "Output Notebook/youtube_ai_hasil_analisis (1).csv"
SOURCE = ROOT / "Dataset/youtube_ai_indonesia.csv"
RAW = ROOT / "Dataset/youtube_ai_raw.csv"
STOP = EXTRA_SW | set((ROOT / "stopwords_id.txt").read_text(encoding="utf8").split())
LEX = {k: re.compile(r"\b(?:" + "|".join(map(re.escape, sorted(v, key=len, reverse=True))) + r")\b")
       for k, v in PERCEPTION_LEXICON.items()}
GREEN, RED, SAND = "#176554", "#aa4734", "#a18a5e"
SENT = {"Negatif": RED, "Netral": "#7a827c", "Positif": GREEN}
EMOTIONS = dict(zip(["Trust", "Anticipation", "Fear", "Anger", "Sadness", "Surprise", "Joy", "Disgust"],
                    ["Kepercayaan", "Antisipasi", "Takut", "Marah", "Sedih", "Terkejut", "Gembira", "Jijik"]))
LABEL = {"tema": "Tema", "video_title": "Video", "sentiment": "Sentimen", "emotion": "Emosi",
         "topic": "Topik", "perception": "Persepsi", "comment_type": "Jenis komentar",
         "like_group": "Jumlah suka", "length_group": "Panjang (kata)", "month": "Bulan"}
TOPICS = {"T1": "Manusia dan kesadaran", "T2": "GPT dan chatbot", "T3": "Film dan fiksi ilmiah",
          "T4": "Kepunahan manusia", "T5": "Penggunaan AI dan percakapan video", "T6": "Robot dan pekerjaan"}


def number(n):
    return f"{n:,.0f}".replace(",", ".")


def percent(fraction):
    return f"{fraction * 100:.1f}%".replace(".", ",")


@st.cache_data(show_spinner="Membaca hasil penelitian…")
def load_data(version):
    df = pd.read_csv(RESULT).merge(pd.read_csv(SOURCE, usecols=["comment_id", "total_reply_count"]),
                                   on="comment_id", validate="one_to_one", how="left")
    df["date"] = pd.to_datetime(df.published_at, utc=True).dt.tz_convert("Asia/Jakarta").dt.tz_localize(None)
    df["month"] = df.date.dt.to_period("M").dt.to_timestamp()
    df["topic"] = df.topic.map(lambda s: TOPICS.get(s.split(":")[0], s))
    df["emotion"] = df.emotion.replace(EMOTIONS)
    df["comment_type"] = df.comment_type.replace({"reply": "Balasan", "top_level": "Komentar utama"})
    text = df.text_model.fillna("")
    clean = text.str.lower().str.replace(r"(.)\1{2,}", r"\1\1", regex=True).str.replace(r"[^a-z\s]", " ", regex=True)
    clean = clean.map(lambda s: " ".join(SLANG.get(w, w) for w in s.split()))
    df["tokens"] = clean.map(lambda s: tuple(w for w in s.split() if len(w) >= 3 and w not in STOP and not LAUGH_RE.match(w)))
    for name, pattern in LEX.items():
        df[name] = clean.str.contains(pattern)
    df["words"] = text.str.split().str.len()
    df["emojis"] = text.map(lambda s: tuple(e["emoji"] for e in emoji.emoji_list(s)))
    df["like_group"] = pd.cut(df.like_count, [-1, 0, 1, 5, 20, np.inf], labels=["0", "1", "2–5", "6–20", ">20"])
    df["length_group"] = pd.cut(df.words, [-1, 3, 8, 20, np.inf], labels=["0–3", "4–8", "9–20", ">20"])
    return df


def plot(fig, height=330):
    fig.update_layout(template="plotly_white", height=height, margin=dict(t=15, b=12, l=8, r=18),
                      paper_bgcolor="#fbfaf6", plot_bgcolor="#fbfaf6", font=dict(color="#233a34", size=13),
                      legend_title_text="", legend=dict(orientation="h", y=-0.23), separators=",.")
    fig.update_xaxes(gridcolor="#e3e4dc", zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor="#e3e4dc", zeroline=False, automargin=True)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def bars(series, heading, unit="Komentar", colors=None):
    st.subheader(heading)
    if series.empty:
        st.caption("Belum ada data untuk grafik ini.")
        return
    series = series.sort_values()
    fig = go.Figure(go.Bar(x=series.values, y=series.index.astype(str), orientation="h",
                            marker_color=[(colors or {}).get(k, GREEN) for k in series.index],
                            text=[number(v) for v in series], textposition="auto",
                            hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    fig.update_xaxes(title=unit)
    plot(fig, max(210, min(580, len(series) * 31 + 75)))


def composition(df, group, target):
    counts = pd.crosstab(df[group], df[target])
    totals = counts.sum(axis=1)
    colors = list(SENT.values()) if target == "sentiment" else px.colors.qualitative.Safe
    fig = go.Figure()
    for i, name in enumerate(counts):
        fig.add_bar(name=name, x=100 * counts[name] / totals, y=counts.index.astype(str), orientation="h",
                    marker_color=SENT.get(name, colors[i % len(colors)]),
                    customdata=np.column_stack((counts[name], totals)),
                    hovertemplate="%{y}<br>%{fullData.name} · %{x:.1f}%<br>%{customdata[0]} dari %{customdata[1]} komentar<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="Persentase komentar dalam kelompok", range=[0, 100])
    plot(fig, max(300, len(counts) * 40 + 120))


def overview(d):
    neg = d.sentiment.eq("Negatif").mean()
    st.header("Nada percakapan")
    st.markdown(f"**{percent(neg)}** komentar dalam pilihan ini diprediksi bernada negatif. "
                f"Emosi yang paling sering muncul adalah **{d.emotion.mode().iat[0].lower()}**.")
    a, b = st.columns(2)
    with a:
        bars(d.sentiment.value_counts(), "Distribusi sentimen", colors=SENT)
    with b:
        bars(d.emotion.value_counts(), "Distribusi emosi")
    st.divider()
    st.subheader("Bagaimana AI dipersepsikan?")
    counts = d.perception.value_counts().reindex([*LEX, "Tidak terkategori"], fill_value=0)
    matched = int(counts.iloc[:3].sum())
    table = pd.DataFrame({"Kategori": counts.index, "Komentar": counts.values,
                          "Dari semua pilihan": [percent(v / len(d)) for v in counts],
                          "Dari yang terkategori": [percent(v / matched) if matched and k in LEX else "—"
                                                      for k, v in counts.items()]})
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(f"{number(matched)} komentar cocok dengan kamus persepsi. Satu kategori utama dipilih berdasarkan jumlah kecocokan kata.")
    with st.expander("Kata kunci yang muncul bersama"):
        flags = d[list(LEX)].astype(int)
        matrix = flags.T @ flags
        plot(px.imshow(matrix, text_auto=True, color_continuous_scale="Greens", labels={"color": "Komentar"}))
        st.caption("Satu komentar dapat memuat kata kunci dari beberapa kategori. Diagonal menunjukkan total kecocokan per kategori.")


def compare(d):
    st.header("Perbandingan kelompok")
    a, b = st.columns(2)
    group = a.selectbox("Bandingkan menurut", ["tema", "video_title", "topic", "perception", "comment_type", "like_group", "length_group", "sentiment"], format_func=LABEL.get)
    targets = [key for key in ["sentiment", "emotion", "perception", "topic"] if key != group]
    target = b.selectbox("Distribusi", targets, format_func=LABEL.get)
    if target == "perception" and st.checkbox("Hanya komentar yang cocok dengan kamus persepsi"):
        d = d[d.perception != "Tidak terkategori"]
        if d.empty:
            st.info("Tidak ada komentar terkategori dalam pilihan ini.")
            return
    composition(d, group, target)
    table = d.groupby(group, observed=True).agg(Komentar=("sentiment", "size"), Polaritas=("polarity", "mean"),
                                                Suka=("like_count", "mean"), SD=("polarity", "std"))
    error = 1.96 * table.SD / np.sqrt(table.Komentar)
    table["Batas bawah 95%"] = table.Polaritas - error
    table["Batas atas 95%"] = table.Polaritas + error
    st.dataframe(table.drop(columns="SD").rename_axis(LABEL[group]).sort_values("Komentar", ascending=False).round(3), width="stretch")
    st.caption("Polaritas rata-rata menggunakan skor −1, 0, +1. Suka adalah rata-rata per komentar. Interval normal 95% bersifat deskriptif.")
    ct = pd.crosstab(d[group], d[target])
    if min(ct.shape) > 1:
        chi, p, _, _ = chi2_contingency(ct, correction=False)
        v = np.sqrt(chi / (ct.values.sum() * (min(ct.shape) - 1)))
        st.caption(f"Asosiasi antarkategori · Cramér’s V = {v:.3f} · p = {p:.2g}. Kelompok kecil dan balasan dalam utas yang sama membatasi interpretasi uji.")
    st.caption(f"Jika setiap video terpilih berbobot sama, rata-rata persentase negatif adalah {percent(d.sentiment.eq('Negatif').groupby(d.video_title).mean().mean())}.")


def activity(d):
    st.header("Ritme percakapan")
    step = st.radio("Interval waktu", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    counts = d.set_index("date").resample({"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}[step]).size()
    fig = go.Figure(go.Scatter(x=counts.index, y=counts.values, name="Komentar", line=dict(color=GREEN), fill="tozeroy", fillcolor="rgba(23,101,84,.10)"))
    if step == "Harian":
        fig.add_scatter(x=counts.index, y=counts.rolling(7, min_periods=1).mean(), name="Rerata 7 hari", line=dict(color=RED))
    fig.update_yaxes(title="Komentar")
    plot(fig)
    st.subheader("Jam aktif sepanjang pekan")
    heat = pd.crosstab(d.date.dt.dayofweek, d.date.dt.hour).reindex(index=range(7), columns=range(24), fill_value=0)
    heat.index = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    plot(px.imshow(heat, aspect="auto", color_continuous_scale="Greens", labels=dict(x="Pukul (WIB)", y="Hari", color="Komentar")))
    st.subheader("Perubahan komposisi bulanan")
    target = st.radio("Label bulanan", ["sentiment", "emotion"], format_func=LABEL.get, horizontal=True)
    ct = pd.crosstab(d.month, d[target])
    plot(px.line(ct.div(ct.sum(axis=1), axis=0) * 100, markers=True,
                 labels={"month": "Bulan", "value": "Persentase komentar"}, color_discrete_map=SENT))
    a, b = st.columns(2)
    with a:
        bars(d.like_group.value_counts(), "Suka per komentar")
    with b:
        bars(d.comment_type.value_counts(), "Komentar utama dan balasan")
    st.caption(f"{percent(d.like_count.eq(0).mean())} komentar tanpa suka. Total balasan tercatat pada komentar utama dalam pilihan ini: {number(d.total_reply_count.sum())}.")


def topics(d):
    st.header("Topik dan bahasa")
    bars(d.topic.value_counts(), "Kelompok topik NMF")
    st.caption("Topik berasal dari pemodelan seluruh korpus. Filter mengubah jumlah komentar pada tiap topik.")
    mode = st.radio("Eksplorasi kosakata", ["Kata & frasa", "WordCloud", "TF-IDF per video", "Kata khas per kelas", "Ciri teks"], horizontal=True)
    tokens = d.tokens
    words = Counter(w for row in tokens for w in row)
    if mode == "Kata & frasa":
        pairs = Counter(" ".join(pair) for row in tokens for pair in zip(row, row[1:]))
        a, b = st.columns(2)
        with a:
            bars(pd.Series(dict(words.most_common(12))), "Kata teratas", "Kemunculan")
        with b:
            bars(pd.Series(dict(pairs.most_common(12))), "Frasa dua kata", "Kemunculan")
    elif mode == "WordCloud" and words:
        cloud = WordCloud(width=1100, height=410, background_color="#fbfaf6", colormap="viridis", random_state=42,
                          max_words=85).generate_from_frequencies(words)
        st.image(cloud.to_array(), width="stretch", caption="Ukuran kata mengikuti frekuensi pada komentar terpilih.")
    elif mode == "TF-IDF per video" and words:
        docs = d.groupby("video_title").tokens.apply(lambda group: " ".join(w for row in group for w in row))
        vec = TfidfVectorizer(tokenizer=str.split, token_pattern=None)
        scores = vec.fit_transform(docs)
        vocab = vec.get_feature_names_out()
        terms = []
        for title, row in zip(docs.index, scores):
            inds = row.indices[np.argsort(-row.data)[:10]]
            terms.append({"Video": title, "Kata berbobot tertinggi": ", ".join(vocab[inds])})
        st.dataframe(terms, width="stretch", hide_index=True)
    elif mode == "Kata khas per kelas" and words:
        col = st.selectbox("Kelompok label", ["sentiment", "emotion"], format_func=LABEL.get)
        lab = st.selectbox("Kelas", sorted(d[col].unique()))
        inside = Counter(w for row in d.loc[d[col].eq(lab), "tokens"] for w in row)
        freq_docs = Counter(w for row in tokens for w in set(row))
        terms = [w for w in words if freq_docs[w] >= (5 if col == "sentiment" else 4)]
        if terms and d[col].nunique() > 1:
            a = np.array([inside[w] + .5 for w in terms])
            b = np.array([words[w] - inside[w] + .5 for w in terms])
            z = (np.log(a / a.sum()) - np.log(b / b.sum())) / np.sqrt(1/a + 1/b)
            st.dataframe(pd.DataFrame({"Kata": terms, "Skor log-odds": z, "Kemunculan di kelas": a.astype(int)}).nlargest(12, "Skor log-odds"), hide_index=True)
        else:
            st.info("Pilih lebih banyak komentar dan sedikitnya dua kelas untuk membandingkan kosakata.")
    elif mode == "Ciri teks":
        t = d.text_model.fillna("")
        signals = {"Emoji": d.emojis.map(bool).sum(), "Tanda seru": t.str.contains("!", regex=False).sum(),
                   "Tanda tanya": t.str.contains("?", regex=False).sum(),
                   "Kata kapital": t.str.contains(r"\b[A-Z]{4,}\b").sum(),
                   "Tawa": t.str.contains(r"\b(?:wk)+w?k?\b|\b(?:ha){2,}|\b(?:he){2,}|\bxi+xi+", case=False).sum()}
        a, b = st.columns(2)
        with a:
            bars(pd.Series(signals), "Ekspresi dalam teks")
        with b:
            bars(d.length_group.value_counts(), "Panjang komentar")
        emojis = Counter(e for row in d.emojis for e in row)
        st.caption(f"Median {number(d.words.median())} kata · {number(t.duplicated().sum())} pengulangan teks setelah kemunculan pertama.")
        if emojis:
            bars(pd.Series(dict(emojis.most_common(8))), "Emoji teratas", "Kemunculan")
    else:
        st.info("Pilihan ini tidak memiliki kata yang lolos penyaringan.")


def methods(d, full):
    st.header("Kualitas prediksi dan sumber data")
    st.write("Sentimen diprediksi oleh IndoBERT (taufiqdp/indonesian-sentiment), dan emosi oleh EmoSense-ID. "
             "Anotasi manual dilewati. Akurasi pada komentar proyek ini belum diukur.")
    a, b = st.columns(2)
    for container, col, title in [(a, "sent_conf", "Keyakinan model sentimen"), (b, "emo_conf", "Keyakinan model emosi")]:
        with container:
            st.subheader(title)
            plot(px.histogram(d, x=col, nbins=25, range_x=[0, 1], color_discrete_sequence=[GREEN],
                              labels={col: "Probabilitas kelas terpilih"}).update_yaxes(title="Komentar"), 240)
    high = (d.sent_conf > .7) & (d.emo_conf > .6)
    bars(pd.Series({"Keyakinan rendah": ((d.sent_conf < .5) | (d.emo_conf < .35)).sum(),
                    "Positif + emosi negatif": (high & d.sentiment.eq("Positif") & d.emotion.isin(["Marah", "Takut", "Jijik", "Sedih"])).sum(),
                    "Negatif + gembira / kepercayaan": (high & d.sentiment.eq("Negatif") & d.emotion.isin(["Gembira", "Kepercayaan"])).sum()}), "Prediksi untuk ditelaah")
    st.caption("Keyakinan rendah mengikuti ambang notebook (sentimen < 0,50 atau emosi < 0,35). Dua kombinasi lainnya memakai sentimen > 0,70 dan emosi > 0,60.")
    with st.expander("Sebaran keyakinan per kelas dan entropi emosi"):
        dimension = st.radio("Model", ["Sentimen", "Emosi"], horizontal=True)
        label, confidence = ("sentiment", "sent_conf") if dimension == "Sentimen" else ("emotion", "emo_conf")
        plot(px.box(d, x=label, y=confidence, points=False, labels={label: dimension, confidence: "Keyakinan model"}))
        probs = d.filter(regex="^p_emo_").to_numpy()
        entropy = -(probs * np.log(np.clip(probs, 1e-12, 1))).sum(axis=1)
        plot(px.histogram(x=entropy, nbins=30, labels={"x": "Entropi emosi (nat)"}).update_yaxes(title="Komentar"), 250)
        st.caption("Entropi tinggi berarti probabilitas lebih tersebar di antara delapan kelas emosi.")
    with st.expander("Cakupan pengumpulan per video"):
        raw = pd.read_csv(RAW, usecols=["video_title"]).video_title.value_counts()
        final = full.video_title.value_counts()
        coverage = pd.DataFrame({"Baris mentah": raw, "Dataset final": final, "Dalam pilihan": d.video_title.value_counts()}).fillna(0).astype(int)
        coverage["Retensi bahasa dan pembersihan"] = (final / raw).map(percent)
        st.dataframe(coverage.loc[d.video_title.unique()], width="stretch")
    st.caption("Sumber: komentar publik YouTube Data API v3. Agregat menggambarkan sepuluh video terpilih. "
               "Bahasa informal, sarkasme, dan pemilihan video membatasi generalisasi. Waktu ditampilkan dalam WIB.")


def reset_filters():
    for k in list(st.session_state):
        if k.startswith("filter_"):
            del st.session_state[k]


def main():
    st.set_page_config(page_title="Percakapan AI · Telematika", layout="wide")
    st.markdown("""<style>
    .stMainBlockContainer{max-width:1450px;padding-top:2.6rem}
    h1,h2{font-family:Georgia,'Times New Roman',serif!important;font-weight:500!important;letter-spacing:-.035em}
    h1{font-size:clamp(2.8rem,6vw,5rem)!important;line-height:1.04!important}
    h3{font-size:1.1rem!important;letter-spacing:-.015em}
    [data-testid="stMetric"]{border-top:2px solid #628478;padding:.6rem 0}
    [data-testid="stMetricValue"]{font-family:Georgia,serif;font-variant-numeric:tabular-nums}
    </style>""", unsafe_allow_html=True)
    full = load_data((RESULT.stat().st_mtime_ns, SOURCE.stat().st_mtime_ns))
    d = full
    with st.sidebar:
        st.header("Filter data")
        st.caption("Pilihan kosong mencakup semua nilai. Filter berbeda diterapkan bersama.")
        for col in ["tema", "video_title", "sentiment", "emotion", "topic", "perception", "comment_type"]:
            options = sorted(full[col].unique())
            if col == "video_title":
                options = sorted(d[col].unique())
                if "filter_video_title" in st.session_state:
                    st.session_state.filter_video_title = [v for v in st.session_state.filter_video_title if v in options]
            values = st.multiselect(LABEL[col], options, placeholder="Semua", key="filter_" + col)
            if values:
                d = d[d[col].isin(values)]
        lo, hi = full.date.min().date(), full.date.max().date()
        dates = st.date_input("Tanggal publikasi (WIB)", (lo, hi), min_value=lo, max_value=hi, key="filter_date")
        if len(dates) == 2:
            d = d[d.date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]) + pd.Timedelta(days=1), inclusive="left")]
        st.button("Reset semua filter", on_click=reset_filters)
    st.caption("TELEMATIKA   /   ANALISIS MEDIA SOSIAL")
    st.title("Percakapan tentang AI")
    st.write("Sentimen, emosi, dan persepsi dalam komentar YouTube berbahasa Indonesia.")
    if d.empty:
        st.info("Tidak ada komentar yang cocok. Longgarkan pilihan atau reset semua filter.")
        st.stop()
    for col, (name, val) in zip(st.columns(4), [("Komentar terpilih", number(len(d))), ("Video", number(d.video_title.nunique())),
                                               ("Tema video", number(d.tema.nunique())), ("Cakupan dataset", percent(len(d)/len(full)))]):
        col.metric(name, val)
    sections = {"Ringkasan": overview, "Perbandingan": compare, "Aktivitas": activity, "Topik & kata": topics, "Metode": methods}
    page = st.segmented_control("Analisis", list(sections), default="Ringkasan", selection_mode="single", label_visibility="collapsed")
    if page == "Metode":
        methods(d, full)
    else:
        sections[page or "Ringkasan"](d)


if __name__ == "__main__":
    main()
