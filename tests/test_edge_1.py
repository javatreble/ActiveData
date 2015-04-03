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

from tests.base_test_class import ActiveDataBaseTest


class TestEdge1(ActiveDataBaseTest):

    def test_no_select(self):
        test = {
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "count": 2},
                    {"a": "c", "count": 3},
                    {"a": None, "count": 1}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "count"],
                "data": [
                    ["b", 2],
                    ["c", 3],
                    [None, 1]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "count": [2, 3, 1]
                }
            }
        }
        self._execute_es_tests(test)



    def test_count_rows(self):
        test = {
            "name": "count rows, 1d",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"aggregate": "count"},
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "count": 2},
                    {"a": "c", "count": 3},
                    {"a": None, "count": 1}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "count"],
                "data": [
                    ["b", 2],
                    ["c", 3],
                    [None, 1]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "count": [2, 3, 1]
                }
            }
        }
        self._execute_es_tests(test)

    def test_count_self(self):
        test = {
            "name": "count column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"name": "count_a", "value": "a", "aggregate": "count"},
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "count_a": 2},
                    {"a": "c", "count_a": 3},
                    {"count_a": 0}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "count_a"],
                "data": [
                    ["b", 2],
                    ["c", 3],
                    [None, 0]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "count_a": [2, 3, 0]
                }
            }
        }
        self._execute_es_tests(test)

    def test_count_other(self):
        test = {
            "name": "count column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"name": "count_v", "value": "v", "aggregate": "count"},
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "count_v": 1},
                    {"a": "c", "count_v": 3},
                    {"count_v": 1}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "count_v"],
                "data": [
                    ["b", 1],
                    ["c", 3],
                    [None, 1]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "count_v": [1, 3, 1]
                }
            }
        }
        self._execute_es_tests(test)

    def test_select_2(self):
        test = {
            "name": "count column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": [
                    {"name": "count", "value": "v", "aggregate": "count"},
                    {"name": "avg", "value": "v", "aggregate": "average"}
                ],
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "count": 1, "avg": 2},
                    {"a": "c", "count": 3, "avg": 31 / 3},
                    {"count": 1, "avg": 3}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "count", "avg"],
                "data": [
                    ["b", 1, 2],
                    ["c", 3, 31 / 3],
                    [None, 1, 3]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "count": [1, 3, 1],
                    "avg": [2, 31 / 3, 3]
                }
            }
        }
        self._execute_es_tests(test)

    def test_sum_column(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "sum"},
                "edges": ["a"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "v": 2},
                    {"a": "c", "v": 31},
                    {"a": None, "v": 3}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "v"],
                "data": [
                    ["b", 2],
                    ["c", 31],
                    [None, 3]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": True,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "v": [2, 31, 3]
                }
            }
        }
        self._execute_es_tests(test)

    def test_where(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": ["a"],
                "where": {"term": {"a": "c"}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "c", "v": 13},
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "v"],
                "data": [
                    ["c", 13]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "v": [13]
                }
            }
        }
        self._execute_es_tests(test)

    def test_where_w_dimension(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": [
                    {"value": "a", "allowNulls": False, "domain": {"type": "set", "partitions": ["b", "c"]}}
                ],
                "where": {"term": {"a": "c"}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "b", "v": None},
                    {"a": "c", "v": 13}
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "v"],
                "data": [
                    ["b", None],
                    ["c", 13]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [{"value": "b"}, {"value": "c"}]
                        }
                    }
                ],
                "data": {
                    "v": [None, 13],
                }
            }
        }
        self._execute_es_tests(test)

    def test_empty_default_domain(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": simple_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": ["a"],
                "where": {"term": {"a": "d"}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "v"],
                "data": []
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "a",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": []
                        }
                    }
                ],
                "data": {
                    "v": []
                }
            }
        }
        self._execute_es_tests(test)


    def test_wo_limit(self):
        """
        TESTING THAT THE DEFAULT LIMIT IS APPLIED
        """
        test = {
            "name": "sum column",
            "metadata": {},
            "data": long_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": ["k"]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"k": "a", "v": 1},
                    {"k": "b", "v": 2},
                    {"k": "c", "v": 3},
                    {"k": "d", "v": 4},
                    {"k": "e", "v": 5},
                    {"k": "f", "v": 6},
                    {"k": "g", "v": 7},
                    {"k": "h", "v": 8},
                    {"k": "i", "v": 9},
                    {"k": "j", "v": 10}
                ]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["k", "v"],
                "data": [
                    ["a", 1],
                    ["b", 2],
                    ["c", 3],
                    ["d", 4],
                    ["e", 5],
                    ["f", 6],
                    ["g", 7],
                    ["h", 8],
                    ["i", 9],
                    ["j", 10]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "k",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [
                                {"value": "a"},
                                {"value": "b"},
                                {"value": "c"},
                                {"value": "d"},
                                {"value": "e"},
                                {"value": "f"},
                                {"value": "g"},
                                {"value": "h"},
                                {"value": "i"},
                                {"value": "j"}
                            ]
                        }
                    }
                ],
                "data": {
                    "v": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                }
            }
        }
        self._execute_es_tests(test)

    def test_edge_limit_big(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": long_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": [{"value": "k", "domain": {"type": "default", "limit": 100}}]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"k": "a", "v": 1},
                    {"k": "b", "v": 2},
                    {"k": "c", "v": 3},
                    {"k": "d", "v": 4},
                    {"k": "e", "v": 5},
                    {"k": "f", "v": 6},
                    {"k": "g", "v": 7},
                    {"k": "h", "v": 8},
                    {"k": "i", "v": 9},
                    {"k": "j", "v": 10},
                    {"k": "k", "v": 11},
                    {"k": "l", "v": 12},
                    {"k": "m", "v": 13}
                ]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["k", "v"],
                "data": [
                    ["a", 1],
                    ["b", 2],
                    ["c", 3],
                    ["d", 4],
                    ["e", 5],
                    ["f", 6],
                    ["g", 7],
                    ["h", 8],
                    ["i", 9],
                    ["j", 10],
                    ["k", 11],
                    ["l", 12],
                    ["m", 13]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "k",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [
                                {"value": "a"},
                                {"value": "b"},
                                {"value": "c"},
                                {"value": "d"},
                                {"value": "e"},
                                {"value": "f"},
                                {"value": "g"},
                                {"value": "h"},
                                {"value": "i"},
                                {"value": "j"},
                                {"value": "k"},
                                {"value": "l"},
                                {"value": "m"}
                            ]
                        }
                    }
                ],
                "data": {
                    "v": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                }
            }
        }
        self._execute_es_tests(test)

    def test_edge_limit_small(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": long_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": [{"value": "k", "domain": {"type": "default", "limit": 1}}]
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"k": "a", "v": 1}
                ]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["k", "v"],
                "data": [
                    ["a", 1]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "k",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [
                                {"value": "a"}
                            ]
                        }
                    }
                ],
                "data": {
                    "v": [1]
                }
            }
        }
        self._execute_es_tests(test)

    def test_general_limit(self):
        test = {
            "name": "sum column",
            "metadata": {},
            "data": long_test_data,
            "query": {
                "from": base_test_class.settings.backend_es.index,
                "select": {"value": "v", "aggregate": "max"},
                "edges": [{"value": "k", "domain": {"type": "default"}}],
                "limit": 5
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"k": "a", "v": 1},
                    {"k": "b", "v": 2},
                    {"k": "c", "v": 3},
                    {"k": "d", "v": 4},
                    {"k": "e", "v": 5}
                ]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["k", "v"],
                "data": [
                    ["a", 1],
                    ["b", 2],
                    ["c", 3],
                    ["d", 4],
                    ["e", 5]
                ]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "k",
                        "allowNulls": False,
                        "domain": {
                            "type": "set",
                            "key": "value",
                            "partitions": [
                                {"value": "a"},
                                {"value": "b"},
                                {"value": "c"},
                                {"value": "d"},
                                {"value": "e"}
                            ]
                        }
                    }
                ],
                "data": {
                    "v": [1, 2, 3, 4, 5]
                }
            }
        }
        self._execute_es_tests(test)


simple_test_data = [
    {"a": "c", "v": 13},
    {"a": "b", "v": 2},
    {"v": 3},
    {"a": "b"},
    {"a": "c", "v": 7},
    {"a": "c", "v": 11}
]

long_test_data = [
    {"k": "a", "v": 1},
    {"k": "b", "v": 2},
    {"k": "c", "v": 3},
    {"k": "d", "v": 4},
    {"k": "e", "v": 5},
    {"k": "f", "v": 6},
    {"k": "g", "v": 7},
    {"k": "h", "v": 8},
    {"k": "i", "v": 9},
    {"k": "j", "v": 10},
    {"k": "k", "v": 11},
    {"k": "l", "v": 12},
    {"k": "m", "v": 13}
]


