from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB: O Banco de Dados
        table = dynamodb.Table(self, "CookiesTable",
            table_name=f"CookiesTable-{environment_tag}",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY # Cuidado em Prod!
        )

        # 2. Lambda: A Lógica (Lendo da pasta src)
        cookie_handler = _lambda.Function(self, "CookieHandler",
            function_name=f"CookieHandler-{environment_tag}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",       # Aponta para src/index.py -> def handler
            code=_lambda.Code.from_asset("src"),
            environment={
                "TABLE_NAME": table.table_name,
                "ENV_TYPE": environment_tag
            },
            timeout=Duration.seconds(10)
        )

        # Permissão: Deixa a Lambda escrever na tabela
        table.grant_read_write_data(cookie_handler)

        # 3. API Gateway: A Porta Pública (HTTP API)
        http_api = apigw.HttpApi(self, "CookieApi",
            api_name=f"CookieApi-{environment_tag}",
            description=f"API Gateway para o ambiente {environment_tag}"
        )

        # Integração: Conecta o Gateway na Lambda
        lambda_int = integrations.HttpLambdaIntegration(
            "CookieIntegration",
            cookie_handler
        )

        # Rotas: Envia tudo de /cookies para a Lambda
        http_api.add_routes(
            path="/cookies",
            methods=[apigw.HttpMethod.GET, apigw.HttpMethod.POST],
            integration=lambda_int
        )

        # Output: Mostra a URL no final do deploy
        CfnOutput(self, "ApiUrl",
            value=http_api.url,
            description="URL publica da API"
        )