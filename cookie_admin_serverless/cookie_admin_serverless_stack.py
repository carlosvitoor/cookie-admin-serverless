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
    # aws_cloudfront as cloudfront, # Comentado temporariamente
    # aws_cloudfront_origins as origins, # Comentado temporariamente
)
from constructs import Construct


class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================================================
        # 1. DYNAMODB
        # ========================================================================
        table = dynamodb.Table(self, "CookiesTable",
                               partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                               removal_policy=RemovalPolicy.DESTROY,
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                               stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
                               )

        # ========================================================================
        # 2. ANALYTICS (DATA LAKE)
        # ========================================================================
        analytics_bucket = s3.Bucket(self, "AnalyticsBucket",
                                     bucket_name=f"cookie-admin-datalake-{environment_tag}",
                                     removal_policy=RemovalPolicy.DESTROY,
                                     auto_delete_objects=True
                                     )

        stream_handler = _lambda.Function(self, "StreamHandler",
                                          function_name=f"StreamHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="stream_handler.handler",
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "ANALYTICS_BUCKET_NAME": analytics_bucket.bucket_name
                                          },
                                          timeout=Duration.seconds(30),
                                          log_retention=logs.RetentionDays.ONE_WEEK
                                          )

        analytics_bucket.grant_write(stream_handler)
        stream_handler.add_event_source(eventsources.DynamoEventSource(table,
                                                                       starting_position=_lambda.StartingPosition.LATEST,
                                                                       batch_size=5,
                                                                       bisect_batch_on_error=True,
                                                                       retry_attempts=2
                                                                       ))

        # ========================================================================
        # 3. FRONTEND (S3 PURO - MODO WEBSITE)
        # ========================================================================
        # Alteração: Public Read Access ativado para funcionar sem CloudFront
        site_bucket = s3.Bucket(self, "SiteBucket",
                                bucket_name=f"cookie-admin-site-{environment_tag}",
                                website_index_document="index.html",  # Ativa modo hospedagem
                                public_read_access=True,  # ATENÇÃO: Bucket Público
                                block_public_access=s3.BlockPublicAccess(
                                    block_public_acls=False,
                                    block_public_policy=False,
                                    ignore_public_acls=False,
                                    restrict_public_buckets=False
                                ),
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )

        # CloudFront removido temporariamente devido ao bloqueio da conta AWS
        # distribution = ...

        # ========================================================================
        # 4. BACKEND (API)
        # ========================================================================

        # Como não temos CloudFront, o CORS deve aceitar a URL do S3 ou '*'
        allowed_origin = "*"
        if environment_tag == 'prod':
            # Em prod, pegamos a URL do site S3
            allowed_origin = site_bucket.bucket_website_url

        cookie_handler = _lambda.Function(self, "CookieHandler",
                                          function_name=f"CookieHandler-{environment_tag}",
                                          runtime=_lambda.Runtime.PYTHON_3_12,
                                          handler="index.handler",
                                          code=_lambda.Code.from_asset("src"),
                                          environment={
                                              "TABLE_NAME": table.table_name,
                                              "ENV_TYPE": environment_tag,
                                              "ALLOWED_ORIGIN": allowed_origin
                                          },
                                          timeout=Duration.seconds(10),
                                          log_retention=logs.RetentionDays.ONE_WEEK
                                          )

        table.grant_read_write_data(cookie_handler)

        api = apigw.HttpApi(self, "CookieAdminApi",
                            api_name=f"CookieAdminApi-{environment_tag}",
                            default_integration=integrations.HttpLambdaIntegration(
                                "CookieHandlerIntegration", cookie_handler
                            )
                            )

        # ========================================================================
        # 5. OUTPUTS
        # ========================================================================
        CfnOutput(self, "ApiUrl", value=api.url)
        # Agora a URL do site é direta do Bucket S3
        CfnOutput(self, "SiteUrl", value=site_bucket.bucket_website_url)
        CfnOutput(self, "SiteBucketName",
                  value=site_bucket.bucket_website_url)  # Usando a URL aqui para facilitar o script de deploy se precisar