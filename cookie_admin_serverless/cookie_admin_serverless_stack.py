from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_s3 as s3,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from aws_cdk import aws_lambda_event_sources as eventsources


class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB (Atualizado para Analytics)
        table = dynamodb.Table(self, "CookiesTable",
                               table_name=f"CookiesTable-{environment_tag}",
                               partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,

                               # --- ATIVAÇÃO DO STREAM (CRUCIAL PARA ANALYTICS) ---
                               # NEW_AND_OLD_IMAGES: Guarda como era o dado antes e como ficou.
                               # Ideal para calcular deltas (ex: tempo que ficou em "EM_PREPARO")
                               stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,

                               removal_policy=RemovalPolicy.DESTROY
                               )

        # 2. Bucket S3 (O Data Lake / Tabela Democratizada)
        analytics_bucket = s3.Bucket(self, "AnalyticsBucket",
                                     bucket_name=f"cookie-admin-datalake-{environment_tag}",
                                     versioned=True,
                                     removal_policy=RemovalPolicy.DESTROY,  # Em prod seria RETAIN
                                     auto_delete_objects=True  # Limpa o bucket se destruir a stack (DEV only)
                                     )

        # ... (Definição da Lambda e API Gateway continua igual) ...
        # Apenas lembre de copiar o restante do código da Lambda/API Gateway aqui
        # Vou omitir para economizar espaço, mas mantenha o que já existia.

        cookie_handler = _lambda.Function(self, "CookieHandler",
                                          function_name=f"CookieHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="index.handler",
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "TABLE_NAME": table.table_name,
                                              "ENV_TYPE": environment_tag
                                          },
                                          timeout=Duration.seconds(10),
                                          log_retention=logs.RetentionDays.ONE_WEEK,  # Guarda logs por 7 dias apenas
                                          )
        table.grant_read_write_data(cookie_handler)

        http_api = apigw.HttpApi(self, "CookieApi", api_name=f"CookieApi-{environment_tag}")
        lambda_int = integrations.HttpLambdaIntegration("CookieIntegration", cookie_handler)
        http_api.add_routes(path="/cookies", methods=[apigw.HttpMethod.ANY], integration=lambda_int)

        CfnOutput(self, "ApiUrl", value=http_api.url)
        CfnOutput(self, "BucketName", value=analytics_bucket.bucket_name)

        stream_handler = _lambda.Function(self, "StreamHandler",
                                          function_name=f"StreamHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="stream_handler.handler",  # Aponta para o novo arquivo
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "ANALYTICS_BUCKET_NAME": analytics_bucket.bucket_name
                                          },
                                          timeout=Duration.seconds(30),
                                          log_retention=logs.RetentionDays.ONE_WEEK
                                          )

        # 3. Dar permissão de escrita no Bucket
        analytics_bucket.grant_write(stream_handler)

        # 4. Conectar o DynamoDB Stream na Lambda
        # Isso faz a mágica: Sempre que o Dynamo mudar, a Lambda roda.
        stream_handler.add_event_source(eventsources.DynamoEventSource(table,
                                                                       starting_position=_lambda.StartingPosition.LATEST,
                                                                       batch_size=5,
                                                                       # Processa de 5 em 5 para economizar
                                                                       bisect_batch_on_error=True,
                                                                       retry_attempts=2
                                                                       ))