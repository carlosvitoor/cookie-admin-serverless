#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cookie_admin_serverless.cookie_admin_serverless_stack import CookieAdminServerlessStack

app = cdk.App()

# Lendo o contexto passado via linha de comando (-c config=dev|homol|prod)
# Se não passar nada, assume 'dev' por segurança.
env_tag = app.node.try_get_context("config") or "dev"

# Define o nome da Stack baseado no ambiente
# Ex: CookieAdmin-Dev, CookieAdmin-Homol, CookieAdmin-Prod
stack_name = f"CookieAdmin-{env_tag.capitalize()}"

print(f"Synthesizing stack for environment: {env_tag}")

CookieAdminServerlessStack(app, stack_name,
    environment_tag=env_tag, # Passamos a tag para dentro da classe
    # Se quiser fixar conta/região, descomente abaixo:
    # env=cdk.Environment(account='123456789012', region='us-east-1'),
)

app.synth()