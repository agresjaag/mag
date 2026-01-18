import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# --- KONFIGURACJA POŁĄCZENIA ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def pokaz_paragon(produkt):
    """Funkcja generująca prosty widok paragonu w Streamlit"""
    st.toast(f"Sprzedano: {produkt['nazwa']}")
    st.markdown("""---""")
    with st.container():
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border: 1px dashed #333; color: black; font-family: monospace;">
            <h3 style="text-align: center; margin-bottom: 5px;">PARAGON FISKALNY</h3>
            <p style="text-align: center; font-size: 0.8em;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr style="border-top: 1px dashed #333;">
            <div style="display: flex; justify-content: space-between;">
                <span>{produkt['nazwa']}</span>
                <span>1 szt. x {produkt['cena']} zł</span>
            </div>
            <hr style="border-top: 1px dashed #333;">
            <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.2em;">
                <span>SUMA PLN:</span>
                <span>{produkt['cena']} zł</span>
            </div>
            <p style="text-align: center; margin-top: 20px; font-size: 0.9em;">DZIĘKUJEMY I ZAPRASZAMY PONOWNIE!</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("""---""")

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Produktami")

tabs = st.tabs(["Produkty", "Kategorie"])

# --- ZAKŁADKA KATEGORIE (Kod bez zmian) ---
with tabs[1]:
    st.header("Zarządzanie Kategoriami")
    with st.form("add_category_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nazwa_kat = col1.text_input("Nazwa kategorii")
        opis_kat = col2.text_input("Opis")
        submit_kat = st.form_submit_button("Dodaj kategorię")
        if submit_kat and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
            st.rerun()

    kategorie_res = supabase.table("kategorie").select("*").execute()
    for kat in kategorie_res.data:
        col_n, col_d = st.columns([4, 1])
        col_n.write(f"**{kat['nazwa']}**")
        if col_d.button("Usuń", key=f"del_kat_{kat['id']}"):
            supabase.table("kategorie").delete().eq("id", kat['id']).execute()
            st.rerun()

# --- ZAKŁADKA PRODUKTY (Z nową funkcją sprzedaży) ---
with tabs[0]:
    st.header("Zarządzanie Produktami")

    # Formularz dodawania (Kod bez zmian)
    kategorie_res = supabase.table("kategorie").select("id, nazwa").execute()
    kat_options = {kat['nazwa']: kat['id'] for kat in kategorie_res.data}

    with st.form("add_product_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        n_p = c1.text_input("Nazwa")
        k_p = c2.selectbox("Kategoria", options=list(kat_options.keys()))
        l_p = c3.number_input("Ilość", min_value=1)
        ce_p = c4.number_input("Cena", min_value=0.0)
        if st.form_submit_button("Dodaj produkt") and n_p:
            supabase.table("produkty").insert({"nazwa": n_p, "kategoria_id": kat_options[k_p], "liczba": l_p, "cena": ce_p}).execute()
            st.rerun()

    # Wyświetlanie listy produktów
    st.subheader("Aktualny asortyment")
    res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    
    # Obsługa stanu sesji dla paragonu, aby nie znikał po odświeżeniu
    if 'ostatnia_sprzedaz' in st.session_state:
        pokaz_paragon(st.session_state.ostatnia_sprzedaz)
        if st.button("Zamknij paragon"):
            del st.session_state.ostatnia_sprzedaz
            st.rerun()

    for p in res.data:
        col_p, col_c, col_sell, col_del = st.columns([3, 1, 2, 1])
        col_p.write(f"**{p['nazwa']}** ({p['kategorie']['nazwa']})")
        col_c.write(f"{p['cena']} zł")
        
        # PRZYCISK SPRZEDAŻY
        if col_sell.button("💰 Sprzedaj i drukuj", key=f"sell_{p['id']}"):
            # Zapisujemy dane do paragonu zanim usuniemy z bazy
            st.session_state.ostatnia_sprzedaz = p
            supabase.table("produkty").delete().eq("id", p['id']).execute()
            st.rerun()

        # PRZYCISK ZWYKŁEGO USUNIĘCIA
        if col_del.button("❌ Usuń", key=f"del_{p['id']}"):
            supabase.table("produkty").delete().eq("id", p['id']).execute()
            st.rerun()
