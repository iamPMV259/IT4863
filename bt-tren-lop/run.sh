#!/bin/bash
source .venv/bin/activate
python3 hust_rss_spider.py "$1"
python3 hust_detail_spider.py "$1"