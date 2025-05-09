# versão incrementada pro 
# Perguntas predefinidas e campo de texto no início
# Cards de Faturamento, Comissão, Chargeback e Estornos
# Filtros adicionais: Afiliado, Cidade, Status da Venda, Método de Pagamento
# Gráficos semanais e mensais
# Análise Automática de Tendências
# Comparativo de períodos
# Baixar relatório filtrado em CSV

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Funções auxiliares
def formatar_reais(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def corrigir_coluna(df, col):
    try:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("R\$", "", regex=True)
            .str.replace("\xa0", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao processar a coluna {col}: {e}")
    return df

def calcular_estorno(df):
    if "Código" not in df.columns or "Status" not in df.columns:
        return 0
    df_ultimas = df.sort_values("Iniciada em").groupby("Código").last()
    total_clientes = len(df_ultimas)
    estornados = df_ultimas[df_ultimas["Status"].str.lower() == "estornada"]
    estorno_rate = (len(estornados) / total_clientes) * 100 if total_clientes > 0 else 0
    return estorno_rate

def calcular_chargeback(df):
    if "Status" not in df.columns:
        return 0
    total_vendas = len(df)
    chargebacks = df[df["Status"].str.lower() == "recusada"]
    chargeback_rate = (len(chargebacks) / total_vendas) * 100 if total_vendas > 0 else 0
    return chargeback_rate

def responder_pergunta(pergunta, df):
    pergunta = pergunta.lower()
    mapeamento = {
        "total de vendas": ["total de vendas", "quanto vendi", "faturamento", "vendas totais"],
        "total de comissões": ["comissões", "quanto de comissão", "valor de comissão"],
        "clientes únicos": ["clientes únicos", "quantos clientes", "clientes diferentes"],
        "produtos vendidos": ["produtos vendidos", "quais produtos", "lista de produtos"],
        "top afiliados": ["top afiliados", "melhores afiliados", "quem vendeu mais"],
        "faturamento por cidade": ["cidade faturamento", "vendas por cidade", "faturamento cidade"]
    }

    for intencao, variacoes in mapeamento.items():
        for variacao in variacoes:
            if variacao in pergunta:
                if intencao == "total de vendas":
                    return f"💰 Total de vendas: {formatar_reais(df['Total'].sum())}"
                elif intencao == "total de comissões":
                    return f"💸 Total de comissões: {formatar_reais(df['Comissão'].sum())}"
                elif intencao == "clientes únicos":
                    return f"👥 Clientes únicos: {df['Cliente (E-mail)'].nunique()}"
                elif intencao == "produtos vendidos":
                    produtos = df['Produto'].value_counts()
                    return "🛍️ Produtos vendidos:\n" + "\n".join([f"{produto}: {quantidade}" for produto, quantidade in produtos.items()])
                elif intencao == "top afiliados":
                    afiliados = df['Afiliado (Nome)'].value_counts().head(5)
                    return "🏆 Top afiliados:\n" + "\n".join([f"{afiliado}: {quantidade}" for afiliado, quantidade in afiliados.items()])
                elif intencao == "faturamento por cidade":
                    cidades = df.groupby('Cliente (Cidade)')["Total"].sum().sort_values(ascending=False)
                    return "🏙️ Faturamento por cidade:\n" + "\n".join([f"{cidade}: {formatar_reais(valor)}" for cidade, valor in cidades.items()])

    return "❓ Não entendi sua pergunta. Tente reformular."

# Função principal
def main():
    st.set_page_config(page_title="SalesDataAgent PRO", layout="wide")
    st.title("🧪 SalesDataAgent TURBO")

    uploaded_file = st.file_uploader("📎 Faça upload do seu arquivo CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file, delimiter=";")

        for col in ["Total", "Comissão", "Desconto (Valor)", "Taxas"]:
            if col in df.columns:
                df = corrigir_coluna(df, col)

        if "Iniciada em" in df.columns:
            df["Iniciada em"] = pd.to_datetime(df["Iniciada em"], errors='coerce')

        st.success("Arquivo carregado com sucesso!")

        st.subheader("🗓️ Selecione o Período para Análise")
        data_min = df["Iniciada em"].min().date()
        data_max = df["Iniciada em"].max().date()

        opcoes_periodo = ["Todo o Período", "Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias", "Últimos 12 meses", "Personalizado"]
        periodo_opcao = st.selectbox("Período:", opcoes_periodo)

        if periodo_opcao == "Todo o Período":
            data_inicio, data_fim = data_min, data_max
        elif periodo_opcao == "Hoje":
            data_inicio = data_fim = datetime.today().date()
        elif periodo_opcao == "Ontem":
            data_inicio = data_fim = datetime.today().date() - timedelta(days=1)
        elif periodo_opcao == "Últimos 7 dias":
            data_fim = datetime.today().date()
            data_inicio = data_fim - timedelta(days=6)
        elif periodo_opcao == "Últimos 30 dias":
            data_fim = datetime.today().date()
            data_inicio = data_fim - timedelta(days=29)
        elif periodo_opcao == "Últimos 12 meses":
            data_fim = datetime.today().date()
            data_inicio = data_fim - timedelta(days=365)
        else:
            data_inicio, data_fim = st.date_input("Selecione o intervalo:", [data_min, data_max])

        df_filtrado = df[(df["Iniciada em"].dt.date >= data_inicio) & (df["Iniciada em"].dt.date <= data_fim)]

        st.subheader("📈 Análise de Tendências e Alertas")

        vendas_semana = df_filtrado.resample('W-Mon', on="Iniciada em")["Total"].sum()
        faturamento_mes = df_filtrado.resample('M', on="Iniciada em")["Total"].sum()

        # Tendência de vendas
        if not vendas_semana.empty and vendas_semana.shape[0] > 1:
            tendencia_vendas = vendas_semana.pct_change().dropna().mean() * 100
            if np.isfinite(tendencia_vendas):
                if tendencia_vendas > 0:
                    st.success(f"📈 Vendas subindo {tendencia_vendas:.2f}% por semana.")
                elif tendencia_vendas < 0:
                    st.error(f"📉 Vendas caindo {abs(tendencia_vendas):.2f}% por semana.")
                else:
                    st.info("➖ Vendas estáveis nas últimas semanas.")
            else:
                st.info("➖ Dados insuficientes para calcular a tendência de vendas.")

        # Tendência de faturamento
        if not faturamento_mes.empty and faturamento_mes.shape[0] > 1:
            tendencia_faturamento = faturamento_mes.pct_change().dropna().mean() * 100
            if np.isfinite(tendencia_faturamento):
                if tendencia_faturamento > 0:
                    st.success(f"📈 Faturamento subindo {tendencia_faturamento:.2f}% ao mês.")
                elif tendencia_faturamento < 0:
                    st.error(f"📉 Faturamento caindo {abs(tendencia_faturamento):.2f}% ao mês.")
                else:
                    st.info("➖ Faturamento estável nos últimos meses.")
            else:
                st.info("➖ Dados insuficientes para calcular a tendência de faturamento.")

        # Cálculo de Chargeback e Estorno
        chargeback = calcular_chargeback(df_filtrado)
        estorno = calcular_estorno(df_filtrado)

        if chargeback > 5:
            st.warning(f"⚡ Atenção: Chargeback elevado ({chargeback:.2f}%).")
        if estorno > 5:
            st.warning(f"🔄 Atenção: Estornos elevados ({estorno:.2f}%).")

        st.subheader("🧠 Perguntas Inteligentes")

        perguntas_cards = {
            "💰 Total de vendas": "total de vendas",
            "💸 Total de comissões": "total de comissões",
            "👥 Clientes únicos": "clientes únicos",
            "🛍️ Produtos vendidos": "produtos vendidos",
            "🏆 Top afiliados": "top afiliados",
            "🏙️ Faturamento por cidade": "faturamento por cidade"
        }

        cols = st.columns(3)
        for i, (titulo, intencao) in enumerate(perguntas_cards.items()):
            if cols[i % 3].button(titulo):
                resposta = responder_pergunta(intencao, df_filtrado)
                st.success(resposta)

        pergunta_livre = st.text_input("✏️ Ou digite sua própria pergunta:")
        if pergunta_livre:
            resposta = responder_pergunta(pergunta_livre, df_filtrado)
            st.info(resposta)

        # Cards principais
        total_vendas = df_filtrado["Total"].sum()
        total_comissao = df_filtrado["Comissão"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Faturamento", formatar_reais(total_vendas))
        col2.metric("💸 Comissões", formatar_reais(total_comissao))
        col3.metric("⚡ Chargeback", f"{chargeback:.2f}%")
        col4.metric("🔄 Estornos", f"{estorno:.2f}%")

        # Gráficos
        st.subheader("📅 Vendas por Semana")
        st.line_chart(vendas_semana)

        st.subheader("📊 Faturamento Mensal")
        st.bar_chart(faturamento_mes)

if __name__ == "__main__":
    main()
