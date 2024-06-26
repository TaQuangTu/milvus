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

#include "grpc/ClientProxy.h"

#include <memory>
#include <string>
#include <vector>

#include "grpc-gen/gen-milvus/milvus.grpc.pb.h"

#define MILVUS_SDK_VERSION "1.1.0";

namespace milvus {

static const char* EXTRA_PARAM_KEY = "params";

bool
UriCheck(const std::string& uri) {
    size_t index = uri.find_first_of(':', 0);
    return (index != std::string::npos);
}

template <typename T>
void
ConstructSearchParam(const std::string& collection_name, const std::vector<std::string>& partition_tag_array,
                     int64_t topk, const std::string& extra_params, T& search_param) {
    search_param.set_collection_name(collection_name);
    search_param.set_topk(topk);
    milvus::grpc::KeyValuePair* kv = search_param.add_extra_params();
    kv->set_key(EXTRA_PARAM_KEY);
    kv->set_value(extra_params);

    for (auto& tag : partition_tag_array) {
        search_param.add_partition_tag_array(tag);
    }
}

void
CopyRowRecord(::milvus::grpc::RowRecord* target, const Entity& src) {
    if (!src.float_data.empty()) {
        auto vector_data = target->mutable_float_data();
        vector_data->Resize(static_cast<int>(src.float_data.size()), 0.0);
        memcpy(vector_data->mutable_data(), src.float_data.data(), src.float_data.size() * sizeof(float));
    }

    if (!src.binary_data.empty()) {
        target->set_binary_data(src.binary_data.data(), src.binary_data.size());
    }
}

void
ConstructTopkResult(const ::milvus::grpc::TopKQueryResult& grpc_result, TopKQueryResult& topk_query_result) {
    topk_query_result.reserve(grpc_result.row_num());
    int64_t nq = grpc_result.row_num();
    int64_t topk = grpc_result.ids().size() / nq;
    for (int64_t i = 0; i < nq; i++) {
        milvus::QueryResult one_result;
        one_result.ids.resize(topk);
        one_result.distances.resize(topk);
        memcpy(one_result.ids.data(), grpc_result.ids().data() + topk * i, topk * sizeof(int64_t));
        memcpy(one_result.distances.data(), grpc_result.distances().data() + topk * i, topk * sizeof(float));

        int valid_size = one_result.ids.size();
        while (valid_size > 0 && one_result.ids[valid_size - 1] == -1) {
            valid_size--;
        }
        if (valid_size != topk) {
            one_result.ids.resize(valid_size);
            one_result.distances.resize(valid_size);
        }

        topk_query_result.emplace_back(one_result);
    }
}

Status
ClientProxy::Connect(const ConnectParam& param) {
    std::string uri = param.ip_address + ":" + param.port;

    ::grpc::ChannelArguments args;
    args.SetMaxSendMessageSize(-1);
    args.SetMaxReceiveMessageSize(-1);
    channel_ = ::grpc::CreateCustomChannel(uri, ::grpc::InsecureChannelCredentials(), args);
    if (channel_ != nullptr) {
        connected_ = true;
        client_ptr_ = std::make_shared<GrpcClient>(channel_);
        return Status::OK();
    }

    std::string reason = "Connect failed!";
    connected_ = false;
    return Status(StatusCode::NotConnected, reason);
}

Status
ClientProxy::Connect(const std::string& uri) {
    if (!UriCheck(uri)) {
        return Status(StatusCode::InvalidAgument, "Invalid uri");
    }
    size_t index = uri.find_first_of(':', 0);

    ConnectParam param;
    param.ip_address = uri.substr(0, index);
    param.port = uri.substr(index + 1);

    return Connect(param);
}

Status
ClientProxy::Connected() const {
    try {
        std::string info;
        return client_ptr_->Cmd("", info);
    } catch (std::exception& ex) {
        return Status(StatusCode::NotConnected, "Connection lost: " + std::string(ex.what()));
    }
}

Status
ClientProxy::Disconnect() {
    try {
        Status status = client_ptr_->Disconnect();
        connected_ = false;
        channel_.reset();
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to disconnect: " + std::string(ex.what()));
    }
}

std::string
ClientProxy::ClientVersion() const {
    return MILVUS_SDK_VERSION;
}

std::string
ClientProxy::ServerVersion() const {
    Status status = Status::OK();
    try {
        std::string version;
        Status status = client_ptr_->Cmd("version", version);
        return version;
    } catch (std::exception& ex) {
        return "";
    }
}

std::string
ClientProxy::ServerStatus() const {
    if (channel_ == nullptr) {
        return "not connected to server";
    }

    try {
        std::string dummy;
        Status status = client_ptr_->Cmd("", dummy);
        return "server alive";
    } catch (std::exception& ex) {
        return "connection lost";
    }
}

Status
ClientProxy::GetConfig(const std::string& node_name, std::string& value) const {
    try {
        return client_ptr_->Cmd("get_config " + node_name, value);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to get config: " + node_name);
    }
}

Status
ClientProxy::SetConfig(const std::string& node_name, const std::string& value) const {
    try {
        std::string dummy;
        return client_ptr_->Cmd("set_config " + node_name + " " + value, dummy);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to set config: " + node_name);
    }
}

Status
ClientProxy::CreateCollection(const CollectionParam& param) {
    try {
        ::milvus::grpc::CollectionSchema schema;
        schema.set_collection_name(param.collection_name);
        schema.set_dimension(param.dimension);
        schema.set_index_file_size(param.index_file_size);
        schema.set_metric_type(static_cast<int32_t>(param.metric_type));

        return client_ptr_->CreateCollection(schema);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to create collection: " + std::string(ex.what()));
    }
}

bool
ClientProxy::HasCollection(const std::string& collection_name) {
    try {
        Status status = Status::OK();
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        return client_ptr_->HasCollection(grpc_collection_name, status);
    } catch (std::exception& ex) {
        return false;
    }
}

Status
ClientProxy::DropCollection(const std::string& collection_name) {
    try {
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        return client_ptr_->DropCollection(grpc_collection_name);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to drop collection: " + std::string(ex.what()));
    }
}

Status
ClientProxy::CreateIndex(const IndexParam& index_param) {
    try {
        ::milvus::grpc::IndexParam grpc_index_param;
        grpc_index_param.set_collection_name(index_param.collection_name);
        grpc_index_param.set_index_type(static_cast<int32_t>(index_param.index_type));
        milvus::grpc::KeyValuePair* kv = grpc_index_param.add_extra_params();
        kv->set_key(EXTRA_PARAM_KEY);
        kv->set_value(index_param.extra_params);
        return client_ptr_->CreateIndex(grpc_index_param);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to build index: " + std::string(ex.what()));
    }
}

Status
ClientProxy::Insert(const std::string& collection_name, const std::string& partition_tag,
                    const std::vector<Entity>& entity_array, std::vector<int64_t>& id_array) {
    Status status = Status::OK();
    try {
        ::milvus::grpc::InsertParam insert_param;
        insert_param.set_collection_name(collection_name);
        insert_param.set_partition_tag(partition_tag);

        for (auto& entity : entity_array) {
            ::milvus::grpc::RowRecord* grpc_record = insert_param.add_row_record_array();
            CopyRowRecord(grpc_record, entity);
        }

        // Single thread
        ::milvus::grpc::VectorIds vector_ids;
        if (!id_array.empty()) {
            /* set user's ids */
            auto row_ids = insert_param.mutable_row_id_array();
            row_ids->Resize(static_cast<int>(id_array.size()), -1);
            memcpy(row_ids->mutable_data(), id_array.data(), id_array.size() * sizeof(int64_t));
            status = client_ptr_->Insert(insert_param, vector_ids);
        } else {
            status = client_ptr_->Insert(insert_param, vector_ids);
            /* return Milvus generated ids back to user */
            id_array.insert(id_array.end(), vector_ids.vector_id_array().begin(), vector_ids.vector_id_array().end());
        }
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to add entities: " + std::string(ex.what()));
    }

    return status;
}

Status
ClientProxy::GetEntityByID(const std::string& collection_name, const std::string& partition_tag,
                           const std::vector<int64_t>& id_array, std::vector<Entity>& entities_data) {
    try {
        entities_data.clear();

        ::milvus::grpc::VectorsIdentity vectors_identity;
        vectors_identity.set_collection_name(collection_name);
        vectors_identity.set_partition_tag(partition_tag);
        for (auto id : id_array) {
            vectors_identity.add_id_array(id);
        }

        ::milvus::grpc::VectorsData grpc_data;
        Status status = client_ptr_->GetEntityByID(vectors_identity, grpc_data);
        if (!status.ok()) {
            return status;
        }

        int vector_count = grpc_data.vectors_data().size();
        for (int i = 0; i < vector_count; i++) {
            const ::milvus::grpc::RowRecord& record = grpc_data.vectors_data(i);
            Entity entity;

            int float_size = record.float_data_size();
            if (float_size > 0) {
                entity.float_data.resize(float_size);
                memcpy(entity.float_data.data(), record.float_data().data(), float_size * sizeof(float));
            }

            auto byte_size = record.binary_data().length();
            if (byte_size > 0) {
                entity.binary_data.resize(byte_size);
                memcpy(entity.binary_data.data(), record.binary_data().data(), byte_size);
            }
            entities_data.emplace_back(entity);
        }

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to get entity by id: " + std::string(ex.what()));
    }
}

Status
ClientProxy::ListIDInSegment(const std::string& collection_name, const std::string& segment_name,
                             std::vector<int64_t>& id_array) {
    try {
        ::milvus::grpc::GetVectorIDsParam param;
        param.set_collection_name(collection_name);
        param.set_segment_name(segment_name);

        ::milvus::grpc::VectorIds vector_ids;
        Status status = client_ptr_->ListIDInSegment(param, vector_ids);
        if (!status.ok()) {
            return status;
        }

        id_array.insert(id_array.end(), vector_ids.vector_id_array().begin(), vector_ids.vector_id_array().end());

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to get ids from segment: " + std::string(ex.what()));
    }
}

Status
ClientProxy::Search(const std::string& collection_name, const std::vector<std::string>& partition_tag_array,
                    const std::vector<Entity>& entity_array, int64_t topk, const std::string& extra_params,
                    TopKQueryResult& topk_query_result) {
    try {
        // step 1: convert vectors data
        ::milvus::grpc::SearchParam search_param;
        ConstructSearchParam(collection_name, partition_tag_array, topk, extra_params, search_param);

        for (auto& entity : entity_array) {
            ::milvus::grpc::RowRecord* row_record = search_param.add_query_record_array();
            CopyRowRecord(row_record, entity);
        }

        // step 2: search vectors
        ::milvus::grpc::TopKQueryResult grpc_result;
        Status status = client_ptr_->Search(search_param, grpc_result);
        if (grpc_result.row_num() == 0) {
            return status;
        }

        // step 3: convert result array
        ConstructTopkResult(grpc_result, topk_query_result);

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to search entities: " + std::string(ex.what()));
    }
}

Status
ClientProxy::GetCollectionInfo(const std::string& collection_name, CollectionParam& collection_param) {
    try {
        ::milvus::grpc::CollectionSchema grpc_schema;

        Status status = client_ptr_->GetCollectionInfo(collection_name, grpc_schema);

        collection_param.collection_name = grpc_schema.collection_name();
        collection_param.dimension = grpc_schema.dimension();
        collection_param.index_file_size = grpc_schema.index_file_size();
        collection_param.metric_type = static_cast<MetricType>(grpc_schema.metric_type());

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to describe collection: " + std::string(ex.what()));
    }
}

Status
ClientProxy::CountEntities(const std::string& collection_name, int64_t& row_count) {
    try {
        Status status;
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        row_count = client_ptr_->CountEntities(grpc_collection_name, status);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to count collection: " + std::string(ex.what()));
    }
}

Status
ClientProxy::ListCollections(std::vector<std::string>& collection_array) {
    try {
        Status status;
        milvus::grpc::CollectionNameList collection_name_list;
        status = client_ptr_->ListCollections(collection_name_list);

        collection_array.resize(collection_name_list.collection_names_size());
        for (uint64_t i = 0; i < collection_name_list.collection_names_size(); ++i) {
            collection_array[i] = collection_name_list.collection_names(i);
        }
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to show collections: " + std::string(ex.what()));
    }
}

Status
ClientProxy::GetCollectionStats(const std::string& collection_name, std::string& collection_stats) {
    try {
        Status status;
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        milvus::grpc::CollectionInfo grpc_collection_stats;
        status = client_ptr_->GetCollectionStats(grpc_collection_name, grpc_collection_stats);

        collection_stats = grpc_collection_stats.json_info();

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to show collection info: " + std::string(ex.what()));
    }
}

Status
ClientProxy::DeleteEntityByID(const std::string& collection_name, const std::string& partition_tag,
                              const std::vector<int64_t>& id_array) {
    try {
        ::milvus::grpc::DeleteByIDParam delete_by_id_param;
        delete_by_id_param.set_collection_name(collection_name);
        delete_by_id_param.set_partition_tag(partition_tag);
        for (auto id : id_array) {
            delete_by_id_param.add_id_array(id);
        }

        return client_ptr_->DeleteEntityByID(delete_by_id_param);
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to delete entity id: " + std::string(ex.what()));
    }
}

Status
ClientProxy::LoadCollection(const std::string& collection_name, PartitionTagList& partition_tag_array) const {
    try {
        ::milvus::grpc::PreloadCollectionParam param;
        param.set_collection_name(collection_name);
        for (auto& tag : partition_tag_array) {
            param.add_partition_tag_array(tag);
        }
        Status status = client_ptr_->LoadCollection(param);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to preload collection: " + std::string(ex.what()));
    }
}

Status
ClientProxy::ReleaseCollection(const std::string& collection_name, PartitionTagList& partition_tag_array) const {
    try {
        ::milvus::grpc::PreloadCollectionParam param;
        param.set_collection_name(collection_name);
        for (auto& tag : partition_tag_array) {
            param.add_partition_tag_array(tag);
        }
        Status status = client_ptr_->ReleaseCollection(param);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to preload collection: " + std::string(ex.what()));
    }
}

Status
ClientProxy::GetIndexInfo(const std::string& collection_name, IndexParam& index_param) const {
    try {
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);

        ::milvus::grpc::IndexParam grpc_index_param;
        Status status = client_ptr_->GetIndexInfo(grpc_collection_name, grpc_index_param);
        index_param.index_type = static_cast<IndexType>(grpc_index_param.index_type());

        for (int i = 0; i < grpc_index_param.extra_params_size(); i++) {
            const milvus::grpc::KeyValuePair& kv = grpc_index_param.extra_params(i);
            if (kv.key() == EXTRA_PARAM_KEY) {
                index_param.extra_params = kv.value();
            }
        }

        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to describe index: " + std::string(ex.what()));
    }
}

Status
ClientProxy::DropIndex(const std::string& collection_name) const {
    try {
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        Status status = client_ptr_->DropIndex(grpc_collection_name);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to drop index: " + std::string(ex.what()));
    }
}

Status
ClientProxy::CreatePartition(const PartitionParam& partition_param) {
    try {
        ::milvus::grpc::PartitionParam grpc_partition_param;
        grpc_partition_param.set_collection_name(partition_param.collection_name);
        grpc_partition_param.set_tag(partition_param.partition_tag);
        Status status = client_ptr_->CreatePartition(grpc_partition_param);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to create partition: " + std::string(ex.what()));
    }
}

bool
ClientProxy::HasPartition(const std::string& collection_name, const std::string& partition_tag) const {
    try {
        Status status = Status::OK();
        ::milvus::grpc::PartitionParam grpc_partition_param;
        grpc_partition_param.set_collection_name(collection_name);
        grpc_partition_param.set_tag(partition_tag);
        return client_ptr_->HasPartition(grpc_partition_param, status);
    } catch (std::exception& ex) {
        return false;
    }
}

Status
ClientProxy::ListPartitions(const std::string& collection_name, PartitionTagList& partition_tag_array) const {
    try {
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        ::milvus::grpc::PartitionList grpc_partition_list;
        Status status = client_ptr_->ListPartitions(grpc_collection_name, grpc_partition_list);
        partition_tag_array.resize(grpc_partition_list.partition_tag_array_size());
        for (uint64_t i = 0; i < grpc_partition_list.partition_tag_array_size(); ++i) {
            partition_tag_array[i] = grpc_partition_list.partition_tag_array(i);
        }
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to show partitions: " + std::string(ex.what()));
    }
}

Status
ClientProxy::DropPartition(const PartitionParam& partition_param) {
    try {
        ::milvus::grpc::PartitionParam grpc_partition_param;
        grpc_partition_param.set_collection_name(partition_param.collection_name);
        grpc_partition_param.set_tag(partition_param.partition_tag);
        Status status = client_ptr_->DropPartition(grpc_partition_param);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to drop partition: " + std::string(ex.what()));
    }
}

Status
ClientProxy::Flush(const std::vector<std::string>& collection_name_array) {
    try {
        if (collection_name_array.empty()) {
            return client_ptr_->Flush("");
        } else {
            for (auto& collection_name : collection_name_array) {
                client_ptr_->Flush(collection_name);
            }
        }
        return Status::OK();
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to flush collection");
    }
}

Status
ClientProxy::Compact(const std::string& collection_name) {
    try {
        ::milvus::grpc::CollectionName grpc_collection_name;
        grpc_collection_name.set_collection_name(collection_name);
        Status status = client_ptr_->Compact(grpc_collection_name);
        return status;
    } catch (std::exception& ex) {
        return Status(StatusCode::UnknownError, "Failed to compact collection: " + std::string(ex.what()));
    }
}

}  // namespace milvus
