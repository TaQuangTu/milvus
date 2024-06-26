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

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>

#include "cache/CacheMgr.h"
#include "cache/DataObj.h"
#include "config/handler/GpuResourceConfigHandler.h"

namespace milvus {
namespace cache {

#ifdef MILVUS_GPU_VERSION

// Define cache key suffix
extern const char* Quantizer_Suffix;

class GpuCacheMgr;
using GpuCacheMgrPtr = std::shared_ptr<GpuCacheMgr>;
using MutexPtr = std::shared_ptr<std::mutex>;

class GpuCacheMgr : public CacheMgr<DataObjPtr>, public server::GpuResourceConfigHandler {
 public:
    explicit GpuCacheMgr(int64_t gpu_id);

    ~GpuCacheMgr();

    void
    InsertItem(const std::string& key, const DataObjPtr& data);

    bool
    Reserve(const int64_t size);

    static GpuCacheMgrPtr
    GetInstance(int64_t gpu_id);

 protected:
    void
    OnGpuCacheCapacityChanged(int64_t capacity) override;

 private:
    bool gpu_enable_ = true;
    int64_t gpu_id_;
    static std::mutex global_mutex_;
    static std::unordered_map<int64_t, GpuCacheMgrPtr> instance_;
    std::string identity_;
};
#endif

}  // namespace cache
}  // namespace milvus
