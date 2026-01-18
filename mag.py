import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Dane najlepiej przechowywać w Streamlit Secrets
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Produktami")

tabs = st.tabs(["Produkty", "Kategorie"])

# --- ZAKŁADKA KATEGORIE ---
with tabs[1]:
    st.header("Zarządzanie Kategoriami")
    
    # Formularz dodawania
    with st.form("add_category_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nazwa_kat = col1.text_input("Nazwa kategorii")
        opis_kat = col2.text_input("Opis")
        submit_kat = st.form_submit_button("Dodaj kategorię")
        
        if submit_kat and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
            st.success(f"Dodano kategorię: {nazwa_kat}")

    # Lista i usuwanie
    kategorie_res = supabase.table("kategorie").select("*").execute()
    kategorie_data = kategorie_res.data
    
    if kategorie_data:
        for kat in kategorie_data:
            col_name, col_del = st.columns([4, 1])
            col_name.write(f"**{kat['nazwa']}** - {kat['opis']}")
            if col_del.button("Usuń", key=f"del_kat_{kat['id']}"):
                supabase.table("kategorie").delete().eq("id", kat['id']).execute()
                st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

# --- ZAKŁADKA PRODUKTY ---
with tabs[0]:
    st.header("Zarządzanie Produktami")

    # Pobieranie kategorii do selectboxa
    kategorie_res = supabase.table("kategorie").select("id, nazwa").execute()
    kat_options = {kat['nazwa']: kat['id'] for kat in kategorie_res.data}

    # Formularz dodawania produktu
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nazwa_prod = col1.text_input("Nazwa produktu")
        kat_prod = col2.selectbox("Kategoria", options=list(kat_options.keys()))
        
        col3, col4 = st.columns(2)
        liczba_prod = col3.number_input("Liczba", min_value=0, step=1)
        cena_prod = col4.number_input("Cena", min_value=0.0, format="%.2f")
        
        submit_prod = st.form_submit_button("Dodaj produkt")

        if submit_prod and nazwa_prod:
            supabase.table("produkty").insert({
                "nazwa": nazwa_prod,
                "kategoria_id": kat_options[kat_prod],
                "liczba": liczba_prod,
                "cena": cena_prod
            }).execute()
            st.success(f"Dodano produkt: {nazwa_prod}")

    # Tabela produktów z usuwaniem
    st.subheader("Lista produktów")
    produkty_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    produkty_data = produkty_res.data

    if produkty_data:
        for prod in produkty_data:
            col_p, col_c, col_k, col_d = st.columns([3, 1, 2, 1])
            col_p.write(f"**{prod['nazwa']}**")
            col_c.write(f"{prod['cena']} zł")
            col_k.write(f"📁 {prod['kategorie']['nazwa']}")
            if col_d.button("Usuń", key=f"del_prod_{prod['id']}"):
                supabase.table("produkty").delete().eq("id", prod['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
