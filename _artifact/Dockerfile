FROM public.ecr.aws/lambda/python:3.11



# Copy requirements file
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]