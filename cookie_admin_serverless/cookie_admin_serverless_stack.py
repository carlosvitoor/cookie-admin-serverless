from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_cognito as cognito,
    aws_s3 as s3,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from aws_cdk import aws_lambda_event_sources as eventsources
from aws_cdk.aws_apigatewayv2_authorizers import HttpUserPoolAuthorizer


class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. BANCO DE DADOS
        table = dynamodb.Table(self, "CookiesTable",
                               table_name=f"CookiesTable-{environment_tag}",
                               partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                               stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
                               removal_policy=RemovalPolicy.DESTROY
                               )

        # 2. AUTENTICAÇÃO (Cognito)
        user_pool = cognito.UserPool(self, "CookieAuthPool",
                                     user_pool_name=f"CookieUsers-{environment_tag}",
                                     self_sign_up_enabled=False,
                                     sign_in_aliases=cognito.SignInAliases(email=True),
                                     removal_policy=RemovalPolicy.DESTROY
                                     )

        user_pool_client = user_pool.add_client("CookieAppClient",
                                                user_pool_client_name=f"CookieAppClient-{environment_tag}",
                                                auth_flows=cognito.AuthFlow(user_password=True)
                                                )

        authorizer = HttpUserPoolAuthorizer("CookieAuthorizer", user_pool,
                                            user_pool_clients=[user_pool_client]
                                            )

        # 3. BUCKETS
        analytics_bucket = s3.Bucket(self, "AnalyticsBucket",
                                     bucket_name=f"cookie-admin-datalake-{environment_tag}",
                                     versioned=True,
                                     removal_policy=RemovalPolicy.DESTROY,
                                     auto_delete_objects=True
                                     )

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

        allowed_origin = "*"
        if environment_tag == 'prod':
            allowed_origin = site_bucket.bucket_website_url

        # 4. LAMBDA PRINCIPAL
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

        # 5. API GATEWAY
        http_api = apigw.HttpApi(self, "CookieApi",
                                 api_name=f"CookieApi-{environment_tag}",
                                 cors_preflight=apigw.CorsPreflightOptions(
                                     allow_origins=["*"],
                                     allow_methods=[apigw.CorsHttpMethod.ANY],
                                     allow_headers=["Content-Type", "Authorization"]
                                 )
                                 )

        lambda_int = integrations.HttpLambdaIntegration("CookieIntegration", cookie_handler)

        # --- TODAS AS ROTAS SÃO PRIVADAS AGORA ---

        # Rotas de Cookies (Listar, Criar, Editar, Deletar)
        http_api.add_routes(path="/cookies", methods=[apigw.HttpMethod.GET, apigw.HttpMethod.POST],
                            integration=lambda_int, authorizer=authorizer)
        http_api.add_routes(path="/cookies/{id}", methods=[apigw.HttpMethod.PUT, apigw.HttpMethod.DELETE],
                            integration=lambda_int, authorizer=authorizer)

        # Rotas de Pedidos (Listar, Criar, Status, Extravio)
        http_api.add_routes(path="/orders", methods=[apigw.HttpMethod.GET, apigw.HttpMethod.POST],
                            integration=lambda_int, authorizer=authorizer)
        http_api.add_routes(path="/orders/{id}/status", methods=[apigw.HttpMethod.PATCH],
                            integration=lambda_int, authorizer=authorizer)
        http_api.add_routes(path="/orders/{id}/loss", methods=[apigw.HttpMethod.POST],
                            integration=lambda_int, authorizer=authorizer)

        # Logística
        http_api.add_routes(path="/logistics/routes", methods=[apigw.HttpMethod.POST],
                            integration=lambda_int, authorizer=authorizer)

        # 6. STREAM LAMBDA
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

        # OUTPUTS
        CfnOutput(self, "ApiUrl", value=http_api.url)
        CfnOutput(self, "SiteUrlS3", value=site_bucket.bucket_website_url)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)