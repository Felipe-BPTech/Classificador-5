import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay
import pickle

import base64

# Função para importar dados do Excel
def import_excel(file):
    data = pd.read_excel(file)
    return data

def w_avg(df, values, weights):
    d = df[values]
    w = df[weights]
    return (d * w).sum() / w.sum()

def agregar(dataframe):
    #geada
    df_geada = pd.read_excel('Bases/GEADA_10_2023 (2).xlsx', 'Geada')
    df_geada2 = pd.melt(df_geada, id_vars=['CD_USO_SOL','Grand Total'])
    df_geada2.drop(['Grand Total'], axis=1, inplace=True)
    df_geada2 = df_geada2.groupby('CD_USO_SOL').apply(w_avg, 'variable', 'value')
    df_geada2 = df_geada2.to_frame()
    df_geada2 = df_geada2.reset_index()
    df_geada2.rename(columns={0:'geada'}, inplace=True)
    #ITW
    df_itw = pd.read_csv('Bases/ITW_NOVO.csv')
    df_itw['CAMALHAO'].replace({"Classe 2":2, "Classe 1":1, "Classe 3":3}, inplace=True)
    df_itw['chave'] = df_itw['ID_PROJETO'] + df_itw['CD_TALHAO']
    df_itw = df_itw[['chave','CAMALHAO']]
    #Classe
    df_solo = pd.read_excel("Bases/Legenda Solos 2020.xlsx", "1")
    #Cadastro
    df_cadastro = pd.read_csv('Bases/Cadastro.csv')
    df_cadastro = df_cadastro.loc[lambda df_cadastro: (df_cadastro['TIP_REG'] == "A") & (df_cadastro['EST_REG'] == "A")]
    df_cadastro['chave'] = df_cadastro['ID_PROJETO'].astype(str) + df_cadastro['CD_TALHAO']
    df_cadastro = df_cadastro.drop(['CD_USUARIO','ID_REGIAO','REGIAO_ADM',
                  'USO_SOLO_DETALHE','USO_SOLO_GRUPO','ESPACAMENTO','NUM_CICLO','NUM_ROTACAO','REGIME','DATA_PLANTIO',
                  'VLR_ENTRELINHA','VLR_ENTREPLANTA','NUM_ARV_HA','GENERO','ESPECIE','CD_MATERIAL_GENETICO',
                  'MATERIAL_GENETICO','VLR_RENDIMENTO','TIPO_PROPRIEDADE','PROJETO_INVESTIMENTO',
                  'BACIA_HIDROGRAFICA','CD_PLANO_OPERACAO','CD_USO_SOLO_PAI','DATA_REG','EST_REG','PROJETO','TIP_REG','VLR_AREA','MUNICIPIO'],
                 axis=1)
    #Agrupar
    dataframe = pd.merge(dataframe, df_cadastro, on='chave', how='inner')
    dataframe = pd.merge(dataframe, df_geada2, left_on='CD_USO_SOLO', right_on='CD_USO_SOL', how='inner')#.fillna(0)
    dataframe = pd.merge(dataframe, df_solo, left_on= 'TIPO_SOLO', right_on='Tipo de solo', how='left').fillna(method='ffill')
    dataframe = pd.merge(dataframe, df_itw, left_on='chave', right_on='chave', how='inner')#.fillna(0)
    #Copia
    dataframe_validacao = dataframe.copy()
    #DROP
    dataframe = dataframe.drop(["CD_TIP_SOLO","TIPOLOGIA", "Tipo de solo",'ID_PROJETO','CD_USO_SOLO','chave', 'CD_TALHAO', 'CD_USO_SOL',
              'BIOMA', 'DIVISAO_OPERACIONAL', 'TIPO_SOLO'], axis=1)
    
    return dataframe, dataframe_validacao


# Configuração da página Streamlit
st.title("Otimismarino v.1")

# Componente para upload do arquivo Excel
uploaded_file = st.file_uploader("Faça o upload do arquivo Excel contendo as CHAVES", type=["xlsx"])

if uploaded_file is not None:
    # Se o arquivo for carregado
    st.write("Arquivo carregado com sucesso!")
    
    # Exibição dos dados importados
    data = import_excel(uploaded_file)
    st.write("Dados do arquivo Excel:")
    st.write(data)

    # Seleção da coluna pelo usuário
    colunas = data.columns.tolist()  # Lista com nomes das colunas
    selected_column = st.selectbox("Selecione a coluna CHAVE para trabalhar", colunas)


    # Exibição dos dados da coluna selecionada
    if selected_column:
        st.write(f"Dados da coluna '{selected_column}':")
        #st.write(data[selected_column])

        df = pd.DataFrame({ 'chave': data[selected_column] }) #DataFrame de Target
        #st.write(df)

#Operações
if not df['chave'].isnull().all():
    df, df_val = agregar(df) #agregar dados para o modelo
    pickled_model = pickle.load(open('model.pkl', 'rb'))
    predictions_df = pickled_model.predict(df)
    predictions_df = pd.DataFrame(predictions_df, columns=['Predicao'])  # Substitua 'coluna_predicao' pelo nome da coluna
    combined_df = pd.concat([df_val, predictions_df], axis=1)
    st.write(combined_df)
    # Salvar o arquivo Excel
    csv = combined_df.to_csv(index=False)  # Convertendo para CSV
    b64 = base64.b64encode(csv.encode()).decode()  # Convertendo para base64 para download


# Função para gerar o link de download
def get_download_link(file_path, link_text):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/xlsx;base64,{b64}" download="{link_text}.xlsx">{link_text}</a>'
    return href  

combined_df.to_excel('arquivo.xlsx', index=False)


# Criar um link para download do arquivo Excel
st.markdown(get_download_link('arquivo.xlsx', 'Baixar Arquivo Excel'), unsafe_allow_html=True)




