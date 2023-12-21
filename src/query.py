
def query_date_time(from_date: str, to_date: str):
    pipeline = [
    {
        "$match": {
        "create_time": {
            "$gte": from_date,
            "$lte": to_date,

        },

        },

    },
    {
        "$project": {
        "date": {
            "$dateFromString": {
            "format": "%Y-%m-%dT%H:%M:%S.%L",
            "dateString": "$create_time"
            },

        },
        "time": {
            "$hour": {
            "$dateFromString": {
                "dateString": "$create_time"
            }
            }
        },
        "CAM": "$CAM"
        }
    },
    {
        "$project": {
        "date": {
            "$dateToString": {
            "format": "%d/%m/%Y",
            "date": "$date"
            }
        },
        "time": "$time",
        "CAM": "$CAM"
        }
    },
    {
        "$unwind": "$CAM"
    },
    {
        "$group": {
        "_id": {
            "CAM_ID": "$CAM.CAM_ID",
            "Time": "$time",
            "Date": "$date"
        },
        "CAR": {
            "$sum": "$CAM.CAR"
        },
        "TRUCK": {
            "$sum": "$CAM.TRUCK"
        },
        "BUS": {
            "$sum": "$CAM.BUS"
        },
        "TRAILER": {
            "$sum": "$CAM.TRAILER"
        },

        }
    },
    {
        "$sort": {
        "_id.Time": 1
        }
    },
    {
        "$group": {
        "_id": {
            "CAM_ID": "$_id.CAM_ID",
            "Date": "$_id.Date",

        },
        "CAR": {
            "$push": "$CAR"
        },
        "TRUCK": {
            "$push": "$TRUCK"
        },
        "BUS": {
            "$push": "$BUS"
        },
        "TRAILER": {
            "$push": "$TRAILER"
        },
        "Time": {
            "$push": "$_id.Time"
        }
        }
    },
    {
        "$group": {
        "_id": "$_id.CAM_ID",
        "Data": {
            "$push": {
            "Date": "$_id.Date",
            "CAR": "$CAR",
            "TRUCK": "$TRUCK",
            "BUS": "$BUS",
            "TRAILER": "$TRAILER",
            "Time": "$Time"
            }
        }
        }
    },
    {
        "$sort": {
        "_id": 1
        }
    }
    ]

    return pipeline


def get_test_data():
    document = [
        {
            "Data": [
            {
                "Date": "2023-04-20",
                "Time": [
                3
                ],
                "left_bus": [
                20
                ],
                "left_car": [
                10
                ],
                "left_trailer": [
                20
                ],
                "left_truck": [
                20
                ],
                "right_bus": [
                20
                ],
                "right_car": [
                10
                ],
                "right_trailer": [
                20
                ],
                "right_truck": [
                20
                ]
            },
            {
                "Date": "2023-04-22",
                "Time": [
                3
                ],
                "left_bus": [
                20
                ],
                "left_car": [
                10
                ],
                "left_trailer": [
                20
                ],
                "left_truck": [
                20
                ],
                "right_bus": [
                20
                ],
                "right_car": [
                10
                ],
                "right_trailer": [
                20
                ],
                "right_truck": [
                20
                ]
            },
            {
                "Date": "2023-05-22",
                "Time": [
                3,
                4,
                5,
                6
                ],
                "left_bus": [
                28,
                20,
                40,
                20
                ],
                "left_car": [
                21,
                10,
                20,
                10
                ],
                "left_trailer": [
                28,
                20,
                40,
                20
                ],
                "left_truck": [
                23,
                20,
                40,
                20
                ],
                "right_bus": [
                28,
                20,
                40,
                20
                ],
                "right_car": [
                21,
                10,
                20,
                10
                ],
                "right_trailer": [
                28,
                20,
                40,
                20
                ],
                "right_truck": [
                23,
                20,
                40,
                20
                ]
            },
            {
                "Date": "2023-05-23",
                "Time": [
                3,
                4
                ],
                "left_bus": [
                40,
                20
                ],
                "left_car": [
                20,
                10
                ],
                "left_trailer": [
                40,
                20
                ],
                "left_truck": [
                40,
                20
                ],
                "right_bus": [
                40,
                20
                ],
                "right_car": [
                20,
                10
                ],
                "right_trailer": [
                40,
                20
                ],
                "right_truck": [
                40,
                20
                ]
            }
            ],
            "_id": "0"
        },
        {
            "Data": [
            {
                "Date": "2023-04-20",
                "Time": [
                3
                ],
                "left_bus": [
                22
                ],
                "left_car": [
                23
                ],
                "left_trailer": [
                22
                ],
                "left_truck": [
                20
                ],
                "right_bus": [
                22
                ],
                "right_car": [
                23
                ],
                "right_trailer": [
                22
                ],
                "right_truck": [
                20
                ]
            },
            {
                "Date": "2023-04-22",
                "Time": [
                3
                ],
                "left_bus": [
                22
                ],
                "left_car": [
                23
                ],
                "left_trailer": [
                22
                ],
                "left_truck": [
                20
                ],
                "right_bus": [
                22
                ],
                "right_car": [
                23
                ],
                "right_trailer": [
                22
                ],
                "right_truck": [
                20
                ]
            },
            {
                "Date": "2023-05-22",
                "Time": [
                3,
                4,
                5,
                6
                ],
                "left_bus": [
                25,
                20,
                40,
                20
                ],
                "left_car": [
                34,
                10,
                20,
                10
                ],
                "left_trailer": [
                25,
                20,
                40,
                20
                ],
                "left_truck": [
                32,
                20,
                40,
                20
                ],
                "right_bus": [
                25,
                20,
                40,
                20
                ],
                "right_car": [
                34,
                10,
                20,
                10
                ],
                "right_trailer": [
                25,
                20,
                40,
                20
                ],
                "right_truck": [
                32,
                20,
                40,
                20
                ]
            },
            {
                "Date": "2023-05-23",
                "Time": [
                3,
                4
                ],
                "left_bus": [
                40,
                20
                ],
                "left_car": [
                20,
                10
                ],
                "left_trailer": [
                40,
                20
                ],
                "left_truck": [
                40,
                20
                ],
                "right_bus": [
                40,
                20
                ],
                "right_car": [
                20,
                10
                ],
                "right_trailer": [
                40,
                20
                ],
                "right_truck": [
                40,
                20
                ]
            }
            ],
            "_id": "1"
        }
        ]
    return document

       # query = {
        #     "create_time": {
        #         "$gte": from_datetime_str,
        #         "$lte": to_datetime_str
        #     }
        # }
        
        # documents = self.collection.find(query)
        
        # pipeline = [
        #         {
        #             "$match": {
        #             "create_time": {
        #                 "$gte": from_datetime_str,
        #                 "$lte": to_datetime_str, 
        #                 }, 
        #             }, 
        #         },
        #         {
        #             "$unwind": "$CAM"
        #         },
        #         {
        #             "$project": {
        #             "_id": 0,
        #             "time_hour": {
        #                 "$hour": {
        #                 "$dateFromString": {
        #                     "dateString": "$create_time"
        #                     }
        #                 }
        #             },
        #             "CAM_ID": "$CAM.CAM_ID",
        #             "CAR": "$CAM.CAR",
        #             "BUS": "$CAM.BUS",
        #             "TRUCK": "$CAM.TRUCK"
        #             }
        #         },
        #         {
        #             "$group": {
        #             "_id": {
        #                 "time_hour": "$time_hour",
        #                 "CAM_ID": "$CAM_ID"
        #                 },
        #             "CAR": {
        #                 "$sum": "$CAR"
        #                 },
        #             "BUS": {
        #                 "$sum": "$BUS"
        #                 },
        #             "TRUCK": {
        #                 "$sum": "$TRUCK"
        #                 },
                    
        #             }
        #         },
        #         {
        #             "$sort": {
        #             "_id.time_hour": 1
        #             }
        #         },
        #         {
        #             "$group": {
        #             "_id": "$_id.CAM_ID",
        #             "CAR": {
        #                 "$push": "$CAR"
        #                 },
        #             "TRUCK": {
        #                 "$push": "$TRUCK"
        #                 },
        #             "BUS": {
        #                 "$push": "$BUS"
        #                 },
        #             "hours": {
        #                 "$push": "$_id.time_hour"
        #                 }
        #             }
        #         }]