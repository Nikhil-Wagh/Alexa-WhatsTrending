zip  -r my_lambda.zip . --exclude events/ --exclude  upload.sh
aws s3 cp my_lambda.zip s3://trendingbucket/
aws lambda update-function-code --function-name "trending-function" --s3-bucket "trendingbucket" --s3-key "my_lambda.zip"
rm my_lambda.zip
echo "DONE"
