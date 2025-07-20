import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Simulasi Monte Carlo", layout="wide")
st.title("🎲 Simulasi Monte Carlo dari File Excel")

# Upload file
uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    selected_sheet = st.selectbox("Pilih Sheet", sheet_names)
    sheet = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

    st.markdown("#### Data Asli (Semua Baris):")
    st.dataframe(sheet, use_container_width=True)

    numeric_columns = sheet.select_dtypes(include=[np.number]).columns.tolist()
    selected_columns = st.multiselect("Pilih kolom yang ingin disimulasikan:", numeric_columns)
    st.markdown("#### Versi Pembulatan dari Kolom Terpilih:")
    if selected_columns:
        versi_bulat = pd.DataFrame()
        for col in selected_columns:
            versi_bulat[f"{col}_dibulatkan"] = np.round(sheet[col])

        st.dataframe(versi_bulat, use_container_width=True)


    def monte_carlo_table(data):
        data = data[~np.isnan(data)]
        data = np.round(data)
        min_val = int(data.min())
        max_val = int(data.max())
        n = len(data)
        jml_kelas = int(np.ceil(1 + 3.3 * np.log10(n)))  # Rumus Sturges
        rentang = int(np.ceil((max_val - min_val + 1) / jml_kelas))


        interval_list = []
        frekuensi = []
        nilai_tengah = []

        for i in range(jml_kelas):
            lower = min_val + i * rentang
            upper = lower + rentang - 1
            if i == jml_kelas - 1:
                upper = max_val + (rentang - (max_val - lower + 1))
            interval_list.append(f"{lower} - {upper}")
            freq = ((data >= lower) & (data <= upper)).sum()
            frekuensi.append(freq)
            nilai_tengah.append((lower + upper) / 2)

        total = sum(frekuensi)
        probabilitas_raw = [f / total for f in frekuensi]
        probabilitas = [round(p, 2) for p in probabilitas_raw]
        prob_kumulatif = [round(sum(probabilitas_raw[:i+1]), 2) for i in range(len(probabilitas_raw))]
        batas_angka_random = [f"{int(prob_kumulatif[i-1]*100)+1 if i > 0 else 1} - {int(p*100)}" for i, p in enumerate(prob_kumulatif)]

        df = pd.DataFrame({
            "Interval Indeks": interval_list,
            "Nilai Tengah": nilai_tengah,
            "Frekuensi": frekuensi,
            "Probabilitas": probabilitas,
            "Probabilitas Kumulatif": prob_kumulatif,
            "Interval Angka Random": batas_angka_random
        })
        return df

    def simulasi_nilai_rng(rng_series, interval_data):
        hasil_simulasi = []
        interval_ranges = interval_data["Interval Angka Random"]
        nilai_tengah = interval_data["Nilai Tengah"]

        for val in rng_series:
            for i, batas in enumerate(interval_ranges):
                lower, upper = map(int, batas.split(" - "))
                if lower <= val <= upper:
                    hasil_simulasi.append(nilai_tengah[i])
                    break
        return hasil_simulasi

    for col in selected_columns:
        st.markdown(f"### 🔍 Simulasi Monte Carlo: {col}")
        data = sheet[col].values
        result_table = monte_carlo_table(data)
        st.dataframe(result_table, use_container_width=True)

        rng = np.random.randint(1, 100, size=len(data[~np.isnan(data)]))
        simulasi = simulasi_nilai_rng(rng, result_table)

        simulasi_df = pd.DataFrame({
            "RNG": rng,
            "Simulasi": simulasi
        })

        # Hitung persentase kenaikan indeks dari nilai dasar 100
        simulasi_df["% Kenaikan Indeks"] = simulasi_df["Simulasi"] - 100
        simulasi_df["% Kenaikan Indeks"] = simulasi_df["% Kenaikan Indeks"].round(2).astype(str) + "%"  # Format %

        st.subheader("🎲 Hasil Simulasi Berdasarkan RNG")
        st.dataframe(simulasi_df, use_container_width=True)

        # Untuk grafik, tetap butuh angka numerik
        simulasi_df["% Kenaikan Indeks (numeric)"] = simulasi_df["Simulasi"] - 100

        # Tambahkan grafik
        st.subheader("📈 Grafik Simulasi")
        col1, col2 = st.columns(2)

        with col1:
            chart_data1 = simulasi_df[["Simulasi"]].reset_index().rename(columns={"index": "Urutan"})
            chart_data1["Urutan"] += 1
            chart_data1["Kategori"] = col
            st.write("Simulasi")
            line_chart1 = alt.Chart(chart_data1).mark_line().encode(
                x="Urutan",
                y=alt.Y("Simulasi",scale=alt.Scale(domain=[100, 150])),
                color="Kategori"
            ).properties(width=500, height=300)
            st.altair_chart(line_chart1, use_container_width=True)

        with col2:
            chart_data2 = simulasi_df[["% Kenaikan Indeks (numeric)"]].reset_index().rename(columns={"index": "Urutan"})
            chart_data2["Urutan"] += 1
            chart_data2["Kategori"] = col
            st.write("Persentase Kenaikan Indeks (berdasarkan 100)")
            line_chart2 = alt.Chart(chart_data2).mark_line().encode(
                x="Urutan",
                y=alt.Y("% Kenaikan Indeks (numeric)", scale=alt.Scale(zero=False)),
                color="Kategori"
            ).properties(width=500, height=300)
            st.altair_chart(line_chart2, use_container_width=True)
