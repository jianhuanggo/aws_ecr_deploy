# import pytest
# from unittest.mock import patch, MagicMock
#
# ECR_REPOSITORY_NAME = "test-repo"
#
# """
# pip install pytest-cov
#
# """
#
#
# @patch('src.deploy_to_ecr.Session')
# @patch('src.deploy_to_ecr.logger')
# def test_create_repository_when_not_exists(mock_logger, mock_session):
#     mock_ecr_client = MagicMock()
#     mock_session.return_value.client.return_value = mock_ecr_client
#     mock_ecr_client.describe_repositories.side_effect = mock_ecr_client.exceptions.RepositoryNotFoundException({})
#     mock_ecr_client.create_repository.return_value = {}
#
#     from lambda_docker.aws_deployment.src.deploy_to_ecr import create_ecr_repository
#     result = create_ecr_repository()
#
#     assert result is True
#     mock_ecr_client.create_repository.assert_called_once()
#     mock_logger.info.assert_any_call(f"Created ECR repository: {ECR_REPOSITORY_NAME}")
#
#
# @patch('src.deploy_to_ecr.Session')
# @patch('src.deploy_to_ecr.logger')
# def test_fail_if_repository_exists(mock_logger, mock_session):
#     mock_ecr_client = MagicMock()
#     mock_session.return_value.client.return_value = mock_ecr_client
#     mock_ecr_client.describe_repositories.return_value = {}
#
#     from lambda_docker.aws_deployment.src.deploy_to_ecr import create_ecr_repository
#     result = create_ecr_repository(fail_if_exists=True)
#
#     assert result is False
#     mock_logger.error.assert_called_with(f"ECR repository {ECR_REPOSITORY_NAME} already exists. Failing as requested.")
#     mock_ecr_client.delete_repository.assert_not_called()
#     mock_ecr_client.create_repository.assert_not_called()
#
#
# @patch('src.deploy_to_ecr.Session')
# @patch('src.deploy_to_ecr.logger')
# def test_delete_and_create_repository_if_exists(mock_logger, mock_session):
#     mock_ecr_client = MagicMock()
#     mock_session.return_value.client.return_value = mock_ecr_client
#     mock_ecr_client.describe_repositories.return_value = {}
#     mock_ecr_client.create_repository.return_value = {}
#
#     from lambda_docker.aws_deployment.src.deploy_to_ecr import create_ecr_repository
#     result = create_ecr_repository()
#
#     assert result is True
#     mock_ecr_client.delete_repository.assert_called_once_with(repositoryName=ECR_REPOSITORY_NAME, force=True)
#     mock_ecr_client.create_repository.assert_called_once()
#     mock_logger.info.assert_any_call(f"Deleted ECR repository: {ECR_REPOSITORY_NAME}")
#
#
# @patch('src.deploy_to_ecr.Session')
# @patch('src.deploy_to_ecr.logger')
# @patch('src.deploy_to_ecr.error_logger')
# def test_handle_exception(mock_error_logger, mock_logger, mock_session):
#     mock_ecr_client = MagicMock()
#     mock_session.return_value.client.return_value = mock_ecr_client
#     mock_ecr_client.create_repository.side_effect = Exception("Some error")
#
#     from lambda_docker.aws_deployment.src.deploy_to_ecr import create_ecr_repository
#     result = create_ecr_repository()
#
#     assert result is False
#     mock_error_logger.assert_called()
#     mock_logger.error.assert_called()


import pytest
from moto import mock_aws
import boto3
from src.deploy_to_ecr import create_ecr_repository, ECR_REPOSITORY_NAME



@mock_aws
def test_create_repository_when_not_exists():
    client = boto3.client("ecr", region_name="us-east-1")

    result = create_ecr_repository()

    assert result is True
    response = client.describe_repositories(repositoryNames=[ECR_REPOSITORY_NAME])
    assert response["repositories"][0]["repositoryName"] == ECR_REPOSITORY_NAME


@mock_aws
def test_fail_if_repository_exists():
    client = boto3.client("ecr", region_name="us-east-1")
    client.create_repository(repositoryName=ECR_REPOSITORY_NAME)

    result = create_ecr_repository(fail_if_exists=True)

    assert result is False


@mock_aws
def test_delete_and_create_repository_if_exists():
    client = boto3.client("ecr", region_name="us-east-1")
    client.create_repository(repositoryName=ECR_REPOSITORY_NAME)

    result = create_ecr_repository()

    assert result is True
    response = client.describe_repositories(repositoryNames=[ECR_REPOSITORY_NAME])
    assert response["repositories"][0]["repositoryName"] == ECR_REPOSITORY_NAME


@mock_aws
def test_handle_exception():
    with pytest.raises(Exception):
        client = boto3.client("ecr", region_name="us-east-1")
        client.create_repository(repositoryName=ECR_REPOSITORY_NAME)

        result = create_ecr_repository()
        assert result is False