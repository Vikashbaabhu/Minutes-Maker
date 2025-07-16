resource "aws_apigatewayv2_api" "video_upload_http_api" {
  name          = "video-upload-http-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "video_upload_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.video_upload_http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.video_upload_handler.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "video_upload_route" {
  api_id    = aws_apigatewayv2_api.video_upload_http_api.id
  route_key = "POST /upload"
  target    = "integrations/${aws_apigatewayv2_integration.video_upload_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "video_upload_get_status_route" {
  api_id    = aws_apigatewayv2_api.video_upload_http_api.id
  route_key = "GET /status"
  target    = "integrations/${aws_apigatewayv2_integration.video_upload_lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "video_upload_api_stage" {
  api_id      = aws_apigatewayv2_api.video_upload_http_api.id
  name        = "prod"
  auto_deploy = true
}

resource "aws_lambda_permission" "video_upload_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.video_upload_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.video_upload_http_api.execution_arn}/*/*"
}
