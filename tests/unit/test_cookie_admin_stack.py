import aws_cdk as core
import aws_cdk.assertions as assertions

from cookie_admin.cookie_admin_stack import CookieAdminStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cookie_admin/cookie_admin_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CookieAdminStack(app, "cookie-admin")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
