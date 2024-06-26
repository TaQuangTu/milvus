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

#include "db/engine/EngineFactory.h"
#include "db/engine/ExecutionEngineImpl.h"
#include "utils/Log.h"

#include <memory>

namespace milvus {
namespace engine {

ExecutionEnginePtr
EngineFactory::Build(uint16_t dimension, const std::string& location, EngineType index_type, MetricType metric_type,
                     const milvus::json& index_params, int64_t time_stamp) {
    if (index_type == EngineType::INVALID) {
        LOG_ENGINE_ERROR_ << "Unsupported engine type";
        return nullptr;
    }

    LOG_ENGINE_DEBUG_ << "EngineFactory index type: " << (int)index_type;
    ExecutionEnginePtr execution_engine_ptr =
        std::make_shared<ExecutionEngineImpl>(dimension, location, index_type, metric_type, index_params, time_stamp);

    execution_engine_ptr->Init();
    return execution_engine_ptr;
}

}  // namespace engine
}  // namespace milvus
