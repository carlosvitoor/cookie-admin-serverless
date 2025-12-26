import aws_cdk as core
import aws_cdk.assertions as assertions

from cookie_admin_serverless.cookie_admin_serverless_stack import CookieAdminServerlessStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cookie_admin_serverless/cookie_admin_serverless_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CookieAdminServerlessStack(app, "cookie-admin-serverless")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
