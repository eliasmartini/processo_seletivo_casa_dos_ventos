# processo_seletivo_casa_dos_ventos
Case de data analytics do processo seletivo para a Casa dos Ventos, agosto de 2025.

# Projeto de Coleta e Tratamento de Dados de Aerogeradores

Este repositório contém um script Python para coletar, processar e tratar dados de aerogeradores a partir da API SIGEL da ANEEL.  

O projeto foi desenvolvido como parte de um processo seletivo e demonstra habilidades em Python, manipulação de dados geográficos e tratamento de inconsistências em datasets.

## Conteúdo do Repositório

- `main.py`: Script principal para consulta da API, tratamento de dados e geração do CSV final.
- `data.csv`: Arquivo CSV com os dados tratados dos aerogeradores.

## Funcionalidades

1. **Consulta à API SIGEL**  
   - Coleta todos os IDs de aerogeradores disponíveis.
   - Faz download dos dados em batches (limite de 1000 objetos por requisição).
   - Retorna os dados em formato GeoDataFrame.

2. **Tratamento dos dados**  
   - Criação de colunas de latitude e longitude a partir da geometria.
   - Conversão de timestamps para o fuso horário `America/Sao_Paulo`.
   - Correção de inconsistências em campos como potência nominal (`POT_MW`) e operação (`OPERACAO`).
   - Remoção de duplicados e ajustes manuais em UF de alguns aerogeradores.

3. **Exportação**  
   - Geração do arquivo `data.csv` contendo todos os registros tratados.
