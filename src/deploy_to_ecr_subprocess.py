"""
Script to build and deploy Docker image to ECR.
"""
import os
import sys
import subprocess
import boto3
import time
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
def run_command_progress(command: str):
    try:
        logger.info(f"running {command} ...")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())

        # stdout = subprocess.PIPE, stderr = subprocess.STDOUT, text = True)

        logger.info(process.stdout)
        logger.info(process.stderr)
        return process
    except subprocess.CalledProcessError as err:
        logger.error(f"An error occurred while executing the command. {err}\n")
        # _common_.error_logger(currentframe().f_code.co_name,
        #                       f"An error occurred while executing the command. \n"
        #                       f"Error code: {err.returncode} \n"
        #                       f"Error message: {err.stderr}",
        #                       logger=logger,
        #                       mode="error",
        #                       ignore_flag=False)


@log_method(level="info")
def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_logger(
            "run_command",
            f"Command failed with exit code {e.returncode}: {e.stderr}",
            logger=logger,
            mode="error"
        )
        raise


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

# @log_method(level="info")
# def create_ecr_repository_if_not_exists():
#     """Create the ECR repository if it doesn't exist."""
#     try:
#         # Create a session with the profile if specified
#         session = Session(**get_boto3_session_args())
#         ecr_client = session.client('ecr')
#
#         # Check if repository exists
#         try:
#             ecr_client.describe_repositories(repositoryNames=[ECR_REPOSITORY_NAME])
#             logger.info(f"ECR repository {ECR_REPOSITORY_NAME} already exists")
#             return True
#         except ecr_client.exceptions.RepositoryNotFoundException:
#             # Create repository
#             response = ecr_client.create_repository(
#                 repositoryName=ECR_REPOSITORY_NAME,
#                 imageScanningConfiguration={'scanOnPush': True},
#                 encryptionConfiguration={'encryptionType': 'AES256'}
#             )
#             logger.info(f"Created ECR repository: {ECR_REPOSITORY_NAME}")
#             return True
#     except Exception as e:
#         error_logger(
#             "create_ecr_repository_if_not_exists",
#             str(e),
#             logger=logger,
#             mode="error"
#         )
#         return False


@log_method(level="info")
def get_ecr_login_command():
    """Get the ECR login command."""
    try:
        # Create a session with the profile if specified
        session = Session(**get_boto3_session_args())
        ecr_client = session.client('ecr')
        token = ecr_client.get_authorization_token()

        # print(token['authorizationData'][0]['authorizationToken'])
        # endpoint = token['authorizationData'][0]['proxyEndpoint']
        # print(endpoint)
        username = "AWS"
        # exit(0)

        # username, password = token['authorizationData'][0]['authorizationToken'].split(':')

        password = token['authorizationData'][0]['authorizationToken']

        # print("!!!!")
        # exit(0)
        endpoint = token['authorizationData'][0]['proxyEndpoint']

        print(username, password, endpoint)

        # exit(0)

        # Use Docker login command
        login_command = f"docker login --username AWS --password-stdin {endpoint}"
        logger.info(f"Generated ECR login command for endpoint: {endpoint}")
        print(f"Login command: {login_command}")
        return login_command, password
    except Exception as e:
        error_logger(
            "get_ecr_login_command",
            str(e),
            logger=logger,
            mode="error"
        )
        return None, None


@log_method(level="info")
def login_to_ecr():
    """Login to ECR."""
    try:
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        ecr_registry = os.getenv("ECR_REGISTRY", "717435123117.dkr.ecr.us-east-1.amazonaws.com")

        # Construct the AWS ECR login command
        login_command = f"aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {ecr_registry}"

        # Execute the command
        process = subprocess.Popen(
            login_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_logger(
                "login_to_ecr",
                f"ECR login failed: {stderr}",
                logger=logger,
                mode="error"
            )
            return False

        logger.info("Successfully logged in to ECR")
        return True
    except Exception as e:
        error_logger(
            "login_to_ecr",
            str(e),
            logger=logger,
            mode="error"
        )
        return False


# def login_to_ecr():
#     """Login to ECR."""
#     try:
#         login_command, password = get_ecr_login_command()
#         if not login_command:
#             return False
#
#         # Execute login command
#         process = subprocess.Popen(
#             login_command,
#             shell=True,
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )
#         stdout, stderr = process.communicate(input=password)
#
#         if process.returncode != 0:
#             error_logger(
#                 "login_to_ecr",
#                 f"ECR login failed: {stderr}",
#                 logger=logger,
#                 mode="error"
#             )
#             return False
#
#         logger.info("Successfully logged in to ECR")
#         return True
#     except Exception as e:
#         error_logger(
#             "login_to_ecr",
#             str(e),
#             logger=logger,
#             mode="error"
#         )
#         return False

@log_method(level="info")
def build_docker_image():
    """Build the Docker image."""
    try:
        image_name = f"{ECR_REPOSITORY_NAME}:{ECR_IMAGE_TAG}"
        print(image_name)


        # Get the directory containing the Dockerfile
        dockerfile_dir = DOCKERFILE_PATH.parent
        # print(dockerfile_dir)
        # exit(0)

        dockerfile_dir = os.environ.get("APP_LOCATION")
        print(dockerfile_dir)


        # Build the Docker image from the directory containing the Dockerfile
        build_command = f"docker build -t {image_name} -f {os.path.join(dockerfile_dir, 'Dockerfile')} {dockerfile_dir}"

        print(build_command)
        output = run_command_progress(build_command)
        logger.info(f"Docker image built successfully: {image_name}")
        return True
    except Exception as e:
        error_logger(
            "build_docker_image",
            str(e),
            logger=logger,
            mode="error"
        )
        return False


@log_method(level="info")
def tag_and_push_image():
    """Tag and push the Docker image to ECR."""
    try:
        local_image = f"{ECR_REPOSITORY_NAME}:{ECR_IMAGE_TAG}"
        ecr_image_uri = get_image_uri()

        if not ecr_image_uri:
            logger.error("Failed to get ECR image URI")
            return False

        # Tag the image
        tag_command = f"docker tag {local_image} {ecr_image_uri}"
        run_command_progress(tag_command)
        # run_command(tag_command)
        logger.info(f"Tagged image: {local_image} -> {ecr_image_uri}")

        # Push the image
        push_command = f"docker push {ecr_image_uri}"
        run_command_progress(push_command)
        # run_command(push_command)
        logger.info(f"Pushed image to ECR: {ecr_image_uri}")

        return True
    except Exception as e:
        error_logger(
            "tag_and_push_image",
            str(e),
            logger=logger,
            mode="error"
        )
        return False


@log_method(level="info")
def run():
    """Main function to deploy the Docker image to ECR."""
    start_time = time.time()
    logger.info(f"Starting deployment to ECR: {ECR_REPOSITORY_NAME}")

    # Create repository if it doesn't exist
    if not create_ecr_repository():
        logger.error("Failed to create ECR repository")
        return False

    # Login to ECR
    if not login_to_ecr():
        logger.error("Failed to login to ECR")
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