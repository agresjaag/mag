import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# --- KONFIGURACJA POŁĄCZENIA ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")

# --- FUNKCJA GENERUJĄCA PARAGON ZBIORCZY ---
def pokaz_paragon_zbiorczy(produkty_do_sprzedazy):
    suma_total = sum(p['cena'] * p['ilosc_do_akcji'] for p in produkty_do_sprzedazy)
    
    st.toast(f"Wygenerowano paragon na sumę: {suma_total:.2f} zł")
    with st.container(border=True):
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border: 1px dashed #333; color: black; font-family: monospace;">
            <h3 style="text-align: center; margin-bottom: 5px;">PARAGON FISKALNY</h3>
            <p style="text-align: center; font-size: 0.8em;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr style="border-top: 1px dashed #333;">
        """, unsafe_allow_html=True)
        
        for p in produkty_do_sprzedazy:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between;">
                <span>{p['nazwa']}</span>
                <span>{p['ilosc_do_akcji']} szt. x {p['cena']:.2f} zł</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
            <hr style="border-top: 1px dashed #333;">
            <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.2em;">
                <span>SUMA PLN:</span>
                <span>{suma_total:.2f} zł</span>
            </div>
            <p style="text-align: center; margin-top: 20px; font-size: 0.9em;">DZIĘKUJEMY I ZAPRASZAMY PONOWNIE!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Zamknij paragon"):
            del st.session_state.ostatni_paragon
            st.rerun()

st.title("📦 System Zarządzania Magazynem")
tabs = st.tabs(["Produkty", "Kategorie"])

# --- ZAKŁADKA KATEGORIE ---
with tabs[1]:
    st.header("Zarządzanie Kategoriami")
    with st.form("add_category_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nazwa_kat = c1.text_input("Nazwa kategorii")
        opis_kat = c2.text_input("Opis")
        if st.form_submit_button("Dodaj kategorię") and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
            st.rerun()

    kat_res = supabase.table("kategorie").select("*").execute()
    for kat in kat_res.data:
        col_n, col_d = st.columns([4, 1])
        col_n.write(f"**{kat['nazwa']}** - {kat['opis']}")
        if col_d.button("Usuń", key=f"del_kat_{kat['id']}"):
            supabase.table("kategorie").delete().eq("id", kat['id']).execute()
            st.rerun()

# --- ZAKŁADKA PRODUKTY ---
with tabs[0]:
    st.header("Zarządzanie Produktami")
    
    # Formularz dodawania
    kat_data = supabase.table("kategorie").select("id, nazwa").execute().data
    kat_options = {k['nazwa']: k['id'] for k in kat_data}
    
    with st.expander("➕ Dodaj nowy produkt"):
        with st.form("new_prod"):
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            n = c1.text_input("Nazwa")
            k = c2.selectbox("Kategoria", options=list(kat_options.keys()))
            l = c3.number_input("Ilość", min_value=1, value=1)
            p = c4.number_input("Cena", min_value=0.0, step=0.01)
            if st.form_submit_button("Zapisz w bazie") and n:
                supabase.table("produkty").insert({"nazwa": n, "kategoria_id": kat_options[k], "liczba": l, "cena": p}).execute()
                st.rerun()

    # WYŚWIETLANIE LISTY I KOSZYK
    st.subheader("Aktualny asortyment")
    if 'ostatni_paragon' in st.session_state:
        pokaz_paragon_zbiorczy(st.session_state.ostatni_paragon)

    res = supabase.table("produkty").select("*, kategorie(nazwa)").order("nazwa").execute()
    produkty = res.data

    if produkty:
        # Nagłówki tabeli
        h1, h2, h3, h4, h5 = st.columns([0.5, 3, 1, 1, 1.5])
        h1.write("S") # Wybór
        h2.write("**Nazwa (Kategoria)**")
        h3.write("**Cena**")
        h4.write("**Stan**")
        h5.write("**Ilość do akcji**")

        wybrane_produkty = []
        
        for p in produkty:
            c1, c2, c3, c4, c5 = st.columns([0.5, 3, 1, 1, 1.5])
            
            # Checkbox wyboru
            is_selected = c1.checkbox("", key=f"check_{p['id']}")
            c2.write(f"{p['nazwa']} ({p['kategorie']['nazwa']})")
            c3.write(f"{p['cena']:.2f} zł")
            c4.write(f"{p['liczba']} szt.")
            
            # Pole do wpisania ilości do sprzedaży/usunięcia
            ilosc_akcja = c5.number_input("Ilość", min_value=1, max_value=int(p['liczba']), value=1, key=f"qty_{p['id']}")
            
            if is_selected:
                p['ilosc_do_akcji'] = ilosc_akcja
                wybrane_produkty.append(p)

        st.divider()
        col_actions = st.columns([1, 1, 3])
        
        # PRZYCISK SPRZEDAŻY
        if col_actions[0].button("💰 Sprzedaj zaznaczone", type="primary", use_container_width=True):
            if wybrane_produkty:
                for prod in wybrane_produkty:
                    nowa_liczba = prod['liczba'] - prod['ilosc_do_akcji']
                    if nowa_liczba <= 0:
                        supabase.table("produkty").delete().eq("id", prod['id']).execute()
                    else:
                        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", prod['id']).execute()
                
                st.session_state.ostatni_paragon = wybrane_produkty
                st.rerun()
            else:
                st.warning("Zaznacz produkty do sprzedaży!")

        # PRZYCISK USUWANIA
        if col_actions[1].button("❌ Usuń zaznaczone", use_container_width=True):
            if wybrane_produkty:
                for prod in wybrane_produkty:
                    nowa_liczba = prod['liczba'] - prod['ilosc_do_akcji']
                    if nowa_liczba <= 0:
                        supabase.table("produkty").delete().eq("id", prod['id']).execute()
                    else:
                        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", prod['id']).execute()
                st.success("Usunięto wybrane ilości z magazynu.")
                st.rerun()
            else:
                st.warning("Zaznacz produkty do usunięcia!")
    else:
        st.info("Magazyn jest pusty.")
