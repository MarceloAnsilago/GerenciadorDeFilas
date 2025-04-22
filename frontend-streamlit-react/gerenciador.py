from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import streamlit.components.v1 as components
API_BASE_URL = "http://127.0.0.1:8000"
from streamlit_autorefresh import st_autorefresh


# Inicializa variáveis de estado
if "ultimo_chamado" not in st.session_state:
    st.session_state.ultimo_chamado = None
if "esperando_contagem" not in st.session_state:
    st.session_state.esperando_contagem = False
if "tempo_restante" not in st.session_state:
    st.session_state.tempo_restante = 0

# Calcular tempo restante
if st.session_state.ultimo_chamado:
    diff = (datetime.now() - st.session_state.ultimo_chamado).total_seconds()
    if diff < 5:
        st.session_state.tempo_restante = 5 - int(diff)
        st.session_state.esperando_contagem = True
        # 🔁 Atualiza a cada segundo enquanto espera
        st_autorefresh(interval=1000, key="refresh_chamada")
    else:
        st.session_state.ultimo_chamado = None
        st.session_state.esperando_contagem = False
        st.session_state.tempo_restante = 0


def exibir_gerenciador():
    # 🔒 Garantir que todas as chaves de sessão estão inicializadas
    st.session_state.setdefault("secao", None)
    st.session_state.setdefault("ultimo_chamado", None)
    st.session_state.setdefault("esperando_contagem", False)
    st.session_state.setdefault("tempo_restante", 0)
    st.session_state.setdefault("ultima_resposta_formatada", "")
    st.session_state.setdefault("ultima_senha", None)
    st.session_state.setdefault("play_audio", False)
    st.session_state.setdefault("usuario_atual", "")
    st.session_state.setdefault("terminal_atual", 0)

 

    st.title(f"🛠 Gerenciador de Senhas - Seção {st.session_state['secao']}" if st.session_state["secao"] else "🛠 Gerenciador de Senhas")

    # Etapa 1: validar seção
    if "secao" not in st.session_state or st.session_state["secao"] is None:
        secao_input = st.text_input("Informe o número da seção atual")
        if secao_input and st.button("🔍 Verificar seção"):
            try:
                response = requests.get(f"{API_BASE_URL}/validar-secao", params={"secao": int(secao_input)})
                if response.status_code == 200 and response.json().get("existe"):
                    st.session_state["secao"] = int(secao_input)
                    st.success(f"Seção {secao_input} confirmada!")
                    st.rerun()
                else:
                    st.error("Número de seção inválido ou não encontrada!")
            except Exception as e:
                st.error(f"Erro ao consultar a API: {e}")
        return


    # Menu lateral
    with st.sidebar:
        escolha = option_menu(
            "Gerenciador de filas", ["🛎 Chamar", "⚙️ Gerar Senhas", "🖨 Imprimir Senhas", "📋 Senhas Chamadas"],
            icons=["bell", "gear", "printer", "list-task"],
            menu_icon="cast",
            default_index=0
        )

    # Redireciona para a função da página correspondente
    if escolha == "🛎 Chamar":
        mostrar_pagina_chamar()
    elif escolha == "⚙️ Gerar Senhas":
        mostrar_pagina_configurar()
    elif escolha == "🖨 Imprimir Senhas":
        mostrar_pagina_imprimir()
    elif escolha == "📋 Senhas Chamadas":
        mostrar_pagina_senhas_chamadas()

def mostrar_painel_fixo(api_url, secao):
    import requests
    import streamlit as st
    from datetime import datetime

    try:
        row = requests.get(f"{api_url}/senha-atual", params={"secao": secao}).json()
    except Exception:
        row = None

    if row:
        senha_atual = row.get("senha")
        resposta_atual = row.get("resposta")
        hora_db = row.get("hora")
        unidade = row.get("unidade")
        usuario = row.get("usuario")
        terminal = row.get("terminal")
        try:
            hora_formatada = datetime.fromisoformat(hora_db).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            hora_formatada = hora_db
    else:
        senha_atual = resposta_atual = unidade = usuario = terminal = None
        hora_formatada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
        <div style="border: 2px solid black; text-align: center; width: 100%; max-width: 300px; margin: auto;">
            <div style="background-color: black; color: white; padding: 15px; font-weight: bold; font-size: 16px;">
                {unidade or "UNIDADE XYZ"}<br/>
                Seção: {secao}
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

    st.markdown(f"""
        <div style="border:1px solid #ddd; padding:15px; font-size:18px; margin-top: 20px;">
            <p><strong>🛑 Atenção:</strong> {resposta_formatada}</p>
            <p><strong>👨‍💼 Atendente:</strong> {usuario or "N/A"}</p>
            <p><strong>🖥 Terminal:</strong> {terminal or "N/A"}</p>
            <p><strong>🕒 Hora da Chamada:</strong> {hora_formatada}</p>
        </div>
    """, unsafe_allow_html=True)


def mostrar_pagina_chamar():
    API_BASE_URL = "http://127.0.0.1:8000"

    # Inicializa os campos
    if "usuario_gerenciador" not in st.session_state:
        st.session_state.usuario_gerenciador = ""
    if "terminal_gerenciador" not in st.session_state:
        st.session_state.terminal_gerenciador = ""

    st.subheader(f"📣 Chamada de Senhas — Seção {st.session_state.get('secao', 'N/A')}")

    # Inputs fora do bloco de contagem, sempre visíveis
    col1, col2 = st.columns(2)
    with col1:
        usuario = st.text_input("👨‍💼 Informe seu usuário", value=st.session_state.usuario_gerenciador, key="usuario_input")
    with col2:
        terminal = st.text_input("🖥 Informe seu terminal", value=st.session_state.terminal_gerenciador, key="terminal_input")

    st.session_state.usuario_gerenciador = usuario
    st.session_state.terminal_gerenciador = terminal

    # Agora verifica contagem
    if st.session_state.get("esperando_contagem", False):
        st_autorefresh(interval=1000, key="auto_refresh")
        if "tempo_restante" not in st.session_state:
            st.session_state.tempo_restante = 5

        if st.session_state.tempo_restante > 0:
            st.session_state.tempo_restante -= 1
            st.button(f"⏳ Aguardando {st.session_state.tempo_restante}s...", disabled=True, use_container_width=True)
            st.divider()
            mostrar_painel_fixo(API_BASE_URL, st.session_state["secao"])
            return
        else:
            st.session_state.tempo_restante = 0
            st.session_state.esperando_contagem = False
            st.rerun()



        # Mantém os valores no session_state após qualquer ação
    st.session_state.usuario_gerenciador = usuario
    st.session_state.terminal_gerenciador = terminal


    st.divider()

    if "modo_chamada" not in st.session_state:
        st.session_state.modo_chamada = "inicial"

    col1, col2, col3 = st.columns(3)

    if st.session_state.modo_chamada == "inicial":
        with col1:
      
            if st.button("📢 Chamar Próximo", type="primary", use_container_width=True):
                usuario = st.session_state.get("usuario_gerenciador", "").strip()
                terminal = st.session_state.get("terminal_gerenciador", "").strip()

                if not terminal.isdigit():
                    st.error("O campo 'Terminal' precisa ser preenchido com um número válido.")
                    return

                # ✅ Verifica se já existe alguém com status aberto
                try:
                    resposta = requests.get(f"{API_BASE_URL}/senha-atual", params={"secao": st.session_state['secao']})
                    if resposta.status_code == 200:
                        dados_aberto = resposta.json()
                        if dados_aberto and dados_aberto.get("status") == "aberto":
                            nome_em_chamada = dados_aberto.get("usuario", "N/A")
                            terminal_em_chamada = dados_aberto.get("terminal", "N/A")
                            st.warning(f"Aguarde o usuário \"{nome_em_chamada} - Terminal {terminal_em_chamada}\" encerrar sua chamada.")
                            st.toast(f"Usuário em atendimento: {nome_em_chamada} (Terminal {terminal_em_chamada})", icon="⏳")
                            time.sleep(1) 
                            return
                except Exception as e:
                    st.error(f"Erro ao verificar chamadas abertas: {e}")
                    return 

                # 🚀 Chamar próxima senha
                try:
                    response = requests.get(f"{API_BASE_URL}/todas-senhas", params={"secao": st.session_state["secao"]})
                    response.raise_for_status()
                    senhas = response.json()

                    aguardando = list(filter(lambda x: x["status"] == "aguardando", senhas))
                    if not aguardando:
                        st.warning("Nenhuma senha aguardando para ser chamada.")
                    else:
                        proxima = sorted(aguardando, key=lambda x: x["senha"])[0]
                        st.session_state.id_ultima_chamada = proxima["id"]

                        payload = {
                            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "resposta": "chamando 1",
                            "status": "aberto",
                            "usuario": usuario or "admin",
                            "terminal": int(terminal)
                        }

                        atualizar = requests.put(f"{API_BASE_URL}/atualizar-senha/{proxima['id']}", json=payload)
                        if atualizar.status_code == 200:
                            st.toast(f"Senha {proxima['senha']:03} chamada!", icon="📢") 
                            time.sleep(1)
                            st.session_state.modo_chamada = "chamando"
                            st.session_state.esperando_contagem = True
                            st.session_state.tempo_restante = 5
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar a senha.")
                except Exception as e:
                    st.error(f"Erro ao chamar próxima senha: {e}")


    elif st.session_state.modo_chamada == "chamando":
        with col1:
            if st.session_state.esperando_contagem:
                st.button(f"⏳ Aguardando {st.session_state.tempo_restante}s...", disabled=True, use_container_width=True)
            else:
                if st.button("🔁 Chamar Novamente", use_container_width=True):
                    try:
                        id_senha = st.session_state.get("id_ultima_chamada")
                        if id_senha:
                            row = requests.get(f"{API_BASE_URL}/senha-atual", params={"secao": st.session_state["secao"]}).json()
                            atual = row.get("resposta", "chamando 1")
                            numero = int(atual.split(" ")[1]) + 1 if "chamando" in atual else 2
                            nova_resposta = f"chamando {numero}"

                            payload = {"resposta": nova_resposta}
                            requests.put(f"{API_BASE_URL}/atualizar-senha/{id_senha}", json=payload)

                            st.session_state.esperando_contagem = True
                            st.session_state.tempo_restante = 5
                            st.toast("Chamando novamente...", icon="🔁")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao chamar novamente: {e}")

        with col2:
            if st.button("✅ Compareceu", use_container_width=True):
                try:
                    id_senha = st.session_state.get("id_ultima_chamada")
                    payload = {"resposta": "compareceu", "status": "encerrado"}
                    requests.put(f"{API_BASE_URL}/atualizar-senha/{id_senha}", json=payload)
                    st.session_state.modo_chamada = "inicial"
                    st.toast("Senha encerrada como compareceu", icon="✅")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao encerrar senha: {e}")

        with col3:
            if st.button("❌ Não Compareceu", use_container_width=True):
                try:
                    id_senha = st.session_state.get("id_ultima_chamada")
                    payload = {"resposta": "não compareceu", "status": "encerrado"}
                    requests.put(f"{API_BASE_URL}/atualizar-senha/{id_senha}", json=payload)
                    st.session_state.modo_chamada = "inicial"
                    st.toast("Senha encerrada como não compareceu", icon="❌")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao encerrar senha: {e}")

    st.divider()
    mostrar_painel_fixo(API_BASE_URL, st.session_state["secao"])




def mostrar_pagina_configurar():
    st.subheader("⚙️ Gerar Senhas em Lote")

    col_data, col_unidade = st.columns(2)
    with col_data:
        data = st.date_input("📅 Data das senhas", value=datetime.today())
    with col_unidade:
        unidade = st.text_input("🏢 Unidade", value="São Miguel Idaron")

    col1, col2 = st.columns(2)
    with col1:
        senha_inicial = st.number_input("🔢 Senha Inicial", min_value=1, max_value=999, step=1)
    with col2:
        senha_final = st.number_input("🔢 Senha Final", min_value=1, max_value=999, step=1, value=senha_inicial)

    if st.button("⚙️ Gerar Senhas"):
        if senha_final < senha_inicial:
            st.error("A senha final deve ser maior ou igual à senha inicial.")
            return

        total = senha_final - senha_inicial + 1
        with st.spinner(f"Gerando {total} senhas..."):

            for i in range(senha_inicial, senha_final + 1):
                hora = datetime.combine(data, datetime.min.time()) + timedelta(seconds=i)
                payload = {
                    "secao": st.session_state["secao"],
                    "senha": i,
                    "hora": hora.strftime("%Y-%m-%d %H:%M:%S"),
                    "usuario": "admin",
                    "resposta": "",
                    "status": "aguardando",  # <-- alterado aqui
                    "terminal": 0,  # fixado como 0 já que foi removido do input
                    "unidade": unidade,
                    "prioridade": "normal"
                }

                try:
                    response = requests.post(f"{API_BASE_URL}/gravar-senha", json=payload)
                    if response.status_code != 200:
                        st.error(f"Erro ao inserir senha {i}: {response.text}")
                        return
                    time.sleep(0.05)
                except Exception as e:
                    st.error(f"Erro ao inserir senha {i}: {e}")
                    return

            st.success(f"✅ {total} senhas geradas com sucesso para {data.strftime('%d/%m/%Y')}!")



def mostrar_pagina_imprimir():
    st.subheader("🖨 Imprimir Senhas da Seção Atual")

    secao = st.session_state.get("secao")
    if not secao:
        st.warning("Nenhuma seção ativa encontrada.")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/todas-senhas", params={"secao": secao})
        response.raise_for_status()
        senhas = response.json()
    except Exception as e:
        st.error(f"Erro ao buscar senhas: {e}")
        return

    if not senhas:
        st.info("Nenhuma senha encontrada para impressão.")
        return

    senhas_ordenadas = sorted(senhas, key=lambda x: x["senha"])

    html = """
    <html>
    <head>
        <style>
            body {
                margin: 0;
                padding: 20px;
                font-family: Arial;
            }
            .print-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                justify-content: left;
            }
            .cartao-senha {
                width: 23%;
                border: 2px solid black;
                text-align: center;
                page-break-inside: avoid;
            }
            .cartao-header {
                background-color: black;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            .cartao-body {
                padding: 20px;
            }
            .cartao-footer {
                background-color: black;
                color: white;
                padding: 10px;
                font-size: 12px;
            }
            .botao-imprimir {
                background-color: #ff4b4b;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .botao-imprimir:hover {
                background-color: #e63c3c;
            }
            @media print {
                .botao-imprimir {
                    display: none;
                }
            }
        </style>
    </head>
    <body>
        <button class="botao-imprimir" onclick="window.print()">🖨 Imprimir Senhas</button>
        <div class="print-container">
    """

    for item in senhas_ordenadas:
        html += f"""
        <div class="cartao-senha">
            <div class="cartao-header">{item['unidade']}<br/>Seção: {item['secao']}</div>
            <div class="cartao-body">
                <div style="font-size: 16px;">SENHA</div>
                <div style="font-size: 36px; font-weight: bold;">{str(item['senha']).zfill(3)}</div>
            </div>
            <div class="cartao-footer">DATA {datetime.fromisoformat(item['hora']).strftime('%d/%m/%Y')}</div>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    components.html(html, height=1000, scrolling=True)

def mostrar_pagina_senhas_chamadas():
    st.subheader("📋 Histórico de Senhas Chamadas")

    API_BASE_URL = "http://127.0.0.1:8000"
    secao = st.session_state.get("secao", None)

    if not secao:
        st.warning("Seção não definida. Volte e inicie uma seção.")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/todas-senhas", params={"secao": secao})
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        st.error(f"Erro ao buscar senhas: {e}")
        return

    encerradas = [s for s in dados if s["status"] == "encerrado" and s["senha"] > 0]

    if not encerradas:
        st.info("Nenhuma senha encerrada encontrada.")
        return

    # Ordenar por hora DESC
    encerradas.sort(key=lambda s: s["hora"], reverse=True)

    # Formatar hora para HH:MM:SS
    for s in encerradas:
        try:
            # Remove o timezone e formata
            hora_sem_tz = s["hora"].split("+")[0]  # Ex: '2025-04-22T10:29:33'
            dt = datetime.strptime(hora_sem_tz, "%Y-%m-%dT%H:%M:%S")
            s["hora"] = dt.strftime("%H:%M:%S")
        except Exception:
            pass

    df = pd.DataFrame(encerradas)[["senha", "hora", "resposta", "usuario", "terminal"]]
    st.table(df)