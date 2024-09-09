import streamlit as st
import pandas as pd
from collections import Counter
import ast

st.image("images/QUOTE.png", use_column_width=True)

# Membaca CSV dari path yang kamu berikan
df = pd.read_csv('pages/new_tokenized.csv')

# Konversi string list di kolom tokenized_quote dan tags ke list yang sesungguhnya
df['tokenized_quote'] = df['tokenized_quote'].apply(ast.literal_eval)
df['tags'] = df['tags'].apply(ast.literal_eval)

# Langkah 1: Menggabungkan semua tag menjadi satu string dari huruf-huruf
all_tags = ''.join([tag for tag_list in df['tags'] for tag in ''.join(tag_list)])

# Langkah 2: Membuat n-gram dari huruf (bisa 2/3/4/5-gram)
def generate_n_grams(letters, n):
    n_grams = list(zip(*[letters[i:] for i in range(n)]))
    return n_grams

# Fungsi untuk menghitung frekuensi N-gram dan (N-1)-gram
def count_n_grams(letters, n):
    n_grams = generate_n_grams(letters, n)
    n_minus1_grams = generate_n_grams(letters, n-1)
    n_gram_freq = Counter(n_grams)
    n_minus1_gram_freq = Counter(n_minus1_grams)
    return n_gram_freq, n_minus1_gram_freq

# Fungsi untuk memprediksi huruf berikutnya berdasarkan probabilitas
def predict_next_letter(input_letters, n_gram_freq, n_minus1_gram_freq, n=2):
    last_n_gram = tuple(input_letters[-(n-1):])
    
    candidate_letters = {pair: freq for pair, freq in n_gram_freq.items() if pair[:-1] == last_n_gram}
    
    if candidate_letters:
        probabilities = {}
        last_n_gram_count = n_minus1_gram_freq[last_n_gram]
        for pair, freq in candidate_letters.items():
            probabilities[pair[-1]] = freq / last_n_gram_count
        
        next_letter = max(probabilities, key=probabilities.get)
        return next_letter
    else:
        return None

# Fungsi untuk Autocomplete dan prediksi tag
def autocomplete_tag(input_letters, n_gram_freq, n_minus1_gram_freq, n, max_length=20):
    completed_tag = input_letters[:]
    
    while len(completed_tag) < max_length:
        next_letter = predict_next_letter(completed_tag, n_gram_freq, n_minus1_gram_freq, n=n)
        
        if next_letter:
            completed_tag.append(next_letter)
        else:
            break  # Stop jika tidak ada prediksi huruf berikutnya
    
    return ''.join(completed_tag)

# Fungsi untuk mengecek apakah tag yang dihasilkan ada di dataset
def is_tag_in_data(predicted_tag, df):
    # Mengecek apakah tag yang diprediksi ada di salah satu list tags
    return any(predicted_tag in tags for tags in df['tags'])

# Halaman autocomplete
def autocomplete_page():
    st.title("Cari Tags untuk Mendapatkan Quotes💬")

    # Input text dari pengguna
    input_text = st.text_input("Mulai mengetik tag:", "").lower()

    # Pilihan n-gram
    n_gram_size = st.selectbox("Pilih ukuran n-gram", [2, 3, 4, 5])

    # Ubah panjang maksimal tag menjadi st.number_input
    max_length = st.number_input("Berapa banyak kata yang ingin dihasilkan?", min_value=1, max_value=100, value=10, step=1)
    
    # Menampilkan panjang maksimal tag saat ini
    st.write(f"Panjang maksimal tag: {max_length}")

    # Jika pengguna sudah memasukkan teks
    if input_text:
        # Convert input text menjadi list huruf
        input_letters = list(input_text)
        
        # Hitung n-gram sesuai ukuran yang dipilih
        n_gram_freq, n_minus1_gram_freq = count_n_grams(all_tags, n_gram_size)
        
        # Autocomplete tag
        completed_tag = autocomplete_tag(input_letters, n_gram_freq, n_minus1_gram_freq, n=n_gram_size, max_length=max_length)
        
        st.write(f"Tag yang dihasilkan: {completed_tag}")
        
        # Cek apakah tag ada di dataset
        if st.button("Konfirmasi Tag"):
            tag_exists = is_tag_in_data(completed_tag, df)
            if tag_exists:
                st.success("Tag cocok dengan data! Lanjut ke Generate Text.")
                # Simpan tag yang dihasilkan ke session_state
                st.session_state['generated_tag'] = completed_tag
                
                # Tampilkan tombol untuk berpindah ke halaman generate text
                if st.button("Lanjutkan ke Generate Text"):
                    st.session_state['page'] = 'generate_text'
            else:
                st.error("Tag yang diprediksi tidak ada di dataset.")
                
# Jalankan fungsi autocomplete page
autocomplete_page()
