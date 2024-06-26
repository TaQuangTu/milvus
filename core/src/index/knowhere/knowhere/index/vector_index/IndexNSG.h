// Copyright (C) 2019-2020 Zilliz. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
// with the License. You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the License
// is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
// or implied. See the License for the specific language governing permissions and limitations under the License

#pragma once

#include <memory>
#include <vector>

#include "knowhere/common/Exception.h"
#include "knowhere/common/Log.h"
#include "knowhere/index/vector_index/VecIndex.h"

namespace milvus {
namespace knowhere {

namespace impl {
class NsgIndex;
}

class NSG : public VecIndex {
 public:
    explicit NSG(const int64_t gpu_num = -1) : gpu_(gpu_num) {
        if (gpu_ >= 0) {
            index_mode_ = IndexMode::MODE_GPU;
        }
        index_type_ = IndexEnum::INDEX_NSG;
    }

    BinarySet
    Serialize(const Config& config = Config()) override;

    void
    Load(const BinarySet&) override;

    void
    BuildAll(const DatasetPtr&, const Config&) override;

    void
    Train(const DatasetPtr&, const Config&) override {
        KNOWHERE_THROW_MSG("NSG not support build item dynamically, please invoke BuildAll interface.");
    }

    void
    AddWithoutIds(const DatasetPtr&, const Config&) override {
        KNOWHERE_THROW_MSG("Incremental index NSG is not supported");
    }

    DatasetPtr
    Query(const DatasetPtr& dataset_ptr, const Config& config, faiss::ConcurrentBitsetPtr blacklist) override;

    int64_t
    Count() override;

    int64_t
    Dim() override;

    void
    UpdateIndexSize() override;

 private:
    int64_t gpu_;
    std::shared_ptr<impl::NsgIndex> index_;
};

using NSGIndexPtr = std::shared_ptr<NSG>();

}  // namespace knowhere
}  // namespace milvus
