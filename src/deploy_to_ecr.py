import os
import sys
import docker
import time
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from boto3.session import Session

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Import the deployment config and logging
from config import (
    AWS_REGION, ECR_REPOSITORY_NAME, ECR_IMAGE_TAG,
    DOCKERFILE_PATH, PROJECT_ROOT, get_ecr_repository_uri, get_image_uri,
    get_boto3_session_args
)
from _logging.pg_logger import get_logger, log_method, error_logger

# Configure the logger
logger = get_logger(
    name="deploy_to_ecr",
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_to_console=True,
    log_to_file=True,
    log_file_path=os.environ.get("LOG_FILE_PATH", "/tmp/ecr_deployment.log")
)

@log_method(level="info")
def check_artifact(checking_dirpath: str, generate_flg: bool = True) -> bool:
    from _util import _util_file as _util_file_



    """whether Dockerfile exists in the directory"""
    if file := _util_file_.find_file(starting_directory=checking_dirpath, filename="Dockerfile", max_depth=0):
        logger.info(f"Dockerfile found in {checking_dirpath}")
    else:
        logger.info(f"Dockerfile is not found in {checking_dirpath}")
        if generate_flg:
            logger.info(f"generating Dockerfile...")
            _util_file_.write_file(os.path.join(checking_dirpath, "Dockerfile"), _util_file_.load_file(
                _util_file_.find_file(starting_directory=sys.prefix, filename="Dockerfile")))
            logger.info(f"Dockerfile is generated.")
        else:
            logger.error(f"please create a Dockerfile in {checking_dirpath}")
            return False

    """whether lambda_function.py exists in the directory"""
    if file := _util_file_.find_file(starting_directory=checking_dirpath, filename="lambda_function.py", max_depth=0):
        logger.info(f"lambda_function.py found in {checking_dirpath}")
    else:
        logger.info(f"lambda_function.py is not found in {checking_dirpath}")
        if generate_flg:
            logger.info(f"generating lambda_function.py...")
            from src.gen_aws_lambda_handler import generate_lambda_handler
            print(os.environ["APP_LOCATION"])

            if not generate_lambda_handler(os.environ["APP_LOCATION"]):
                logger.error("Convert lambda handler failed")
                return False
            logger.info(f"lambda_function.py is generated.")
        else:
            logger.error(f"please create lambda_function.py in {checking_dirpath}")
            return False


    """whether requirements.txt exists in the directory"""
    if file := _util_file_.find_file(starting_directory=checking_dirpath, filename="requirements.txt", max_depth=0):
        logger.info(f"requirements.txt found in {checking_dirpath}")
    else:
        logger.error(f"requirements.txt not found in {checking_dirpath}")
        return False

    return True




@log_method(level="info")
def create_ecr_repository(fail_if_exists=False):
    """Create the ECR repository, deleting it first if it already exists unless fail_if_exists is True."""
    try:
        # Create a session with the profile if specified
        session = Session(**get_boto3_session_args())
        ecr_client = session.client('ecr')

        # Check if repository exists
        try:
            ecr_client.describe_repositories(repositoryNames=[ECR_REPOSITORY_NAME])

            if fail_if_exists:
                logger.error(f"ECR repository {ECR_REPOSITORY_NAME} already exists. Failing as requested.")
                return False

            logger.info(f"ECR repository {ECR_REPOSITORY_NAME} already exists. Deleting it first.")

            # Delete repository (force delete including images)
            ecr_client.delete_repository(repositoryName=ECR_REPOSITORY_NAME, force=True)
            logger.info(f"Deleted ECR repository: {ECR_REPOSITORY_NAME}")
        except ecr_client.exceptions.RepositoryNotFoundException:
            logger.info(f"ECR repository {ECR_REPOSITORY_NAME} does not exist, proceeding with creation.")

        # Create repository
        response = ecr_client.create_repository(
            repositoryName=ECR_REPOSITORY_NAME,
            imageScanningConfiguration={'scanOnPush': True},
            encryptionConfiguration={'encryptionType': 'AES256'}
        )
        logger.info(f"Created ECR repository: {ECR_REPOSITORY_NAME}")
        return True

    except Exception as e:
        error_logger(
            "create_ecr_repository",
            str(e),
            logger=logger,
            mode="error"
        )
        return False

@log_method(level="info")
def login_to_ecr():
    """Login to AWS ECR using Docker SDK."""
    try:
        import base64
        # session = Session(**get_boto3_session_args())
        # ecr_client = session.client('ecr')
        # token = ecr_client.get_authorization_token()
        #
        # username = "AWS"
        # password = token['authorizationData'][0]['authorizationToken']
        # decoded_token = base64.b64decode(password).decode("utf-8")
        # registry_url = token['authorizationData'][0]['proxyEndpoint'].replace("https://", "")
        #
        # client = docker.from_env()
        # print(client, decoded_token, registry_url)
        # # registry_url = "717435123117.dkr.ecr.us-east-1.amazonaws.com"
        #
        # client.login(username=username, password=decoded_token, registry=registry_url)
        # print(f"Successfully logged in to ECR: {registry_url}")
        # exit(0)
        #
        # logger.info(f"Successfully logged in to ECR: {registry_url}")
        import subprocess
        session = Session(**get_boto3_session_args())
        ecr_client = session.client('ecr')
        token = ecr_client.get_authorization_token()

        # Decode Base64-encoded token
        encoded_token = token['authorizationData'][0]['authorizationToken']
        decoded_token = base64.b64decode(encoded_token).decode("utf-8")
        username, password = decoded_token.split(":")

        # Extract the registry URL and remove `https://`
        registry_url = token['authorizationData'][0]['proxyEndpoint'].replace("https://", "")

        # Use subprocess to execute `docker login`
        login_command = f"echo {password} | docker login --username {username} --password-stdin {registry_url}"
        process = subprocess.run(login_command, shell=True, capture_output=True, text=True)

        if process.returncode != 0:
            raise Exception(f"Docker login failed: {process.stderr}")

        logger.info(f"Successfully logged in to ECR: {registry_url}")

        return True
    except (BotoCoreError, NoCredentialsError) as e:
        error_logger("login_to_ecr", str(e), logger=logger, mode="error")
        return False


@log_method(level="info")
def build_docker_image():
    """Build the Docker image using Docker SDK and show detailed logs."""
    try:
        image_name = f"{ECR_REPOSITORY_NAME}:{ECR_IMAGE_TAG}"
        dockerfile_dir = os.environ.get("APP_LOCATION", ".")
        dockerfile_path = os.path.join(dockerfile_dir, "Dockerfile")

        # Print Dockerfile content if exists
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path, "r") as dockerfile:
                dockerfile_content = dockerfile.read()
                logger.info(f"Dockerfile content:\n{dockerfile_content}")
        else:
            logger.warning("Dockerfile not found in the specified directory.")



        client = docker.from_env()

        logger.info(f"Starting Docker build for image: {image_name}")

        image, build_logs = client.images.build(path=dockerfile_dir, tag=image_name, dockerfile=dockerfile_path)

        # Print detailed logs from build process
        for log in build_logs:
            if 'stream' in log:
                logger.info(log['stream'].strip())
            elif 'error' in log:
                logger.error(log['error'].strip())

        logger.info(f"Docker image built successfully: {image_name}")
        return True
    except docker.errors.BuildError as e:
        error_logger("build_docker_image", str(e), logger=logger, mode="error")
        return False

@log_method(level="info")
def tag_and_push_image():
    """Tag and push the Docker image to ECR using Docker SDK."""
    try:
        ecr_image_uri = get_image_uri()
        if not ecr_image_uri:
            logger.error("Failed to get ECR image URI")
            return False

        local_image = f"{ECR_REPOSITORY_NAME}:{ECR_IMAGE_TAG}"

        client = docker.from_env()
        image = client.images.get(local_image)
        image.tag(ecr_image_uri)

        logger.info(f"Tagged image: {local_image} -> {ecr_image_uri}")

        push_result = client.images.push(ecr_image_uri)
        print(push_result)
        logger.info(f"Pushed image to ECR: {ecr_image_uri}\n{push_result}")

        return True
    except (docker.errors.ImageNotFound, docker.errors.APIError) as e:
        error_logger("tag_and_push_image", str(e), logger=logger, mode="error")
        return False



@log_method(level="info")
def run(app_location: str, ecr_repository_name: str = None):
    """Main function to deploy the Docker image to ECR."""
    start_time = time.time()
    
    # Override ECR_REPOSITORY_NAME if provided
    if ecr_repository_name:
        os.environ["ECR_REPOSITORY_NAME"] = ecr_repository_name
        logger.info(f"Overriding ECR repository name: {ecr_repository_name}")
        
    logger.info(f"Starting deployment to ECR: {ECR_REPOSITORY_NAME}")

    # Create repository if it doesn't exist
    if not create_ecr_repository():
        logger.error("Failed to create ECR repository")
        return False

    # Login to ECR
    if not login_to_ecr():
        logger.error("Failed to login to ECR")
        return False

    if not check_artifact(app_location):
        logger.error("Required files do not exist")
        return False

    # Build Docker image
    if not build_docker_image():
        logger.error("Failed to build Docker image")
        return False

    # Tag and push image
    if not tag_and_push_image():
        logger.error("Failed to tag and push image")
        return False

    elapsed_time = time.time() - start_time
    logger.info(f"Deployment to ECR completed successfully in {elapsed_time:.2f} seconds")
    return True
