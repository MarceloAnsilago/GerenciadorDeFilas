# painel.py
import datetime
import random
import pandas as pd
import streamlit as st
import base64
import streamlit.components.v1 as components
import requests
from streamlit_autorefresh import st_autorefresh

API_BASE_URL = "http://127.0.0.1:8000"

def exibir_painel():


    if not st.session_state.get("painel_iniciado", False):
        st.session_state["secao"] = random.randint(1000, 9999)
        st.session_state["painel_iniciado"] = True
        payload = {"secao": st.session_state["secao"]}
        try:
            init_response = requests.post(f"{API_BASE_URL}/init-secao", json=payload)
            st.write(init_response.json())
        except Exception as e:
            st.error(f"Erro ao iniciar seção: {e}")
            return

    # st.write(f"Seção existente: {st.session_state['secao']}")

    def tem_senha_aberta(secao):
        try:
            response = requests.get(f"{API_BASE_URL}/tem-senha-aberta", params={"secao": secao})
            if response.status_code == 200:
                return response.json().get("aberta", False)
        except:
            return False
        return False

    def obter_ultima_senha(secao):
        try:
            response = requests.get(f"{API_BASE_URL}/senha-atual", params={"secao": secao})
            if response.status_code == 200:
                return response.json()
        except:
            return None
        return None

    def ultimas_senhas_chamadas(secao):
        try:
            response = requests.get(f"{API_BASE_URL}/ultimas-senhas", params={"secao": secao})
            if response.status_code == 200:
                return response.json()
        except:
            return []
        return []

    senha_aberta = tem_senha_aberta(st.session_state.secao)
    ultima_senha = obter_ultima_senha(st.session_state.secao)

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Painel" if senha_aberta else "Última Senha"
    elif senha_aberta:
        st.session_state.active_tab = "Painel"
    else:
        st.session_state.active_tab = "Última Senha"

    col_video, col_content = st.columns([5, 3] if st.session_state.active_tab == "Painel" else [5, 1])

    with col_video:
        components.html(
            """
            <div style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0;">
                <iframe 
                    src="https://www.youtube.com/embed?listType=playlist&list=PLrBhE4oLMMj95y5nobzQgDT8ygY-Pqbk3"
                    allow="autoplay; encrypted-media"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;">
                </iframe>
            </div>
            """,
            height=700,
        )

    with col_content:
        st_autorefresh(interval=4000, limit=1000, key="refresh_senhas")

        if st.session_state.active_tab == "Painel" and ultima_senha:
            senha_atual = ultima_senha.get("senha")
            resposta_atual = ultima_senha.get("resposta")
            hora_db = ultima_senha.get("hora")
            unidade = ultima_senha.get("unidade")
            usuario = ultima_senha.get("usuario")
            terminal = ultima_senha.get("terminal")

            try:
                hora_formatada = datetime.datetime.fromisoformat(hora_db).strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                hora_formatada = hora_db or "N/A"

            st.markdown(f"""
                <div style="border: 2px solid black; text-align: center; width: 100%; max-width: 300px; margin: auto;">
                    <div style="background-color: black; color: white; padding: 15px; font-weight: bold; font-size: 16px;">
                        {unidade or "UNIDADE XYZ"}<br/>
                        Seção: {st.session_state.secao}
                    </div>
                    <div style="padding: 20px; font-size: 24px; font-weight: bold;">
                        <div>SENHA</div>
                        <div style="font-size: 54px;">{str(senha_atual).zfill(3) if senha_atual else "000"}</div>
                    </div>
                    <div style="background-color: black; color: white; padding: 15px; font-size: 14px;">
                        DATA {hora_formatada}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            def formatar_resposta(resposta):
                if resposta and resposta.startswith("chamando"):
                    try:
                        partes = resposta.split(" ")
                        if len(partes) == 2:
                            num = int(partes[1])
                            return f"chamando {num} vez" if num == 1 else f"chamando {num} vezes"
                    except ValueError:
                        return resposta
                return resposta or "N/A"

            resposta_formatada = formatar_resposta(resposta_atual)

            st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; font-size:18px; margin-top: 20px;">
                    <p><strong>🛑 Atenção:</strong> {resposta_formatada}</p>
                    <p><strong>👨‍💼 Atendente:</strong> {usuario or "N/A"}</p>
                    <p><strong>🖥 Terminal:</strong> {terminal or "N/A"}</p>
                    <p><strong>🕒 Hora da Chamada:</strong> {hora_formatada}</p>
                </div>
            """, unsafe_allow_html=True)

            if (
                (st.session_state.get("ultima_resposta_formatada") != resposta_formatada or
                st.session_state.get("ultima_senha") != senha_atual)
                and resposta_formatada.startswith("chamando")
            ):
                st.session_state.ultima_resposta_formatada = resposta_formatada
                st.session_state.ultima_senha = senha_atual
                st.session_state.play_audio = True

        elif st.session_state.active_tab == "Última Senha":
            st.write("## 📜 Últimas Senhas Chamadas")
            st.markdown(f"### Seção: {st.session_state.secao}")

            ultimas = ultimas_senhas_chamadas(st.session_state.secao)

            if ultimas:
                # Formatando hora para HH:MM:SS
                for senha in ultimas:
                    try:
                        hora_obj = datetime.datetime.fromisoformat(senha["hora"])
                        senha["hora"] = hora_obj.strftime("%H:%M:%S")
                        senha["hora_obj"] = hora_obj  # Adiciona objeto datetime para ordenação real
                    except:
                        senha["hora_obj"] = datetime.datetime.min  # fallback para ordenação

                df = pd.DataFrame(ultimas)[["senha", "hora", "resposta", "hora_obj"]]

                # Ordena pela hora (mais recente primeiro) e remove a coluna auxiliar
                df = df.sort_values(by="hora_obj", ascending=False).drop(columns=["hora_obj"])

                # Gera tabela HTML
                df_html = df.to_html(index=False, classes="my_table", border=0)

                custom_css = """
                <style>
                .my_table th {
                    background-color: black;
                    color: white;
                    font-size: 18px;
                    text-align: center;
                    padding: 8px;
                }
                .my_table td {
                    text-align: center;
                    font-size: 16px;
                    padding: 8px;
                }
                .my_table td:nth-child(1) {
                    background-color: #FFEEAA;
                    color: red;
                    font-weight: bold;
                }
                </style>
                """

                st.markdown(custom_css, unsafe_allow_html=True)
                st.markdown(df_html, unsafe_allow_html=True)

            else:
                st.info("Nenhuma senha encerrada encontrada.")


    if st.session_state.get("play_audio", False):
        try:
            audio_path = "1430_mobile-rington.mp3"
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            audio_html = f"""
            <script>
                var audio = new Audio("data:audio/mp3;base64,{audio_base64}");
                audio.play();
            </script>
            """
            components.html(audio_html, height=0)
        except Exception as e:
            st.error(f"Erro ao tocar áudio: {e}")
        st.session_state.play_audio = False
