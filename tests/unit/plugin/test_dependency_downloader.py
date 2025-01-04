"""依赖下载器测试"""
import pytest
from unittest.mock import patch, MagicMock
from plugin_manager.features.dependencies.dependency_downloader import DependencyDownloader

@pytest.fixture
def dependency_downloader():
    return DependencyDownloader()

class TestDependencyDownloader:
    @patch('pip.main')
    def test_download_package(self, mock_pip, dependency_downloader):
        """测试包下载"""
        mock_pip.return_value = 0
        result = dependency_downloader.download("test-package==1.0.0")
        assert result is True
        mock_pip.assert_called_once()

    def test_validate_package_spec(self, dependency_downloader):
        """测试包规格验证"""
        valid_specs = [
            "package==1.0.0",
            "package>=1.0.0",
            "package~=1.0.0"
        ]
        for spec in valid_specs:
            assert dependency_downloader.validate_spec(spec)

    def test_cleanup_downloaded(self, dependency_downloader):
        """测试清理下载"""
        with patch('os.remove') as mock_remove:
            dependency_downloader.cleanup("test-package")
            mock_remove.assert_called() 