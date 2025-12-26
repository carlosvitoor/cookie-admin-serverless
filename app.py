import os
import aws_cdk as cdk
# ATENÇÃO: Verifique se o nome da pasta gerada é 'cookie_admin_serverless' ou 'cookie_admin'
# O CDK usa o nome da pasta pai. Ajuste o import abaixo conforme o nome da pasta criada.
from cookie_admin_serverless.cookie_admin_serverless_stack import CookieAdminServerlessStack

app = cdk.App()

# DEV
CookieAdminServerlessStack(app, "CookieAdmin-Dev",
    stack_name="CookieAdmin-Dev",
    environment_tag="dev",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-east-1')
)

# STAGING
CookieAdminServerlessStack(app, "CookieAdmin-Staging",
    stack_name="CookieAdmin-Staging",
    environment_tag="staging",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-east-1')
)

# PROD
CookieAdminServerlessStack(app, "CookieAdmin-Prod",
    stack_name="CookieAdmin-Prod",
    environment_tag="prod",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-east-1')
)

app.synth()