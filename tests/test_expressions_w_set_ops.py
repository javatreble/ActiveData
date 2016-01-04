# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals
from __future__ import division

import base_test_class

from pyLibrary.dot import wrap
from pyLibrary.queries.expressions import NullOp
from tests.base_test_class import ActiveDataBaseTest


lots_of_data = wrap([{"a": i} for i in range(30)])


class TestSetOps(ActiveDataBaseTest):

    def test_length(self):
        test = {
            "data": [
                {"v": "1"},
                {"v": "22"},
                {"v": "333"},
                {"v": "4444"},
                {"v": "55555"}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"name": "l", "value": {"length": "v"}},
                "sort": "v"
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [1, 2, 3, 4, 5]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["l"],
                "data": [
                    [1],
                    [2],
                    [3],
                    [4],
                    [5]
                ]
           },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "rownum",
                        "domain": {"type": "rownum", "min": 0, "max": 5, "interval": 1}
                    }
                ],
                "data": {
                    "l": [1, 2, 3, 4, 5]
                }
            }
        }
        self._execute_es_tests(test)

    def test_length_w_inequality(self):
        test = {
            "data": [
                {"v": "1"},
                {"v": "22"},
                {"v": "333"},
                {"v": "4444"},
                {"v": "55555"}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": "v",
                "where": {
                    "gt": [
                        {
                            "length": "v"
                        },
                        2
                    ]
                },
                "sort": "v"
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": ["333", "4444", "55555"]
            }
        }
        self._execute_es_tests(test)

    def test_left(self):
        test = {
            "data": [
                {},
                {"v": "1"},
                {"v": "22"},
                {"v": "333"},
                {"v": "4444"}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"name": "v", "value": {"left": {"v": 2}}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [None, "1", "22", "33", "44"]
            }
        }
        self._execute_es_tests(test)

    def test_eq(self):
        test = {
            "data": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": ".",
                "where": {"eq": ["a", "b"]}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "b": 0},
                    {"a": 1, "b": 1},
                    {}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_ne(self):
        test = {
            "data": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": ".",
                "where": {"ne": ["a", "b"]}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "b": 1},
                    {"a": 1, "b": 0}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_select_when(self):
        test = {
            "data": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": ["a", "b", {"name": "io", "value": {"when": {"eq": ["a", "b"]}, "then": 1, "else": 2}}]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "b": 0, "io": 1},
                    {"a": 0, "b": 1, "io": 2},
                    {"a": 0, "io": 2},
                    {"a": 1, "b": 0, "io": 2},
                    {"a": 1, "b": 1, "io": 1},
                    {"a": 1, "io": 2},
                    {"b": 0, "io": 2},
                    {"b": 1, "io": 2},
                    {"io": 1}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_select_add(self):
        test = {
            "data": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": ["a", "b", {"name": "t", "value": {"add": ["a", "b"]}}]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "b": 0, "t": 0},
                    {"a": 0, "b": 1, "t": 1},
                    {"a": 0, "t": 0},
                    {"a": 1, "b": 0, "t": 1},
                    {"a": 1, "b": 1, "t": 2},
                    {"a": 1, "t": 1},
                    {"b": 0, "t": 0},
                    {"b": 1, "t": 1},
                    {}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_select_add_w_default(self):
        test = {
            "data": [
                {"a": 1, "b": -1},  # DUMMY VALUE TO CREATE COLUMNS
                {}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": ["a", "b", {"name": "t", "value": {"add": ["a", "b"], "default": 0}}]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 1, "b": -1, "t": 0},
                    {"t": 0}
                ]
            }
        }
        self._execute_es_tests(test)


    def test_select_average(self):
        test = {
            "data": [{"a": {"_b": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ]}}],
            "query": {
                "from": base_test_class.settings.backend_es.index+".a._b",
                "select": [
                    {"aggregate": "count"},
                    {"name": "t", "value": {"add": ["a", "b"]}, "aggregate": "average"}
                ],
                "edges": ["a", "b"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "b": 0, "count": 1, "t": 0},
                    {"a": 0, "b": 1, "count": 1, "t": 1},
                    {"a": 0, "count": 1, "t": 0},
                    {"a": 1, "b": 0, "count": 1, "t": 1},
                    {"a": 1, "b": 1, "count": 1, "t": 2},
                    {"a": 1, "count": 1, "t": 1},
                    {"b": 0, "count": 1, "t": 0},
                    {"b": 1, "count": 1, "t": 1},
                    {"t": NullOp(), "count": 1}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_select_average_on_none(self):
        test = {
            "data": [{"a": {"_b": [
                {"a": 0},
                {}
            ]}}],
            "query": {
                "from": base_test_class.settings.backend_es.index+".a._b",
                "select": [
                    {"name": "t", "value": {"add": ["a", "a"]}, "aggregate": "average"}
                ],
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 0, "t": 0},
                    {"t": NullOp()}
                ]
            }
        }
        self._execute_es_tests(test)


    def test_select_gt_on_sub(self):
        test = {
            "data": [{"a": {"_b": [
                {"a": 0, "b": 0},
                {"a": 0, "b": 1},
                {"a": 0},
                {"a": 1, "b": 0},
                {"a": 1, "b": 1},
                {"a": 1},
                {"b": 0},
                {"b": 1},
                {}
            ]}}],
            "query": {
                "from": base_test_class.settings.backend_es.index+".a._b",
                "select": [
                    "a",
                    "b",
                    {"name": "diff", "value": {"sub": ["a", "b"]}}
                ],
                "where": {"gt": [{"sub": ["a", "b"]}, 0]},
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": 1, "b": 0, "diff": 1}
                ]
            }
        }
        self._execute_es_tests(test)

    def test_contains(self):
        test = {
            "data": [
                {"v": "test"},
                {"v": "not test"},
                {"v": None},
                {},
                {"v": "a"}
            ],
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "where": {"contains": {"v": "test"}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"v": "test"},
                    {"v": "not test"}
                ]
            }
        }
        self._execute_es_tests(test)




