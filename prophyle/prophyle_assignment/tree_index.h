#pragma once

#include "knhx.h"
#include <string>
#include <ostream>
#include <unordered_map>
#include <iostream>
#include <vector>

class TreeIndex {
public:
  explicit TreeIndex(const std::string& tree_filename);

  const knhx1_t* root() const {
    return root_;
  }

  const knhx1_t* first_node() const {
    return first_node_;
  }

  int32_t nodes_count() const {
    return nodes_count_;
  }

  const knhx1_t* node_by_id(int32_t id) const {
    return first_node_ + id;
  }

  int32_t id_by_name(const std::string& name) const {
    const auto &node = id_by_name_.find(name);
    if (node == id_by_name_.end()) {
      return -1;
    } else {
      return node->second;
    }
  }

  const std::vector<int32_t>& upper_nodes(int32_t node_id) const {
    return upper_nodes_[node_id];
  }

private:
  void fill_upper_nodes(const knhx1_t* node);

  knhx1_t* first_node_;
  knhx1_t* root_;
  int32_t nodes_count_;
  std::unordered_map<std::string, int32_t> id_by_name_;
  std::vector<std::vector<int32_t>> upper_nodes_;
};

std::ostream& operator<<(std::ostream& sout, const TreeIndex& tree);
