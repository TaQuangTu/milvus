import time
import random
import pdb
import threading
import logging
from multiprocessing import Pool, Process
import pytest
from milvus import IndexType, MetricType
from utils import *
import ujson


dim = 128
index_file_size = 10
CONFIG_TIMEOUT = 80
nprobe = 1
top_k = 1
tag = "1970-01-01"
nb = 6000


class TestCacheConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def reset_configs(self, connect):
        '''
        reset configs so the tests are stable
        '''
        status, reply = connect.set_config("cache", "cache_size", '4GB')
        assert status.OK()
        status, config_value = connect.get_config("cache", "cache_size")
        assert config_value == '4GB'
        status, reply = connect.set_config("cache", "insert_buffer_size", '1GB')
        assert status.OK()
        status, config_value = connect.get_config("cache", "insert_buffer_size")
        assert config_value == '1GB'

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_cache_size_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: cache
        expected: status not ok
        '''
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Cache_config", "cache config", "cache_Config", "cacheconfig"])
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "cache_size")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_cache_size_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: cache_size
        expected: status not ok
        '''
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Cpu_cache_size", "cpu cache_size", "cpucachecapacity"])
        for config in invalid_configs:
            status, config_value = connect.get_config("cache", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_cache_size_valid(self, connect, collection):
        '''
        target: get cache_size
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("cache", "cache_size")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_insert_buffer_size_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: cache
        expected: status not ok
        '''
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Cache_config", "cache config", "cache_Config", "cacheconfig"])
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "insert_buffer_size")
            assert not status.OK()

    @pytest.mark.level(2)
    def test_get_insert_buffer_size_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: insert_buffer_size
        expected: status not ok
        '''
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Insert_buffer_size", "insert buffer_size", "insertbuffersize"])
        for config in invalid_configs:
            status, config_value = connect.get_config("cache", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_insert_buffer_size_valid(self, connect, collection):
        '''
        target: get insert_buffer_size
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("cache", "insert_buffer_size")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_preload_collection_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: preload_collection
        expected: status not ok
        '''
        invalid_configs = ["preloadtable", "preload_collection "]
        for config in invalid_configs:
            status, config_value = connect.get_config("cache", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_preload_collection_valid(self, connect, collection):
        '''
        target: get preload_collection
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("cache", "preload_collection")
        assert status.OK()

    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    def get_memory_available(self, connect):
        _, info = connect._cmd("get_system_info")
        mem_info = ujson.loads(info)
        mem_total = int(mem_info["memory_total"])
        mem_used = int(mem_info["memory_used"])
        logging.getLogger().info(mem_total)
        logging.getLogger().info(mem_used)
        mem_available = mem_total - mem_used
        return int(mem_available / 1024 / 1024 / 1024)

    def get_memory_total(self, connect):
        _, info = connect._cmd("get_system_info")
        mem_info = ujson.loads(info)
        mem_total = int(mem_info["memory_total"])
        return int(mem_total / 1024 / 1024 / 1024)

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_size_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: cache
        expected: status not ok
        '''
        self.reset_configs(connect)
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Cache_config", "cache config", "cache_Config", "cacheconfig"])
        for config in invalid_configs:
            status, reply = connect.set_config(config, "cache_size", '4GB')
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        self.reset_configs(connect)
        invalid_configs = gen_invalid_cache_config()
        for config in invalid_configs:
            status, reply = connect.set_config("cache", config, '4GB')
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_size_valid(self, connect, collection):
        '''
        target: set cache_size
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        self.reset_configs(connect)
        status, reply = connect.set_config("cache", "cache_size", '2GB')
        assert status.OK()
        status, config_value = connect.get_config("cache", "cache_size")
        assert status.OK()
        assert config_value == '2GB'

    @pytest.mark.level(2)
    def test_set_cache_size_valid_multiple_times(self, connect, collection):
        '''
        target: set cache_size
        method: call set_config correctly and repeatedly
        expected: status ok
        '''
        self.reset_configs(connect)
        for i in range(20):
            status, reply = connect.set_config("cache", "cache_size", '4GB')
            assert status.OK()
            status, config_value = connect.get_config("cache", "cache_size")
            assert status.OK()
            assert config_value == '4GB'
        for i in range(20):
            status, reply = connect.set_config("cache", "cache_size", '2GB')
            assert status.OK()
            status, config_value = connect.get_config("cache", "cache_size")
            assert status.OK()
            assert config_value == '2GB'

    @pytest.mark.level(2)
    def test_set_insert_buffer_size_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: cache
        expected: status not ok
        '''
        self.reset_configs(connect)
        invalid_configs = gen_invalid_cache_config()
        invalid_configs.extend(["Cache_config", "cache config", "cache_Config", "cacheconfig"])
        for config in invalid_configs:
            status, reply = connect.set_config(config, "insert_buffer_size", '1GB')
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_insert_buffer_size_valid(self, connect, collection):
        '''
        target: set insert_buffer_size
        method: call get_config correctly
        expected: status ok, set successfully
        '''
        self.reset_configs(connect)
        status, reply = connect.set_config("cache", "insert_buffer_size", '2GB')
        assert status.OK()
        status, config_value = connect.get_config("cache", "insert_buffer_size")
        assert status.OK()
        assert config_value == '2GB'

    @pytest.mark.level(2)
    def test_set_insert_buffer_size_valid_multiple_times(self, connect, collection):
        '''
        target: set insert_buffer_size
        method: call get_config correctly and repeatedly
        expected: status ok
        '''
        self.reset_configs(connect)
        for i in range(20):
            status, reply = connect.set_config("cache", "insert_buffer_size", '1GB')
            assert status.OK()
            status, config_value = connect.get_config("cache", "insert_buffer_size")
            assert status.OK()
            assert config_value == '1GB'
        for i in range(20):
            status, reply = connect.set_config("cache", "insert_buffer_size", '2GB')
            assert status.OK()
            status, config_value = connect.get_config("cache", "insert_buffer_size")
            assert status.OK()
            assert config_value == '2GB'

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_out_of_memory_value_A(self, connect, collection):
        '''
        target: set cache_size / insert_buffer_size to be out-of-memory
        method: call set_config with child values bigger than current system memory
        expected: status not ok (cache_size + insert_buffer_size < system memory)
        '''
        self.reset_configs(connect)
        mem_total = self.get_memory_total(connect)
        logging.getLogger().info(mem_total)
        status, reply = connect.set_config("cache", "cache_size", str(int(mem_total + 1))+'GB')
        assert not status.OK()
        status, reply = connect.set_config("cache", "insert_buffer_size", str(int(mem_total + 1))+'GB')
        assert not status.OK()

    def test_set_preload_collection_valid(self, connect, collection):
        '''
        target: set preload_collection
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("cache", "preload_collection", "")
        assert status.OK()
        status, config_value = connect.get_config("cache", "preload_collection")
        assert status.OK()
        assert config_value == ""


class TestGPUConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.level(2)
    def test_get_gpu_search_threshold_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Engine_config", "engine config"]
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "gpu_search_threshold")
            assert not status.OK()

    @pytest.mark.level(2)
    def test_get_gpu_search_threshold_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: gpu_search_threshold
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_search_threshold", "gpusearchthreshold"]
        for config in invalid_configs:
            status, config_value = connect.get_config("gpu", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_gpu_search_threshold_valid(self, connect, collection):
        '''
        target: get gpu_search_threshold
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "gpu_search_threshold")
        assert status.OK()

    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        invalid_configs = gen_invalid_gpu_config()
        for config in invalid_configs:
            status, reply = connect.set_config("gpu", config, 1000)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_search_threshold_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = gen_invalid_gpu_config()
        invalid_configs.extend(["Engine_config", "engine config"])
        for config in invalid_configs:
            status, reply = connect.set_config(config, "gpu_search_threshold", 1000)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_search_threshold_valid(self, connect, collection):
        '''
        target: set gpu_search_threshold
        method: call set_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, reply = connect.set_config("gpu", "gpu_search_threshold", 2000)
        assert status.OK()
        status, config_value = connect.get_config("gpu", "gpu_search_threshold")
        assert status.OK()
        assert config_value == '2000'

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_invalid_values(self, connect, collection):
        '''
        target: set gpu
        method: call set_config with invalid child values
        expected: status not ok
        '''
        for i in [-1, "1000\n", "1000\t", "1000.0", 1000.35]:
            status, reply = connect.set_config("gpu", "use_blas_threshold", i)
            assert not status.OK()
            if str(connect._cmd("mode")[1]) == "GPU":
                status, reply = connect.set_config("gpu", "gpu_search_threshold", i)
                assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def reset_configs(self, connect):
        '''
        reset configs so the tests are stable
        '''
        status, reply = connect.set_config("gpu", "enable", "true")
        assert status.OK()
        status, config_value = connect.get_config("gpu", "enable")
        assert config_value == "true"
        status, reply = connect.set_config("gpu", "cache_size", 1)
        assert status.OK()
        status, config_value = connect.get_config("gpu", "cache_size")
        assert config_value == '1'
        status, reply = connect.set_config("gpu", "search_devices", "gpu0")
        assert status.OK()
        status, config_value = connect.get_config("gpu", "search_devices")
        assert config_value == 'gpu0'
        status, reply = connect.set_config("gpu", "build_index_devices", "gpu0")
        assert status.OK()
        status, config_value = connect.get_config("gpu", "build_index_devices")
        assert config_value == 'gpu0'

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_gpu_enable_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "enable")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_gpu_enable_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: enable
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Enable", "enable ", "disable", "true"]
        for config in invalid_configs:
            status, config_value = connect.get_config("gpu", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_gpu_enable_valid(self, connect, collection):
        '''
        target: get enable status
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "enable")
        assert status.OK()
        assert config_value == "true" or config_value == "false"

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_gpu_cache_enable_valid(self, connect, collection):
        '''
        target: get gpu_cache
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "cache.enable")
        assert status.OK()
        assert config_value == "true" or config_value == "false"

    @pytest.mark.level(2)
    def test_get_cache_size_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "cache_size")
            assert not status.OK()

    @pytest.mark.level(2)
    def test_get_cache_size_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: cache_size
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Cache_capacity", "cachecapacity"]
        for config in invalid_configs:
            status, config_value = connect.get_config("gpu", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_cache_size_valid(self, connect, collection):
        '''
        target: get cache_size
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "cache_size")
        assert status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_search_devices_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "search_devices")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_search_devices_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: search_devices
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Search_resources"]
        for config in invalid_configs:
            status, config_value = connect.get_config("gpu", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_search_devices_valid(self, connect, collection):
        '''
        target: get search_devices
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "search_devices")
        logging.getLogger().info(config_value)
        assert status.OK()
    
    @pytest.mark.level(2)
    def test_get_build_index_devices_invalid_parent_key(self, connect, collection):
        '''
        target: get invalid parent key
        method: call get_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, config_value = connect.get_config(config, "build_index_devices")
            assert not status.OK()

    @pytest.mark.level(2)
    def test_get_build_index_devices_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: build_index_devices
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Build_index_resources"]
        for config in invalid_configs:
            status, config_value = connect.get_config("gpu", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_build_index_devices_valid(self, connect, collection):
        '''
        target: get build_index_devices
        method: call get_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, config_value = connect.get_config("gpu", "build_index_devices")
        logging.getLogger().info(config_value)
        assert status.OK()

    
    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_enable_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, reply = connect.set_config(config, "enable", "true")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, reply = connect.set_config("gpu", config, "true")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_enable_invalid_values(self, connect, collection):
        '''
        target: set "enable" param
        method: call set_config with invalid child values
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        for i in [-1, -2, 100]:
            status, reply = connect.set_config("gpu", "enable", i)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_gpu_enable_valid(self, connect, collection):
        '''
        target: set "enable" param
        method: call set_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        valid_configs = ["off", "False", "0", "nO", "on", "True", 1, "yES"]
        for config in valid_configs:
            status, reply = connect.set_config("gpu", "enable", config)
            assert status.OK()
            status, config_value = connect.get_config("gpu", "enable")
            assert status.OK()
            assert config_value == str(config)

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_size_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, reply = connect.set_config(config, "cache_size", 2)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_size_valid(self, connect, collection):
        '''
        target: set cache_size
        method: call set_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, reply = connect.set_config("gpu", "cache_size", 2)
        assert status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_cache_size_invalid_values(self, connect, collection):
        '''
        target: set cache_size
        method: call set_config with invalid child values
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        self.reset_configs(connect)
        for i in [-1, "1\n", "1\t"]:
            logging.getLogger().info(i)
            status, reply = connect.set_config("gpu", "cache_size", i)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_search_devices_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, reply = connect.set_config(config, "search_devices", "gpu0")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_search_devices_valid(self, connect, collection):
        '''
        target: set search_devices
        method: call set_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, reply = connect.set_config("gpu", "search_devices", "gpu0")
        assert status.OK()
        status, config_value = connect.get_config("gpu", "search_devices")
        assert config_value == "gpu0"

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_search_devices_invalid_values(self, connect, collection):
        '''
        target: set search_devices
        method: call set_config with invalid child values
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        for i in [-1, "10", "gpu-1", "gpu0, gpu1", "gpu22,gpu44","gpu10000","gpu 0","-gpu0"]:
            status, reply = connect.set_config("gpu", "search_devices", i)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_build_index_devices_invalid_parent_key(self, connect, collection):
        '''
        target: set invalid parent key
        method: call set_config without parent_key: gpu
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        invalid_configs = ["Gpu_resource_config", "gpu resource config", \
            "gpu_resource"]
        for config in invalid_configs:
            status, reply = connect.set_config(config, "build_index_devices", "gpu0")
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_build_index_devices_valid(self, connect, collection):
        '''
        target: set build_index_devices
        method: call set_config correctly
        expected: status ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        status, reply = connect.set_config("gpu", "build_index_devices", "gpu0")
        assert status.OK()
        status, config_value = connect.get_config("gpu", "build_index_devices")
        assert config_value == "gpu0"

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_build_index_devices_invalid_values(self, connect, collection):
        '''
        target: set build_index_devices
        method: call set_config with invalid child values
        expected: status not ok
        '''
        if str(connect._cmd("mode")[1]) == "CPU":
            pytest.skip("Only support GPU mode")
        for i in [-1, "10", "gpu-1", "gpu0, gpu1", "gpu22,gpu44","gpu10000","gpu 0","-gpu0"]:
            status, reply = connect.set_config("gpu", "build_index_devices", i)
            assert not status.OK()
        self.reset_configs(connect)


class TestNetworkConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_address_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: address
        expected: status not ok
        '''
        invalid_configs = ["Address", "addresses", "address "]
        for config in invalid_configs:
            status, config_value = connect.get_config("network", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_address_valid(self, connect, collection):
        '''
        target: get address
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("network", "bind.address")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_port_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: port
        expected: status not ok
        '''
        invalid_configs = ["Port", "PORT", "port "]
        for config in invalid_configs:
            status, config_value = connect.get_config("network", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_port_valid(self, connect, collection):
        '''
        target: get port
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("network", "http.port")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_http_port_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: http.port
        expected: status not ok
        '''
        invalid_configs = ["webport", "Web_port", "http.port "]
        for config in invalid_configs:
            status, config_value = connect.get_config("network", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_http_port_valid(self, connect, collection):
        '''
        target: get http.port
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("network", "http.port")
        assert status.OK()


    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    def gen_valid_timezones(self):
        timezones = []
        for i in range(0, 13):
            timezones.append("UTC+" + str(i))
            timezones.append("UTC-" + str(i))
        timezones.extend(["UTC+13", "UTC+14"])
        return timezones

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_network_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        status, reply = connect.set_config("network", "child_key", 19530)
        assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_address_valid(self, connect, collection):
        '''
        target: set address
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("network", "bind.address", '0.0.0.0')
        assert status.OK()
        status, config_value = connect.get_config("network", "bind.address")
        assert status.OK()
        assert config_value == '0.0.0.0'

    def test_set_port_valid(self, connect, collection):
        '''
        target: set port
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_port in [1025, 65534, 12345, "19530"]:
            status, reply = connect.set_config("network", "http.port", valid_port)
            assert status.OK()
            status, config_value = connect.get_config("network", "http.port")
            assert status.OK()
            assert config_value == str(valid_port)
    
    def test_set_port_invalid(self, connect, collection):
        '''
        target: set port
        method: call set_config with port number out of range(1024, 65535)
        expected: status not ok
        '''
        for invalid_port in [1024, 65535, "0", "True", "19530 ", "100000"]:
            logging.getLogger().info(invalid_port)
            status, reply = connect.set_config("network", "http.port", invalid_port)
            assert not status.OK()

    def test_set_http_port_valid(self, connect, collection):
        '''
        target: set http.port
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_http_port in [1025, 65534, "12345", 19121]:
            status, reply = connect.set_config("network", "http.port", valid_http_port)
            assert status.OK()
            status, config_value = connect.get_config("network", "http.port")
            assert status.OK()
            assert config_value == str(valid_http_port)
    
    def test_set_http_port_invalid(self, connect, collection):
        '''
        target: set http.port
        method: call set_config with http.port number out of range(1024, 65535)
        expected: status not ok
        '''
        for invalid_http_port in [1024, 65535, "0", "True", "19530 ", "1000000"]:
            status, reply = connect.set_config("network", "http.port", invalid_http_port)
            assert not status.OK()


class TestGeneralConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_meta_uri_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: meta_uri
        expected: status not ok
        '''
        invalid_configs = ["backend_Url", "backend-url", "meta_uri "]
        for config in invalid_configs:
            status, config_value = connect.get_config("general", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_meta_uri_valid(self, connect, collection):
        '''
        target: get meta_uri
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("general", "meta_uri")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_timezone_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: timezone
        expected: status not ok
        '''
        invalid_configs = ["time", "timezone "]
        for config in invalid_configs:
            status, config_value = connect.get_config("general", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_timezone_valid(self, connect, collection):
        '''
        target: get timezone
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("general", "timezone")
        assert status.OK()
        assert "UTC" in config_value

    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    def test_set_timezone_invalid(self, connect, collection):
        '''
        target: set timezone
        method: call set_config with invalid timezone
        expected: status not ok
        '''
        for invalid_timezone in ["utc+8", "UTC++8", "GMT+8"]:
            logging.getLogger().info(invalid_timezone)
            status, reply = connect.set_config("general", "timezone", invalid_timezone)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_general_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        status, reply = connect.set_config("general", "child_key", 1)
        assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_meta_uri_valid(self, connect, collection):
        '''
        target: set meta_uri
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("general", "meta_uri", 'sqlite://:@:/')
        assert status.OK()
        status, config_value = connect.get_config("general", "meta_uri")
        assert status.OK()
        assert config_value == 'sqlite://:@:/'


class TestStorageConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_path_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: path
        expected: status not ok
        '''
        invalid_configs = ["Primary_path", "primarypath", "path "]
        for config in invalid_configs:
            status, config_value = connect.get_config("storage", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_path_valid(self, connect, collection):
        '''
        target: get path
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("storage", "path")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_auto_flush_interval_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: auto_flush_interval
        expected: status not ok
        '''
        invalid_configs = ["autoFlushInterval", "auto_flush", "auto_flush_interval "]
        for config in invalid_configs:
            status, config_value = connect.get_config("storage", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_auto_flush_interval_valid(self, connect, collection):
        '''
        target: get auto_flush_interval
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("storage", "auto_flush_interval")
        assert status.OK()

    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_storage_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        status, reply = connect.set_config("storage", "child_key", "")
        assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_path_valid(self, connect, collection):
        '''
        target: set path
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("storage", "path", '/var/lib/milvus')
        assert status.OK()
        status, config_value = connect.get_config("storage", "path")
        assert status.OK()
        assert config_value == '/var/lib/milvus'

    def test_set_auto_flush_interval_valid(self, connect, collection):
        '''
        target: set auto_flush_interval
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_auto_flush_interval in [2, 1]:
            logging.getLogger().info(valid_auto_flush_interval)
            status, reply = connect.set_config("storage", "auto_flush_interval", valid_auto_flush_interval)
            assert status.OK()
            status, config_value = connect.get_config("storage", "auto_flush_interval")
            assert status.OK()
            assert config_value == str(valid_auto_flush_interval)

    def test_set_auto_flush_interval_invalid(self, connect, collection):
        '''
        target: set auto_flush_interval
        method: call set_config with invalid auto_flush_interval
        expected: status not ok
        '''
        for invalid_auto_flush_interval in [-1, "1.5", "invalid", "1+2"]:
            status, reply = connect.set_config("storage", "auto_flush_interval", invalid_auto_flush_interval)
            assert not status.OK()


class TestMetricConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_enable_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: enable
        expected: status not ok
        '''
        invalid_configs = ["enablemonitor", "Enable_monitor", "enable "]
        for config in invalid_configs:
            status, config_value = connect.get_config("metric", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_enable_valid(self, connect, collection):
        '''
        target: get enable
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("metric", "enable")
        assert status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_address_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: address
        expected: status not ok
        '''
        invalid_configs = ["Address", "addresses", "address "]
        for config in invalid_configs:
            status, config_value = connect.get_config("metric", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_address_valid(self, connect, collection):
        '''
        target: get address
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("metric", "address")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_port_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: port
        expected: status not ok
        '''
        invalid_configs = ["Port", "PORT", "port "]
        for config in invalid_configs:
            status, config_value = connect.get_config("metric", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_port_valid(self, connect, collection):
        '''
        target: get port
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("metric", "port")
        assert status.OK()


    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_metric_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        status, reply = connect.set_config("metric", "child_key", 19530)
        assert not status.OK()

    def test_set_enable_valid(self, connect, collection):
        '''
        target: set enable
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_enable in ["Off", "false", 0, "yes", "On", "true", "1", "NO"]:
            status, reply = connect.set_config("metric", "enable", valid_enable)
            assert status.OK()
            status, config_value = connect.get_config("metric", "enable")
            assert status.OK()
            assert config_value == str(valid_enable)

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_address_valid(self, connect, collection):
        '''
        target: set address
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("metric", "address", '127.0.0.1')
        assert status.OK()
        status, config_value = connect.get_config("metric", "address")
        assert status.OK()
        assert config_value == '127.0.0.1'

    def test_set_port_valid(self, connect, collection):
        '''
        target: set port
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_port in [1025, 65534, "19530", "9091"]:
            status, reply = connect.set_config("metric", "port", valid_port)
            assert status.OK()
            status, config_value = connect.get_config("metric", "port")
            assert status.OK()
            assert config_value == str(valid_port)
    
    def test_set_port_invalid(self, connect, collection):
        '''
        target: set port
        method: call set_config with port number out of range(1024, 65535), or same as http.port number
        expected: status not ok
        '''
        for invalid_port in [1024, 65535, "0", "True", "19530 ", "100000"]:
            status, reply = connect.set_config("metric", "port", invalid_port)
            assert not status.OK()


# class TestTracingConfig:
#     """
#     ******************************************************************
#       The following cases are used to test `get_config` function
#     ******************************************************************
#     """
#     @pytest.fixture(scope="function", autouse=True)
#     def skip_http_check(self, args):
#         if args["handler"] == "HTTP":
#             pytest.skip("skip in http mode")
# 
#     @pytest.mark.timeout(CONFIG_TIMEOUT)
#     def test_get_json_config_path_invalid_child_key(self, connect, collection):
#         '''
#         target: get invalid child key
#         method: call get_config without child_key: json_config_path
#         expected: status not ok
#         '''
#         invalid_configs = ["json_config", "jsonconfigpath", "json_config_path "]
#         for config in invalid_configs:
#             status, config_value = connect.get_config("tracing_config", config)
#             assert not status.OK()
# 
#     @pytest.mark.timeout(CONFIG_TIMEOUT)
#     def test_get_json_config_path_valid(self, connect, collection):
#         '''
#         target: get json_config_path
#         method: call get_config correctly
#         expected: status ok
#         '''
#         status, config_value = connect.get_config("tracing_config", "json_config_path")
#         assert status.OK()
# 
# 
#     """
#     ******************************************************************
#       The following cases are used to test `set_config` function
#     ******************************************************************
#     """
#     @pytest.mark.timeout(CONFIG_TIMEOUT)
#     def test_set_tracing_config_invalid_child_key(self, connect, collection):
#         '''
#         target: set invalid child key
#         method: call set_config with invalid child_key
#         expected: status not ok
#         '''
#         status, reply = connect.set_config("tracing_config", "child_key", "")
#         assert not status.OK()
# 
#     @pytest.mark.skip(reason="Currently not supported")
#     def test_set_json_config_path_valid(self, connect, collection):
#         '''
#         target: set json_config_path
#         method: call set_config correctly
#         expected: status ok, set successfully
#         '''
#         status, reply = connect.set_config("tracing_config", "json_config_path", "")
#         assert status.OK()
#         status, config_value = connect.get_config("tracing_config", "json_config_path")
#         assert status.OK()
#         assert config_value == ""


class TestWALConfig:
    """
    ******************************************************************
      The following cases are used to test `get_config` function
    ******************************************************************
    """
    @pytest.fixture(scope="function", autouse=True)
    def skip_http_check(self, args):
        if args["handler"] == "HTTP":
            pytest.skip("skip in http mode")

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_enable_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: enable
        expected: status not ok
        '''
        invalid_configs = ["enabled", "Enable", "enable "]
        for config in invalid_configs:
            status, config_value = connect.get_config("wal", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_enable_valid(self, connect, collection):
        '''
        target: get enable
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("wal", "enable")
        assert status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_recovery_error_ignore_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: recovery_error_ignore
        expected: status not ok
        '''
        invalid_configs = ["recovery-error-ignore", "Recovery_error_ignore", "recovery_error_ignore "]
        for config in invalid_configs:
            status, config_value = connect.get_config("wal", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_recovery_error_ignore_valid(self, connect, collection):
        '''
        target: get recovery_error_ignore
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("wal", "recovery_error_ignore")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_buffer_size_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: buffer_size
        expected: status not ok
        '''
        invalid_configs = ["buffersize", "Buffer_size", "buffer_size "]
        for config in invalid_configs:
            status, config_value = connect.get_config("wal", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_buffer_size_valid(self, connect, collection):
        '''
        target: get buffer_size
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("wal", "buffer_size")
        assert status.OK()

    @pytest.mark.level(2)
    def test_get_wal_path_invalid_child_key(self, connect, collection):
        '''
        target: get invalid child key
        method: call get_config without child_key: wal_path
        expected: status not ok
        '''
        invalid_configs = ["wal", "Wal_path", "wal_path "]
        for config in invalid_configs:
            status, config_value = connect.get_config("wal", config)
            assert not status.OK()

    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_get_wal_path_valid(self, connect, collection):
        '''
        target: get wal_path
        method: call get_config correctly
        expected: status ok
        '''
        status, config_value = connect.get_config("wal", "path")
        assert status.OK()


    """
    ******************************************************************
      The following cases are used to test `set_config` function
    ******************************************************************
    """
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_wal_invalid_child_key(self, connect, collection):
        '''
        target: set invalid child key
        method: call set_config with invalid child_key
        expected: status not ok
        '''
        status, reply = connect.set_config("wal", "child_key", 256)
        assert not status.OK()

    def test_set_enable_valid(self, connect, collection):
        '''
        target: set enable
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_enable in ["Off", "false", 0, "no", "On", "true", "1", "YES"]:
            status, reply = connect.set_config("wal", "enable", valid_enable)
            assert status.OK()
            status, config_value = connect.get_config("wal", "enable")
            assert status.OK()
            assert config_value == str(valid_enable)

    def test_set_recovery_error_ignore_valid(self, connect, collection):
        '''
        target: set recovery_error_ignore
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_recovery_error_ignore in ["Off", "false", "0", "no", "On", "true", "1", "YES"]:
            status, reply = connect.set_config("wal", "recovery_error_ignore", valid_recovery_error_ignore)
            assert status.OK()
            status, config_value = connect.get_config("wal", "recovery_error_ignore")
            assert status.OK()
            assert config_value == valid_recovery_error_ignore

    def test_set_buffer_size_valid_A(self, connect, collection):
        '''
        target: set buffer_size
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        for valid_buffer_size in ["64MB", "128MB", "4096MB", "1000MB", "256MB"]:
            status, reply = connect.set_config("wal", "buffer_size", valid_buffer_size)
            assert status.OK()
            status, config_value = connect.get_config("wal", "buffer_size")
            assert status.OK()
            assert config_value == str(valid_buffer_size)
        
    @pytest.mark.timeout(CONFIG_TIMEOUT)
    def test_set_wal_path_valid(self, connect, collection, args):
        '''
        target: set wal_path
        method: call set_config correctly
        expected: status ok, set successfully
        '''
        status, reply = connect.set_config("wal", "path", "/var/lib/milvus/wal")
        assert status.OK()
        status, config_value = connect.get_config("wal", "path")
        assert status.OK()
        assert config_value == "/var/lib/milvus/wal"
