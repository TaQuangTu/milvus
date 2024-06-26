// Copyright (C) 2019-2020 Zilliz. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
// with the License. You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the License
// is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
// or implied. See the License for the specific language governing permissions and limitations under the License.

#include "cache/GpuCacheMgr.h"
#include "config/Config.h"
#include "utils/Log.h"

#include <fiu-local.h>
#include <sstream>
#include <utility>

namespace milvus {
namespace cache {

#ifdef MILVUS_GPU_VERSION
const char* Quantizer_Suffix = ".quantizer";

std::mutex GpuCacheMgr::global_mutex_;
std::unordered_map<int64_t, GpuCacheMgrPtr> GpuCacheMgr::instance_;

GpuCacheMgr::GpuCacheMgr(int64_t gpu_id) : gpu_id_(gpu_id) {
    // All config values have been checked in Config::ValidateConfig()
    server::Config& config = server::Config::GetInstance();

    int64_t gpu_cache_cap;
    config.GetGpuResourceConfigCacheCapacity(gpu_cache_cap);
    int64_t cap = gpu_cache_cap;
    std::string header = "[CACHE GPU" + std::to_string(gpu_id) + "]";
    cache_ = std::make_shared<Cache<DataObjPtr>>(cap, 1UL << 32, header);

    float gpu_mem_threshold;
    config.GetGpuResourceConfigCacheThreshold(gpu_mem_threshold);
    cache_->set_freemem_percent(gpu_mem_threshold);

    SetIdentity("GpuCacheMgr");
    AddGpuEnableListener();
    AddGpuCacheCapacityListener();
}

GpuCacheMgr::~GpuCacheMgr() {
    server::Config& config = server::Config::GetInstance();
    config.CancelCallBack(server::CONFIG_GPU_RESOURCE, server::CONFIG_GPU_RESOURCE_ENABLE, identity_);
}

void
GpuCacheMgr::InsertItem(const std::string& key, const milvus::cache::DataObjPtr& data) {
    if (gpu_enable_) {
        CacheMgr<DataObjPtr>::InsertItem(key, data);
    }
}

bool
GpuCacheMgr::Reserve(const int64_t size) {
    return CacheMgr<DataObjPtr>::Reserve(size);
}

GpuCacheMgrPtr
GpuCacheMgr::GetInstance(int64_t gpu_id) {
    if (instance_.find(gpu_id) == instance_.end()) {
        std::lock_guard<std::mutex> lock(global_mutex_);
        if (instance_.find(gpu_id) == instance_.end()) {
            instance_[gpu_id] = std::make_shared<GpuCacheMgr>(gpu_id);
        }
    }
    return instance_[gpu_id];
}

void
GpuCacheMgr::OnGpuCacheCapacityChanged(int64_t capacity) {
    for (auto& iter : instance_) {
        iter.second->SetCapacity(capacity);
    }
}

#endif

}  // namespace cache
}  // namespace milvus
