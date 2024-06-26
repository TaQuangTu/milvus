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

#include <faiss/utils/ConcurrentBitset.h>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

#include "knowhere/common/Dataset.h"
#include "knowhere/common/Exception.h"
#include "knowhere/common/Typedef.h"
#include "knowhere/index/Index.h"
#include "knowhere/index/vector_index/IndexType.h"

namespace milvus {
namespace knowhere {

class VecIndex : public Index {
 public:
    virtual void
    BuildAll(const DatasetPtr& dataset_ptr, const Config& config) {
        Train(dataset_ptr, config);
        AddWithoutIds(dataset_ptr, config);
    }

    virtual void
    Train(const DatasetPtr& dataset, const Config& config) = 0;

    virtual void
    AddWithoutIds(const DatasetPtr& dataset, const Config& config) = 0;

    virtual DatasetPtr
    Query(const DatasetPtr& dataset_ptr, const Config& config, faiss::ConcurrentBitsetPtr blacklist) = 0;

    virtual int64_t
    Dim() = 0;

    virtual int64_t
    Count() = 0;

    virtual IndexType
    index_type() const {
        return index_type_;
    }

    virtual IndexMode
    index_mode() const {
        return index_mode_;
    }

    std::shared_ptr<std::vector<IDType>>
    GetUids() const {
        return uids_;
    }

    void
    SetUids(std::shared_ptr<std::vector<IDType>> uids) {
        uids_ = uids;
    }

    void
    MapOffsetToUid(IDType* id, size_t n) {
        if (uids_) {
            for (size_t i = 0; i < n; i++) {
                if (id[i] >= 0) {
                    id[i] = uids_->at(id[i]);
                }
            }
        }
    }

    size_t
    UidsSize() {
        return (uids_ == nullptr) ? 0 : (uids_->size() * sizeof(IDType));
    }

    virtual int64_t
    IndexSize() {
        if (index_size_ == -1) {
            KNOWHERE_THROW_MSG("Index size not set");
        }
        return index_size_;
    }

    void
    SetIndexSize(int64_t size) {
        index_size_ = size;
    }

    virtual void
    UpdateIndexSize() {
    }

    int64_t
    Size() override {
        return UidsSize() + IndexSize();
    }

 protected:
    IndexType index_type_ = "";
    IndexMode index_mode_ = IndexMode::MODE_CPU;
    std::shared_ptr<std::vector<IDType>> uids_ = nullptr;
    int64_t index_size_ = -1;
};

using VecIndexPtr = std::shared_ptr<VecIndex>;

}  // namespace knowhere
}  // namespace milvus
