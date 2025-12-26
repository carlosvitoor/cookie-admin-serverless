from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class CookieAdminServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_tag: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB
        table = dynamodb.Table(self, "CookiesTable",
            table_name=f"CookiesTable-{environment_tag}",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 2. Lambda Function (Apontando para a pasta src)
        cookie_handler = _lambda.Function(self, "CookieHandler",
            function_name=f"CookieHandler-{environment_tag}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",       # Arquivo index.py, funcao handler
            code=_lambda.Code.from_asset("src"), # Pega o conteudo da pasta src
            environment={
                "TABLE_NAME": table.table_name,
                "ENV_TYPE": environment_tag
            },
            timeout=Duration.seconds(10)
        )

        # 3. Permissões
        table.grant_read_write_data(cookie_handler)