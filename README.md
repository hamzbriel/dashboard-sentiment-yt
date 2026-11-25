# Percakapan tentang AI di YouTube Indonesia

Dashboard Streamlit untuk mengeksplorasi **14.215 komentar berbahasa Indonesia dari 10 video YouTube** dalam lima tema tentang kecerdasan buatan. Dashboard ini dikembangkan untuk Mini Proyek Telematika dan membaca hasil analisis yang sudah disimpan dalam CSV. Pengguna dapat langsung membandingkan video tanpa menjalankan notebook atau menyiapkan kunci YouTube Data API.

## Menjalankan secara lokal

Proyek ini telah diuji dengan Python 3.13. Dari folder utama repository, jalankan perintah berikut di PowerShell. Perintah memakai interpreter virtual environment secara langsung sehingga aktivasi tidak diperlukan.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Untuk macOS atau Linux, gunakan `python3 -m venv .venv`, lalu ganti `.\.venv\Scripts\python.exe` dengan `./.venv/bin/python` pada dua perintah berikutnya. Buka alamat lokal yang dicetak Streamlit di terminal, biasanya [localhost:8501](http://localhost:8501).

## Menggunakan dashboard

Saat pertama dibuka, dashboard menampilkan seluruh dataset. Gunakan panel kiri untuk memilih beberapa tema sekaligus, lalu pilih video dari tema tersebut. Hasil bisa dipersempit lagi menurut sentimen, emosi, topik, persepsi, jenis komentar, atau rentang tanggal publikasi dalam WIB. Filter yang kosong mencakup semua nilai. Tombol **Reset semua filter** mengembalikan pilihan awal.

| Tampilan | Pertanyaan yang dapat dijawab |
| --- | --- |
| Ringkasan | Bagaimana distribusi sentimen dan emosi? Berapa banyak komentar yang memuat kata kunci ancaman, peluang, atau alat bantu? |
| Perbandingan | Bagaimana proporsi tersebut berubah antarvideo atau antartema, dan berapa jumlah komentar di balik tiap persentase? |
| Aktivitas | Kapan diskusi paling aktif? Bagaimana komposisi bulanan, jumlah suka, serta perbandingan komentar utama dan balasan? |
| Topik & kata | Kata, frasa, dan topik NMF apa yang menonjol? Jelajahi WordCloud, TF-IDF per video, kata khas per kelas, dan ciri teks. |
| Metode | Seberapa yakin model saat memilih kelas? Bagaimana cakupan pengumpulan dan penyaringan data per video? |

Untuk mencoba perbandingan, pilih tema **Risiko & Kekhawatiran** dan **Pendidikan**, buka **Perbandingan**, lalu pilih **Tema** dan **Sentimen**. Grafik memperlihatkan persentase di dalam masing-masing tema. Tabel di bawahnya menunjukkan perbedaan ukuran sampelnya.

## Berkas yang diperlukan

Pertahankan nama dan lokasi ketiga CSV berikut relatif terhadap `dashboard.py`. Jika CSV disediakan terpisah dari kode, salin ke lokasi ini sebelum menjalankan aplikasi.

| Berkas | Kegunaan |
| --- | --- |
| `Output Notebook/youtube_ai_hasil_analisis (1).csv` | Sumber utama untuk filter, teks olahan, prediksi sentimen dan emosi, probabilitas, topik, serta persepsi. |
| `Dataset/youtube_ai_indonesia.csv` | Menambahkan jumlah balasan melalui kolom `comment_id` dan `total_reply_count`. |
| `Dataset/youtube_ai_raw.csv` | Menghitung jumlah baris mentah per video untuk membandingkan cakupan sebelum dan sesudah penyaringan. Dashboard hanya membaca kolom `video_title` dari berkas ini. |

Aturan normalisasi dan kamus persepsi berada di `kosakata.py`. Daftar stopword bahasa Indonesia tersedia secara lokal di `stopwords_id.txt` dari korpus NLTK. Tema antarmuka diatur melalui `.streamlit/config.toml`.

## Membaca hasil dan membagikan data

Sentimen dan emosi merupakan prediksi model pralatih. Evaluasi dengan anotasi manual tidak dilakukan pada dataset ini sehingga akurasi model pada sampel belum diketahui. Persepsi dihitung dengan pencocokan kata kunci. Pada tampilan Ringkasan, perhatikan perbedaan penyebut antara **semua komentar terpilih** dan **komentar yang berhasil dikategorikan**. Hasil menggambarkan percakapan pada sepuluh video terpilih.

Dashboard menampilkan agregat, tetapi kedua CSV sumber di folder `Dataset` memuat kolom `author`, dan CSV hasil analisis memuat teks komentar serta ID. Jika repository akan dibuka untuk publik, tinjau berkas yang dibagikan. Untuk dua CSV sumber, salinan yang hanya memuat kolom yang disebutkan pada tabel di atas sudah cukup untuk menjalankan aplikasi.
