import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.types import TypeDeserializer

# Configuração
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('ANALYTICS_BUCKET_NAME')
deserializer = TypeDeserializer()


def handler(event, context):
    """
    Escuta o DynamoDB Stream e projeta os dados no S3 (Data Lake).
    """
    records_to_save = []

    for record in event['Records']:
        # Só nos interessa inserções ou atualizações (INSERT/MODIFY)
        if record['eventName'] == 'REMOVE':
            continue

        # 1. Deserializar o formato estranho do Dynamo ({'S': 'valor'}) para Python normal
        dynamo_image = record['dynamodb']['NewImage']
        item = {k: deserializer.deserialize(v) for k, v in dynamo_image.items()}

        # 2. Filtrar: Só queremos PEDIDOS para o Analytics de Vendas
        if item.get('tipo_item') != 'PEDIDO':
            continue

        # 3. TRANSFORMAÇÃO (O Segredo do OLAP)
        # Vamos "explodir" o pedido. Se tem 3 cookies, viram 3 linhas de venda.

        data_criacao = item.get('criado_em', datetime.now().isoformat())
        # Extrai ano/mes/dia para particionar no S3 (Melhora performance e custo)
        dt_obj = datetime.fromisoformat(data_criacao)
        partition_path = f"year={dt_obj.year}/month={dt_obj.month:02d}/day={dt_obj.day:02d}"

        # Dados comuns a todos os itens do pedido (Dimensões)
        base_record = {
            "pedido_id": item['id'],
            "data_venda": data_criacao,
            "status": item.get('status'),
            "cliente_nome": item.get('cliente_nome'),
            "forma_pagamento": item.get('forma_pagamento'),
            "motoboy_custo_rateado": float(item.get('custo_entrega_rateado', 0) or 0)
        }

        # Achata os itens (Fatos)
        itens = item.get('itens', [])
        qtd_itens_total = sum(int(i.get('qtd', 0)) for i in itens)

        for line_item in itens:
            # Clona o registro base
            fact_row = base_record.copy()

            # Adiciona dados específicos do produto
            fact_row['produto_id'] = line_item.get('cookie_id')
            fact_row['sabor'] = line_item.get('sabor')
            fact_row['qtd'] = int(line_item.get('qtd', 0))

            # Finanças (Importante converter Decimal pra float pro JSON final)
            preco_venda = float(line_item.get('preco_venda_unitario', 0))
            custo_prod = float(line_item.get('custo_producao_unitario', 0))

            fact_row['receita_item'] = preco_venda * fact_row['qtd']
            fact_row['custo_item'] = custo_prod * fact_row['qtd']

            # Custo Logístico por ITEM (Rateio do Rateio)
            # Se o pedido tem 5 itens e o frete foi 5 reais, é 1 real por item.
            if qtd_itens_total > 0:
                fact_row['custo_logistico_item'] = base_record['motoboy_custo_rateado'] / qtd_itens_total
            else:
                fact_row['custo_logistico_item'] = 0

            # LUCRO FINAL (A métrica de ouro)
            fact_row['lucro_liquido'] = fact_row['receita_item'] - fact_row['custo_item'] - fact_row[
                'custo_logistico_item']

            # Adiciona na lista para salvar
            # Formato JSON Line (um JSON por linha)
            records_to_save.append({
                "path": partition_path,
                "data": json.dumps(fact_row, default=str)
            })

    # 4. Salvar no S3 (Batch Write)
    if records_to_save:
        save_to_s3(records_to_save)

    return {"message": f"Processados {len(records_to_save)} itens de venda."}


def save_to_s3(records):
    """
    Agrupa por partição e salva arquivos no S3.
    """
    # Agrupamento simples para não criar 1000 arquivos pequenos
    grouped = {}
    for rec in records:
        path = rec['path']
        if path not in grouped:
            grouped[path] = []
        grouped[path].append(rec['data'])

    for path, rows in grouped.items():
        # Nome do arquivo único para não sobrescrever
        filename = f"sales_data/{path}/vendas_{datetime.now().timestamp()}.json"

        # Junta tudo com quebra de linha (NDJSON)
        body_content = "\n".join(rows)

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=body_content,
            ContentType='application/json'
        )
        print(f"Salvo no S3: {filename}")