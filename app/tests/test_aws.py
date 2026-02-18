import unittest
from unittest.mock import MagicMock, patch
from app.services import aws

class TestAWSRemediation(unittest.TestCase):

    @patch('app.services.aws.get_ec2_client')
    def test_delete_volumes_success(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        
        vids = ["vol-1", "vol-2"]
        success, failed = aws.delete_volumes(vids)
        
        self.assertEqual(len(success), 2)
        self.assertEqual(len(failed), 0)
        self.assertEqual(mock_client.delete_volume.call_count, 2)

    @patch('app.services.aws.get_ec2_client')
    def test_delete_volumes_partial_failure(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.delete_volume.side_effect = [None, Exception("Access Denied")]
        mock_client_factory.return_value = mock_client
        
        vids = ["vol-1", "vol-2"]
        success, failed = aws.delete_volumes(vids)
        
        self.assertEqual(len(success), 1)
        self.assertEqual(len(failed), 1)
        self.assertIn("Access Denied", failed[0])

    @patch('app.services.aws.get_s3_client')
    def test_delete_s3_buckets(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        
        buckets = ["bucket-1"]
        success, failed = aws.delete_s3_buckets(buckets)
        
        self.assertEqual(success, ["bucket-1"])
        mock_client.delete_bucket.assert_called_with(Bucket="bucket-1")

    @patch('app.services.aws.get_iam_client')
    def test_delete_iam_users(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        
        users = ["user-1"]
        success, failed = aws.delete_iam_users(users)
        
        self.assertEqual(success, ["user-1"])
        mock_client.delete_user.assert_called_with(UserName="user-1")

if __name__ == '__main__':
    unittest.main()
