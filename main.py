"""
================================================================================
Projeto: Coleta e Tratamento de Dados de Aerogeradores
Autor: Elias Martini
Data de Criação: 26/08/2025
Última Atualização: 26/08/2025
Descrição: 
  Script Python para coletar dados de aerogeradores a partir da API SIGEL 
  da ANEEL, realizar tratamento de inconsistências, e gerar arquivo CSV 
  com os dados tratados.
Versão: 1.0
================================================================================
"""

import requests
import geopandas as gpd
import pandas as pd

def FetchAllIds(url: str):
  """
  Consulta a API do SIGEL e retorna todos os ids de objetos.
  """
  params = {
    "f": "json",
    "where": "1=1",
    "returnIdsOnly": "true"
  }
  result = requests.get(url, params=params).json()
  ids = result["objectIds"]
  return ids

def FetchObjectsBatch(url: str, object_ids: list):
  """
  A partir de uma lista de ids, consulta a API do SIGEL e retorna os objetos correspondentes.
  """
  where_condition = f"OBJECTID IN ({','.join(map(str, object_ids))})"
  params = {
    "f": "geojson",
    "where": where_condition,
    "outFields": "*",
    "returnGeometry": "true"
  }
  result = requests.get(url, params=params)
  result.raise_for_status()
  return gpd.read_file(result.text)

def CorrectNominalPower(power: float):
  """
  Corrige valores de potência, considerando que valores coerentes 
  para aerogeradores não são maiores do que 100 MW ou menores do que 0,05 MW.
  """
  if power > 100:
    return power / 1000
  elif power < 0.05:
    return power * 1000
  else:
    return power

if __name__ == "__main__":

  url = "https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/WFS/MapServer/0/query"

  # Query de todos os Ids
  object_ids = FetchAllIds(url)
  print(f"Total de objetos: {len(object_ids)}")

  # Query dos objetos em batchs de 1000 (limite da API)
  batch_size = 1000
  gdfs = []
  for i in range(0, len(object_ids), batch_size):
    batch_ids = object_ids[i:i+batch_size]
    gdf_batch = FetchObjectsBatch(url, batch_ids)
    gdfs.append(gdf_batch)
    print(f"Lote {i//batch_size+1}: {len(gdf_batch)} registros")

  # Empilha geoDataFrame final
  gdf_total = pd.concat(gdfs, ignore_index=True)
  print(f"GeoDataFrame final: {len(gdf_total)} registros")

  # Cria colunas de lat/lon
  gdf_total["longitude"] = gdf_total.geometry.x
  gdf_total["latitude"] = gdf_total.geometry.y

  # Converte coluna de timestamp (ms) em data
  gdf_total["DATA_ATUALIZACAO_FORMATADA"] = (
      pd.to_datetime(gdf_total["DATA_ATUALIZACAO"], unit="ms", utc=True).dt.tz_convert("America/Sao_Paulo")
  )

  # Tratamento
  """
  # Valores vazios
  - ALT_TORRE: 4 rows (Serra de Gentio do Ouro XXIII)
    -> Decisão: desconsiderar NOME_EOL == "Serra de Gentio do Ouro XXIII", pois está duplicado e com valores incoerentes 
    (correto são as linhas NOME_EOL == "Serra do Gentio do Ouro XXIII")

  - EOL_VERSAO_ID: 9 rows (Asa Branca III)
  - PROPRIETARIO: 9 rows (Asa Branca III)
  - UF: 9 rows (Asa Branca III)
  - CEG: 9 rows (Asa Branca III)
    -> Decisão: aplicar UF = "RN" para Asa Branca III (conforme outros empreendimentos Asa Branca, exceto 1), 
    manter outras colunas Nan sem tratamento

  - OPERACAO 206 rows
    -> Decisão: substituir "1" por "Sim" e valores vazios por "Sem informação"
  - ORIGEM: ALL rows
    -> Decisão: manter valores Nan sem tratamento

  # Valores de Potência nominal
  - São Manoel: 12 registros com POT_MW = 4200, 2 registros com POT_MW = 4.2, mesmo EOL_VERSAO_ID
    -> Decisão: aplicar o valor de 4.2 MW para os registros com 4200 MW (valor coerente de potência nominal de um aerogerador)
  - Asa Branca III: 1 registro com POT_MW = 6750, 8 registros com POT_MW = 3032
    -> Decisão: aplicar os valores de 6.75 MW e 3.032 MW respectivamente, assumindo que o erro está na ordem de grandeza
  - Ventos de Santa Inês, Ventos de São Carlos e Ventos de Santa Rosa: 330 registros com POT_MW = 0.0042
    -> Decisão: aplicar o valor de 4.2 MW (de acordo com outros aerogeradores destes conjuntos), assumindo que o erro está na ordem de grandeza
  - Juramento: 64 registros com POT_MW = 0.006
    -> Decisão: aplicar o valor de 6 MW (de acordo com outros aerogeradores destes conjuntos), assumindo que o erro está na ordem de grandeza
  - Serra da Gameleira, Serra do Alagamar, Ventos de Santa Dulce: 114 registros com POT_MW = 0.0062
    -> Decisão: aplicar o valor de 6.2 MW (de acordo com outros aerogeradores destes conjuntos), assumindo que o erro está na ordem de grandeza

  # Outras inconsistências
  - Conjunto Barra XI: UF cadastrada como RN, mas pelo mapa os aerogeradores estão localizados em MG
    -> Decisão: alterar UF para MG
  - 36 registros com "NOME_EOL", "DEN_AEG", "latitude" e "longitude" duplicados
    -> Decisão: excluir registros duplicados
  """

  gdf_total = gdf_total[gdf_total["NOME_EOL"] != "Serra de Gentio do Ouro XXIII"]
  gdf_total.loc[gdf_total["NOME_EOL"] == "Asa Branca III", "UF"] = "RN"
  gdf_total.loc[gdf_total["NOME_EOL"] == "Barra XI", "UF"] = "MG"
  gdf_total["POT_MW"] = gdf_total["POT_MW"].apply(CorrectNominalPower)
  gdf_total["OPERACAO"] = gdf_total["OPERACAO"].apply(
    lambda x: "Sem informação" if pd.isna(x) 
    else "Sim" if str(x) == "1" 
    else x
  )
  gdf_total = gdf_total.drop_duplicates(subset=["NOME_EOL", "DEN_AEG", "latitude", "longitude"])

  gdf_total.to_csv("data.csv")
