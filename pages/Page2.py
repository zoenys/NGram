import streamlit as st
import pandas as pd
from collections import defaultdict
import ast

# Fungsi untuk menghitung frekuensi n-gram
def calculate_ngram_frequencies(all_tokens, n):
    ngram_counts = defaultdict(dict)
    for i in range(len(all_tokens) - n):
        ngram = tuple(all_tokens[i:i+n])
        next_token = all_tokens[i+n]
        if next_token not in ngram_counts[ngram]:
            ngram_counts[ngram][next_token] = 0
        ngram_counts[ngram][next_token] += 1
    return ngram_counts

# Fungsi untuk menghitung probabilitas dari frekuensi n-gram
def calculate_ngram_probabilities(ngram_counts):
    ngram_probs = {}
    for ngram, next_tokens in ngram_counts.items():
        sum_of_counts = sum(next_tokens.values())
        ngram_probs[ngram] = {
            next_token: count / sum_of_counts
            for next_token, count in next_tokens.items()
        }
    return ngram_probs

# Fungsi untuk memilih token dengan probabilitas tertinggi
def sample_next_token(ngram, ngram_probs):
    if ngram in ngram_probs:
        # Pilih token dengan probabilitas tertinggi menggunakan max()
        next_token_sampled = max(ngram_probs[ngram], key=ngram_probs[ngram].get)
        return next_token_sampled
    else:
        return None  # Jika n-gram tidak ditemukan

# Fungsi untuk menghasilkan teks berdasarkan n-gram
def generate_text(start_tokens, ngram_probs, n_words_to_generate, n):
    text = " ".join(start_tokens)
    current_ngram = tuple(start_tokens[-n:])  # Memulai dengan n-gram terakhir
    generated_tokens = start_tokens[:]
    
    for _ in range(n_words_to_generate):
        next_token = sample_next_token(current_ngram, ngram_probs)
        if next_token is None:
            break
        generated_tokens.append(next_token)
        text += " " + next_token
        current_ngram = tuple(list(current_ngram[1:]) + [next_token])  # Perbarui n-gram
    return text, generated_tokens

# Fungsi untuk menghitung perplexity dari teks yang dihasilkan
# Fungsi untuk menghitung perplexity dari teks yang dihasilkan
def calculate_perplexity(text_tokens, ngram_probs, n):
    if len(text_tokens) <= n:
        return '-'  # Jika terlalu sedikit token untuk dihitung perplexity
    
    perplexity = 1
    N = len(text_tokens)
    
    try:
        for i in range(n, N):
            ngram = tuple(text_tokens[i-n:i])  # N-gram terakhir
            next_token = text_tokens[i]
            if ngram in ngram_probs and next_token in ngram_probs[ngram]:
                perplexity *= 1 / ngram_probs[ngram][next_token]
            else:
                perplexity *= 1 / 1e-9  # Asumsikan probabilitas sangat kecil jika tidak ditemukan
        return perplexity ** (1 / (N - n))
    except ZeroDivisionError:
        return '-'  # Jika ada pembagian dengan nol, tampilkan '-'

df = pd.read_csv('pages/new_tokenized.csv')

# Konversi string list ke list yang sesungguhnya
df['tokenized_quote'] = df['tokenized_quote'].apply(ast.literal_eval)
df['tags'] = df['tags'].apply(ast.literal_eval)

# Cek apakah tag sudah ada di session_state
if 'generated_tag' in st.session_state:
    selected_tag = st.session_state['generated_tag']
    st.title(f"Temukan Quote📖: {selected_tag}")

    # Filter quotes berdasarkan tag yang dipilih
    filtered_df = df[df['tags'].apply(lambda tags: selected_tag in tags)]

    if not filtered_df.empty:
        # Gabungkan semua token dari quotes yang sesuai dengan tag yang dipilih
        all_tokens = [token for sublist in filtered_df['tokenized_quote'] for token in sublist]

        # Pilih jenis n-gram (unigram, bigram, trigram)
        n = st.selectbox("Pilih jenis n-gram", [1, 2, 3], format_func=lambda x: f"{x}-gram")

        # Pilih berapa banyak kata yang ingin dihasilkan
        n_words_to_generate = st.number_input("Berapa banyak kata yang ingin dihasilkan?", min_value=1, max_value=100, value=10, step=1)

        start_token_input = st.text_input(f"Masukkan {n} token awal (dipisahkan oleh spasi)").lower().split()

        # Validasi jumlah token yang diinput
        if len(start_token_input) != n:
            st.warning(f"Harap masukkan tepat {n} token.")
        else:
            # Menghitung frekuensi n-gram
            ngram_counts = calculate_ngram_frequencies(all_tokens, n)
            ngram_probs = calculate_ngram_probabilities(ngram_counts)

            # Menghasilkan teks dari start token yang diinput oleh pengguna
            generated_text, generated_tokens = generate_text(start_token_input, ngram_probs, n_words_to_generate, n)

            # Baca gambar lokal
            with open("images/Img.png", "rb") as file:
                image_data = file.read()

            # Encode the image to base64 to use in HTML/CSS
            import base64
            image_url = base64.b64encode(image_data).decode("utf-8")
            image_url = f"data:image/jpeg;base64,{image_url}"

            # Use the base64-encoded image URL in your HTML block
            st.markdown(f"""
                <style>
                    .image-container {{
                        position: relative;
                        text-align: center;
                        width: 100%;
                    }}
                    .image-container img {{
                        width: 100%;
                        height: auto;
                    }}
                    .centered-text {{
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        font-size: 24px;
                        font-weight: bold;
                        background-color: rgba(255, 255, 255, 0.7);
                        padding: 10px;
                        border-radius: 10px;
                        color: black;
                    }}
                </style>

                <div class="image-container">
                    <img src="{image_url}" alt="Your Image">
                    <div class="centered-text">{generated_text}</div>
                </div>
            """, unsafe_allow_html=True)

            # Hitung perplexity dan tampilkan di bawah gambar
            perplexity = calculate_perplexity(generated_tokens, ngram_probs, n)

            # Tampilkan perplexity, cek apakah hasilnya string atau angka
            if isinstance(perplexity, str):
                st.write(f"Perplexity Score: {perplexity}")
            else:
                st.write(f"Perplexity Score: {perplexity:.2f}")  # Format hanya jika itu angka
    else:
        st.error(f"Tidak ada quotes yang cocok dengan tag '{selected_tag}'.")
else:
    st.error("Tag belum dipilih dari halaman sebelumnya.")
