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

        # 1. DynamoDB
        table = dynamodb.Table(self, "CookiesTable",
                               table_name=f"CookiesTable-{environment_tag}",
                               partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                               stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
                               removal_policy=RemovalPolicy.DESTROY
                               )

        # 2. Analytics Bucket
        analytics_bucket = s3.Bucket(self, "AnalyticsBucket",
                                     bucket_name=f"cookie-admin-datalake-{environment_tag}",
                                     versioned=True,
                                     removal_policy=RemovalPolicy.DESTROY,
                                     auto_delete_objects=True
                                     )

        # 3. Site Bucket (Frontend)
        site_bucket = s3.Bucket(self, "SiteBucket",
                                bucket_name=f"cookie-admin-site-{environment_tag}",
                                website_index_document="index.html",
                                public_read_access=True,
                                block_public_access=s3.BlockPublicAccess(
                                    block_public_acls=False,
                                    block_public_policy=False,
                                    ignore_public_acls=False,
                                    restrict_public_buckets=False
                                ),
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )

        # Configuração de Origem (CORS) para o Bucket (Opcional, mas bom para segurança)
        allowed_origin = "*"
        if environment_tag == 'prod':
            allowed_origin = site_bucket.bucket_website_url

        # 4. Lambda Principal
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
                                          log_retention=logs.RetentionDays.ONE_WEEK,
                                          )
        table.grant_read_write_data(cookie_handler)

        # --- MUDANÇA PRINCIPAL: CORS NO API GATEWAY ---
        http_api = apigw.HttpApi(self, "CookieApi",
                                 api_name=f"CookieApi-{environment_tag}",
                                 cors_preflight=apigw.CorsPreflightOptions(
                                     allow_origins=["*"],
                                     allow_methods=[
                                         apigw.HttpMethod.GET,
                                         apigw.HttpMethod.POST,
                                         apigw.HttpMethod.PUT,
                                         apigw.HttpMethod.PATCH,
                                         apigw.HttpMethod.OPTIONS
                                     ],
                                     allow_headers=["Content-Type", "Authorization"]
                                 )
                                 )

        lambda_int = integrations.HttpLambdaIntegration("CookieIntegration", cookie_handler)

        # Rotas explícitas garantem que o Gateway saiba rotear corretamente
        http_api.add_routes(path="/cookies", methods=[apigw.HttpMethod.ANY], integration=lambda_int)
        http_api.add_routes(path="/cookies/{id}", methods=[apigw.HttpMethod.ANY], integration=lambda_int)
        http_api.add_routes(path="/orders", methods=[apigw.HttpMethod.ANY], integration=lambda_int)
        http_api.add_routes(path="/logistics/routes", methods=[apigw.HttpMethod.ANY], integration=lambda_int)
        # ----------------------------------------------

        # 5. Stream Lambda
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

        # Outputs
        CfnOutput(self, "ApiUrl", value=http_api.url)
        CfnOutput(self, "SiteUrl", value=site_bucket.bucket_website_url)
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)