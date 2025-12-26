from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_s3 as s3,
    aws_logs as logs,
    aws_lambda_event_sources as eventsources,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================================================
        # 1. CAMADA DE DADOS (DYNAMODB)
        # ========================================================================
        table = dynamodb.Table(self, "CookiesTable",
                               partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                               removal_policy=RemovalPolicy.DESTROY,  # Em PROD real, mude para RETAIN
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                               stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES  # Necessário para o Analytics
                               )

        # ========================================================================
        # 2. CAMADA DE ANALYTICS (DATA LAKE)
        # ========================================================================
        # Bucket para salvar o histórico de vendas (OLAP)
        analytics_bucket = s3.Bucket(self, "AnalyticsBucket",
                                     bucket_name=f"cookie-admin-datalake-{environment_tag}",
                                     removal_policy=RemovalPolicy.DESTROY,
                                     auto_delete_objects=True
                                     )

        # Lambda que processa o Stream do Dynamo e joga no S3
        stream_handler = _lambda.Function(self, "StreamHandler",
                                          function_name=f"StreamHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="stream_handler.handler",
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "ANALYTICS_BUCKET_NAME": analytics_bucket.bucket_name
                                          },
                                          timeout=Duration.seconds(30),
                                          log_retention=logs.RetentionDays.ONE_WEEK  # FinOps: Limpa logs antigos
                                          )

        # Permissões do Stream
        analytics_bucket.grant_write(stream_handler)
        stream_handler.add_event_source(eventsources.DynamoEventSource(table,
                                                                       starting_position=_lambda.StartingPosition.LATEST,
                                                                       batch_size=5,
                                                                       bisect_batch_on_error=True,
                                                                       retry_attempts=2
                                                                       ))

        # ========================================================================
        # 3. CAMADA DE FRONTEND (S3 + CLOUDFRONT)
        # ========================================================================
        # Bucket que hospeda o site React
        site_bucket = s3.Bucket(self, "SiteBucket",
                                bucket_name=f"cookie-admin-site-{environment_tag}",
                                website_index_document="index.html",
                                public_read_access=False,
                                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )

        # CloudFront (CDN) - Distribui o site mundialmente via HTTPS
        distribution = cloudfront.Distribution(self, "SiteDistribution",
                                               default_behavior=cloudfront.BehaviorOptions(
                                                   origin=origins.S3Origin(site_bucket),
                                                   viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                                               ),
                                               default_root_object="index.html",
                                               )

        # ========================================================================
        # 4. CAMADA DE BACKEND (API)
        # ========================================================================

        # Definição Dinâmica de CORS (Segurança)
        # Se for PROD, só aceita chamadas vindas do CloudFront.
        # Se for DEV, aceita tudo ('*') para facilitar testes locais.
        allowed_origin = "*"
        if environment_tag == 'prod':
            allowed_origin = f"https://{distribution.distribution_domain_name}"

        # Lambda Principal (Controller da API)
        cookie_handler = _lambda.Function(self, "CookieHandler",
                                          function_name=f"CookieHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="index.handler",
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "TABLE_NAME": table.table_name,
                                              "ENV_TYPE": environment_tag,
                                              "ALLOWED_ORIGIN": allowed_origin  # Injeção da URL segura
                                          },
                                          timeout=Duration.seconds(10),
                                          log_retention=logs.RetentionDays.ONE_WEEK
                                          )

        # Permissão para a Lambda ler/escrever na tabela
        table.grant_read_write_data(cookie_handler)

        # API Gateway (HTTP API - Mais barato e rápido que REST API)
        api = apigw.HttpApi(self, "CookieAdminApi",
                            api_name=f"CookieAdminApi-{environment_tag}",
                            default_integration=integrations.HttpLambdaIntegration(
                                "CookieHandlerIntegration", cookie_handler
                            )
                            )

        # ========================================================================
        # 5. OUTPUTS (Informações Úteis)
        # ========================================================================
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "SiteUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)
        CfnOutput(self, "DataLakeBucketName", value=analytics_bucket.bucket_name)