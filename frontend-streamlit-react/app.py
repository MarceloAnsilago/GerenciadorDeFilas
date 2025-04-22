import streamlit as st
import painel
import gerenciador

st.set_page_config(page_title="Sistema de Senhas", layout="wide")

if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

def mostrar_menu():
    st.title("🔀 Escolha uma opção")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖥 Ver Painel"):
            st.session_state.pagina = "painel"
            st.rerun()  # força a mudança imediata
    with col2:
        if st.button("🧑‍💻 Acessar Gerenciador"):
            st.session_state.pagina = "gerenciador"
            st.rerun()  # força a mudança imediata

def mostrar_painel():
    painel.exibir_painel()

def mostrar_gerenciador():
    gerenciador.exibir_gerenciador()

# Roteamento
if st.session_state.pagina == "menu":
    mostrar_menu()
elif st.session_state.pagina == "painel":
    mostrar_painel()
elif st.session_state.pagina == "gerenciador":
    mostrar_gerenciador()



# cd "D:\Documentos\Gerenciador de Senhas Streamlit3\frontend-streamlit-react"
