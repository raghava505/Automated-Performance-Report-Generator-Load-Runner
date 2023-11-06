from elasticsearch import Elasticsearch
import datetime

elasticsearch_host = "http://192.168.136.53:5601"

elastic_client = Elasticsearch(hosts=[elasticsearch_host])

this_day = datetime.datetime.now()-datetime.timedelta(days=0)
this_day_date_time_str = this_day.strftime("%Y.%m.%d")
index_name="uptycs-"+this_day_date_time_str

elasticsearch_query = {
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "2023-11-03T15:03:22.265Z",
              "lte": "2023-11-04T15:03:22.265Z",
              "format": "strict_date_optional_time"
            }
          }
        }
      ],
      "filter": [
        {
          "bool": {
            "filter": [
              {
                "bool": {
                  "should": [
                    {
                      "match_phrase": {
                        "log_type": "ruleengine"
                      }
                    }
                  ],
                  "minimum_should_match": 1
                }
              },
              {
                "bool": {
                  "should": [
                    {
                      "match_phrase": {
                        "message": "error"
                      }
                    }
                  ],
                  "minimum_should_match": 1
                }
              }
            ]
          }
        }
      ],
      "should": [],
      "must_not": []
    }
  },
  "aggs": {
    "e3fb4502-e184-4880-a205-41d33ce365b1": {
      "filters": {
        "filters": {
          "e7b3e5c0-17cb-11ed-b19a-873925a4a05f": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Unable to associate yara profile with the alert"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "02876bb0-17cc-11ed-b19a-873925a4a05f": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failed to get"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "410a6b90-1ded-11ed-affa-03dffacbf413": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error in consumer Local"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "53a1d2a0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Returned Zero Rows of querypackQuery"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "53ebace0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Login Error"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "54578e10-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error while setting"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "798e3a30-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error in retrieving "
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "79cec5a0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "No rows returned for"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "7a54be80-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error parsing"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "7b3e5b30-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error returned"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "a546b3a0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error while retrieving"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "a57f9df0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error getting "
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "a5e40510-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error in consumer Broker"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "c3a0a130-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error sending data to"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "c3e2b340-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Delivery failed"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "dc3d7100-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failed to Publish data to"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "dc8d65c0-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failure in Sending events into"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "eaade210-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "error querying column info"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "eaf7bc50-1fb1-11ed-bef5-fb54e2a8069a": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error while getting"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "8160e890-2432-11ed-a3c7-03ede39325a8": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error AssetTags Value returned"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "0b427470-2433-11ed-a3c7-03ede39325a8": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error objectGroup Value returned"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "82589230-3f11-11ed-aa6b-ef1db798c3e5": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "failed to read column info from metastore"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "fb348820-474a-11ee-ba5e-d7d4efd698e0": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Error in Fetching kubernetes cluster info for cluster_id"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "a4b37de0-583d-11ee-ae1b-c570d609d445": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failed to parse exception rule"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "a9593830-583d-11ee-ae1b-c570d609d445": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failed to parse transformation "
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "b2c9c100-583d-11ee-ae1b-c570d609d445": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Failed to parse rule"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "baf100f0-583d-11ee-ae1b-c570d609d445": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "failed to fetch PG_OWNER_USER from hvault: unable to log in to auth method:"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "714e8040-6787-11ee-bc6b-938a1cae5ffb": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "match_phrase": {
                          "message": "Invalid Query Pack tableName"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      },
      "aggs": {
        "timeseries": {
          "auto_date_histogram": {
            "field": "@timestamp",
            "buckets": 1
          },
          "aggs": {
            "bcff0fc3-5801-488a-ae72-a01934538e7d": {
              "bucket_script": {
                "buckets_path": {
                  "count": "_count"
                },
                "script": {
                  "source": "count * 1",
                  "lang": "expression"
                },
                "gap_policy": "skip"
              }
            }
          }
        }
      },
      "meta": {
        "timeField": "@timestamp",
        "panelId": "198b651b-a390-42de-ae46-a84e559f49ff",
        "seriesId": "e3fb4502-e184-4880-a205-41d33ce365b1",
        "intervalString": "86400000ms",
        "dataViewId": "uptycs_logs",
        "indexPatternString": "uptycs-*"
      }
    }
  },
  "runtime_mappings": {},
  "timeout": "30000ms"
}


result = elastic_client.search(index=index_name, body=elasticsearch_query)

print(result)
